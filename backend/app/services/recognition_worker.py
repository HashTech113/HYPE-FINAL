"""Per-camera recognition worker (Path B Stage 4).

Each active camera in the ``cameras`` table gets one daemon thread that:

1. Opens its RTSP URL via ``cv2.VideoCapture``
2. Reads one frame every ~1/CAMERA_FPS seconds
3. Runs the shared :class:`FaceService` to detect faces
4. Asks :class:`RecognitionService` to match each face's embedding
5. On a match that clears the per-employee cooldown, calls
   ``record_capture()`` so the row lands in ``snapshot_logs`` /
   ``attendance_logs`` and Live Captures picks it up.

Failure isolation: every per-camera loop has its own try/except so one
flaky camera can't take down the others. RTSP drops trigger a bounded
exponential backoff (1, 2, 4, 8, 16, 30 capped) before re-opening.

Coexists with the legacy ``capture.py`` Hikvision-API poller — the
recognition worker reads RTSP directly without disturbing it. Both
write to the same tables, so until the operator disables one, you'll
get two snapshot rows per detection.
"""

from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import quote

import cv2
import numpy as np

# Force RTSP-over-TCP for all cv2.VideoCapture calls in this process.
# Default is UDP, which on a typical Ethernet/Wi-Fi LAN drops enough
# packets to corrupt HEVC reference frames — that's the source of the
# "Could not find ref with POC ..." / "cu_qp_delta out of range" decoder
# warnings. TCP is slightly higher latency but eliminates the drops.
# Set BEFORE the first VideoCapture is constructed (i.e. at module load).
os.environ.setdefault(
    "OPENCV_FFMPEG_CAPTURE_OPTIONS",
    "rtsp_transport;tcp|stimeout;5000000",
)

from ..config import CAPTURE_INTERVAL_SECONDS
from ..db import session_scope
from ..models import Camera as CameraModel
from . import live_frames
from . import logs as logs_service
from .face_service import FaceRecognitionError, get_face_service
from .recognition import get_cooldown, get_recognition_service

log = logging.getLogger(__name__)

# Bounded exponential backoff between RTSP reconnect attempts.
_BACKOFF_BASE = 1.0
_BACKOFF_MAX = 30.0
# How long to wait for VideoCapture.read() before treating the frame as
# missing. The cv2 read itself can block ~indefinitely on a half-open
# socket — the wallclock check below is the actual safeguard.
_READ_DEADLINE_SECONDS = 5.0


@dataclass
class WorkerStatus:
    camera_id: str
    name: str
    rtsp_url: str  # masked
    running: bool = False
    connected: bool = False
    frames_read: int = 0
    faces_detected: int = 0
    matches_recorded: int = 0
    last_frame_at: Optional[float] = None     # monotonic
    last_match_at: Optional[float] = None     # monotonic
    last_error: Optional[str] = None
    backoff_seconds: float = 0.0


@dataclass
class _CameraJob:
    """The minimum we need to feed a worker — pulled from the cameras
    table and crypto-decrypted ahead of time so the worker never has
    to touch the DB during its hot loop."""
    id: str
    name: str
    rtsp_url: str  # full credential URL
    rtsp_url_masked: str


