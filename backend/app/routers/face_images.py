"""Admin-only face training image management."""

from __future__ import annotations

import base64
import logging
import time
from typing import Optional

import cv2
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..dependencies import require_admin
from ..services import face_images as face_images_service
from ..services import face_training as face_training_service
from ..services.auth import User
from ..services.face_service import FaceRecognitionError, get_face_service
from ..services.recognition_worker import get_worker_manager

log = logging.getLogger(__name__)
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


class TrainingStatus(BaseModel):
    """Per-employee training-set summary. Drives the inline status
    block at the top of the Face Training panel — embeddings count is
    the truth (image_data gets cleared post-train and would otherwise
    misrepresent the actual trained state)."""
    employeeId: str
    embeddingsCount: int
    minRequired: int
    maxRecommended: int
    # "untrained"  — 0 embeddings
    # "partial"    — 1..min-1 embeddings (still under the required floor)
    # "trained"    — min..max embeddings (healthy)
    # "over_cap"   — > max (only seen on legacy data; new uploads can't reach this)
    status: str
    atCapacity: bool


class FaceImageListResponse(BaseModel):
    items: list[FaceImageOut]
    count: int
    training: TrainingStatus


class FaceImageCreate(BaseModel):
    image: str = Field(..., min_length=1, description="Base64 image (with or without data URL prefix).")
    label: str = Field("", max_length=64)


class FullRetrainRequest(BaseModel):
    """Body for the Full Retrain endpoint: a fresh set of training
    photos that will REPLACE every existing embedding for the
    employee. Each entry is validated independently — if any fail the
    quality gate the whole batch is rejected so we don't end up with a
    mixed-quality re-enrollment."""
    images: list[FaceImageCreate] = Field(..., min_length=1)


def _training_status(employee_id: str, *, count: Optional[int] = None) -> TrainingStatus:
    """Compute the inline training status. Accepts an optional
    pre-computed ``count`` so callers that already queried the DB
    (e.g. immediately after a write) don't pay for a second roundtrip."""
    if count is None:
        count = face_training_service.capacity_state(employee_id).count
    if count <= 0:
        status = "untrained"
    elif count < face_training_service.MIN_EMBEDDINGS_FOR_TRAINING:
        status = "partial"
    elif count <= face_training_service.MAX_EMBEDDINGS_PER_EMPLOYEE:
        status = "trained"
    else:
        status = "over_cap"
    return TrainingStatus(
        employeeId=employee_id,
        embeddingsCount=count,
        minRequired=face_training_service.MIN_EMBEDDINGS_FOR_TRAINING,
        maxRecommended=face_training_service.MAX_EMBEDDINGS_PER_EMPLOYEE,
        status=status,
        atCapacity=count >= face_training_service.MAX_EMBEDDINGS_PER_EMPLOYEE,
    )


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
    return FaceImageListResponse(
        items=items,
        count=len(items),
        training=_training_status(employee_id),
    )


