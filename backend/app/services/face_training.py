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


# ---------------------------------------------------------------------------
# Per-employee training-set sizing rules.
#
# These are the AUTHORITATIVE limits — both the upload endpoint and the
# UI read them from here, so changing the cap doesn't require touching
# the frontend constant separately. The frontend used to enforce 6
# images on its own and the backend was unbounded; that combination let
# the post-train cleanup (which clears `image_data` and effectively
# hides rows from the UI) "reset" the visible count and accumulate
# unbounded embeddings. The hard backend cap below closes that loop.
# ---------------------------------------------------------------------------
MIN_EMBEDDINGS_FOR_TRAINING = 3
MAX_EMBEDDINGS_PER_EMPLOYEE = 6

# Quality gates for upload-time training photos. Stricter than the live
# camera detector because the operator gets to choose this photo and we
# don't want one fuzzy enrollment dragging down recognition for an
# entire employee.
TRAIN_MIN_FACE_PX = 80          # min(bbox_w, bbox_h) — bigger == more pixels for embedding
TRAIN_MIN_DET_SCORE = 0.65      # InsightFace detector confidence floor for training

# Same-employee duplicate detection uses a TIGHTER threshold than the
# live recognition floor. Reason: an admin enrolling multiple angles for
# one person should NOT get nagged by a duplicate prompt — different
# angles of the same face naturally score 0.65–0.89 against the existing
# embeddings (the model is angle-invariant, so the same person matches
# strongly even from a different side). We only want to prompt when the
# upload is essentially the SAME photo as one already on file (≥ 0.90).
# Cross-employee matches keep using the regular live threshold —
# that's the "wrong-employee-selected" safety net and shouldn't be
# relaxed.
SAME_FACE_NEAR_IDENTICAL_THRESHOLD = 0.90


@dataclass
class EnrollOutcome:
    """One row's worth of feedback for the upload UI."""
    embedding_id: Optional[int]
    image_id: int
    accepted: bool
    quality_score: float
    error: Optional[str]


@dataclass(frozen=True)
class DuplicateMatch:
    """A pre-save match against an already-trained employee. Surfaced to
    the upload endpoint so it can prompt the admin instead of silently
    enrolling a face the system would already recognise as someone
    else."""
    matched_employee_id: str
    matched_name: str
    score: float
    same_employee: bool


def detect_face_in_image_data(
    raw: str | bytes,
) -> tuple[Optional[np.ndarray], Optional[float], Optional[str]]:
    """Lenient detector — returns embedding for any face the model finds
    above the live recognition threshold. Used by call sites that only
    need an embedding (e.g. live-frame paths) and don't enforce the
    stricter "single clear face" training rules.
    """
    bgr = _decode_to_bgr(raw)
    if bgr is None:
        return None, None, "could not decode image"
    face_svc = get_face_service()
    try:
        best = face_svc.detect_single(bgr)
    except FaceRecognitionError as exc:
        return None, None, str(exc)
    return best.embedding, float(best.det_score), None


# Generic message returned to the frontend for any quality failure — the
# spec calls for one polite copy regardless of the exact reason. Internal
# logs still record the specific cause.
TRAINING_BAD_IMAGE_MESSAGE = (
    "Image not suitable for training. Please upload a clear "
    "front/left/right face image."
)


