"""GET /api/attendance/* — daily and range attendance, sourced from the DB."""

from __future__ import annotations

from datetime import date as date_cls, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ..config import (
    EARLY_EXIT_GRACE_MIN,
    LATE_GRACE_MIN,
    LOCAL_TZ_OFFSET_MIN,
    SHIFT_END,
    SHIFT_START,
)
from ..db import session_scope
from ..dependencies import hr_scope, require_admin, require_admin_or_hr
from ..schemas.attendance import (
    AttendanceDayResponse,
    AttendanceRangeResponse,
    AttendanceRecord,
    ShiftConfig,
)
from ..services import employees as employees_service
from ..services.attendance import ShiftSettings, parse_hhmm
from ..services.auth import User
from ..services.daily_attendance import DailyAttendanceService, list_events_for_day
from ..services.logs import build_attendance_daily, build_attendance_range

router = APIRouter(
    tags=["attendance"],
    prefix="/api/attendance",
)


def _filter_rows_by_hr_company(rows: list[dict], target: str) -> list[dict]:
    """Resolve each row's owning employee (by name) and keep only rows
    whose company matches the HR caller's company (case-insensitive).
    Rows with no matching employee are dropped — they belong to no
    company and would otherwise leak across HR scopes."""
    if not target:
        return []
    directory = employees_service.all_employees()
    kept: list[dict] = []
    for row in rows:
        company = employees_service.company_for(row.get("name") or "", employees=directory)
        if company and company.strip().lower() == target:
            kept.append(row)
    return kept


def _shift_settings(
    start_q: Optional[str],
    end_q: Optional[str],
    late_grace_q: Optional[int],
    early_grace_q: Optional[int],
    tz_q: Optional[int],
) -> ShiftSettings:
    try:
        start_t = parse_hhmm(start_q or SHIFT_START)
        end_t = parse_hhmm(end_q or SHIFT_END)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="shift_start/shift_end must be HH:MM")
    if (start_t.hour * 60 + start_t.minute) >= (end_t.hour * 60 + end_t.minute):
        raise HTTPException(status_code=400, detail="shift_start must be before shift_end")
    return ShiftSettings(
        start=start_t,
        end=end_t,
        late_grace_min=late_grace_q if late_grace_q is not None else LATE_GRACE_MIN,
        early_exit_grace_min=early_grace_q if early_grace_q is not None else EARLY_EXIT_GRACE_MIN,
        tz_offset_min=tz_q if tz_q is not None else LOCAL_TZ_OFFSET_MIN,
    )


def _shift_response(shift: ShiftSettings) -> ShiftConfig:
    return ShiftConfig(
        start=shift.start.strftime("%H:%M"),
        end=shift.end.strftime("%H:%M"),
        late_grace_min=shift.late_grace_min,
        early_exit_grace_min=shift.early_exit_grace_min,
        timezone_offset_minutes=shift.tz_offset_min,
    )


def _today_local(tz_offset_min: int) -> date_cls:
    return datetime.now(timezone.utc).astimezone(
        timezone(timedelta(minutes=tz_offset_min))
    ).date()


def _parse_iso_date(value: str, field: str) -> date_cls:
    try:
        return date_cls.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{field} must be YYYY-MM-DD")


@router.get("/config", response_model=ShiftConfig)
def get_config(_user: User = Depends(require_admin_or_hr)) -> ShiftConfig:
    """Return the active shift configuration."""
    return _shift_response(_shift_settings(None, None, None, None, None))


