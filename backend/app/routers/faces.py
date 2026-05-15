"""GET /api/faces/history — paginated face-capture history (DB-backed)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from ..config import DEFAULT_HISTORY_START, DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ..db import session_scope
from ..dependencies import hr_scope, require_admin_or_hr
from ..schemas.faces import FaceHistoryItem, FaceHistoryResponse
from ..services import employees as employees_service
from ..services.auth import User

router = APIRouter(tags=["faces"])


def _parse_boundary(value: str, field: str, *, end: bool) -> datetime:
    raw = value.strip()
    try:
        if raw.lower() == "now":
            return datetime.now(timezone.utc)
        if len(raw) == 10:
            dt = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
            if end:
                dt = dt.replace(hour=23, minute=59, second=59)
            return dt
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid '{field}' value: {value!r}. Expected 'now', 'YYYY-MM-DD', or ISO-8601.",
        )


def _build_image_url(row: dict) -> Optional[str]:
    data = row.get("image_data")
    return f"data:image/jpeg;base64,{data}" if data else None


def _ts_to_str(value: Any) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value or "")


@router.get("/api/faces/history", response_model=FaceHistoryResponse)
def face_history(
    start: str = Query(DEFAULT_HISTORY_START),
    end: str = Query("now"),
    limit: int = Query(DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(0, ge=0),
    latest: Optional[int] = Query(None, ge=1, le=MAX_PAGE_LIMIT),
    user: User = Depends(require_admin_or_hr),
) -> FaceHistoryResponse:
    # image_data IS NOT NULL hides rows pruned by the retention job
    # (services/cleanup.py): for older dates only the kept entry/exit
    # captures surface; today/yesterday are unaffected. Without this clause
    # pruned rows leak into the dashboard as bare timestamps with no image.
    where_sql = " WHERE image_data IS NOT NULL"
    where_params: dict = {}
    if latest is not None:
        effective_limit = latest
        effective_offset = 0
    else:
        start_dt = _parse_boundary(start, "start", end=False)
        end_dt = _parse_boundary(end, "end", end=True)
        if start_dt > end_dt:
            raise HTTPException(
                status_code=400,
                detail=f"'start' ({start}) must be on or before 'end' ({end}).",
            )
        effective_limit = limit
        effective_offset = offset
        where_sql += " AND timestamp >= :start_ts AND timestamp <= :end_ts"
        where_params = {"start_ts": start_dt, "end_ts": end_dt}

    filter_active, target = hr_scope(user)

    with session_scope() as session:
        if filter_active:
            # HR view: pull the unpaginated window from DB, filter by company
            # (resolved via name → employee match), then paginate the result
            # so HR pagination matches what they can actually see.
            rows = [
                dict(r)
                for r in session.execute(
                    text(
                        "SELECT id, name, timestamp, image_path, image_data FROM snapshot_logs"
                        f"{where_sql} ORDER BY timestamp DESC, id DESC"
                    ),
                    where_params,
                ).mappings().all()
            ]
            directory = employees_service.all_employees()
            filtered = [
                r for r in rows
                if (
                    employees_service.company_for(r.get("name") or "", employees=directory)
                    or ""
                ).strip().lower() == target
            ]
            total = len(filtered)
            window = filtered[effective_offset : effective_offset + effective_limit]
        else:
            total = int(session.execute(
                text(f"SELECT COUNT(*) FROM snapshot_logs{where_sql}"), where_params,
            ).scalar_one() or 0)
            window = [
                dict(r)
                for r in session.execute(
                    text(
                        "SELECT id, name, timestamp, image_path, image_data FROM snapshot_logs"
                        f"{where_sql} ORDER BY timestamp DESC, id DESC "
                        "LIMIT :limit OFFSET :offset"
                    ),
                    {**where_params, "limit": effective_limit, "offset": effective_offset},
                ).mappings().all()
            ]

    items = [
        FaceHistoryItem(
            id=row["image_path"],
            name=row["name"],
            entry=_ts_to_str(row["timestamp"]),
            exit=_ts_to_str(row["timestamp"]),
            image_url=_build_image_url(row),
        )
        for row in window
    ]
    return FaceHistoryResponse(
        count=len(items),
        total=total,
        limit=effective_limit,
        offset=effective_offset,
        items=items,
    )