def validate_for_training(
    raw: str | bytes,
) -> tuple[Optional[np.ndarray], Optional[float], Optional[str]]:
    """Strict pre-flight for training uploads. Returns
    ``(embedding, det_score, error_message)``.

    Rejects (returns ``error_message``) when:
      * the file can't be decoded as an image,
      * no face is detected,
      * MORE than one face is in the frame (group photos / two people
        in front of the camera) — admin must crop or retake,
      * the largest face is smaller than ``TRAIN_MIN_FACE_PX`` on its
        shortest side (subject too far / framed too loosely),
      * the InsightFace detector score is below
        ``TRAIN_MIN_DET_SCORE`` (catches blur, off-angle, occluded
        faces — the score correlates strongly with all three).

    The user-facing string is uniform on purpose; the specific reason
    is logged so ops can audit, but the admin only sees one consistent
    "image not suitable" message per the product spec.
    """
    bgr = _decode_to_bgr(raw)
    if bgr is None:
        log.info("training upload rejected: could not decode image")
        return None, None, TRAINING_BAD_IMAGE_MESSAGE
    face_svc = get_face_service()
    try:
        faces = face_svc.detect(bgr)
    except FaceRecognitionError as exc:
        log.info("training upload rejected: detect failed: %s", exc)
        return None, None, TRAINING_BAD_IMAGE_MESSAGE
    if not faces:
        log.info("training upload rejected: no face detected")
        return None, None, TRAINING_BAD_IMAGE_MESSAGE
    if len(faces) > 1:
        log.info(
            "training upload rejected: multiple faces detected (n=%d)", len(faces),
        )
        return None, None, TRAINING_BAD_IMAGE_MESSAGE
    best = faces[0]
    face_w = int(best.bbox[2] - best.bbox[0])
    face_h = int(best.bbox[3] - best.bbox[1])
    if min(face_w, face_h) < TRAIN_MIN_FACE_PX:
        log.info(
            "training upload rejected: face too small (%dx%d < %d)",
            face_w, face_h, TRAIN_MIN_FACE_PX,
        )
        return None, None, TRAINING_BAD_IMAGE_MESSAGE
    if float(best.det_score) < TRAIN_MIN_DET_SCORE:
        log.info(
            "training upload rejected: low detector score (%.2f < %.2f)",
            float(best.det_score), TRAIN_MIN_DET_SCORE,
        )
        return None, None, TRAINING_BAD_IMAGE_MESSAGE
    return best.embedding, float(best.det_score), None


@dataclass(frozen=True)
class CapacityState:
    """Snapshot of how full an employee's embedding slot is. Returned
    by :func:`capacity_state` so the upload endpoint can decide whether
    to admit, reject, or replace, and so the UI can show real numbers."""
    count: int
    at_cap: bool
    weakest_embedding_id: Optional[int]
    weakest_quality: float


def capacity_state(employee_id: str) -> CapacityState:
    with session_scope() as session:
        rows = session.execute(
            select(FaceEmbedding.id, FaceEmbedding.quality_score)
            .where(FaceEmbedding.employee_id == employee_id)
            .order_by(FaceEmbedding.quality_score.asc(), FaceEmbedding.id.asc())
        ).all()
    count = len(rows)
    if count == 0:
        return CapacityState(0, False, None, 0.0)
    weakest_id, weakest_q = int(rows[0][0]), float(rows[0][1])
    return CapacityState(
        count=count,
        at_cap=(count >= MAX_EMBEDDINGS_PER_EMPLOYEE),
        weakest_embedding_id=weakest_id,
        weakest_quality=weakest_q,
    )


def replace_weakest_embedding(
    *,
    employee_id: str,
    new_embedding: np.ndarray,
    new_quality: float,
    new_face_image_id: int,
) -> tuple[bool, Optional[int], Optional[int]]:
    """When at capacity, atomically swap out the lowest-quality stored
    embedding for the new one IF the new one is better. Returns
    ``(success, evicted_embedding_id, new_embedding_id)``.

    ``success=False`` means the new image's quality was below the
    existing weakest — caller should surface "image quality lower than
    existing trained faces" to the admin and NOT save anything. The
    caller is responsible for deleting/retaining the source FaceImage
    row appropriately.
    """
    cache = get_embedding_cache()
    with session_scope() as session:
        rows = session.execute(
            select(FaceEmbedding)
            .where(FaceEmbedding.employee_id == employee_id)
            .order_by(FaceEmbedding.quality_score.asc(), FaceEmbedding.id.asc())
        ).scalars().all()
        if not rows:
            # Race: someone deleted the row between capacity_state and
            # this call. Fall through to a plain insert.
            weakest_q = -1.0
        else:
            weakest = rows[0]
            weakest_q = float(weakest.quality_score)
            if float(new_quality) <= weakest_q:
                # Don't silently overwrite a better photo with a worse one.
                return False, None, None
            session.delete(weakest)
            session.flush()
        emb_row = FaceEmbedding(
            employee_id=str(employee_id),
            face_image_id=int(new_face_image_id),
            vector=cache.pack(new_embedding),
            dim=int(new_embedding.shape[0]),
            model_name="buffalo_l",
            quality_score=float(new_quality),
        )
        session.add(emb_row)
        session.flush()
        evicted_id = int(weakest.id) if rows else None
        new_id = int(emb_row.id)
    try:
        cache.reload_employee(str(employee_id))
    except Exception:
        log.exception("face cache refresh failed for emp_id=%s", employee_id)
    log.info(
        "replace_weakest: emp=%s evicted=%s new=%d new_quality=%.3f weakest_quality=%.3f",
        employee_id, evicted_id, new_id, float(new_quality), weakest_q,
    )
    return True, evicted_id, new_id


