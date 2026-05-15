"""Bridge from a stored face image to a face_embeddings row.

Splits the work the admin folder's TrainingService bundled into one
class: image bytes → InsightFace detection → 512-dim L2-normalised
vector → DB write → cache delta. Keeping it small and synchronous so
the existing /api/employees/{id}/face-images upload path can call it
inline without a worker queue.
"""

from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image
from sqlalchemy import select, update

from ..db import session_scope
from ..models import Employee, FaceEmbedding, FaceImage
from .embedding_cache import get_embedding_cache
from .face_service import FaceRecognitionError, get_face_service

log = logging.getLogger(__name__)


@dataclass
class EnrollOutcome:
    """One row's worth of feedback for the upload UI."""
    embedding_id: Optional[int]
    image_id: int
    accepted: bool
    quality_score: float
    error: Optional[str]


def _decode_to_bgr(raw: str | bytes) -> Optional[np.ndarray]:
    """Decode a base64 (with or without ``data:`` prefix) or raw bytes
    payload into a BGR numpy array suitable for InsightFace."""
    if isinstance(raw, str):
        if raw.startswith("data:") and "," in raw:
            raw = raw.split(",", 1)[1]
        try:
            data = base64.b64decode(raw, validate=False)
        except Exception:
            return None
    else:
        data = raw
    try:
        img = Image.open(io.BytesIO(data))
        # InsightFace's default cv2 path expects BGR; PIL gives RGB.
        rgb = np.array(img.convert("RGB"))
        return rgb[:, :, ::-1].copy()
    except Exception:
        return None


def enroll_face_image(image_id: int) -> EnrollOutcome:
    """Compute + persist the embedding for an existing FaceImage row.

    Skips silently if an embedding for this image already exists. The
    in-memory cache is refreshed for the affected employee on success
    so the next /api/recognition/identify call sees the new vector.
    """
    face = get_face_service()
    with session_scope() as session:
        img_row = session.get(FaceImage, image_id)
        if img_row is None:
            return EnrollOutcome(None, image_id, False, 0.0, "image not found")

        existing = session.execute(
            select(FaceEmbedding.id).where(FaceEmbedding.face_image_id == image_id)
        ).scalar_one_or_none()
        if existing is not None:
            return EnrollOutcome(int(existing), image_id, True, 0.0, None)

        emp_row = session.get(Employee, img_row.employee_id)
        if emp_row is None or not emp_row.is_active:
            return EnrollOutcome(None, image_id, False, 0.0, "employee inactive or missing")

        bgr = _decode_to_bgr(img_row.image_data or "")
        if bgr is None:
            return EnrollOutcome(None, image_id, False, 0.0, "could not decode image")

        try:
            best = face.detect_single(bgr)
        except FaceRecognitionError as exc:
            return EnrollOutcome(None, image_id, False, 0.0, str(exc))

        cache = get_embedding_cache()
        emb_row = FaceEmbedding(
            employee_id=str(img_row.employee_id),
            face_image_id=int(img_row.id),
            vector=cache.pack(best.embedding),
            dim=int(best.embedding.shape[0]),
            model_name="buffalo_l",
            quality_score=float(best.det_score),
        )
        session.add(emb_row)
        session.flush()
        emb_id = int(emb_row.id)
        emp_id = str(img_row.employee_id)
        score = float(best.det_score)

    # Refresh cache OUTSIDE the write transaction so an open session
    # isn't held during the cache lock.
    try:
        get_embedding_cache().reload_employee(emp_id)
    except Exception:
        log.exception("face cache refresh failed for emp_id=%s", emp_id)

    log.info(
        "face enrolled: image_id=%d emp_id=%s embedding_id=%d quality=%.2f",
        image_id, emp_id, emb_id, score,
    )
    return EnrollOutcome(emb_id, image_id, True, score, None)


