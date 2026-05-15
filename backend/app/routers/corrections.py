"""HR/Admin attendance corrections — report-level overrides keyed on
(employee, local date).

These endpoints power the **Settings → Edit Attendance Report** UI. HR
users can correct status, mark Paid Leave / WFH / LOP, and override
entry/exit times. Admin can do the same for any company; HR is scoped to
their own company by checking the named employee's record.

Raw camera logs are never mutated. Corrections are stored in the
``attendance_corrections`` table and applied on top of auto-detected
records by ``services.attendance.build_daily_records``.
"""

from __future__ import annotations

import logging
from datetime import date as date_cls, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..dependencies import require_admin_or_hr
from ..services import corrections as corrections_service
from ..services import employees as employees_service
from ..services.auth import User

log = logging.getLogger(__name__)

router = APIRouter(
    tags=["corrections"],
    prefix="/api/attendance/corrections",
)


def _validate_iso(value: Optional[str], field: str) -> Optional[str]:
    if value is None:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{field} must be ISO8601")
    return dt.isoformat()


def _validate_date(value: str) -> str:
    try:
        date_cls.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    return value


def _hr_company_check(user: User, employee_name: str) -> None:
    """HR can only correct employees in their own company. Admin: no check."""
    if user.role != "hr":
        return
    if not user.company:
        raise HTTPException(status_code=403, detail="HR account has no company assigned")
    employee = employees_service.match(employee_name)
    if employee is None:
        raise HTTPException(
            status_code=404,
            detail=f"No employee matched name {employee_name!r}",
        )
    if (employee.company or "").strip().lower() != user.company.strip().lower():
        raise HTTPException(
            status_code=403,
            detail="Cannot edit attendance for an employee outside your company",
        )


class CorrectionOut(BaseModel):
    name: str
    date: str
    entry_iso: Optional[str] = None
    exit_iso: Optional[str] = None
    total_break_seconds: Optional[int] = None
    missing_checkout_resolved: bool = False
    note: Optional[str] = None
    status_override: Optional[str] = None
    paid_leave: bool = False
    lop: bool = False
    wfh: bool = False
    updated_by: Optional[str] = None
    updated_at: str


def _row_to_out(row: dict) -> CorrectionOut:
    return CorrectionOut(
        name=row["name"],
        date=row["date"],
        entry_iso=row.get("entry_iso"),
        exit_iso=row.get("exit_iso"),
        total_break_seconds=row.get("total_break_seconds"),
        missing_checkout_resolved=bool(row.get("missing_checkout_resolved")),
        note=row.get("note"),
        status_override=row.get("status_override"),
        paid_leave=bool(int(row.get("paid_leave") or 0)),
        lop=bool(int(row.get("lop") or 0)),
        wfh=bool(int(row.get("wfh") or 0)),
        updated_by=row.get("updated_by"),
        updated_at=row["updated_at"],
    )


class ListCorrectionsResponse(BaseModel):
    items: list[CorrectionOut]


@router.get("", response_model=ListCorrectionsResponse)
def list_corrections(
    name: Optional[str] = Query(None, description="Filter to one employee"),
    start: Optional[str] = Query(None, description="Inclusive start, YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="Inclusive end, YYYY-MM-DD"),
    user: User = Depends(require_admin_or_hr),
) -> ListCorrectionsResponse:
    if start:
        _validate_date(start)
    if end:
        _validate_date(end)
    if name:
        _hr_company_check(user, name)
    rows = corrections_service.list_corrections(
        name=name, start_date=start, end_date=end
    )
    # When HR queries without a name filter, drop rows that aren't in their
    # company so the response can't leak other companies' edit history.
    if user.role == "hr" and not name:
        scoped = []
        user_company = user.company.strip().lower()
        for row in rows:
            employee = employees_service.match(row["name"])
            if employee and (employee.company or "").strip().lower() == user_company:
                scoped.append(row)
        rows = scoped
    return ListCorrectionsResponse(items=[_row_to_out(r) for r in rows])


class UpsertCorrectionRequest(BaseModel):
    name: str = Field(..., min_length=1)
    date: str = Field(..., description="YYYY-MM-DD (local)")
    entry_iso: Optional[str] = None
    exit_iso: Optional[str] = None
    total_break_seconds: Optional[int] = Field(None, ge=0)
    missing_checkout_resolved: bool = False
    note: Optional[str] = None
    status_override: Optional[str] = Field(
        None,
        description="One of: Present, Late, Early Exit, Absent, WFH, Paid Leave, LOP, Holiday",
    )
    paid_leave: Optional[bool] = None
    lop: Optional[bool] = None
    wfh: Optional[bool] = None


@router.post("", response_model=CorrectionOut)
def upsert(
    payload: UpsertCorrectionRequest,
    user: User = Depends(require_admin_or_hr),
) -> CorrectionOut:
    _validate_date(payload.date)
    _hr_company_check(user, payload.name)
    entry_iso = _validate_iso(payload.entry_iso, "entry_iso")
    exit_iso = _validate_iso(payload.exit_iso, "exit_iso")

    # Reject empty payloads — every accepted call must change something.
    if (
        entry_iso is None
        and exit_iso is None
        and payload.total_break_seconds is None
        and not payload.missing_checkout_resolved
        and not payload.note
        and payload.status_override is None
        and payload.paid_leave is None
        and payload.lop is None
        and payload.wfh is None
    ):
        raise HTTPException(
            status_code=400,
            detail="provide at least one field to change",
        )

    try:
        row = corrections_service.upsert_correction(
            name=payload.name,
            date=payload.date,
            entry_iso=entry_iso,
            exit_iso=exit_iso,
            total_break_seconds=payload.total_break_seconds,
            missing_checkout_resolved=payload.missing_checkout_resolved,
            note=payload.note,
            status_override=payload.status_override,
            paid_leave=payload.paid_leave,
            lop=payload.lop,
            wfh=payload.wfh,
            updated_by=user.username,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    log.info(
        "attendance correction upserted by %s for %s on %s",
        user.username, payload.name, payload.date,
    )
    return _row_to_out(row)


@router.delete("")
def delete(
    name: str = Query(...),
    date: str = Query(...),
    user: User = Depends(require_admin_or_hr),
) -> dict:
    _validate_date(date)
    _hr_company_check(user, name)
    deleted = corrections_service.delete_correction(name=name, date=date)
    log.info(
        "attendance correction deleted by %s for %s on %s (rows=%d)",
        user.username, name, date, deleted,
    )
    return {"status": "ok", "deleted": deleted}