@router.get("/daily", response_model=AttendanceDayResponse)
def daily(
    request: Request,
    date: Optional[str] = Query(None, description="YYYY-MM-DD (local). Defaults to today."),
    names: Optional[str] = Query(
        None,
        description="Comma-separated list of expected names; missing names are reported as Absent.",
    ),
    shift_start: Optional[str] = Query(None, description="Override shift start, HH:MM."),
    shift_end: Optional[str] = Query(None, description="Override shift end, HH:MM."),
    late_grace_min: Optional[int] = Query(None, ge=0, le=240),
    early_exit_grace_min: Optional[int] = Query(None, ge=0, le=240),
    tz_offset_minutes: Optional[int] = Query(None, ge=-720, le=840),
    user: User = Depends(require_admin_or_hr),
) -> AttendanceDayResponse:
    shift = _shift_settings(shift_start, shift_end, late_grace_min, early_exit_grace_min, tz_offset_minutes)
    target = _parse_iso_date(date, "date") if date else _today_local(shift.tz_offset_min)

    expected = [n for n in (names.split(",") if names else []) if n.strip()]
    base_url = str(request.base_url).rstrip("/")

    rows = build_attendance_daily(
        target_date=target,
        shift=shift,
        base_url=base_url,
        expected_names=expected or None,
    )
    filter_active, target_company = hr_scope(user)
    if filter_active:
        rows = _filter_rows_by_hr_company(rows, target_company)
    items = [AttendanceRecord(**row) for row in rows]
    return AttendanceDayResponse(
        date=target.isoformat(),
        shift=_shift_response(shift),
        count=len(items),
        items=items,
    )


@router.get("/range", response_model=AttendanceRangeResponse)
def range_(
    request: Request,
    start: str = Query(..., description="Range start date, YYYY-MM-DD (local)."),
    end: str = Query(..., description="Range end date, YYYY-MM-DD (local)."),
    name: Optional[str] = Query(None, description="Filter to one person (case-insensitive)."),
    shift_start: Optional[str] = Query(None),
    shift_end: Optional[str] = Query(None),
    late_grace_min: Optional[int] = Query(None, ge=0, le=240),
    early_exit_grace_min: Optional[int] = Query(None, ge=0, le=240),
    tz_offset_minutes: Optional[int] = Query(None, ge=-720, le=840),
    user: User = Depends(require_admin_or_hr),
) -> AttendanceRangeResponse:
    shift = _shift_settings(shift_start, shift_end, late_grace_min, early_exit_grace_min, tz_offset_minutes)
    start_d = _parse_iso_date(start, "start")
    end_d = _parse_iso_date(end, "end")
    if start_d > end_d:
        raise HTTPException(status_code=400, detail="start must be on or before end")
    if (end_d - start_d).days > 366:
        raise HTTPException(status_code=400, detail="range cannot exceed 366 days")

    base_url = str(request.base_url).rstrip("/")
    rows = build_attendance_range(
        start_date=start_d,
        end_date=end_d,
        shift=shift,
        base_url=base_url,
        name_filter=name,
    )
    filter_active, target_company = hr_scope(user)
    if filter_active:
        rows = _filter_rows_by_hr_company(rows, target_company)
    items = [AttendanceRecord(**row) for row in rows]
    return AttendanceRangeResponse(
        start=start_d.isoformat(),
        end=end_d.isoformat(),
        shift=_shift_response(shift),
        count=len(items),
        items=items,
    )


# ---------------------------------------------------------------------------
# State-machine admin endpoints
#
# Recompute / close-day operate on the persisted ``daily_attendance``
# rollup. They never touch `attendance_logs` rows directly (except the
# trailing BREAK_OUT → OUT relabel in close-day, which is intentional).
# All admin-only — these are operational tools for HR / IT, not
# something a regular HR user should be running.
# ---------------------------------------------------------------------------


class RecomputeRequest(BaseModel):
    employee_id: str = Field(..., min_length=1)
    date: str = Field(..., description="Local date YYYY-MM-DD")


class RecomputeResponse(BaseModel):
    employee_id: str
    date: str
    status: str
    in_time: Optional[str]
    out_time: Optional[str]
    total_work_seconds: int
    total_break_seconds: int
    break_count: int
    late_minutes: int
    early_exit_minutes: int
    is_day_closed: bool


class RecomputeRangeRequest(BaseModel):
    employee_id: Optional[str] = Field(default=None, min_length=1)
    start: str
    end: str


class RecomputeRangeResponse(BaseModel):
    start: str
    end: str
    rows_touched: int


class CloseDayRequest(BaseModel):
    date: str = Field(..., description="Local date YYYY-MM-DD to close")


class CloseDayResponse(BaseModel):
    date: str
    closed: int
    already_closed: int
    no_activity: int
    synthetic_outs: int


