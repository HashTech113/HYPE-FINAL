"""Backend-side face recognition endpoints (Path B Stage 3).

* ``POST /api/recognition/identify`` — upload a frame, get back the
  matched employee + similarity score. Pure read; no DB write.
* ``POST /api/recognition/mark`` — same, but on a match also records
  a snapshot/attendance event via the existing ``record_capture()``
  pipeline so the captured face shows up in Live Captures and counts
  toward the day's attendance.
* ``GET /api/recognition/cache/stats`` — diagnostic for the admin UI.
* ``POST /api/recognition/cache/reload`` — full cache rebuild from DB
  (use after bulk training imports).

These endpoints exist whether or not the camera workers are running.
The Stage 4 RTSP worker calls the same RecognitionService instance
under the hood, so anything you debug here applies there.
"""

from __future__ import annotations

import base64
import binascii
import io
import logging
import time
import uuid
from typing import Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from PIL import Image
from pydantic import BaseModel, Field

from ..dependencies import require_admin_or_hr
from ..services import logs as logs_service
from ..services.embedding_cache import get_embedding_cache
from ..services.face_service import FaceRecognitionError, get_face_service
from ..services.recognition import get_cooldown, get_recognition_service

log = logging.getLogger(__name__)

router = APIRouter(tags=["recognition"], prefix="/api/recognition")


def _decode_image(image_b64: str) -> np.ndarray:
    """Decode a base64 (with or without ``data:`` URL prefix) JPEG/PNG
    payload into a BGR numpy array. Raises 422 on bad input."""
    if image_b64.startswith("data:") and "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]
    try:
        data = base64.b64decode(image_b64, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid base64: {exc}")
    try:
        img = Image.open(io.BytesIO(data))
        rgb = np.array(img.convert("RGB"))
        return rgb[:, :, ::-1].copy()
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not decode image: {exc}")


class IdentifyRequest(BaseModel):
    image: str = Field(..., min_length=1, description="Base64 JPEG/PNG, with or without data URL prefix")
    threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Override the default cosine match threshold (default uses FACE_MATCH_THRESHOLD)",
    )


class IdentifyResponse(BaseModel):
    matched: bool
    employeeId: Optional[str]
    employeeName: Optional[str]
    employeeCode: Optional[str]
    score: float
    secondBestScore: float
    detScore: float
    bbox: list[int]


def _build_identify_response(image_b64: str, threshold: Optional[float]) -> IdentifyResponse:
    face = get_face_service()
    if not face.is_loaded():
        try:
            face.load()
        except FaceRecognitionError as exc:
            raise HTTPException(status_code=503, detail=str(exc))

    bgr = _decode_image(image_b64)
    try:
        best = face.detect_single(bgr)
    except FaceRecognitionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    result = get_recognition_service().match(best.embedding, threshold=threshold)
    name = code = None
    if result.employee_id:
        name_map = get_embedding_cache().id_to_name_map()
        name = name_map.get(result.employee_id)
        # Per-employee_code lookup is cheaper as a one-shot DB query than
        # caching another map; the identify path is low-QPS.
        from ..services import employees as employees_service
        emp = employees_service.get_by_id(result.employee_id)
        if emp is not None:
            code = emp.employee_id
    return IdentifyResponse(
        matched=result.employee_id is not None,
        employeeId=result.employee_id,
        employeeName=name,
        employeeCode=code,
        score=round(float(result.score), 4),
        secondBestScore=round(float(result.second_best_score), 4),
        detScore=round(float(best.det_score), 4),
        bbox=list(best.bbox),
    )


@router.post(
    "/identify",
    response_model=IdentifyResponse,
    dependencies=[Depends(require_admin_or_hr)],
)
def identify(payload: IdentifyRequest) -> IdentifyResponse:
    return _build_identify_response(payload.image, payload.threshold)


class MarkRequest(IdentifyRequest):
    cameraId: Optional[str] = Field(
        None, description="If supplied, recorded on the snapshot row so Live Captures shows the source camera."
    )


class MarkResponse(IdentifyResponse):
    recorded: bool
    snapshotName: Optional[str] = None


