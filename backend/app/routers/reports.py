"""Excel report exports — admin and HR (HR scoped to their own company)."""

from __future__ import annotations

from datetime import date as date_cls, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from ..config import (
    EARLY_EXIT_GRACE_MIN,
    LATE_GRACE_MIN,
    LOCAL_TZ_OFFSET_MIN,
    SHIFT_END,
    SHIFT_START,
)
from ..dependencies import hr_scope, require_admin_or_hr
from ..services import reports as reports_service
from ..services.attendance import ShiftSettings, parse_hhmm
from ..services.auth import User

router = APIRouter(tags=["reports"], prefix="/api/reports")


def _parse_date(value: str, field: str) -> date_cls:
    try:
        return date_cls.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{field} must be YYYY-MM-DD")


def _today_local(tz_offset_min: int) -> date_cls:
    return datetime.now(timezone.utc).astimezone(
        timezone(timedelta(minutes=tz_offset_min))
    ).date()


def _shift() -> ShiftSettings:
    return ShiftSettings(
        start=parse_hhmm(SHIFT_START),
        end=parse_hhmm(SHIFT_END),
        late_grace_min=LATE_GRACE_MIN,
        early_exit_grace_min=EARLY_EXIT_GRACE_MIN,
        tz_offset_min=LOCAL_TZ_OFFSET_MIN,
    )


def _xlsx_response(payload: bytes, filename: str) -> Response:
    return Response(
        content=payload,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _resolve_company_filter(user: User, requested: Optional[str]) -> Optional[str]:
    """Honour HR scoping when present; admins may pass any ``company`` filter."""
    filter_active, target = hr_scope(user)
    if filter_active:
        # HR ignores any incoming ?company= override and is always pinned to
        # their own company (or empty -> empty result).
        return target or "__no_company__"
    return requested


@router.get("/daily.xlsx")
def daily_xlsx(
    date: Optional[str] = Query(None, description="YYYY-MM-DD (local). Defaults to today."),
    company: Optional[str] = Query(None),
    user: User = Depends(require_admin_or_hr),
) -> Response:
    shift = _shift()
    target = _parse_date(date, "date") if date else _today_local(shift.tz_offset_min)
    payload = reports_service.build_daily_xlsx(
        target_date=target,
        shift=shift,
        company_filter=_resolve_company_filter(user, company),
    )
    return _xlsx_response(payload, f"attendance-daily-{target.isoformat()}.xlsx")


@router.get("/range.xlsx")
def range_xlsx(
    start: str = Query(..., description="YYYY-MM-DD"),
    end: str = Query(..., description="YYYY-MM-DD"),
    name: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    user: User = Depends(require_admin_or_hr),
) -> Response:
    shift = _shift()
    start_d = _parse_date(start, "start")
    end_d = _parse_date(end, "end")
    if start_d > end_d:
        raise HTTPException(status_code=400, detail="start must be on or before end")
    if (end_d - start_d).days > 366:
        raise HTTPException(status_code=400, detail="range cannot exceed 366 days")
    payload = reports_service.build_range_xlsx(
        start_date=start_d,
        end_date=end_d,
        shift=shift,
        name_filter=name,
        company_filter=_resolve_company_filter(user, company),
    )
    return _xlsx_response(
        payload, f"attendance-range-{start_d.isoformat()}_to_{end_d.isoformat()}.xlsx",
    )


@router.get("/summary.xlsx")
def summary_xlsx(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    user: User = Depends(require_admin_or_hr),
) -> Response:
    shift = _shift()
    end_d = _parse_date(end, "end") if end else _today_local(shift.tz_offset_min)
    start_d = _parse_date(start, "start") if start else (end_d - timedelta(days=89))
    if start_d > end_d:
        raise HTTPException(status_code=400, detail="start must be on or before end")
    payload = reports_service.build_summary_xlsx(
        start_date=start_d,
        end_date=end_d,
        shift=shift,
        name_filter=name,
        company_filter=_resolve_company_filter(user, company),
    )
    return _xlsx_response(
        payload, f"attendance-summary-{start_d.isoformat()}_to_{end_d.isoformat()}.xlsx",
    )