@router.post(
    "/api/employees/{employee_id}/face-images",
    response_model=FaceImageOut,
    status_code=201,
)
def add_face_image(
    employee_id: str,
    payload: FaceImageCreate,
    user: User = Depends(require_admin),
    force: bool = Query(
        False,
        description=(
            "Skip the duplicate-face safety check. Set after the admin "
            "has explicitly confirmed a duplicate-face warning."
        ),
    ),
    mode: str = Query(
        "add",
        regex=r"^(add|replace_weakest)$",
        description=(
            "'add' (default) appends a new embedding — rejected with "
            "409 'at_capacity' when the cap is reached. "
            "'replace_weakest' is the retrain path: when at cap, evict "
            "the lowest-quality embedding ONLY if the new image is "
            "better, otherwise reject with 409 'quality_lower'."
        ),
    ),
) -> FaceImageOut:
    # 1) Quality gate. Strict for training (single face, large enough,
    #    detector-confident). Bad images are rejected outright with
    #    422 — we never persist a row we wouldn't be willing to train
    #    on. The user-facing message is uniform; the specific reason
    #    sits in the server log.
    embedding, quality, validation_error = face_training_service.validate_for_training(
        payload.image
    )
    if embedding is None:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "bad_image",
                "message": validation_error or face_training_service.TRAINING_BAD_IMAGE_MESSAGE,
            },
        )

    # 2) Duplicate-face check. Same employee → "already trained, skip
    #    or add anyway"; different employee → "matches X, are you
    #    sure". Frontend retries with ?force=true after admin confirms.
    if not force:
        dup = face_training_service.find_duplicate_match(
            embedding=embedding,
            target_employee_id=employee_id,
        )
        if dup is not None:
            log.warning(
                "duplicate-face on upload: target=%s matched=%s name=%s score=%.3f same=%s",
                employee_id, dup.matched_employee_id, dup.matched_name,
                dup.score, dup.same_employee,
            )
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "duplicate_face",
                    "matched_employee_id": dup.matched_employee_id,
                    "matched_name": dup.matched_name,
                    "score": dup.score,
                    "same_employee": dup.same_employee,
                    "message": (
                        "This face already appears to be trained for this "
                        "employee. Retrain only if you want to replace the "
                        "old face data."
                        if dup.same_employee
                        else f"This face already matches {dup.matched_name}. "
                             "Please check the selected employee."
                    ),
                },
            )

    # 3) Capacity check. Hard limit lives here, not the frontend, so the
    #    post-train cleanup can't repeatedly "reset" the visible count
    #    and accumulate unbounded embeddings.
    cap = face_training_service.capacity_state(employee_id)
    if cap.at_cap and mode == "add":
        log.info(
            "training upload at cap: emp=%s count=%d max=%d",
            employee_id, cap.count, face_training_service.MAX_EMBEDDINGS_PER_EMPLOYEE,
        )
        raise HTTPException(
            status_code=409,
            detail={
                "code": "at_capacity",
                "embeddings_count": cap.count,
                "max_recommended": face_training_service.MAX_EMBEDDINGS_PER_EMPLOYEE,
                "message": (
                    f"This employee is already trained with {cap.count} face "
                    "embeddings. Use Retrain to replace the weakest one or do "
                    "a Full Retrain instead."
                ),
            },
        )

    # 4) Persist the source image row. The base64 payload itself will
    #    be cleared by the post-train cleanup on the next 'Train all'
    #    pass; we keep the metadata for audit.
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

    # 5) Enroll. Three branches:
    #    a) Replace-weakest mode AND at cap: try to evict + insert; if
    #       new quality is worse than the existing weakest, REJECT and
    #       drop the just-saved face_image row so we don't leak a stub.
    #    b) Normal append (under cap, or replace_weakest with capacity
    #       to spare): just insert. Reuses the embedding we already
    #       computed in step 1 — no second InsightFace pass.
    if mode == "replace_weakest" and cap.at_cap:
        ok, _evicted, new_emb_id = face_training_service.replace_weakest_embedding(
            employee_id=employee_id,
            new_embedding=embedding,
            new_quality=quality or 0.0,
            new_face_image_id=rec.id,
        )
        if not ok:
            # New image is worse than what's already stored — undo the
            # FaceImage insert so we don't litter the DB and surface a
            # clear "quality lower" 409 to the UI.
            face_images_service.delete(rec.id)
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "quality_lower",
                    "message": (
                        "Image quality is lower than the existing trained "
                        "faces. Not added."
                    ),
                },
            )
        outcome = face_training_service.EnrollOutcome(
            embedding_id=new_emb_id,
            image_id=rec.id,
            accepted=True,
            quality_score=quality or 0.0,
            error=None,
        )
    else:
        outcome = face_training_service.enroll_with_known_embedding(
            image_id=rec.id,
            embedding=embedding,
            quality_score=quality or 0.0,
        )

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
    training: TrainingStatus


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
        training=_training_status(employee_id),
    )


class FullRetrainResponse(BaseModel):
    employeeId: str
    deletedEmbeddings: int
    accepted: int
    rejected: int
    items: list[FaceImageOut]
    training: TrainingStatus


