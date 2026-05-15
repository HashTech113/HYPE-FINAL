"""Admin-only face training image management."""

from __future__ import annotations

import base64
import time
from typing import Optional

import cv2
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..dependencies import require_admin
from ..services import face_images as face_images_service
from ..services import face_training as face_training_service
from ..services.auth import User
from ..services.face_service import FaceRecognitionError, get_face_service
from ..services.recognition_worker import get_worker_manager

router = APIRouter(tags=["face-images"])


class FaceImageOut(BaseModel):
    id: int
    employeeId: str
    label: str
    imageUrl: str
    createdBy: Optional[str] = None
    createdAt: str
    # Populated when the embedding extraction succeeded inline. The UI
    # uses this to show "trained" vs "needs re-train" per image.
    embeddingId: Optional[int] = None
    embeddingError: Optional[str] = None
    qualityScore: Optional[float] = None


class FaceImageListResponse(BaseModel):
    items: list[FaceImageOut]
    count: int


class FaceImageCreate(BaseModel):
    image: str = Field(..., min_length=1, description="Base64 image (with or without data URL prefix).")
    label: str = Field("", max_length=64)


def _to_out(
    rec,
    *,
    embedding_id: Optional[int] = None,
    embedding_error: Optional[str] = None,
    quality_score: Optional[float] = None,
) -> FaceImageOut:
    return FaceImageOut(
        id=rec.id,
        employeeId=rec.employee_id,
        label=rec.label,
        imageUrl=rec.image_data,
        createdBy=rec.created_by,
        createdAt=rec.created_at.isoformat(),
        embeddingId=embedding_id,
        embeddingError=embedding_error,
        qualityScore=quality_score,
    )


@router.get(
    "/api/employees/{employee_id}/face-images",
    response_model=FaceImageListResponse,
    dependencies=[Depends(require_admin)],
)
def list_face_images(employee_id: str) -> FaceImageListResponse:
    items = [_to_out(r) for r in face_images_service.list_for_employee(employee_id)]
    return FaceImageListResponse(items=items, count=len(items))


