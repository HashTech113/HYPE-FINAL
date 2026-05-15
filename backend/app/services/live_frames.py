"""Per-camera buffer of the most recent annotated MJPEG frame.

The recognition worker (``recognition_worker.RecognitionWorker``) writes
here once per detection cycle, after it has drawn bounding boxes +
employee names onto a copy of the frame it just consumed. The MJPEG
stream endpoint (``cameras.mjpeg_stream``) reads from here so the live
view shows boxes + names *without* opening a second RTSP socket or
running duplicate face inference per frame.

Fallback: when no worker is running for a given camera (e.g.
``RECOGNITION_WORKERS_ENABLED=0``, worker crashed, camera not yet
spawned) the cache stays empty and the MJPEG endpoint falls back to its
existing direct-RTSP read path. Live video still works — there are just
no overlays in that case.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AnnotatedFrame:
    """A JPEG-encoded frame with overlays baked in + its capture time."""
    jpeg_bytes: bytes
    captured_at: float  # ``time.monotonic()`` at publish time


# Frames older than this are treated as stale. We're generous (8 s)
# because HEVC streams hit occasional decoder hiccups where
# ``cv2.VideoCapture.read()`` can block a couple of seconds. A worker
# that stalls beyond this window is treated as genuinely dead and the
# MJPEG endpoint closes the stream so the browser can reconnect and
# pick up a recovered worker on its next try.
STALE_AFTER_SECONDS: float = 8.0


_buffer: dict[str, AnnotatedFrame] = {}
_lock = threading.Lock()


def publish(camera_id: str, jpeg_bytes: bytes) -> None:
    """Store the latest annotated JPEG for ``camera_id``. Thread-safe."""
    frame = AnnotatedFrame(jpeg_bytes=jpeg_bytes, captured_at=time.monotonic())
    with _lock:
        _buffer[camera_id] = frame


def get_fresh(camera_id: str) -> Optional[AnnotatedFrame]:
    """Return the most recent annotated frame if still fresh, else None.

    Returning None tells callers to fall back to direct RTSP read — used
    by ``cameras.mjpeg_stream`` to decide whether to switch streaming
    modes per request.
    """
    with _lock:
        frame = _buffer.get(camera_id)
    if frame is None:
        return None
    if time.monotonic() - frame.captured_at > STALE_AFTER_SECONDS:
        return None
    return frame


def has_recent(camera_id: str) -> bool:
    """Cheaper version of :func:`get_fresh` when the bytes aren't needed."""
    return get_fresh(camera_id) is not None


def clear(camera_id: str) -> None:
    """Drop the buffered frame for one camera — used when the worker for
    this camera is stopped/replaced so the MJPEG endpoint doesn't serve
    a stale annotated frame after the worker is gone."""
    with _lock:
        _buffer.pop(camera_id, None)