@router.post(
    "/api/employees/{employee_id}/face-images/full-retrain",
    response_model=FullRetrainResponse,
)
def full_retrain(
    employee_id: str,
    payload: FullRetrainRequest,
    user: User = Depends(require_admin),
) -> FullRetrainResponse:
    """Replace EVERY embedding for one employee with a fresh batch of
    training photos. Two-phase: validate every photo first, then on
    pass clear the old embeddings and insert the new ones.

    Designed for the "I want to start over" flow — e.g. the admin
    realises an employee has been recognised inconsistently because
    the original training photos were taken in poor lighting and they
    want to redo the whole set.
    """
    if len(payload.images) > face_training_service.MAX_EMBEDDINGS_PER_EMPLOYEE:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "too_many_images",
                "message": (
                    f"Full Retrain accepts at most "
                    f"{face_training_service.MAX_EMBEDDINGS_PER_EMPLOYEE} photos."
                ),
            },
        )
    if len(payload.images) < face_training_service.MIN_EMBEDDINGS_FOR_TRAINING:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "too_few_images",
                "message": (
                    f"Full Retrain needs at least "
                    f"{face_training_service.MIN_EMBEDDINGS_FOR_TRAINING} clear photos."
                ),
            },
        )

    # Phase 1: validate everything UP FRONT and capture the new
    # embeddings in memory. If any single photo fails the quality
    # gate we 422 the whole batch BEFORE touching the existing
    # embeddings. This is the user-facing safety contract: validation
    # failures must never destroy a working face training set.
    staged: list[face_training_service.RetrainStagedImage] = []
    for idx, img in enumerate(payload.images):
        emb, q, err = face_training_service.validate_for_training(img.image)
        if emb is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "bad_image",
                    "image_index": idx,
                    "message": err or face_training_service.TRAINING_BAD_IMAGE_MESSAGE,
                },
            )
        staged.append(
            face_training_service.RetrainStagedImage(
                image_data=img.image,
                label=img.label,
                embedding=emb,
                quality_score=q or 0.0,
            )
        )

    # Verify the employee exists before opening the atomic transaction
    # — gives a clean 404 instead of a less-helpful IntegrityError if
    # someone deleted the employee between page load and submit.
    if not face_images_service.list_for_employee(employee_id) and not _employee_exists(employee_id):
        raise HTTPException(status_code=404, detail=f"employee {employee_id} not found")

    # Phase 2: atomic swap. The helper opens ONE session_scope around
    # (insert new face_image rows → insert new embeddings → delete old
    # embeddings) so any failure rolls back to the pre-call state —
    # the admin's existing trained set is never destroyed by a half-
    # finished retrain.
    try:
        deleted, new_image_ids, _new_emb_ids = face_training_service.retrain_employee_atomic(
            employee_id=employee_id,
            staged=staged,
            created_by=user.id,
        )
    except Exception:
        log.exception("retrain_employee_atomic failed for emp=%s — old set preserved", employee_id)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "retrain_failed",
                "message": (
                    "Retrain failed. Existing trained faces were preserved. "
                    "Please try again."
                ),
            },
        )

    # Build the response from the freshly-inserted rows. list_for_
    # employee returns post-commit data so the UI grid lines up with
    # the new state.
    items: list[FaceImageOut] = []
    for rec in face_images_service.list_for_employee(employee_id):
        if rec.id in set(new_image_ids):
            items.append(_to_out(
                rec,
                embedding_id=None,
                embedding_error=None,
                quality_score=None,
            ))
    accepted = len(new_image_ids)
    log.info(
        "retrain done: emp=%s deleted_old=%d accepted_new=%d",
        employee_id, deleted, accepted,
    )
    return FullRetrainResponse(
        employeeId=employee_id,
        deletedEmbeddings=deleted,
        accepted=accepted,
        rejected=0,
        items=items,
        training=_training_status(employee_id),
    )


def _employee_exists(employee_id: str) -> bool:
    """Cheap existence check used right before opening the atomic
    retrain transaction. Saves a confusing IntegrityError if someone
    deleted the employee in another tab between page-load and submit."""
    from ..db import session_scope
    from ..models import Employee
    with session_scope() as session:
        return session.get(Employee, employee_id) is not None


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

    # Honor the same per-employee cap the upload path enforces — without
    # this, the camera-capture button would be a side-door around the
    # limit. Capture is admin-deliberate so we don't run a duplicate
    # check, but we do reject when the slot is full so the admin has
    # to use the Retrain flow on the upload panel.
    cap = face_training_service.capacity_state(employee_id)
    if cap.at_cap:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "at_capacity",
                "embeddings_count": cap.count,
                "max_recommended": face_training_service.MAX_EMBEDDINGS_PER_EMPLOYEE,
                "message": (
                    f"This employee already has {cap.count} face embeddings. "
                    "Use Retrain on the Face Training panel to replace the weakest."
                ),
            },
        )

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
