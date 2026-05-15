"""Manual attendance corrections.

Two flavors of override live in the same ``attendance_report_edits`` table
(renamed from the legacy ``attendance_corrections``), keyed on (employee
name, local date):

* **Log corrections** — entry/exit ISO time + break seconds + missing-checkout
  flag. Used when face-capture timestamps are wrong (camera outage, missed
  exit, etc).
* **Report-level overrides** — ``status_override`` (final string), and the
  flags ``paid_leave``/``lop``/``wfh``. Used by HR/Admin to mark days that
  the camera pipeline can't infer (paid leave, LOP, WFH days).

Both flavors are applied on top of the auto-detected record at read time
inside ``services.attendance.build_daily_records``. Raw camera logs are
never mutated.

The DB column for the ``note`` field is ``notes`` and the day column is
``work_date`` (``Date`` type). The public dict shape this module returns
keeps the legacy keys ``note`` and ``date`` so callers (routers, the
attendance reducer) don't have to change.
"""

from __future__ import annotations

from datetime import date as date_cls, datetime, timezone
from typing import Optional

from sqlalchemy import and_, select

from ..db import excluded_of, session_scope, upsert_on_conflict_do_update
from ..models import AttendanceReportEdit
from . import employees as employees_service


def _normalize(name: str) -> str:
    return " ".join(name.strip().split())


# Whitelist for status_override. Includes the auto-classified statuses plus
# the HR-only overrides that the camera pipeline can't infer.
ALLOWED_STATUS_OVERRIDES: frozenset[str] = frozenset(
    {"Present", "Late", "Early Exit", "Absent", "WFH", "Paid Leave", "LOP", "Holiday"}
)


def _parse_date(value: str) -> date_cls:
    return date_cls.fromisoformat(value)


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _row_to_dict(row: AttendanceReportEdit) -> dict:
    """Public dict shape — preserves legacy keys (``date`` not ``work_date``,
    ``note`` not ``notes``) so callers don't have to change."""
    return {
        "name": row.name,
        "date": row.work_date.isoformat() if row.work_date else None,
        "entry_iso": _iso(row.entry_iso),
        "exit_iso": _iso(row.exit_iso),
        "total_break_seconds": row.total_break_seconds,
        "missing_checkout_resolved": int(bool(row.missing_checkout_resolved)),
        "note": row.notes,
        "status_override": row.status_override,
        "paid_leave": int(bool(row.paid_leave)),
        "lop": int(bool(row.lop)),
        "wfh": int(bool(row.wfh)),
        "updated_by": row.updated_by,
        "updated_at": _iso(row.updated_at) or "",
    }


