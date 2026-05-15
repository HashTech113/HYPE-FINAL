"""RTSP frame reader with drop-old buffering and resilient reconnect.

Each instance owns a dedicated background thread that drives
`cv2.VideoCapture.read()` at the camera's native rate. Only the most
recent decoded frame is kept; older frames are dropped immediately. The
`read()` method returns that latest frame without blocking.

Why this matters: OpenCV's FFmpeg-backed RTSP capture has an internal
queue we can't bound (`CAP_PROP_BUFFERSIZE` is a UVC flag, ignored by
the FFmpeg backend for RTSP). If the consumer reads slower than the
camera streams, every read returns a progressively older frame —
the live preview drifts seconds behind real time and "teleports" when
it eventually catches up. Draining the socket on a dedicated thread
gives us predictable end-to-end latency (~camera frame interval) at
the cost of one more thread per camera.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any

import cv2
import numpy as np

from app.config import get_settings
from app.core.logger import get_logger

log = get_logger(__name__)

# RTSP capture options:
#   * rtsp_transport=tcp — UDP fails on most enterprise networks
#   * stimeout=2000000us (2s) — bound how long FFmpeg blocks on a stalled read
#   * threads=1 — single-threaded h264 decoder. CRITICAL when the stall
#     watchdog releases `cv2.VideoCapture` from a non-reader thread:
#     FFmpeg's multi-thread frame decoder asserts (`pthread_frame.c:173`,
#     "fctx->async_lock failed") if release happens while another thread
#     is inside a frame-decode worker. Single-thread decoding is plenty
#     fast for ~720p sub-streams and avoids the entire class of crash.
os.environ.setdefault(
    "OPENCV_FFMPEG_CAPTURE_OPTIONS",
    "rtsp_transport;tcp|stimeout;2000000|threads;1",
)


class RTSPReader:
    """Always-fresh RTSP frame source.

    `read()` is non-blocking and returns the latest decoded frame, or
    `None` if the stream is currently disconnected (the background
    thread will keep trying to reconnect with exponential backoff).
    Each returned frame is a fresh copy — safe to pass to other threads
    or mutate in place.
    """

    def __init__(self, url: str, name: str) -> None:
        self.url = url
        self.name = name

        self._stop = threading.Event()
        self._frame_lock = threading.Lock()
        self._latest_frame: np.ndarray | None = None
        self._latest_at_monotonic: float = 0.0
        self._latest_seq: int = 0
        self._frames_dropped: int = 0
        self._last_error: str | None = None
        # When the current cap was opened. Reset on every reconnect.
        # Watchdog uses this to detect "open but never produced a
        # first frame" — the failure mode that hung Entry 2 silently
        # for 3.5h. 0.0 means no cap currently open.
        self._cap_opened_at_monotonic: float = 0.0

        # Shared reference to the active VideoCapture. The reader thread
        # owns it; the watchdog thread reads it (under `_cap_lock`) so it
        # can call `release()` to unblock a hung native read() — releasing
        # cap from another thread is the only documented way to escape
        # FFmpeg's blocking read in a stuck-stream scenario.
        self._cap: cv2.VideoCapture | None = None
        self._cap_lock = threading.Lock()

        self._thread = threading.Thread(
            target=self._reader_loop,
            name=f"rtsp-{name}",
            daemon=True,
        )
        self._thread.start()
        self._watchdog = threading.Thread(
            target=self._watchdog_loop,
            name=f"rtsp-{name}-wd",
            daemon=True,
        )
        self._watchdog.start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def frames_dropped(self) -> int:
        return self._frames_dropped

    def read(self) -> np.ndarray | None:
        """Return the latest decoded frame, or None if disconnected.

        Never blocks waiting for a new frame. Always returns a fresh
        copy so callers can mutate or hand off without coordination.
        """
        with self._frame_lock:
            if self._latest_frame is None:
                return None
            return self._latest_frame.copy()

    def latest_age_seconds(self) -> float | None:
        """Time since the last decoded frame landed in the buffer."""
        with self._frame_lock:
            if self._latest_at_monotonic <= 0.0:
                return None
            return max(0.0, time.monotonic() - self._latest_at_monotonic)

    def stop(self) -> None:
        self._stop.set()
        # Force-release any active cap so a blocked read() returns.
        with self._cap_lock:
            if self._cap is not None:
                self._safe_release(self._cap)
                self._cap = None
        self._thread.join(timeout=5.0)
        self._watchdog.join(timeout=2.0)

    # ------------------------------------------------------------------
    # Internal — background reader
    # ------------------------------------------------------------------

    def _reader_loop(self) -> None:
        """Drive cv2.VideoCapture flat-out, keep only the latest frame."""
        # Start backoff small (300 ms) so a transient network blip heals
        # in well under a second instead of the original 1 s base which
        # combined with FFmpeg connect-timeout produced 5+ s "stuck"
        # tiles. Exponential growth still kicks in if the camera is
        # genuinely down — capped by RTSP_RECONNECT_MAX_SECONDS.
        backoff = 0.3
        while not self._stop.is_set():
            cap = self._open()
            if cap is None:
                self._sleep_with_backoff(backoff)
                backoff = min(
                    backoff * 2,
                    float(get_settings().RTSP_RECONNECT_MAX_SECONDS),
                )
                continue
            backoff = 0.3
            with self._cap_lock:
                self._cap = cap
            # Stamp the open time so the watchdog can detect a cap
            # that's open but never produced a first frame.
            with self._frame_lock:
                self._cap_opened_at_monotonic = time.monotonic()

            # Schedule a proactive reconnect for this cap. Long-uptime
            # FFmpeg sessions accumulate decoder + demuxer state that
            # eventually leaks (visible as creeping latency or memory
            # growth over days). Cycling the cap once every N hours
            # keeps the backend sharp without operator intervention.
            recycle_hours = float(getattr(get_settings(), "RTSP_RECYCLE_HOURS", 6.0))
            recycle_at = time.monotonic() + max(300.0, recycle_hours * 3600.0)

            while not self._stop.is_set():
                try:
                    ok, frame = cap.read()
                except Exception as exc:
                    self._last_error = f"read exc: {exc}"
                    log.warning("[%s] RTSP read exception: %s", self.name, exc)
                    break

                if not ok or frame is None:
                    self._last_error = "empty frame"
                    log.warning(
                        "[%s] RTSP read returned empty; reconnecting",
                        self.name,
                    )
                    break

                now = time.monotonic()
                with self._frame_lock:
                    if self._latest_frame is not None:
                        self._frames_dropped += 1
                    self._latest_frame = frame
                    self._latest_at_monotonic = now
                    self._latest_seq += 1

                if now >= recycle_at:
                    log.info(
                        "[%s] proactive reconnect after %.1fh uptime",
                        self.name,
                        recycle_hours,
                    )
                    break

            # Inner loop broke — clean up cap (watchdog may have already
            # released it; double-release is safe via _safe_release).
            with self._cap_lock:
                if self._cap is cap:
                    self._cap = None
            with self._frame_lock:
                self._cap_opened_at_monotonic = 0.0
            self._safe_release(cap)

        with self._cap_lock:
            if self._cap is not None:
                self._safe_release(self._cap)
                self._cap = None

    def _watchdog_loop(self) -> None:
        """Force-reconnect when the reader hasn't produced a frame in
        `RTSP_FRAME_STALL_SECONDS` despite holding an open cap.

        Two stall classes are distinguished:

          * Post-first-frame stall — `_latest_at_monotonic > 0` and no
            new frame in `stall` seconds. Classic mid-stream hang.
          * Never-first-frame stall — cap has been open for `stall * 2`
            seconds without ever producing a frame. This is the
            "Entry 2" failure mode: FFmpeg returned a cap from
            VideoCapture(), the TCP handshake succeeded, but no media
            ever arrived. The previous code SKIPPED this case (the
            `if last_at <= 0.0: continue` guard) and the cap could sit
            stuck for HOURS. We now treat it as a stall — release and
            let the reader reopen.

        FFmpeg's `stimeout` covers most stuck-read cases, but some
        misbehaving cameras keep the TCP socket alive while sending no
        media (corrupt SDP renegotiation, codec resync). Releasing the
        cap from this thread unblocks the reader's pending `read()`
        immediately — much better than waiting on the OS keepalive.
        """
        while not self._stop.is_set():
            stall = float(get_settings().RTSP_FRAME_STALL_SECONDS)
            # No-first-frame stall is a separate (longer) horizon: give
            # the camera time to negotiate codec / IDR / SDP before we
            # force-cycle. Without this we'd kick a cap during a slow
            # but legitimate startup. 2× stall is conservative.
            no_first_frame_stall = stall * 2.0

            self._stop.wait(min(1.0, stall / 2))
            if self._stop.is_set():
                return

            with self._frame_lock:
                last_at = self._latest_at_monotonic
                opened_at = self._cap_opened_at_monotonic

            now = time.monotonic()
            stuck_reason: str | None = None
            stuck_age: float = 0.0

            if last_at > 0.0:
                age = now - last_at
                if age >= stall:
                    stuck_reason = "no fresh frame"
                    stuck_age = age
            elif opened_at > 0.0:
                # Cap is open but never produced a frame — the silent-
                # death case that hung Entry 2 for 3.5h.
                age = now - opened_at
                if age >= no_first_frame_stall:
                    stuck_reason = "open but no first frame"
                    stuck_age = age

            if stuck_reason is None:
                continue

            with self._cap_lock:
                cap = self._cap
                self._cap = None
            if cap is not None:
                log.warning(
                    "[%s] watchdog: %.1fs (%s) — releasing cap",
                    self.name,
                    stuck_age,
                    stuck_reason,
                )
                self._safe_release(cap)
                self._last_error = (
                    f"stalled {stuck_age:.1f}s ({stuck_reason}) — reconnecting"
                )

    def _open(self) -> cv2.VideoCapture | None:
        settings = get_settings()
        try:
            cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
            try:
                cap.set(
                    cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,
                    settings.RTSP_CONNECT_TIMEOUT_MS,
                )
                cap.set(
                    cv2.CAP_PROP_READ_TIMEOUT_MSEC,
                    settings.RTSP_READ_TIMEOUT_MS,
                )
            except Exception:
                pass
            try:
                # Hint only — FFmpeg backend ignores it for RTSP. The
                # real drop-old behavior is handled by the reader loop
                # always overwriting the latest frame in our own buffer.
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass
            if not cap.isOpened():
                cap.release()
                self._last_error = "open failed"
                return None
            self._last_error = None
            log.info("[%s] RTSP opened", self.name)
            return cap
        except Exception as exc:
            self._last_error = f"open exc: {exc}"
            log.warning("[%s] RTSP open failed: %s", self.name, exc)
            return None

    @staticmethod
    def _safe_release(cap: cv2.VideoCapture) -> None:
        try:
            cap.release()
        except Exception:
            pass

    def _sleep_with_backoff(self, delay: float) -> None:
        self._stop.wait(delay)

    # ------------------------------------------------------------------
    # Context manager (kept for backward compat with old call sites)
    # ------------------------------------------------------------------

    def __enter__(self) -> RTSPReader:
        return self

    def __exit__(self, *_: Any) -> None:
        self.stop()