@router.post(
    "/api/employees/{employee_id}/face-images",
    response_model=FaceImageOut,
    status_code=201,
)
def add_face_image(
    employee_id: str,
    payload: FaceImageCreate,
    user: User = Depends(require_admin),
) -> FaceImageOut:
    try:
        rec = face_images_service.add(
            employee_id=employee_id,
            image_data=payload.image,
            label=payload.label,
            created_by=user.id,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    # Inline enroll: if InsightFace can't extract a face the row stays
    # but the response surfaces the reason so the UI can prompt for a
    # better photo. A 422 here would also force the admin to re-upload,
    # which is annoying for a multi-photo enrollment session.
    outcome = face_training_service.enroll_face_image(rec.id)
    return _to_out(
        rec,
        embedding_id=outcome.embedding_id,
        embedding_error=outcome.error,
        quality_score=outcome.quality_score if outcome.accepted else None,
    )


class EnrollSummary(BaseModel):
    employeeId: str
    accepted: int
    rejected: int
    total: int
    items: list[FaceImageOut]


@router.post(
    "/api/employees/{employee_id}/face-images/enroll",
    response_model=EnrollSummary,
)
def enroll_employee_all(
    employee_id: str,
    _user: User = Depends(require_admin),
) -> EnrollSummary:
    """Re-extract embeddings for every face image already on file for
    an employee. Used by the Face Training page's 'Train' button so an
    admin can re-train after uploading a batch or after the buffalo_l
    model is upgraded."""
    outcomes = face_training_service.enroll_employee_all(employee_id)
    # Count from outcomes — NOT from the filtered list_for_employee view.
    # After successful Train, the cleanup pass clears image_data on every
    # trained row, and list_for_employee hides cleared rows so the panel
    # only shows pending uploads. If we counted from that list the dialog
    # would always report 0 after retraining a previously-enrolled
    # employee, which is misleading: the embeddings ARE on file.
    accepted = sum(1 for o in outcomes if o.accepted)
    rejected = sum(1 for o in outcomes if not o.accepted)
    # Items are sourced from the visible list (post-cleanup) so the
    # frontend can update its in-memory grid — typically empty after
    # Train, since all sources just got cleared.
    items: list[FaceImageOut] = []
    for rec in face_images_service.list_for_employee(employee_id):
        outcome = next((o for o in outcomes if o.image_id == rec.id), None)
        items.append(_to_out(
            rec,
            embedding_id=outcome.embedding_id if outcome else None,
            embedding_error=outcome.error if outcome else None,
            quality_score=(outcome.quality_score if outcome and outcome.accepted else None),
        ))
    return EnrollSummary(
        employeeId=employee_id,
        accepted=accepted,
        rejected=rejected,
        total=len(outcomes),
        items=items,
    )


@router.delete(
    "/api/face-images/{image_id}",
    dependencies=[Depends(require_admin)],
)
def delete_face_image(image_id: int) -> dict:
    # Drop the dependent embedding row first so the cache stops matching
    # against an image that no longer exists. The face_images CASCADE
    # would handle the DB side either way; this also refreshes the cache.
    embeddings_dropped = face_training_service.remove_embeddings_for_image(image_id)
    if not face_images_service.delete(image_id):
        raise HTTPException(status_code=404, detail=f"face image {image_id} not found")
    return {"status": "deleted", "id": image_id, "embeddings_dropped": embeddings_dropped}


# ---- Capture-from-camera enrollment ----------------------------------------

class CaptureFromCameraRequest(BaseModel):
    cameraId: str = Field(..., min_length=1, description="cameras.id of an active recognition worker")
    label: str = Field("", max_length=64, description="Optional human label, e.g. 'live-front'")
    # Frame freshness gate. Reject the capture if the worker's most
    # recent frame is older than this — usually means the camera
    # disconnected and the buffered frame is stale.
    maxFrameAgeSeconds: float = Field(5.0, ge=0.5, le=60.0)


class CaptureFromCameraResponse(FaceImageOut):
    cameraId: str
    detectedFaces: int
    bbox: list[int]


@router.post(
    "/api/employees/{employee_id}/face-images/capture",
    response_model=CaptureFromCameraResponse,
    status_code=201,
)
def capture_from_camera(
    employee_id: str,
    payload: CaptureFromCameraRequest,
    user: User = Depends(require_admin),
) -> CaptureFromCameraResponse:
    """Pull the most recent frame from a running camera worker, detect
    a face in it, store the cropped face as a training image, and
    enroll its embedding — all in one round trip. Lets the admin
    enroll an employee by walking them in front of the camera and
    clicking a button instead of uploading photo files.
    """
    worker = get_worker_manager().get_worker(payload.cameraId)
    if worker is None:
        raise HTTPException(
            status_code=404,
            detail=f"No active recognition worker for camera {payload.cameraId}",
        )

    frame, frame_at = worker.latest_frame()
    if frame is None or frame_at is None:
        raise HTTPException(
            status_code=503,
            detail="Camera worker hasn't read a frame yet — wait a moment and retry",
        )
    age = time.monotonic() - frame_at
    if age > payload.maxFrameAgeSeconds:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Latest frame is {age:.1f}s old (threshold {payload.maxFrameAgeSeconds}s); "
                "the camera may have disconnected"
            ),
        )

    face = get_face_service()
    try:
        best = face.detect_single(frame)
    except FaceRecognitionError as exc:
        # 422 so the UI prompts the operator to reposition the subject
        # rather than blame the camera.
        raise HTTPException(status_code=422, detail=str(exc))

    # Crop with a small margin so the stored thumbnail is recognisable
    # — same crop helper the worker uses when recording a match.
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = best.bbox
    pad_x = int(0.15 * (x2 - x1))
    pad_y = int(0.15 * (y2 - y1))
    x1c = max(0, x1 - pad_x)
    y1c = max(0, y1 - pad_y)
    x2c = min(w, x2 + pad_x)
    y2c = min(h, y2 + pad_y)
    crop = frame[y1c:y2c, x1c:x2c]
    ok, jpg = cv2.imencode(".jpg", crop, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise HTTPException(status_code=500, detail="Could not encode captured frame as JPEG")
    image_b64 = base64.b64encode(jpg.tobytes()).decode("ascii")

    # Reuse the existing add → enroll path so the on-disk + DB layout
    # of camera-captured photos is identical to upload-from-file ones.
    try:
        rec = face_images_service.add(
            employee_id=employee_id,
            image_data=image_b64,
            label=payload.label or "camera-capture",
            created_by=user.id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Use the embedding we already computed during detect_single on the
    # full frame — re-running detection on the tight crop frequently
    # fails at typical face sizes (a 120-px-wide crop scaled to the
    # 640×640 detector loses too much signal).
    outcome = face_training_service.enroll_with_known_embedding(
        image_id=rec.id,
        embedding=best.embedding,
        quality_score=best.det_score,
    )
    return CaptureFromCameraResponse(
        **_to_out(
            rec,
            embedding_id=outcome.embedding_id,
            embedding_error=outcome.error,
            quality_score=outcome.quality_score if outcome.accepted else None,
        ).model_dump(),
        cameraId=payload.cameraId,
        detectedFaces=1,
        bbox=list(best.bbox),
    )