@router.post(
    "/mark",
    response_model=MarkResponse,
    dependencies=[Depends(require_admin_or_hr)],
)
def mark(payload: MarkRequest) -> MarkResponse:
    """Identify the face AND record a snapshot/attendance event when
    matched. Subject to the per-employee cooldown — if the same
    employee was recorded in the last few seconds the row is skipped
    and ``recorded=False`` is returned. Caller should treat that as a
    successful identify (the cooldown is a feature, not an error)."""
    base = _build_identify_response(payload.image, payload.threshold)
    if not base.matched or not base.employeeId:
        return MarkResponse(**base.model_dump(), recorded=False, snapshotName=None)

    if not get_cooldown().hit(base.employeeId):
        log.info("recognition.mark suppressed by cooldown emp_id=%s", base.employeeId)
        return MarkResponse(**base.model_dump(), recorded=False, snapshotName=base.employeeName)

    # Reuse the same record_capture path the existing camera ingest uses
    # so the snapshot lands in snapshot_logs/attendance_logs and the
    # Live Captures page picks it up via /api/snapshots.
    image_b64 = payload.image
    if image_b64.startswith("data:") and "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]
    timestamp_iso = _isoformat_now()
    image_path = f"recog_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}.jpg"
    stored = logs_service.record_capture(
        name=base.employeeName or base.employeeId,
        timestamp_iso=timestamp_iso,
        image_path=image_path,
        image_data=image_b64,
        camera_id=payload.cameraId or None,
    )
    return MarkResponse(
        **base.model_dump(),
        recorded=bool(stored),
        snapshotName=base.employeeName,
    )


def _isoformat_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ---- diagnostics ------------------------------------------------------------

class CacheStats(BaseModel):
    employeeCount: int
    vectorCount: int
    modelName: str
    threshold: float


@router.get(
    "/cache/stats",
    response_model=CacheStats,
    dependencies=[Depends(require_admin_or_hr)],
)
def cache_stats() -> CacheStats:
    from ..config import FACE_MATCH_THRESHOLD, FACE_MODEL_NAME
    cache = get_embedding_cache()
    return CacheStats(
        employeeCount=cache.employee_count(),
        vectorCount=cache.size(),
        modelName=FACE_MODEL_NAME,
        threshold=FACE_MATCH_THRESHOLD,
    )


@router.post(
    "/cache/reload",
    response_model=CacheStats,
    dependencies=[Depends(require_admin_or_hr)],
)
def cache_reload() -> CacheStats:
    """Force a full reload of the in-memory cache from the DB. Useful
    after bulk-importing embeddings or after rotating the model."""
    cache = get_embedding_cache()
    cache.load_from_db()
    return cache_stats()


# ---- Worker health (Stage 4) ------------------------------------------------

class WorkerHealth(BaseModel):
    cameraId: str
    name: str
    rtspUrl: str
    running: bool
    connected: bool
    framesRead: int
    facesDetected: int
    matchesRecorded: int
    secondsSinceLastFrame: Optional[int] = None
    secondsSinceLastMatch: Optional[int] = None
    lastError: Optional[str] = None
    backoffSeconds: float


class WorkersHealthResponse(BaseModel):
    workers: list[WorkerHealth]
    enabled: bool


@router.get(
    "/workers/health",
    response_model=WorkersHealthResponse,
    dependencies=[Depends(require_admin_or_hr)],
)
def workers_health() -> WorkersHealthResponse:
    """Per-camera RTSP recognition-worker status. Empty when the
    workers are disabled (RECOGNITION_WORKERS_ENABLED=0) or when no
    cameras are configured."""
    from ..services.recognition_worker import get_worker_manager
    now = time.monotonic()
    items: list[WorkerHealth] = []
    for s in get_worker_manager().status_all():
        items.append(WorkerHealth(
            cameraId=s.camera_id,
            name=s.name,
            rtspUrl=s.rtsp_url,
            running=s.running,
            connected=s.connected,
            framesRead=s.frames_read,
            facesDetected=s.faces_detected,
            matchesRecorded=s.matches_recorded,
            secondsSinceLastFrame=int(now - s.last_frame_at) if s.last_frame_at else None,
            secondsSinceLastMatch=int(now - s.last_match_at) if s.last_match_at else None,
            lastError=s.last_error,
            backoffSeconds=s.backoff_seconds,
        ))
    return WorkersHealthResponse(workers=items, enabled=True)
