"""Persisted daily attendance rollup.

One row per (employee, work_date). Maintained by
``services.daily_attendance.DailyAttendanceService`` after every auto/
manual event and after every day-close. The existing
``/api/attendance/daily`` endpoint reads from this table when a row
exists; legacy days without rows fall back to the gap-based
computation in ``services.attendance.build_daily_records``.

``status`` mirrors the string values the frontend already renders
(``Present``, ``Late``, ``Early Exit``, ``Absent``, ``Incomplete``, plus
the HR override values like ``WFH``/``Paid Leave``/``LOP``/``Holiday``)
so we don't have to change the response shape or any UI.
"""

from __future__ import annotations

from datetime import date as date_cls, datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DailyAttendance(Base):
    __tablename__ = "daily_attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    work_date: Mapped[date_cls] = mapped_column(Date, nullable=False)
    in_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    break_out_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    break_in_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    out_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_work_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    total_break_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    break_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    late_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    early_exit_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # Status string — kept compatible with the frontend's existing chip
    # values (``Present``/``Late``/``Early Exit``/``Absent``/``Incomplete``
    # plus HR overrides like ``WFH``/``Paid Leave``/``LOP``/``Holiday``).
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="Absent", server_default="Absent"
    )
    is_manually_adjusted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    is_day_closed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now,
    )

    __table_args__ = (
        UniqueConstraint("employee_id", "work_date", name="uq_daily_attendance_employee_date"),
        Index("ix_daily_attendance_date_status", "work_date", "status"),
        Index("ix_daily_attendance_employee_date", "employee_id", "work_date"),
    )