def upsert_correction(
    *,
    name: str,
    date: str,
    entry_iso: Optional[str] = None,
    exit_iso: Optional[str] = None,
    total_break_seconds: Optional[int] = None,
    missing_checkout_resolved: bool = False,
    note: Optional[str] = None,
    status_override: Optional[str] = None,
    paid_leave: Optional[bool] = None,
    lop: Optional[bool] = None,
    wfh: Optional[bool] = None,
    updated_by: Optional[str] = None,
) -> dict:
    canonical = _normalize(name)
    if not canonical:
        raise ValueError("name must be non-empty")
    if not date:
        raise ValueError("date must be non-empty")
    if status_override is not None and status_override not in ALLOWED_STATUS_OVERRIDES:
        raise ValueError(
            f"status_override must be one of {sorted(ALLOWED_STATUS_OVERRIDES)}"
        )

    work_date = _parse_date(date)
    now = datetime.now(timezone.utc)

    # Resolve to employees.id for the FK column. NULL on miss is fine —
    # the schema allows it, and the (name, work_date) UNIQUE keeps upsert
    # semantics intact even for unmatched names.
    matched = employees_service.match(canonical)
    employee_id = matched.id if matched else None

    # INSERT defaults: missing fields use SQL defaults via the ORM; flags
    # default to False on the model. Only fields that were explicitly set
    # by the caller (i.e. not None) are included in BOTH the INSERT values
    # and the ON CONFLICT SET dict — preserving the legacy "None means
    # leave existing alone" semantic.
    values: dict = {
        "name": canonical,
        "work_date": work_date,
        "missing_checkout_resolved": bool(missing_checkout_resolved),
        "updated_at": now,
        "created_at": now,
        "employee_id": employee_id,
    }
    if entry_iso is not None:
        values["entry_iso"] = _parse_iso(entry_iso)
    if exit_iso is not None:
        values["exit_iso"] = _parse_iso(exit_iso)
    if total_break_seconds is not None:
        values["total_break_seconds"] = total_break_seconds
    if note is not None:
        values["notes"] = note
    if status_override is not None:
        values["status_override"] = status_override
    if paid_leave is not None:
        values["paid_leave"] = bool(paid_leave)
    if lop is not None:
        values["lop"] = bool(lop)
    if wfh is not None:
        values["wfh"] = bool(wfh)
    if updated_by is not None:
        values["updated_by"] = updated_by

    # ON CONFLICT SET: every field that was supplied (excluding the conflict
    # keys themselves) is updated from `excluded.<col>`. Fields not
    # supplied are omitted from SET, so the existing row's values stay put.
    excluded = excluded_of(AttendanceReportEdit)
    set_: dict = {
        # missing_checkout_resolved is always overwritten (legacy behavior).
        "missing_checkout_resolved": excluded.missing_checkout_resolved,
        "updated_at": excluded.updated_at,
    }
    if "entry_iso" in values:
        set_["entry_iso"] = excluded.entry_iso
    if "exit_iso" in values:
        set_["exit_iso"] = excluded.exit_iso
    if "total_break_seconds" in values:
        set_["total_break_seconds"] = excluded.total_break_seconds
    if "notes" in values:
        set_["notes"] = excluded.notes
    if "status_override" in values:
        set_["status_override"] = excluded.status_override
    if "paid_leave" in values:
        set_["paid_leave"] = excluded.paid_leave
    if "lop" in values:
        set_["lop"] = excluded.lop
    if "wfh" in values:
        set_["wfh"] = excluded.wfh
    if "updated_by" in values:
        set_["updated_by"] = excluded.updated_by
    if employee_id is not None:
        # Only refresh employee_id when we successfully resolved one — don't
        # clobber an existing FK with NULL just because the new write missed.
        set_["employee_id"] = excluded.employee_id

    with session_scope() as session:
        upsert_on_conflict_do_update(
            session,
            AttendanceReportEdit,
            values,
            index_elements=["name", "work_date"],
            set_=set_,
        )
        session.flush()
        row = session.execute(
            select(AttendanceReportEdit).where(
                and_(
                    AttendanceReportEdit.name == canonical,
                    AttendanceReportEdit.work_date == work_date,
                )
            )
        ).scalar_one_or_none()
        return _row_to_dict(row) if row else {}


def delete_correction(*, name: str, date: str) -> int:
    canonical = _normalize(name)
    work_date = _parse_date(date)
    with session_scope() as session:
        row = session.execute(
            select(AttendanceReportEdit).where(
                and_(
                    AttendanceReportEdit.name == canonical,
                    AttendanceReportEdit.work_date == work_date,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            return 0
        session.delete(row)
        return 1


def list_corrections(
    *,
    name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict]:
    """Return corrections optionally filtered by name and/or inclusive date
    range. Used by the HR-facing editor to pre-populate the month grid."""
    stmt = select(AttendanceReportEdit)
    if name:
        canonical = _normalize(name).lower()
        from sqlalchemy import func as _func
        stmt = stmt.where(_func.lower(AttendanceReportEdit.name) == canonical)
    if start_date:
        stmt = stmt.where(AttendanceReportEdit.work_date >= _parse_date(start_date))
    if end_date:
        stmt = stmt.where(AttendanceReportEdit.work_date <= _parse_date(end_date))
    stmt = stmt.order_by(
        AttendanceReportEdit.work_date.asc(), AttendanceReportEdit.name.asc()
    )
    with session_scope() as session:
        rows = session.execute(stmt).scalars().all()
        return [_row_to_dict(r) for r in rows]


def load_corrections() -> dict[tuple[str, str], dict]:
    """Return all corrections keyed by (lowercased_name, date)."""
    out: dict[tuple[str, str], dict] = {}
    with session_scope() as session:
        rows = session.execute(select(AttendanceReportEdit)).scalars().all()
        for r in rows:
            row_dict = _row_to_dict(r)
            key = (str(r.name).strip().lower(), row_dict["date"])
            out[key] = row_dict
    return out
