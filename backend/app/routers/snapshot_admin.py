"""Admin-only snapshot housekeeping endpoints — Settings → Snapshots."""

from __future__ import annotations

from datetime import date as date_cls

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import require_admin
from ..services import cleanup as cleanup_service

router = APIRouter(tags=["snapshots-admin"])


@router.get(
    "/api/admin/snapshots/stats",
    dependencies=[Depends(require_admin)],
)
def snapshots_stats() -> dict:
    return cleanup_service.snapshot_storage_stats()


@router.delete(
    "/api/admin/snapshots/purge",
    dependencies=[Depends(require_admin)],
)
def snapshots_purge(
    before_date: str = Query(..., description="YYYY-MM-DD (local). Image data on rows older than this date is cleared."),
) -> dict:
    try:
        cutoff = date_cls.fromisoformat(before_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="before_date must be YYYY-MM-DD")
    if cutoff > cleanup_service.today_local():
        raise HTTPException(
            status_code=400,
            detail="before_date cannot be in the future",
        )
    cleared = cleanup_service.purge_image_data_before(cutoff)
    return {"status": "purged", "before_date": cutoff.isoformat(), "cleared": cleared}
