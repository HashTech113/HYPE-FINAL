"""InsightFace ``buffalo_l`` wrapper.

A ``FaceService`` instance owns a single ``FaceAnalysis`` pipeline. The
pipeline's internal numpy buffers are NOT thread-safe — concurrent
``app.get(frame)`` calls corrupt state — so ``detect()`` is gated by a
per-instance lock.

The shared singleton is exposed via :func:`get_face_service` and used by
the API (upload identify, training enrollments) where there's only ever
one caller at a time. Per-camera worker threads should construct their
own instance via :meth:`FaceService.create_worker_instance` to get
parallelism — the underlying ORT scheduler serialises GPU execution but
pre/post-processing runs independently per instance.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..config import (
    FACE_DET_SIZE,
    FACE_MIN_QUALITY,
    FACE_MODEL_NAME,
    FACE_MODEL_ROOT,
    FACE_PROVIDER,
    FACE_RECOGNITION_ENABLED,
)

log = logging.getLogger(__name__)


class FaceRecognitionError(RuntimeError):
    """Raised when face detection / recognition can't produce a result.

    Surfaced to the API as 422 (no face detected, low quality) or 503
    (engine disabled / model load failed)."""


@dataclass(frozen=True)
class DetectedFace:
    bbox: tuple[int, int, int, int]
    embedding: np.ndarray  # L2-normalised buffalo_l vector, dim=512
    det_score: float
    kps: np.ndarray         # 5 landmarks (l_eye, r_eye, nose, l_mouth, r_mouth) — shape (5, 2)


class FaceService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._app = None  # type: ignore[var-annotated]
        self._loaded = False

    @classmethod
    def create_worker_instance(cls) -> "FaceService":
        """Build + load a FaceService for use by exactly one camera worker.
        Loaded eagerly so spin-up fails fast at startup if the model
        files are missing/corrupt rather than crashing one worker thread
        later."""
        svc = cls()
        svc.load()
        return svc

    def load(self) -> None:
        if not FACE_RECOGNITION_ENABLED:
            raise FaceRecognitionError(
                "face recognition disabled (FACE_RECOGNITION_ENABLED=0)"
            )
        with self._lock:
            if self._loaded:
                return
            # Import lazily so that operators who set FACE_RECOGNITION_ENABLED=0
            # don't pay the ~3-5s insightface load cost just to import this
            # module (which other unrelated routes will trigger transitively).
            from insightface.app import FaceAnalysis  # noqa: WPS433
            try:
                app = FaceAnalysis(
                    name=FACE_MODEL_NAME,
                    root=FACE_MODEL_ROOT,
                    providers=[FACE_PROVIDER],
                    # Restrict to detection + recognition. The buffalo_l
                    # pack also ships landmark_2d_106 / landmark_3d_68 /
                    # genderage; loading them adds ONNX sessions that run
                    # on every detected face for no benefit to attendance.
                    allowed_modules=["detection", "recognition"],
                )
                app.prepare(ctx_id=0, det_size=(FACE_DET_SIZE, FACE_DET_SIZE))
            except Exception as exc:
                log.exception("Failed to initialise InsightFace model")
                raise FaceRecognitionError(f"Face model init failed: {exc}") from exc
            self._app = app
            self._loaded = True
            log.info(
                "InsightFace '%s' loaded (provider=%s, det=%d)",
                FACE_MODEL_NAME, FACE_PROVIDER, FACE_DET_SIZE,
            )

    def is_loaded(self) -> bool:
        return self._loaded

    def _ensure_loaded(self):
        if not self._loaded or self._app is None:
            self.load()
        return self._app

    def detect(self, frame_bgr: np.ndarray) -> list[DetectedFace]:
        """Find faces in ``frame_bgr`` and return ones whose detector score
        clears the active ``face_min_quality`` setting (admin-tunable; env
        var ``FACE_MIN_QUALITY`` is the backstop default). The lock
        serialises calls per-instance so the underlying numpy buffers
        stay consistent."""
        # Local import — defers the small recognition_config DB read off
        # the import path of this module (which the API touches at boot).
        from .recognition_config import get_recognition_settings
        min_quality = get_recognition_settings().face_min_quality
        app = self._ensure_loaded()
        with self._lock:
            raw = app.get(frame_bgr)
        out: list[DetectedFace] = []
        for f in raw:
            det_score = float(getattr(f, "det_score", 0.0))
            if det_score < min_quality:
                continue
            emb = getattr(f, "normed_embedding", None)
            kps = getattr(f, "kps", None)
            if emb is None or kps is None:
                continue
            bbox = f.bbox.astype(int).tolist()
            out.append(
                DetectedFace(
                    bbox=(int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])),
                    embedding=np.asarray(emb, dtype=np.float32),
                    det_score=det_score,
                    kps=np.asarray(kps, dtype=np.float32),
                )
            )
        return out

    def detect_single(self, frame_bgr: np.ndarray) -> DetectedFace:
        """Detect the best (largest) face in the frame. Raises
        FaceRecognitionError if no face passes the quality floor."""
        from .recognition_config import get_recognition_settings
        min_quality = get_recognition_settings().face_min_quality
        faces = self.detect(frame_bgr)
        if not faces:
            raise FaceRecognitionError("No face detected")
        if len(faces) > 1:
            faces.sort(
                key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
                reverse=True,
            )
        best = faces[0]
        if best.det_score < min_quality:
            raise FaceRecognitionError(
                f"Face quality too low ({best.det_score:.2f} < {min_quality})"
            )
        return best


_singleton_lock = threading.Lock()
_singleton: Optional[FaceService] = None


def get_face_service() -> FaceService:
    """Process-wide FaceService used by the request-handling routes."""
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = FaceService()
        return _singleton