def _build_job_from_row(row: CameraModel) -> _CameraJob:
    """Decrypt the camera's password and assemble a ready-to-use RTSP
    URL. Matches the layout services/cameras.py uses for masked_rtsp_url."""
    from . import crypto
    pw = ""
    try:
        pw = crypto.decrypt(str(row.password_encrypted or ""))
    except Exception:
        # If the key is missing or rotated we still want the worker
        # to attempt a no-credential URL — useful for streams that
        # don't require auth and for surfacing the issue in the
        # status object instead of crashing here.
        log.warning("could not decrypt password for camera %s", row.name)
    path = (
        row.rtsp_path if str(row.rtsp_path or "").startswith("/")
        else f"/{row.rtsp_path or ''}"
    )
    user = str(row.username or "").strip()
    if user:
        # URL-encode user + password so characters that have meaning in
        # RTSP URIs ('@', ':', '/', etc.) don't break parsing. The
        # camera-services builder uses the same pattern via
        # ``cameras_service.build_rtsp_url`` — without this the worker
        # silently fails auth on any camera whose password contains
        # '@' / ':' / etc., even though the matching MJPEG endpoint
        # (built via the service helper) succeeds.
        enc_user = quote(user, safe="")
        enc_pw = quote(pw, safe="")
        full = f"rtsp://{enc_user}:{enc_pw}@{row.ip}:{row.port}{path}"
        masked = f"rtsp://{user}:****@{row.ip}:{row.port}{path}"
    else:
        full = f"rtsp://{row.ip}:{row.port}{path}"
        masked = full
    return _CameraJob(
        id=str(row.id),
        name=str(row.name),
        rtsp_url=full,
        rtsp_url_masked=masked,
    )


