"""Admin endpoints for the unknown-face review queue.

Surfaces the cluster review flow:

* List + detail of clusters (paginated, filterable by status/label).
* Per-capture image stream (auth'd JPEG from disk).
* Patch label / discard cluster / discard single capture.
* Promote cluster to a new or existing employee.
* Retention purge.

All endpoints are admin-only. HR is intentionally excluded — clustering
state is cross-company by nature and an HR account shouldn't see faces
captured in front of cameras outside their own company.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies import require_admin
from ..models import (
    Camera,
    UnknownCaptureStatus,
    UnknownClusterStatus,
    UnknownFaceCapture,
    UnknownFaceCluster,
)
from ..services.auth import User
from ..services.unknown_capture import UnknownCaptureService
from ..services.unknown_promotion import PromotionError, UnknownPromotionService
from ..services.unknown_purge import UnknownPurgeService

log = logging.getLogger(__name__)
router = APIRouter(tags=["unknowns"])


# ---------------------------------------------------------------------------
# Pydantic schemas (kept inline to match the small-routers convention used
# elsewhere in this backend — e.g. routers/employees.py).
# ---------------------------------------------------------------------------


class UnknownCaptureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cluster_id: int
    file_path: str
    camera_id: Optional[int] = None
    camera_name: Optional[str] = None
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    det_score: float
    sharpness_score: float
    captured_at: datetime
    status: UnknownCaptureStatus
    created_at: datetime


class UnknownClusterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: Optional[str] = None
    status: UnknownClusterStatus
    member_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    promoted_employee_id: Optional[str] = None
    merged_into_cluster_id: Optional[int] = None
    representative_capture_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class UnknownClusterDetail(UnknownClusterRead):
    captures: list[UnknownCaptureRead] = []


class UnknownClusterListResponse(BaseModel):
    items: list[UnknownClusterRead]
    total: int
    limit: int
    offset: int


class UnknownClusterUpdate(BaseModel):
    label: Optional[str] = Field(default=None, max_length=128)


class PromoteToNewRequest(BaseModel):
    employee_code: Optional[str] = Field(default=None, min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    # Either ``designation`` (Super_Admin payload) or ``department`` is
    # accepted; routers fold both into the Employee.department column.
    designation: Optional[str] = Field(default=None, max_length=128)
    department: Optional[str] = Field(default=None, max_length=128)
    company: Optional[str] = Field(default=None, max_length=128)
    shift: Optional[str] = Field(default=None, max_length=64)
    dob: Optional[date] = None
    # Plain str (not EmailStr) to match the rest of this backend — adding
    # the email-validator dep just for this one field isn't worth it; the
    # employees router has the same convention.
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=32)
    mobile: Optional[str] = Field(default=None, max_length=32)
    is_active: bool = True


class PromoteResponse(BaseModel):
    cluster_id: int
    employee_id: str
    employee_code: str
    employee_name: str
    cluster_was_new_employee: bool
    captures_promoted: int
    captures_skipped: int
    total_employee_embeddings: int


class PurgeRequest(BaseModel):
    max_age_days: Optional[int] = Field(default=None, ge=1, le=3650)
    include_promoted: bool = False


class PurgeResponse(BaseModel):
    cutoff: datetime
    clusters_examined: int
    clusters_deleted: int
    captures_deleted: int
    files_deleted: int
    bytes_freed: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _representative_capture_ids(db: Session, cluster_ids: list[int]) -> dict[int, int]:
    """For each cluster id, return the id of its highest-quality KEEP
    capture (max ``det_score``, tie-break ``sharpness_score``). Two-step
    query so it works on both SQLite and Postgres without window functions.
    """
    if not cluster_ids:
        return {}
    max_per_cluster = (
        select(
            UnknownFaceCapture.cluster_id,
            func.max(UnknownFaceCapture.det_score).label("max_score"),
        )
        .where(
            and_(
                UnknownFaceCapture.cluster_id.in_(cluster_ids),
                UnknownFaceCapture.status == UnknownCaptureStatus.KEEP,
            )
        )
        .group_by(UnknownFaceCapture.cluster_id)
        .subquery()
    )
    stmt = (
        select(
            UnknownFaceCapture.cluster_id,
            func.max(UnknownFaceCapture.id).label("capture_id"),
        )
        .join(
            max_per_cluster,
            and_(
                UnknownFaceCapture.cluster_id == max_per_cluster.c.cluster_id,
                UnknownFaceCapture.det_score == max_per_cluster.c.max_score,
            ),
        )
        .where(UnknownFaceCapture.status == UnknownCaptureStatus.KEEP)
        .group_by(UnknownFaceCapture.cluster_id)
    )
    return {int(r[0]): int(r[1]) for r in db.execute(stmt).all()}


def _cluster_to_read(
    cluster: UnknownFaceCluster, *, representative_capture_id: Optional[int]
) -> UnknownClusterRead:
    base = UnknownClusterRead.model_validate(cluster)
    return base.model_copy(update={"representative_capture_id": representative_capture_id})


def _capture_to_read(
    cap: UnknownFaceCapture, *, camera_name: Optional[str]
) -> UnknownCaptureRead:
    base = UnknownCaptureRead.model_validate(cap)
    return base.model_copy(update={"camera_name": camera_name})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/api/unknowns/clusters", response_model=UnknownClusterListResponse)
def list_clusters(
    status_filter: Optional[UnknownClusterStatus] = Query(default=None, alias="status"),
    label: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> UnknownClusterListResponse:
    stmt = select(UnknownFaceCluster)
    count_stmt = select(func.count(UnknownFaceCluster.id))
    conds = []
    if status_filter is not None:
        conds.append(UnknownFaceCluster.status == status_filter)
    if label:
        like = f"%{label}%"
        conds.append(UnknownFaceCluster.label.ilike(like))
    if conds:
        stmt = stmt.where(and_(*conds))
        count_stmt = count_stmt.where(and_(*conds))
    stmt = stmt.order_by(UnknownFaceCluster.last_seen_at.desc()).limit(limit).offset(offset)
    items = list(db.execute(stmt).scalars().all())
    total = int(db.execute(count_stmt).scalar_one())
    rep_ids = _representative_capture_ids(db, [c.id for c in items])
    return UnknownClusterListResponse(
        items=[_cluster_to_read(c, representative_capture_id=rep_ids.get(c.id)) for c in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/api/unknowns/clusters/{cluster_id}", response_model=UnknownClusterDetail)
def get_cluster(
    cluster_id: int = PathParam(..., ge=1),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> UnknownClusterDetail:
    cluster = db.get(UnknownFaceCluster, cluster_id)
    if cluster is None:
        raise HTTPException(status_code=404, detail=f"Unknown cluster {cluster_id} not found")

    capture_rows = db.execute(
        select(UnknownFaceCapture)
        .where(UnknownFaceCapture.cluster_id == cluster_id)
        .order_by(UnknownFaceCapture.captured_at.desc())
    ).scalars().all()

    cam_ids = {int(c.camera_id) for c in capture_rows if c.camera_id is not None}
    cam_names: dict[int, str] = {}
    if cam_ids:
        for row in db.execute(
            select(Camera.id, Camera.name).where(Camera.id.in_(list(cam_ids)))
        ).all():
            cam_names[int(row[0])] = str(row[1] or "")

    captures = [
        _capture_to_read(
            cap,
            camera_name=cam_names.get(int(cap.camera_id)) if cap.camera_id is not None else None,
        )
        for cap in capture_rows
    ]
    rep_id = _representative_capture_ids(db, [cluster.id]).get(cluster.id)
    base = _cluster_to_read(cluster, representative_capture_id=rep_id)
    return UnknownClusterDetail(**base.model_dump(), captures=captures)


@router.get("/api/unknowns/captures/{capture_id}/image")
def get_capture_image(
    capture_id: int = PathParam(..., ge=1),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> FileResponse:
    cap = db.get(UnknownFaceCapture, capture_id)
    if cap is None:
        raise HTTPException(status_code=404, detail=f"Unknown capture {capture_id} not found")
    p = Path(cap.file_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Capture file missing on disk: {p}")
    return FileResponse(p, media_type="image/jpeg", filename=p.name)


@router.patch("/api/unknowns/clusters/{cluster_id}", response_model=UnknownClusterRead)
def update_cluster(
    payload: UnknownClusterUpdate,
    cluster_id: int = PathParam(..., ge=1),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> UnknownClusterRead:
    cluster = db.get(UnknownFaceCluster, cluster_id)
    if cluster is None:
        raise HTTPException(status_code=404, detail=f"Unknown cluster {cluster_id} not found")
    if cluster.status != UnknownClusterStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot edit cluster in status {cluster.status.value}",
        )
    data = payload.model_dump(exclude_unset=True)
    if "label" in data:
        cluster.label = data["label"]
    db.flush()
    rep_id = _representative_capture_ids(db, [cluster.id]).get(cluster.id)
    return _cluster_to_read(cluster, representative_capture_id=rep_id)


@router.delete(
    "/api/unknowns/captures/{capture_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_capture(
    capture_id: int = PathParam(..., ge=1),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    cap = db.get(UnknownFaceCapture, capture_id)
    if cap is None:
        raise HTTPException(status_code=404, detail=f"Unknown capture {capture_id} not found")
    if cap.status != UnknownCaptureStatus.KEEP:
        # Already discarded — idempotent no-op.
        return None
    UnknownCaptureService(db).demote_capture_and_recompute(
        capture=cap, cluster_id=int(cap.cluster_id),
    )
    return None


@router.delete(
    "/api/unknowns/clusters/{cluster_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def discard_cluster(
    cluster_id: int = PathParam(..., ge=1),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    cluster = db.get(UnknownFaceCluster, cluster_id)
    if cluster is None:
        raise HTTPException(status_code=404, detail=f"Unknown cluster {cluster_id} not found")
    if cluster.status not in (UnknownClusterStatus.PENDING, UnknownClusterStatus.MERGED):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot discard cluster in status {cluster.status.value}",
        )
    cluster.status = UnknownClusterStatus.IGNORED
    db.flush()
    UnknownCaptureService.reset_cooldown(cluster_id)
    UnknownCaptureService.invalidate_match_cache()
    return None


@router.post(
    "/api/unknowns/clusters/{cluster_id}/promote/new",
    response_model=PromoteResponse,
    status_code=201,
)
def promote_to_new_employee(
    payload: PromoteToNewRequest,
    cluster_id: int = PathParam(..., ge=1),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> PromoteResponse:
    data = payload.model_dump()
    try:
        outcome = UnknownPromotionService(db).promote_to_new_employee(
            cluster_id=cluster_id, employee_data=data, created_by=user.id,
        )
    except PromotionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    return PromoteResponse(
        cluster_id=outcome.cluster_id,
        employee_id=outcome.employee_id,
        employee_code=outcome.employee_code,
        employee_name=outcome.employee_name,
        cluster_was_new_employee=outcome.cluster_was_new_employee,
        captures_promoted=outcome.captures_promoted,
        captures_skipped=outcome.captures_skipped,
        total_employee_embeddings=outcome.total_employee_embeddings,
    )


@router.post(
    "/api/unknowns/clusters/{cluster_id}/promote/existing/{employee_id}",
    response_model=PromoteResponse,
)
def promote_to_existing_employee(
    cluster_id: int = PathParam(..., ge=1),
    employee_id: str = PathParam(..., min_length=1),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
) -> PromoteResponse:
    try:
        outcome = UnknownPromotionService(db).promote_to_existing_employee(
            cluster_id=cluster_id, employee_id=employee_id, created_by=user.id,
        )
    except PromotionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    return PromoteResponse(
        cluster_id=outcome.cluster_id,
        employee_id=outcome.employee_id,
        employee_code=outcome.employee_code,
        employee_name=outcome.employee_name,
        cluster_was_new_employee=outcome.cluster_was_new_employee,
        captures_promoted=outcome.captures_promoted,
        captures_skipped=outcome.captures_skipped,
        total_employee_embeddings=outcome.total_employee_embeddings,
    )


@router.post("/api/unknowns/purge", response_model=PurgeResponse)
def purge(
    payload: Optional[PurgeRequest] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> PurgeResponse:
    p = payload or PurgeRequest()
    outcome = UnknownPurgeService(db).purge(
        max_age_days=p.max_age_days, include_promoted=p.include_promoted,
    )
    return PurgeResponse(
        cutoff=outcome.cutoff,
        clusters_examined=outcome.clusters_examined,
        clusters_deleted=outcome.clusters_deleted,
        captures_deleted=outcome.captures_deleted,
        files_deleted=outcome.files_deleted,
        bytes_freed=outcome.bytes_freed,
    )
