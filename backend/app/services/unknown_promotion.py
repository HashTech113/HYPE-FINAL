"""Promote an unknown-face cluster to an Employee.

Headline UX: admin reviews a cluster, clicks "Add as new employee" or
"Add to existing employee", and the system enrols every quality-ranked
KEEP capture as a training image — using the **stored capture-time
embedding** verbatim instead of re-running face detection on the
saved JPG crop.

Why reuse the stored embedding?

* It was produced by the same InsightFace ``buffalo_l`` pipeline the
  recognition path uses at runtime, against the full-resolution camera
  frame.
* Re-running detection on a cropped, JPEG-compressed sub-image
  introduces a measurable accuracy drop (smaller context, JPEG
  quantization perturbing pixel values).
* The cluster *was already formed* by these embeddings — promoting
  them as-is preserves whatever similarity grouped the captures.

Storage adaptation: the current backend stores training images as
**base64 text** in ``face_images.image_data`` (not a file path), so the
JPG bytes are read off disk, base64-encoded, and inserted into that
column. The ``face_embeddings`` row reuses the capture's stored
embedding bytes — never re-extracted.

On success, ``embedding_cache.load_from_db()`` is invoked so the very
next camera frame of this person matches the new employee, not the
(now stale) cluster centroid.
"""

from __future__ import annotations

import base64
import logging
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..models import (
    Employee,
    FaceEmbedding,
    FaceImage,
    UnknownCaptureStatus,
    UnknownClusterStatus,
    UnknownFaceCapture,
    UnknownFaceCluster,
)
from .embedding_cache import get_embedding_cache
from .face_training import MAX_EMBEDDINGS_PER_EMPLOYEE
from .lookups import (
    get_or_create_company_id,
    get_or_create_department_id,
    get_or_create_shift_id,
)
from .unknown_capture import UnknownCaptureService

log = logging.getLogger(__name__)