class RecognitionWorker:
    """Owns one camera's read+detect+match loop in a daemon thread."""

    def __init__(self, job: _CameraJob) -> None:
        self.job = job
        self.status = WorkerStatus(
            camera_id=job.id, name=job.name, rtsp_url=job.rtsp_url_masked,
        )
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        # Each worker keeps its OWN cv2.VideoCapture; opencv's capture
        # state is per-instance and not safe to share across threads.
        self._cap: Optional[cv2.VideoCapture] = None
        # Each worker uses the shared FaceService singleton — a single
        # GIL-bound process means concurrent detects are serialised by
        # FaceService's internal lock anyway. Per-camera FaceService
        # instances would help on GPU but offer nothing on CPU.
        self._face = get_face_service()
        self._recog = get_recognition_service()
        # Keeps the latest decoded frame (BGR) so external callers (the
        # /training/capture endpoint) can snap a still without having to
        # open a second RTSP socket. Locked because a reader can race
        # the worker's loop overwriting the slot.
        self._latest_frame: Optional[np.ndarray] = None
        self._latest_frame_at: Optional[float] = None
        self._latest_frame_lock = threading.Lock()
        # Structured detection cache for the JSON live-view endpoint —
        # populated on every inference pass with the bbox/name/score for
        # every face in the most recent frame (matched AND unmatched).
        # The live MJPEG already paints these onto the JPEG bytes; this
        # field exposes them as JSON so the React UI can render a
        # separate detection list with confidence numbers.
        self._latest_detections: list[dict] = []
        self._latest_detections_at: Optional[float] = None
        self._latest_detections_lock = threading.Lock()

    def latest_detections(self) -> tuple[list[dict], Optional[float]]:
        """Return (detections_list, monotonic_ts) for the most recent
        inference pass. Returns an empty list when no inference has run
        yet. Detection dicts have the keys: bbox, name, employee_id,
        score, matched."""
        with self._latest_detections_lock:
            return list(self._latest_detections), self._latest_detections_at

    def latest_frame(self) -> tuple[Optional[np.ndarray], Optional[float]]:
        """Return a copy of the most recent frame + the monotonic clock
        timestamp it was captured at, or (None, None) if no frame has
        been read yet. Returns a copy so the caller can mutate freely
        without racing the reader loop."""
        with self._latest_frame_lock:
            if self._latest_frame is None:
                return None, None
            return self._latest_frame.copy(), self._latest_frame_at

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name=f"recog-{self.job.name}", daemon=True,
        )
        self._thread.start()
        self.status.running = True
        log.info("recognition worker start: %s rtsp=%s", self.job.name, self.job.rtsp_url_masked)

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        cap = self._cap
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        self.status.running = False
        self.status.connected = False
        # Drop any buffered annotated frame so the MJPEG endpoint falls
        # back to direct RTSP (or nothing) instead of replaying the last
        # frame this worker captured.
        live_frames.clear(self.job.id)
        log.info("recognition worker stop: %s", self.job.name)

    def _open(self) -> bool:
        try:
            cap = cv2.VideoCapture(self.job.rtsp_url, cv2.CAP_FFMPEG)
        except Exception as exc:
            self.status.last_error = f"cv2.VideoCapture init failed: {exc}"
            return False
        if not cap or not cap.isOpened():
            self.status.last_error = "RTSP open failed"
            try:
                cap.release()
            except Exception:
                pass
            return False
        # Tell the decoder to keep at most 1 frame queued. Without this,
        # cv2 buffers ~25 FPS HEVC internally while we only read 8 FPS —
        # the backlog grows, decoder falls behind, .read() stalls long
        # enough for ``live_frames`` to mark the camera as idle and the
        # MJPEG endpoint closes. Some FFMPEG builds ignore this and the
        # call returns False; we don't treat that as fatal.
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        self._cap = cap
        self.status.connected = True
        self.status.last_error = None
        return True

    def _close(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        self.status.connected = False

    def _run(self) -> None:
        attempt = 0
        try:
            while not self._stop.is_set():
                if not self._open():
                    attempt += 1
                    backoff = min(_BACKOFF_MAX, _BACKOFF_BASE * (2 ** min(attempt, 5)))
                    self.status.backoff_seconds = backoff
                    log.warning(
                        "recog %s: RTSP unreachable (attempt %d) — retry in %.1fs",
                        self.job.name, attempt, backoff,
                    )
                    self._stop.wait(backoff)
                    continue
                attempt = 0
                self.status.backoff_seconds = 0.0
                self._loop_until_disconnect()
                # Loop returns when the stream goes silent; close + retry.
                self._close()
        except Exception:
            log.exception("recognition worker crashed: %s", self.job.name)
            self.status.last_error = "worker crashed (see logs)"
            self.status.running = False
        finally:
            self._close()

    def _loop_until_disconnect(self) -> None:
        """Two cadences, one thread:

        * **Frame cadence (~8 FPS)** — read RTSP, draw the last known
          bounding boxes/names on a copy, JPEG-encode, and publish to
          the live-frame cache. Cheap operation (~5-10 ms / frame), so
          /cameras/live looks smooth and the cache stays well within
          ``live_frames.STALE_AFTER_SECONDS``.
        * **Inference cadence (~CAPTURE_INTERVAL_SECONDS)** — actually
          run face detection + recognition match + snapshot logging.
          Expensive (~50-300 ms / frame), so we throttle it. Between
          inference passes we reuse the previous detection set to draw
          the overlay — boxes lag the subject slightly but the video
          itself stays smooth.

        Snapshot logging + cooldown behavior is unchanged: a row lands
        in ``snapshot_logs`` only when an inference pass produces a
        match that clears the per-employee cooldown.
        """
        cap = self._cap
        assert cap is not None
        # 20 FPS live-feed cadence — frame_period bounds the publish loop,
        # NOT the (heavier) face-detection cadence which still runs at
        # ``RecognitionConfig.camera_fps`` (typically 1–4 FPS). Bumping
        # this from 8 to 20 makes the MJPEG visibly smooth without
        # touching inference cost: between detections we just re-draw
        # the most recent ``last_faces_with_match`` overlays on the new
        # frame, which is cheap.
        frame_period = 1.0 / 20.0
        # Downscale ceiling for the published JPEG. Full-res 2560×1440
        # encodes at ~150–300 KB per frame; at 20 FPS that's ~3–6 MB/s
        # per camera. Capping the published frame at 1280 px wide cuts
        # encode cost ~4× (a key budget freer when several cameras share
        # one CPU) and proportionally drops bandwidth — face detection
        # already ran at the original resolution so accuracy is unchanged.
        live_publish_max_width = 1280
        cooldown = get_cooldown()
        # Carry detections from one inference pass to subsequent frames
        # so the overlay stays drawn even on frames where we didn't
        # re-run detection.
        last_faces_with_match: list[tuple] = []
        next_detect_at = 0.0  # ``time.monotonic()`` threshold

        # Track time of last successful read separately from per-iteration t0
        # so a long string of fast-failing reads (camera reachable on TCP but
        # the RTSP session is half-dead) trips the deadline and triggers a
        # reconnect via _run()'s outer loop. Previously the check measured
        # only the current call's blocking time, so quick consecutive
        # False/None returns reset the clock on every iteration and the worker
        # could spin silently for hours with no `last_error` and no recovery.
        last_success = time.monotonic()
        while not self._stop.is_set():
            t0 = time.monotonic()
            ok, frame = cap.read()
            read_blocked_for = time.monotonic() - t0
            if not ok or frame is None:
                # Bail and let the outer loop reconnect when EITHER:
                #   * the single read blocked past the per-call deadline
                #     (FFmpeg is hung on a dead socket), OR
                #   * we've been failing for the cumulative deadline
                #     since the last good frame (half-dead session).
                stalled_for = time.monotonic() - last_success
                if read_blocked_for > _READ_DEADLINE_SECONDS:
                    self.status.last_error = f"RTSP read blocked >{_READ_DEADLINE_SECONDS:.0f}s"
                    log.warning(
                        "recog %s: RTSP read blocked %.1fs — forcing reconnect",
                        self.job.name, read_blocked_for,
                    )
                    return
                if stalled_for > _READ_DEADLINE_SECONDS:
                    self.status.last_error = (
                        f"RTSP read failed for {stalled_for:.0f}s — reconnecting"
                    )
                    log.warning(
                        "recog %s: RTSP read stalled %.1fs — reconnecting",
                        self.job.name, stalled_for,
                    )
                    return
                self._stop.wait(0.2)
                continue
            last_success = time.monotonic()
            # Clear any prior reconnect/error message now that we're reading
            # successfully again — operators see a single rolling status
            # rather than a stuck "RTSP read failed" message.
            if self.status.last_error and "RTSP read" in self.status.last_error:
                self.status.last_error = None
            self.status.frames_read += 1
            self.status.last_frame_at = time.monotonic()
            with self._latest_frame_lock:
                self._latest_frame = frame
                self._latest_frame_at = self.status.last_frame_at

            # ----- Inference cadence: heavy work, throttled to camera_fps -----
            if t0 >= next_detect_at:
                # Read live settings (TTL-cached, so this is sub-ms).
                # `camera_fps` controls detection cadence; `recognize_min_
                # face_size_px` filters out distant faces too small for a
                # reliable embedding match.
                from .recognition_config import get_recognition_settings
                rcfg = get_recognition_settings()
                detect_interval = 1.0 / float(max(1, rcfg.camera_fps))
                min_size_px = int(rcfg.recognize_min_face_size_px)
                try:
                    faces = self._face.detect(frame)
                except FaceRecognitionError as exc:
                    self.status.last_error = f"detect: {exc}"
                    log.warning("recog %s: face detect failed: %s", self.job.name, exc)
                    faces = []
                except Exception as exc:
                    self.status.last_error = f"detect crashed: {exc}"
                    log.exception("recog %s: face detect crashed", self.job.name)
                    faces = []

                if min_size_px > 0 and faces:
                    faces = [
                        f for f in faces
                        if min(f.bbox[2] - f.bbox[0], f.bbox[3] - f.bbox[1]) >= min_size_px
                    ]

                self.status.faces_detected += len(faces)

                # Resolve match results for EVERY detected face (matched
                # or unknown) — cooldown only gates whether we *log* to
                # snapshot_logs, not whether we draw an overlay box. The
                # operator needs to see "Unknown" boxes for un-enrolled
                # people too.
                from .embedding_cache import get_embedding_cache
                id_to_name = get_embedding_cache().id_to_name_map()
                new_faces_with_match: list[tuple] = []
                unmatched_faces: list = []
                structured: list[dict] = []
                for face in faces:
                    result = self._recog.match(face.embedding)
                    if result.employee_id:
                        name = id_to_name.get(result.employee_id, result.employee_id)
                        new_faces_with_match.append((face.bbox, name, result.score, result.employee_id))
                        structured.append({
                            "bbox": [int(face.bbox[0]), int(face.bbox[1]), int(face.bbox[2]), int(face.bbox[3])],
                            "name": name,
                            "employee_id": result.employee_id,
                            "score": float(result.score),
                            "matched": True,
                        })
                    else:
                        new_faces_with_match.append((face.bbox, None, result.score, None))
                        unmatched_faces.append(face)
                        structured.append({
                            "bbox": [int(face.bbox[0]), int(face.bbox[1]), int(face.bbox[2]), int(face.bbox[3])],
                            "name": "Unknown",
                            "employee_id": None,
                            "score": float(result.score),
                            "matched": False,
                        })

                # Publish the structured detection list so /api/cameras/
                # {id}/detections can surface it to the React UI without
                # parsing the painted MJPEG.
                with self._latest_detections_lock:
                    self._latest_detections = structured
                    self._latest_detections_at = time.monotonic()

                # Unknown-face capture: every face that failed to match an
                # employee gets handed to the clustering pipeline. Failures
                # here NEVER touch attendance logging — try/except keeps the
                # recognition loop alive even if the DB or disk hiccups.
                if unmatched_faces:
                    try:
                        from .unknown_capture import UnknownCaptureService
                        from ..db import session_scope
                        with session_scope() as unk_session:
                            svc = UnknownCaptureService(unk_session)
                            for f in unmatched_faces:
                                svc.maybe_capture(
                                    face=f,
                                    frame_bgr=frame,
                                    camera_id=self.job.id,
                                )
                    except Exception:
                        log.exception(
                            "recog %s: unknown-capture dispatch failed (continuing)",
                            self.job.name,
                        )

                # Matched faces past their per-employee cooldown get fed
                # to the attendance state machine, which decides whether
                # this detection becomes an IN / BREAK_OUT / BREAK_IN /
                # (no-op) based on the camera's type and the employee's
                # current state for the local day. The state machine
                # writes the row + recomputes the daily rollup; failures
                # are logged but never break the recognition loop.
                from datetime import datetime, timezone
                from ..config import LOCAL_TZ_OFFSET_MIN
                from ..db import session_scope
                from .attendance_state import AttendanceStateMachine

                for bbox, name, score, employee_id in new_faces_with_match:
                    if employee_id is None:
                        continue
                    if not cooldown.hit(employee_id):
                        continue
                    try:
                        with session_scope() as ev_session:
                            outcome = AttendanceStateMachine(
                                ev_session, tz_offset_min=int(LOCAL_TZ_OFFSET_MIN),
                            ).process_auto_event(
                                employee_id=employee_id,
                                employee_name=name or employee_id,
                                camera_id=self.job.id,
                                captured_at=datetime.now(timezone.utc),
                                bbox=bbox,
                                frame_bgr=frame,
                                score=float(score) if score is not None else None,
                            )
                        if outcome.created:
                            self.status.matches_recorded += 1
                            self.status.last_match_at = time.monotonic()
                        else:
                            # Re-open the cooldown when the FSM rejected the
                            # event (invalid transition / day_closed /
                            # duplicate) so the next valid detection isn't
                            # blocked behind a stale cooldown stamp.
                            if outcome.reason.startswith("invalid_transition") or outcome.reason in (
                                "day_closed", "duplicate", "camera_not_found",
                                "employee_not_found_or_inactive",
                            ):
                                # Keep cooldown for "day_closed" and similar
                                # terminal states — we don't want to re-attempt
                                # for the same employee within the window.
                                pass
                    except Exception:
                        log.exception(
                            "recog %s: attendance state-machine dispatch failed (continuing)",
                            self.job.name,
                        )

                last_faces_with_match = new_faces_with_match
                next_detect_at = time.monotonic() + detect_interval

            # ----- Frame cadence: light work, every loop iteration -----
            # Draw the most recently known detections on this frame and
            # push to the live-frame buffer. Drawing happens on a copy
            # so the original frame stays clean for the snapshot crop.
            try:
                annotated = _draw_overlays(frame, last_faces_with_match)
                # Downscale before JPEG encode. Full-res frames are kept
                # in ``self._latest_frame`` (training/capture endpoint
                # uses those) and detection ran on ``frame`` already —
                # only the live-stream JPEG gets shrunk, so accuracy is
                # untouched. cv2.INTER_AREA is the right pick for
                # downsampling (avoids aliasing on text/edges).
                fh, fw = annotated.shape[:2]
                if fw > live_publish_max_width:
                    scale = live_publish_max_width / float(fw)
                    new_w = live_publish_max_width
                    new_h = int(round(fh * scale))
                    annotated = cv2.resize(
                        annotated, (new_w, new_h), interpolation=cv2.INTER_AREA,
                    )
                ok_pub, jpg_pub = cv2.imencode(
                    ".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 75]
                )
                if ok_pub:
                    live_frames.publish(self.job.id, jpg_pub.tobytes())
            except Exception:
                # Never let overlay rendering kill the recognition loop —
                # log silently and move on.
                log.exception("recog %s: overlay render failed", self.job.name)

            elapsed = time.monotonic() - t0
            sleep_for = max(0.0, frame_period - elapsed)
            if sleep_for > 0:
                self._stop.wait(sleep_for)


def _expand_bbox_to_head(
    bbox: tuple[int, int, int, int],
    frame_shape: tuple[int, int, int],
    *,
    top_pad_ratio: float = 0.55,
    side_pad_ratio: float = 0.18,
    bottom_pad_ratio: float = 0.10,
) -> tuple[int, int, int, int]:
    """Expand a tight face bbox so it covers the full head (forehead +
    hair on top, a bit of the ears on the sides, the chin/jawline
    underneath).

    InsightFace's detector returns a tight box around the facial
    features only — when drawn straight, the rectangle visibly cuts the
    top of the head off. Padding by ~55% of face height on top and ~18%
    of face width on each side restores natural head framing without
    over-zooming on small/distant faces. Result is clamped to the frame
    so the rectangle never escapes the canvas.
    """
    h, w = frame_shape[:2]
    x1, y1, x2, y2 = (int(v) for v in bbox)
    face_w = max(1, x2 - x1)
    face_h = max(1, y2 - y1)
    x1 = max(0, x1 - int(side_pad_ratio * face_w))
    x2 = min(w, x2 + int(side_pad_ratio * face_w))
    y1 = max(0, y1 - int(top_pad_ratio * face_h))
    y2 = min(h, y2 + int(bottom_pad_ratio * face_h))
    return (x1, y1, x2, y2)


def _draw_overlays(
    frame: np.ndarray,
    faces_with_match: list[tuple],
) -> np.ndarray:
    """Return a COPY of ``frame`` with a bounding box + label drawn for
    each detected face. Matched faces get a green box with
    ``"<name> (<score>%)"``; unmatched faces get a red box labeled
    ``"Unknown"``. The box covers the full head (forehead + hair), not
    just the tight face crop the detector returns. Done on a copy so
    the caller's untouched frame is still available for snapshot crops.
    """
    annotated = frame.copy()
    # OpenCV uses BGR, so colors are (B, G, R).
    GREEN = (60, 180, 60)
    RED = (60, 60, 220)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    for entry in faces_with_match:
        # Tolerate either 3-tuple (no id) or 4-tuple (with id) — the
        # logging path passes 4-tuples; future callers might pass 3.
        if len(entry) >= 4:
            bbox, name, score, _employee_id = entry[0], entry[1], entry[2], entry[3]
        else:
            bbox, name, score = entry[0], entry[1], entry[2]
        x1, y1, x2, y2 = _expand_bbox_to_head(bbox, annotated.shape)
        matched = name is not None
        color = GREEN if matched else RED
        label = (
            f"{name} ({int(round(float(score) * 100))}%)" if matched else "Unknown"
        )
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        # Filled label background above the box — keeps the text readable
        # against busy scenes.
        (tw, th), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1
        )
        label_top = max(0, y1 - th - baseline - 6)
        cv2.rectangle(
            annotated,
            (x1, label_top),
            (x1 + tw + 8, y1),
            color,
            thickness=-1,
        )
        text_color = WHITE if matched else BLACK
        cv2.putText(
            annotated,
            label,
            (x1 + 4, y1 - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            text_color,
            1,
            cv2.LINE_AA,
        )
    return annotated


def _crop_face(frame: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    """Crop with a small margin around the bbox for a more recognisable
    snapshot. Clamped to the frame to avoid OpenCV slice issues."""
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = bbox
    pad_x = int(0.15 * (x2 - x1))
    pad_y = int(0.15 * (y2 - y1))
    x1 = max(0, x1 - pad_x)
    y1 = max(0, y1 - pad_y)
    x2 = min(w, x2 + pad_x)
    y2 = min(h, y2 + pad_y)
    return frame[y1:y2, x1:x2]


# ---- Manager ----------------------------------------------------------------

class RecognitionWorkerManager:
    """Owns the set of running workers. Started during app lifespan;
    rebuilds the worker set whenever ``refresh_from_db`` is called
    (e.g., after a camera CRUD)."""

    def __init__(self) -> None:
        self._workers: dict[str, RecognitionWorker] = {}
        self._lock = threading.Lock()

    def start_all(self) -> int:
        """Spawn a worker for every camera that actually needs one.

        A camera needs a recognition worker only when BOTH:
          * ``connection_status == 'connected'`` — otherwise we'd be
            spinning up an RTSP retry loop for an unreachable host every
            30 s forever (wastes a thread, FFMPEG memory, and floods
            the logs).
          * ``enable_face_ingest`` is True — live-only cameras can be
            served by the MJPEG endpoint's direct-RTSP fallback without
            any face-detection cost. Live view still works.

        The MJPEG endpoint reads from the worker's annotated-frame
        buffer when one exists, and falls back to opening RTSP directly
        when one doesn't — so dropping the worker for a live-only
        camera doesn't lose its video tile.
        """
        from sqlalchemy import select
        with session_scope() as session:
            rows = session.execute(
                select(CameraModel).where(
                    CameraModel.connection_status == "connected",
                    CameraModel.enable_face_ingest.is_(True),
                )
            ).scalars().all()
            jobs = [_build_job_from_row(r) for r in rows]

        with self._lock:
            wanted = {j.id for j in jobs}
            # Stop workers for cameras that no longer qualify (deleted,
            # disconnected, or face_ingest toggled off).
            for cam_id in list(self._workers):
                if cam_id not in wanted:
                    self._workers.pop(cam_id).stop()
            # Start workers for new cameras.
            for job in jobs:
                if job.id in self._workers:
                    continue
                worker = RecognitionWorker(job)
                worker.start()
                self._workers[job.id] = worker
            count = len(self._workers)
        log.info("recognition workers: %d running", count)
        return count

    def stop_all(self) -> None:
        with self._lock:
            for w in self._workers.values():
                w.stop()
            self._workers.clear()

    def status_all(self) -> list[WorkerStatus]:
        with self._lock:
            return [w.status for w in self._workers.values()]

    def get_worker(self, camera_id: str) -> Optional[RecognitionWorker]:
        with self._lock:
            return self._workers.get(camera_id)


_manager_lock = threading.Lock()
_manager: Optional[RecognitionWorkerManager] = None


def get_worker_manager() -> RecognitionWorkerManager:
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = RecognitionWorkerManager()
        return _manager