def delete_all_embeddings_for_employee(employee_id: str) -> int:
    """Wipe every embedding for one employee + clear the matching
    image_data stubs. Returns the number of embedding rows deleted.

    NOTE: This function uses its own session_scope and commits on its
    own. Prefer :func:`retrain_employee_atomic` for the Retrain flow —
    that one wraps the delete + new-insert in a single transaction so
    a mid-batch DB failure can't strand the employee with neither old
    nor new embeddings.
    """
    cache = get_embedding_cache()
    with session_scope() as session:
        rows = session.execute(
            select(FaceEmbedding)
            .where(FaceEmbedding.employee_id == employee_id)
        ).scalars().all()
        for r in rows:
            session.delete(r)
        deleted = len(rows)
    if deleted:
        try:
            cache.reload_employee(str(employee_id))
        except Exception:
            log.exception("face cache refresh failed for emp_id=%s", employee_id)
    log.info("delete_all_embeddings: cleared %d embedding(s) for emp=%s", deleted, employee_id)
    return deleted


@dataclass
class RetrainStagedImage:
    """One pre-validated training photo ready to commit during an
    atomic retrain. Caller builds this list AFTER `validate_for_training`
    succeeds — the embedding is already extracted at that point, so the
    transaction below never needs to talk to InsightFace."""
    image_data: str           # base64 / data-URL, will be persisted to face_images
    label: str
    embedding: np.ndarray     # 512-dim L2-normalised
    quality_score: float