class PromotionError(RuntimeError):
    """Raised when a cluster can't be promoted. The router translates this
    into the appropriate HTTP status. ``code`` is the structured error
    code (e.g. 'at_capacity', 'too_many_images') that the frontend
    matches against — keeps the UI from string-matching the message."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        code: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.extra = extra or {}


@dataclass(frozen=True)
class PromoteOutcome:
    cluster_id: int
    employee_id: str
    employee_code: str
    employee_name: str
    cluster_was_new_employee: bool
    captures_promoted: int
    captures_skipped: int
    total_employee_embeddings: int


class UnknownPromotionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def promote_to_new_employee(
        self,
        *,
        cluster_id: int,
        employee_data: dict,
        capture_ids: Optional[list[int]] = None,
        created_by: Optional[str] = None,
    ) -> PromoteOutcome:
        cluster = self._load_promotable(cluster_id)
        # Bound the request size at the per-employee cap. New employee
        # path is always mode='add' (there are no existing embeddings to
        # replace), so > MAX is unambiguously wrong.
        if capture_ids is not None and len(capture_ids) > MAX_EMBEDDINGS_PER_EMPLOYEE:
            raise PromotionError(
                f"Cannot promote more than {MAX_EMBEDDINGS_PER_EMPLOYEE} captures.",
                status_code=422,
                code="too_many_images",
                extra={"max": MAX_EMBEDDINGS_PER_EMPLOYEE, "selected": len(capture_ids)},
            )

        supplied_code = (employee_data.get("employee_code") or "").strip() or None
        code = supplied_code if supplied_code else self._next_employee_code()
        if supplied_code is not None and self._employee_code_taken(supplied_code):
            raise PromotionError(
                f"employee_code '{supplied_code}' already exists", status_code=409
            )

        new_id = f"emp-{uuid.uuid4().hex[:10]}"
        company = (employee_data.get("company") or "").strip()
        department = (employee_data.get("department") or "").strip()
        shift = (employee_data.get("shift") or "").strip()
        dob = employee_data.get("dob")
        if isinstance(dob, date):
            dob = dob.isoformat()
        elif dob is None:
            dob = ""
        designation_raw = (employee_data.get("designation") or "").strip()
        # Current Employee model has no "designation" column — but it has
        # "department". Most callers will send department + designation
        # separately; we keep department authoritative and only fall back
        # to designation if department is blank.
        if not department and designation_raw:
            department = designation_raw

        company_id = get_or_create_company_id(self.db, company) if company else None
        department_id = (
            get_or_create_department_id(self.db, department) if department else None
        )
        shift_id = get_or_create_shift_id(self.db, shift) if shift else None

        employee = Employee(
            id=new_id,
            name=str(employee_data["name"]).strip(),
            employee_code=code,
            company=company,
            company_id=company_id,
            department=department,
            department_id=department_id,
            shift=shift,
            shift_id=shift_id,
            role="Employee",
            dob=str(dob),
            image_url="",
            email=(employee_data.get("email") or "").strip(),
            mobile=(employee_data.get("phone") or employee_data.get("mobile") or "").strip(),
            salary_package="",
            is_active=bool(employee_data.get("is_active", True)),
        )
        self.db.add(employee)
        self.db.flush()

        promoted, skipped = self._migrate_captures(
            cluster=cluster, employee=employee,
            capture_ids=capture_ids, created_by=created_by,
        )
        self._finalize_cluster(cluster, employee_id=employee.id)

        total = int(
            self.db.execute(
                select(func.count(FaceEmbedding.id)).where(
                    FaceEmbedding.employee_id == employee.id
                )
            ).scalar_one()
        )
        log.info(
            "Promoted cluster=%s -> NEW employee=%s code=%s promoted=%d skipped=%d",
            cluster.id, employee.id, employee.employee_code, promoted, skipped,
        )
        return PromoteOutcome(
            cluster_id=cluster.id,
            employee_id=employee.id,
            employee_code=employee.employee_code,
            employee_name=employee.name,
            cluster_was_new_employee=True,
            captures_promoted=promoted,
            captures_skipped=skipped,
            total_employee_embeddings=total,
        )

    def promote_to_existing_employee(
        self,
        *,
        cluster_id: int,
        employee_id: str,
        capture_ids: Optional[list[int]] = None,
        mode: str = "add",
        created_by: Optional[str] = None,
    ) -> PromoteOutcome:
        """Add the selected cluster captures to an existing employee.

        ``mode='add'``     — appends. Rejects with 409 ``at_capacity``
                             when the new total would exceed
                             :data:`MAX_EMBEDDINGS_PER_EMPLOYEE`. The
                             admin's selection isn't truncated; the
                             frontend is expected to either trim the
                             selection or re-submit with ``mode='replace'``.
        ``mode='replace'`` — wipes every existing embedding for this
                             employee first, then inserts the selected
                             ones. Atomic: the deletes share the same
                             transaction as the inserts, so any
                             mid-flight failure rolls back to the
                             pre-call state (old embeddings preserved).
        """
        if mode not in ("add", "replace"):
            raise PromotionError(
                f"Invalid mode '{mode}', expected 'add' or 'replace'",
                status_code=422, code="invalid_mode",
            )

        cluster = self._load_promotable(cluster_id)
        employee = self.db.get(Employee, employee_id)
        if employee is None:
            raise PromotionError(f"Employee {employee_id} not found", status_code=404)
        if not employee.is_active:
            raise PromotionError("Cannot promote into an inactive employee")

        # Selection size guard (applies to both modes).
        selected_count = len(capture_ids) if capture_ids is not None else None
        if selected_count is not None and selected_count > MAX_EMBEDDINGS_PER_EMPLOYEE:
            raise PromotionError(
                f"Cannot promote more than {MAX_EMBEDDINGS_PER_EMPLOYEE} captures.",
                status_code=422, code="too_many_images",
                extra={"max": MAX_EMBEDDINGS_PER_EMPLOYEE, "selected": selected_count},
            )

        # Capacity check (mode='add' only — replace wipes first so the
        # final count is just the new selection).
        if mode == "add":
            current = int(
                self.db.execute(
                    select(func.count(FaceEmbedding.id)).where(
                        FaceEmbedding.employee_id == employee.id
                    )
                ).scalar_one()
            )
            # Use the explicit selection size when provided; otherwise
            # fall back to the cluster's KEEP count so legacy callers
            # that pass capture_ids=None still get cap protection.
            incoming = selected_count if selected_count is not None else self._count_keep_captures(cluster.id)
            if current + incoming > MAX_EMBEDDINGS_PER_EMPLOYEE:
                raise PromotionError(
                    f"Employee already has {current} embeddings — adding "
                    f"{incoming} more would exceed the cap of "
                    f"{MAX_EMBEDDINGS_PER_EMPLOYEE}. Use Retrain to replace "
                    f"the existing set.",
                    status_code=409, code="at_capacity",
                    extra={
                        "embeddings_count": current,
                        "incoming": incoming,
                        "max_recommended": MAX_EMBEDDINGS_PER_EMPLOYEE,
                    },
                )

        # mode='replace' → delete first, in the SAME db session so any
        # mid-flight failure rolls back together with the inserts.
        deleted = 0
        if mode == "replace":
            old = self.db.execute(
                select(FaceEmbedding).where(
                    FaceEmbedding.employee_id == employee.id
                )
            ).scalars().all()
            for e in old:
                self.db.delete(e)
            deleted = len(old)
            self.db.flush()
            log.info(
                "promote(replace): wiped %d existing embedding(s) for emp=%s before insert",
                deleted, employee.id,
            )

        promoted, skipped = self._migrate_captures(
            cluster=cluster, employee=employee,
            capture_ids=capture_ids, created_by=created_by,
        )
        if promoted == 0:
            raise PromotionError(
                f"No captures could be added to employee {employee.employee_code}: "
                f"{skipped} skipped (duplicates or missing files)"
            )
        self._finalize_cluster(cluster, employee_id=employee.id)

        total = int(
            self.db.execute(
                select(func.count(FaceEmbedding.id)).where(
                    FaceEmbedding.employee_id == employee.id
                )
            ).scalar_one()
        )
        log.info(
            "Promoted cluster=%s -> EXISTING employee=%s code=%s mode=%s "
            "promoted=%d skipped=%d deleted_old=%d total_now=%d",
            cluster.id, employee.id, employee.employee_code, mode,
            promoted, skipped, deleted, total,
        )
        return PromoteOutcome(
            cluster_id=cluster.id,
            employee_id=employee.id,
            employee_code=employee.employee_code,
            employee_name=employee.name,
            cluster_was_new_employee=False,
            captures_promoted=promoted,
            captures_skipped=skipped,
            total_employee_embeddings=total,
        )

    def _count_keep_captures(self, cluster_id: int) -> int:
        return int(
            self.db.execute(
                select(func.count(UnknownFaceCapture.id)).where(
                    and_(
                        UnknownFaceCapture.cluster_id == cluster_id,
                        UnknownFaceCapture.status == UnknownCaptureStatus.KEEP,
                    )
                )
            ).scalar_one()
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _load_promotable(self, cluster_id: int) -> UnknownFaceCluster:
        cluster = self.db.get(UnknownFaceCluster, cluster_id)
        if cluster is None:
            raise PromotionError(f"Unknown cluster {cluster_id} not found", status_code=404)
        if cluster.status != UnknownClusterStatus.PENDING:
            raise PromotionError(
                f"Cluster {cluster_id} is {cluster.status.value}, not PENDING — "
                f"only PENDING clusters can be promoted",
                status_code=409,
            )
        return cluster

    def _employee_code_taken(self, code: str) -> bool:
        row = self.db.execute(
            select(Employee.id).where(Employee.employee_code == code).limit(1)
        ).scalar_one_or_none()
        return row is not None

    def _next_employee_code(self) -> str:
        """Same allocation strategy as the rest of the codebase — sequential
        ``EMP-NNNNNN`` with a probe loop in case the count-based candidate is
        taken (after manual codes or deletes).
        """
        count = int(self.db.execute(select(func.count(Employee.id))).scalar_one())
        base = count + 1
        for offset in range(64):
            candidate = f"EMP-{base + offset:06d}"
            if not self._employee_code_taken(candidate):
                return candidate
        raise PromotionError(
            "could not allocate a unique employee_code", status_code=500
        )

    def _migrate_captures(
        self,
        *,
        cluster: UnknownFaceCluster,
        employee: Employee,
        capture_ids: Optional[list[int]],
        created_by: Optional[str],
    ) -> tuple[int, int]:
        """Copy KEEP captures into the employee's training images. Reuses
        each capture's stored embedding verbatim (already produced by
        the same buffalo_l pipeline live recognition uses).

        ``capture_ids`` filters the migration to a specific subset of
        the cluster's KEEP captures — the admin-selected set from the
        Cluster Detail dialog. Each requested id MUST belong to this
        cluster AND still be in KEEP status; mismatches raise so the
        admin sees a clear error instead of a silent partial promote.

        Returns ``(promoted, skipped)``. Skip reasons: file missing on
        disk, unreadable, or capture id not eligible for this cluster.
        """
        base_q = (
            select(UnknownFaceCapture)
            .where(
                and_(
                    UnknownFaceCapture.cluster_id == cluster.id,
                    UnknownFaceCapture.status == UnknownCaptureStatus.KEEP,
                )
            )
            .order_by(
                UnknownFaceCapture.det_score.desc(),
                UnknownFaceCapture.sharpness_score.desc(),
            )
        )
        all_captures = self.db.execute(base_q).scalars().all()
        if not all_captures:
            return 0, 0

        if capture_ids is None:
            captures = all_captures
        else:
            wanted = set(int(i) for i in capture_ids)
            captures = [c for c in all_captures if int(c.id) in wanted]
            # Surface mismatched ids as a hard error — a missing id
            # usually means the admin's UI is out of date or someone
            # discarded a capture between selection and submit.
            missing = wanted - {int(c.id) for c in captures}
            if missing:
                raise PromotionError(
                    f"Selected captures not found or not eligible: {sorted(missing)}",
                    status_code=422, code="invalid_capture_ids",
                    extra={"missing_ids": sorted(missing)},
                )
            if not captures:
                return 0, 0

        promoted = 0
        skipped = 0
        for cap in captures:
            src = Path(cap.file_path)
            if not src.exists():
                log.warning("Capture %s file missing at %s; skipping", cap.id, src)
                skipped += 1
                continue
            try:
                jpg_bytes = src.read_bytes()
            except OSError as exc:
                log.warning("Capture %s read failed: %s", cap.id, exc)
                skipped += 1
                continue

            image_b64 = base64.b64encode(jpg_bytes).decode("ascii")

            image_row = FaceImage(
                employee_id=employee.id,
                label=cluster.label or f"cluster_{cluster.id}",
                image_data=image_b64,
                created_by=created_by,
            )
            self.db.add(image_row)
            self.db.flush()

            emb_row = FaceEmbedding(
                employee_id=employee.id,
                face_image_id=image_row.id,
                vector=cap.embedding,
                dim=int(cap.embedding_dim),
                model_name=cap.model_name,
                quality_score=float(cap.det_score),
            )
            self.db.add(emb_row)
            promoted += 1

        self.db.flush()
        return promoted, skipped

    def _finalize_cluster(
        self, cluster: UnknownFaceCluster, *, employee_id: str
    ) -> None:
        cluster.status = UnknownClusterStatus.PROMOTED
        cluster.promoted_employee_id = employee_id
        self.db.flush()
        # Hot-reload the recognition cache so the next frame of this
        # person matches the new employee — the alternative is a delay
        # until the worker re-loads on its own cadence.
        try:
            get_embedding_cache().load_from_db()
        except Exception:
            log.exception("embedding cache reload failed after promotion")
        UnknownCaptureService.reset_cooldown(cluster.id)
        UnknownCaptureService.invalidate_match_cache()