class AttendanceEventOut(BaseModel):
    id: int
    employee_id: Optional[str]
    name: str
    timestamp: str
    event_type: str
    camera_id: Optional[str]
    score: Optional[float]
    source: str


class AttendanceEventsResponse(BaseModel):
    date: str
    count: int
    items: list[AttendanceEventOut]


def _rollup_to_response(row) -> RecomputeResponse:  # type: ignore[no-untyped-def]
    return RecomputeResponse(
        employee_id=str(row.employee_id),
        date=row.work_date.isoformat(),
        status=str(row.status),
        in_time=row.in_time.isoformat() if row.in_time else None,
        out_time=row.out_time.isoformat() if row.out_time else None,
        total_work_seconds=int(row.total_work_seconds or 0),
        total_break_seconds=int(row.total_break_seconds or 0),
        break_count=int(row.break_count or 0),
        late_minutes=int(row.late_minutes or 0),
        early_exit_minutes=int(row.early_exit_minutes or 0),
        is_day_closed=bool(row.is_day_closed),
    )


@router.post("/recompute", response_model=RecomputeResponse)
def recompute_day(
    payload: RecomputeRequest,
    _user: User = Depends(require_admin),
) -> RecomputeResponse:
    work_date = _parse_iso_date(payload.date, "date")
    with session_scope() as session:
        row = DailyAttendanceService(session).recompute(
            employee_id=payload.employee_id, work_date=work_date,
        )
        return _rollup_to_response(row)


@router.post("/recompute-range", response_model=RecomputeRangeResponse)
def recompute_range(
    payload: RecomputeRangeRequest,
    _user: User = Depends(require_admin),
) -> RecomputeRangeResponse:
    start_d = _parse_iso_date(payload.start, "start")
    end_d = _parse_iso_date(payload.end, "end")
    if (end_d - start_d).days > 366:
        raise HTTPException(status_code=400, detail="range cannot exceed 366 days")
    with session_scope() as session:
        touched = DailyAttendanceService(session).recompute_range(
            employee_id=payload.employee_id, start=start_d, end=end_d,
        )
    return RecomputeRangeResponse(
        start=start_d.isoformat(), end=end_d.isoformat(), rows_touched=touched,
    )


@router.post("/close-day", response_model=CloseDayResponse)
def close_day(
    payload: CloseDayRequest,
    _user: User = Depends(require_admin),
) -> CloseDayResponse:
    work_date = _parse_iso_date(payload.date, "date")
    with session_scope() as session:
        result = DailyAttendanceService(session).close_day(work_date=work_date)
    return CloseDayResponse(
        date=work_date.isoformat(),
        closed=result.closed,
        already_closed=result.already_closed,
        no_activity=result.no_activity,
        synthetic_outs=result.synthetic_outs,
    )


@router.get("/events", response_model=AttendanceEventsResponse)
def list_events(
    date: str = Query(..., description="Local date YYYY-MM-DD"),
    employee_id: Optional[str] = Query(default=None),
    user: User = Depends(require_admin_or_hr),
) -> AttendanceEventsResponse:
    work_date = _parse_iso_date(date, "date")
    with session_scope() as session:
        rows = list_events_for_day(
            session, work_date=work_date, employee_id=employee_id,
        )
        items = [
            AttendanceEventOut(
                id=int(r.id),
                employee_id=r.employee_id,
                name=str(r.name),
                timestamp=r.timestamp.isoformat() if r.timestamp else "",
                event_type=str(r.event_type),
                camera_id=r.camera_id,
                score=float(r.score) if r.score is not None else None,
                source=str(r.source or ""),
            )
            for r in rows
            if r.event_type
        ]
    # HR scoping: restrict to events for employees inside the caller's
    # own company. Admin sees everything.
    filter_active, target_company = hr_scope(user)
    if filter_active:
        directory = employees_service.all_employees()
        own = target_company.strip().lower()
        keep_emp_ids = {
            e.id for e in directory if (e.company or "").strip().lower() == own
        }
        items = [it for it in items if it.employee_id in keep_emp_ids]
    return AttendanceEventsResponse(
        date=work_date.isoformat(), count=len(items), items=items,
    )