def retrain_employee_atomic(
    *,
    employee_id: str,
    staged: list[RetrainStagedImage],
    created_by: Optional[str],
) -> tuple[int, list[int], list[int]]:
    """Atomically replace EVERY embedding for one employee with a fresh
    pre-validated batch. Returns ``(deleted_old, new_image_ids,
    new_embedding_ids)``.

    Safety guarantee: the delete of old embeddings AND the insert of
    new image rows + embedding rows all live in ONE session_scope
    transaction. Anything that raises mid-flight — DB error, FK
    violation, anything — rolls the whole transaction back, leaving
    the employee's previous embeddings intact. The caller never gets
    a state where the old set is gone but the new set isn't saved.

    Validation is the CALLER's responsibility — only call this once
    every staged image has cleared ``validate_for_training``. The
    cache reload happens AFTER the commit so the in-memory match
    matrix never sees a partial state.
    """
    # Pull base64 normalisation logic from face_images_service so the
    # rows written here match the layout the GET endpoint expects.
    from . import face_images as face_images_service
    cache = get_embedding_cache()

    with session_scope() as session:
        # 1) Stage new FaceImage rows. We insert these FIRST so their
        #    auto-generated ids exist for the new FaceEmbedding.face_
        #    image_id FK below — without this the embedding rows would
        #    point at nothing.
        new_image_rows: list[FaceImage] = []
        for s in staged:
            payload = face_images_service._normalize_image(s.image_data)  # noqa: SLF001
            row = FaceImage(
                employee_id=str(employee_id),
                label=(s.label or "").strip()[:64],
                image_data=payload,
                created_by=created_by,
            )
            session.add(row)
            session.flush()  # populate row.id
            new_image_rows.append(row)

        # 2) Build the new FaceEmbedding rows in memory.
        new_emb_rows: list[FaceEmbedding] = []
        for s, img_row in zip(staged, new_image_rows, strict=True):
            er = FaceEmbedding(
                employee_id=str(employee_id),
                face_image_id=int(img_row.id),
                vector=cache.pack(s.embedding),
                dim=int(s.embedding.shape[0]),
                model_name="buffalo_l",
                quality_score=float(s.quality_score),
            )
            new_emb_rows.append(er)

        # 3) Only AFTER staging the new state do we drop the old
        #    embeddings. Sitting inside the same transaction means
        #    if any of the next steps fails, the deletes roll back
        #    along with everything else.
        old_embs = session.execute(
            select(FaceEmbedding)
            .where(FaceEmbedding.employee_id == str(employee_id))
        ).scalars().all()
        deleted_count = len(old_embs)
        for e in old_embs:
            session.delete(e)

        # 4) Insert the new embeddings. flush() materialises ids
        #    while still inside the transaction so we can return them.
        for er in new_emb_rows:
            session.add(er)
        session.flush()

        new_image_ids = [int(r.id) for r in new_image_rows]
        new_emb_ids = [int(e.id) for e in new_emb_rows]

    # Outside the transaction: refresh the in-memory match matrix so
    # the next /identify call sees the new vectors and stops matching
    # the deleted ones.
    try:
        cache.reload_employee(str(employee_id))
    except Exception:
        log.exception("face cache refresh failed for emp_id=%s", employee_id)

    log.info(
        "retrain_employee_atomic: emp=%s deleted_old=%d new_emb=%d new_img=%d",
        employee_id, deleted_count, len(new_emb_ids), len(new_image_ids),
    )
    return deleted_count, new_image_ids, new_emb_ids


def find_duplicate_match(
    *,
    embedding: np.ndarray,
    target_employee_id: str,
) -> Optional[DuplicateMatch]:
    """Match an embedding against the in-memory cache and return match
    details, with two-tier thresholding:

      * **Cross-employee match** — uses the live recognition threshold.
        If a different employee's face looks like this upload, the
        admin gets prompted — that's the "wrong employee selected"
        safety net and must stay loose enough to fire reliably.

      * **Same-employee match** — uses a tighter threshold
        (``SAME_FACE_NEAR_IDENTICAL_THRESHOLD = 0.90``). The model is
        angle-invariant, so a brand-new side-view of the same person
        still matches their existing front view at ~0.75-0.88. Treating
        those as duplicates would block every legitimate multi-angle
        enrollment with a prompt. We only flag the upload as a
        "same-face duplicate" when the score is essentially saying
        "this is the SAME photo you already uploaded".

    Returns ``None`` when the upload should be allowed through
    silently (no match, or same-employee match below the tighter
    threshold = a legitimate new angle).
    """
    # Late import: recognition service depends on the embedding cache
    # which is built lazily and reads from the DB at first use.
    from .recognition import get_recognition_service
    result = get_recognition_service().match(embedding)
    if result.employee_id is None:
        return None
    same_employee = (str(result.employee_id) == str(target_employee_id))
    # Silently allow new-angle uploads for the same employee — only
    # near-identical photos should trip the dialog.
    if same_employee and float(result.score) < SAME_FACE_NEAR_IDENTICAL_THRESHOLD:
        log.info(
            "same-employee upload below near-identical threshold — "
            "treating as new angle: emp=%s score=%.3f thr=%.2f",
            target_employee_id, float(result.score), SAME_FACE_NEAR_IDENTICAL_THRESHOLD,
        )
        return None
    name_map = get_embedding_cache().id_to_name_map()
    return DuplicateMatch(
        matched_employee_id=str(result.employee_id),
        matched_name=name_map.get(result.employee_id, result.employee_id),
        score=float(result.score),
        same_employee=same_employee,
    )


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