def enroll_with_known_embedding(
    *,
    image_id: int,
    embedding: np.ndarray,
    quality_score: float,
) -> EnrollOutcome:
    """Persist an embedding for an existing FaceImage row WITHOUT
    re-running face detection. Used by the capture-from-camera path
    where we already detected the face on the full frame and would
    otherwise lose the embedding by re-detecting on the cropped JPEG
    (tight crops fail detection at typical face sizes).

    Skips silently if an embedding for this image already exists.
    """
    cache = get_embedding_cache()
    with session_scope() as session:
        img_row = session.get(FaceImage, image_id)
        if img_row is None:
            return EnrollOutcome(None, image_id, False, 0.0, "image not found")
        existing = session.execute(
            select(FaceEmbedding.id).where(FaceEmbedding.face_image_id == image_id)
        ).scalar_one_or_none()
        if existing is not None:
            return EnrollOutcome(int(existing), image_id, True, float(quality_score), None)
        emb_row = FaceEmbedding(
            employee_id=str(img_row.employee_id),
            face_image_id=int(img_row.id),
            vector=cache.pack(embedding),
            dim=int(embedding.shape[0]),
            model_name="buffalo_l",
            quality_score=float(quality_score),
        )
        session.add(emb_row)
        session.flush()
        emb_id = int(emb_row.id)
        emp_id = str(img_row.employee_id)

    try:
        get_embedding_cache().reload_employee(emp_id)
    except Exception:
        log.exception("face cache refresh failed for emp_id=%s", emp_id)

    log.info(
        "face enrolled (known embedding): image_id=%d emp_id=%s embedding_id=%d quality=%.2f",
        image_id, emp_id, emb_id, quality_score,
    )
    return EnrollOutcome(emb_id, image_id, True, float(quality_score), None)


def enroll_employee_all(employee_id: str) -> list[EnrollOutcome]:
    """Re-process every stored face image for an employee, then **discard
    the inline image_data** for every row that now has an embedding so the
    DB isn't carrying redundant training photos forever (privacy + storage).

    The recognition hot-path only reads ``face_embeddings.vector`` — once
    the embedding row exists, the source image is no longer needed for
    live matching. The ``face_images`` row itself stays as an audit trail
    (id, employee_id, label, created_at, created_by) so we can answer
    "how many photos was this person trained on?" later; only the heavy
    base64 payload is cleared.

    Used by the 'Train' button.
    """
    with session_scope() as session:
        image_ids = [
            int(r[0])
            for r in session.execute(
                select(FaceImage.id)
                .where(FaceImage.employee_id == employee_id)
                .order_by(FaceImage.created_at.desc(), FaceImage.id.desc())
            ).all()
        ]
    outcomes = [enroll_face_image(i) for i in image_ids]
    # Cleanup pass: clear image_data on every face_image of this employee
    # that now has at least one embedding. Idempotent and safe to re-run
    # — already-cleared rows just match nothing.
    if any(o.accepted for o in outcomes):
        purge_trained_image_data(employee_id=employee_id)
    return outcomes


def purge_trained_image_data(*, employee_id: Optional[str] = None) -> int:
    """Wipe the heavy ``image_data`` payload on every FaceImage that has
    an embedding on file. Returns the number of rows cleaned.

    Scope: when ``employee_id`` is provided, only that employee's images
    are touched (used by the Train button). When ``None``, every trained
    image in the table is cleaned (used by the one-off retroactive
    backfill — the rows imported before this policy landed).

    Privacy + storage rationale: recognition only needs the 2 KB
    embedding vector; the 50–200 KB base64 source photo is dead weight
    once the embedding has been computed.
    """
    with session_scope() as session:
        # Subquery: ids of face_images that have at least one embedding.
        trained_ids_subq = (
            select(FaceEmbedding.face_image_id)
            .where(FaceEmbedding.face_image_id.is_not(None))
            .distinct()
        )
        stmt = (
            update(FaceImage)
            .where(FaceImage.id.in_(trained_ids_subq))
            # Skip rows already cleared so the rowcount reflects real work
            # and we don't pointlessly bump updated_at.
            .where(FaceImage.image_data != "")
            .values(image_data="")
        )
        if employee_id is not None:
            stmt = stmt.where(FaceImage.employee_id == employee_id)
        result = session.execute(stmt)
        n = int(result.rowcount or 0)
    if n:
        log.info(
            "face_images: cleared image_data on %d trained row(s) for emp=%s",
            n, employee_id or "(all)",
        )
    return n


def remove_embeddings_for_image(image_id: int) -> int:
    """Cascade delete via SQLAlchemy + refresh cache. Called when a
    face image is deleted via the existing /api/face-images/{id}
    endpoint so stale embeddings don't keep matching."""
    affected_emp: Optional[str] = None
    with session_scope() as session:
        rows = session.execute(
            select(FaceEmbedding).where(FaceEmbedding.face_image_id == image_id)
        ).scalars().all()
        for r in rows:
            affected_emp = str(r.employee_id)
            session.delete(r)
        count = len(rows)
    if affected_emp:
        try:
            get_embedding_cache().reload_employee(affected_emp)
        except Exception:
            log.exception("face cache refresh failed for emp_id=%s", affected_emp)
    return count
