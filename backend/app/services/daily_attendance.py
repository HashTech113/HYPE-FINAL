"""Persisted daily-attendance rollup.

One row per (employee_id, work_date) in the ``daily_attendance`` table.
Maintained after every auto/manual event by ``AttendanceStateMachine``
and after every ``POST /api/attendance/close-day`` admin call.

Compute walk (mirrors Super_Admin's ``DailyAttendanceService``):

* ``IN``        → enter ``WORKING`` from ``None``; set ``in_time``.
* ``BREAK_OUT`` → leave ``WORKING``; accumulate work seconds; bump
  ``break_count``; enter ``ON_BREAK``.
* ``BREAK_IN``  → leave ``ON_BREAK``; accumulate break seconds; re-enter
  ``WORKING``.
* ``OUT``       → final; closes whichever segment was open and sets
  ``out_time``.

A trailing ``BREAK_OUT`` (without a matching ``BREAK_IN`` or ``OUT``)
leaves the day ``Incomplete`` until ``close_day`` runs.

Status mapping (keeps the existing frontend chip values intact):

* ``OUT`` present + ``IN`` present  → ``Present`` (or ``Late`` / ``Early Exit``
  if the worker arrived late / left early past the grace window).
* ``IN`` present, ``OUT`` missing  → ``Incomplete``.
* No events                         → ``Absent``.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import date as date_cls, datetime, time as time_cls, timedelta, timezone
from typing import Iterable, Optional

from sqlalchemy import and_, distinct, select
from sqlalchemy.orm import Session

from ..config import (
    EARLY_EXIT_GRACE_MIN,
    LATE_GRACE_MIN,
    LOCAL_TZ_OFFSET_MIN,
    SHIFT_END,
    SHIFT_START,
)
from ..models import AttendanceLog, DailyAttendance, Employee

log = logging.getLogger(__name__)


_close_lock = threading.Lock()
_close_dates_in_progress: set[date_cls] = set()


@dataclass(frozen=True)
class ComputedDay:
    in_time: Optional[datetime]
    out_time: Optional[datetime]
    break_out_time: Optional[datetime]   # first BREAK_OUT seen
    break_in_time: Optional[datetime]    # first BREAK_IN seen
    break_count: int
    total_work_seconds: int
    total_break_seconds: int
    late_minutes: int
    early_exit_minutes: int


@dataclass(frozen=True)
class CloseDayResult:
    closed: int
    already_closed: int
    no_activity: int
    synthetic_outs: int
    cutoff: datetime


def _local_tz() -> timezone:
    return timezone(timedelta(minutes=int(LOCAL_TZ_OFFSET_MIN)))


def _parse_hhmm(value: str, default: str) -> time_cls:
    try:
        h, m = value.split(":", 1)
        return time_cls(hour=int(h), minute=int(m))
    except (ValueError, AttributeError):
        h, m = default.split(":", 1)
        return time_cls(hour=int(h), minute=int(m))


def _local_day_bounds_utc(work_date: date_cls) -> tuple[datetime, datetime]:
    tz = _local_tz()
    start_local = datetime.combine(work_date, time_cls.min, tzinfo=tz)
    end_local = datetime.combine(work_date, time_cls.max, tzinfo=tz)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


class DailyAttendanceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Pure computation
    # ------------------------------------------------------------------

    def _compute(self, events: list[AttendanceLog], work_date: date_cls) -> ComputedDay:
        in_time: Optional[datetime] = None
        out_time: Optional[datetime] = None
        first_break_out: Optional[datetime] = None
        first_break_in: Optional[datetime] = None
        break_count = 0
        total_work = 0
        total_break = 0

        state: Optional[str] = None  # "WORKING" | "ON_BREAK" | None
        last_boundary: Optional[datetime] = None

        for ev in events:
            et = ev.event_type
            ts = ev.timestamp
            if et == "IN":
                if in_time is None:
                    in_time = ts
                    state = "WORKING"
                    last_boundary = ts
            elif et == "BREAK_OUT":
                if state == "WORKING" and last_boundary is not None:
                    total_work += int((ts - last_boundary).total_seconds())
                state = "ON_BREAK"
                last_boundary = ts
                if first_break_out is None:
                    first_break_out = ts
                break_count += 1
            elif et == "BREAK_IN":
                if state == "ON_BREAK" and last_boundary is not None:
                    total_break += int((ts - last_boundary).total_seconds())
                state = "WORKING"
                last_boundary = ts
                if first_break_in is None:
                    first_break_in = ts
            elif et == "OUT":
                if state == "WORKING" and last_boundary is not None:
                    total_work += int((ts - last_boundary).total_seconds())
                elif state == "ON_BREAK" and last_boundary is not None:
                    total_break += int((ts - last_boundary).total_seconds())
                out_time = ts
                state = None
                last_boundary = ts

        total_work = max(0, total_work)
        total_break = max(0, total_break)
        late_min, early_min = self._late_early(in_time, out_time, work_date)
        return ComputedDay(
            in_time=in_time,
            out_time=out_time,
            break_out_time=first_break_out,
            break_in_time=first_break_in,
            break_count=break_count,
            total_work_seconds=total_work,
            total_break_seconds=total_break,
            late_minutes=late_min,
            early_exit_minutes=early_min,
        )

    @staticmethod
    def _late_early(
        in_time: Optional[datetime],
        out_time: Optional[datetime],
        work_date: date_cls,
    ) -> tuple[int, int]:
        tz = _local_tz()
        start_t = _parse_hhmm(SHIFT_START, "09:30")
        end_t = _parse_hhmm(SHIFT_END, "18:30")
        late = 0
        early = 0
        if in_time is not None:
            expected_in = datetime.combine(work_date, start_t, tzinfo=tz)
            delta_min = int(
                (in_time.astimezone(tz) - expected_in).total_seconds() // 60
            )
            late = max(0, delta_min - int(LATE_GRACE_MIN))
        if out_time is not None:
            expected_out = datetime.combine(work_date, end_t, tzinfo=tz)
            delta_min = int(
                (expected_out - out_time.astimezone(tz)).total_seconds() // 60
            )
            early = max(0, delta_min - int(EARLY_EXIT_GRACE_MIN))
        return late, early

    def _status_for(self, computed: ComputedDay) -> str:
        """Map the FSM result to the frontend's existing status chips.

        Late/Early Exit win over Present so the operator gets the visible
        warning chip; if both fire we surface ``Late`` (entry is the more
        actionable signal). ``Incomplete`` indicates an open day — admin
        should review or wait for day-close.
        """
        if computed.in_time is None:
            return "Absent"
        if computed.out_time is None:
            return "Incomplete"
        if computed.late_minutes > 0:
            return "Late"
        if computed.early_exit_minutes > 0:
            return "Early Exit"
        return "Present"

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def _upsert_for_day(
        self, employee_id: str, work_date: date_cls
    ) -> DailyAttendance:
        row = self.db.execute(
            select(DailyAttendance).where(
                and_(
                    DailyAttendance.employee_id == employee_id,
                    DailyAttendance.work_date == work_date,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            row = DailyAttendance(employee_id=employee_id, work_date=work_date)
            self.db.add(row)
            self.db.flush()
        return row

    def _list_events_for_day(
        self, employee_id: str, work_date: date_cls
    ) -> list[AttendanceLog]:
        start_utc, end_utc = _local_day_bounds_utc(work_date)
        return list(
            self.db.execute(
                select(AttendanceLog)
                .where(
                    and_(
                        AttendanceLog.employee_id == employee_id,
                        AttendanceLog.timestamp >= start_utc,
                        AttendanceLog.timestamp <= end_utc,
                        AttendanceLog.event_type.is_not(None),
                    )
                )
                .order_by(AttendanceLog.timestamp.asc())
            )
            .scalars()
            .all()
        )

    def recompute(self, *, employee_id: str, work_date: date_cls) -> DailyAttendance:
        events = self._list_events_for_day(employee_id, work_date)
        computed = self._compute(events, work_date)
        row = self._upsert_for_day(employee_id, work_date)
        row.in_time = computed.in_time
        row.break_out_time = computed.break_out_time
        row.break_in_time = computed.break_in_time
        row.out_time = computed.out_time
        row.total_work_seconds = computed.total_work_seconds
        row.total_break_seconds = computed.total_break_seconds
        row.break_count = computed.break_count
        row.late_minutes = computed.late_minutes
        row.early_exit_minutes = computed.early_exit_minutes
        row.status = self._status_for(computed)
        self.db.flush()
        log.debug(
            "daily recompute emp=%s date=%s status=%s work=%ds break=%ds breaks=%d late=%dm early=%dm",
            employee_id, work_date, row.status,
            computed.total_work_seconds, computed.total_break_seconds,
            computed.break_count, computed.late_minutes, computed.early_exit_minutes,
        )
        return row

    def recompute_range(
        self,
        *,
        employee_id: Optional[str],
        start: date_cls,
        end: date_cls,
    ) -> int:
        if end < start:
            start, end = end, start
        # Distinct (employee_id, local_date) combinations from the events.
        # SQLite doesn't have DATE(timestamp at time zone X) cleanly, so we
        # iterate days in Python and call recompute per (emp, day).
        touched = 0
        cur = start
        while cur <= end:
            day_start_utc, day_end_utc = _local_day_bounds_utc(cur)
            stmt = select(distinct(AttendanceLog.employee_id)).where(
                and_(
                    AttendanceLog.timestamp >= day_start_utc,
                    AttendanceLog.timestamp <= day_end_utc,
                    AttendanceLog.event_type.is_not(None),
                )
            )
            if employee_id is not None:
                stmt = stmt.where(AttendanceLog.employee_id == employee_id)
            emp_ids = [str(r) for r in self.db.execute(stmt).scalars().all() if r]
            for emp_id in emp_ids:
                self.recompute(employee_id=emp_id, work_date=cur)
                touched += 1
            cur += timedelta(days=1)
        return touched

    def close_day(self, *, work_date: date_cls) -> CloseDayResult:
        """Seal ``work_date`` for every employee with events.

        - Trailing ``BREAK_OUT`` → relabel that row's ``event_type`` to
          ``OUT`` in place (the BREAK_OUT *was* their actual exit).
        - Trailing ``IN`` or ``BREAK_IN`` → synthesize an ``OUT`` event
          at ``work_date + SHIFT_END`` so the day is sealed sharply at
          end-of-day.
        - Trailing ``OUT`` → no-op.

        Idempotent: rows already marked ``is_day_closed=True`` are
        skipped. Concurrency: a process-wide lock keyed on ``work_date``
        prevents two callers from racing to insert duplicate synthetic
        OUTs for the same employee.
        """
        # Serialise close-day per date so two admin clicks in parallel,
        # or an admin click racing the scheduler, can't double-synthesise.
        with _close_lock:
            if work_date in _close_dates_in_progress:
                return CloseDayResult(0, 0, 0, 0, datetime.now(timezone.utc))
            _close_dates_in_progress.add(work_date)
        try:
            return self._close_day_inner(work_date)
        finally:
            with _close_lock:
                _close_dates_in_progress.discard(work_date)

    def _close_day_inner(self, work_date: date_cls) -> CloseDayResult:
        start_utc, end_utc = _local_day_bounds_utc(work_date)
        tz = _local_tz()
        end_t = _parse_hhmm(SHIFT_END, "18:30")
        synthetic_out_dt = datetime.combine(work_date, end_t, tzinfo=tz).astimezone(
            timezone.utc
        )

        emp_ids = [
            str(r)
            for r in self.db.execute(
                select(distinct(AttendanceLog.employee_id))
                .where(
                    and_(
                        AttendanceLog.timestamp >= start_utc,
                        AttendanceLog.timestamp <= end_utc,
                        AttendanceLog.event_type.is_not(None),
                    )
                )
            )
            .scalars()
            .all()
            if r
        ]

        closed = 0
        already_closed = 0
        no_activity = 0
        synthetic_outs = 0

        for emp_id in emp_ids:
            existing = self.db.execute(
                select(DailyAttendance).where(
                    and_(
                        DailyAttendance.employee_id == emp_id,
                        DailyAttendance.work_date == work_date,
                    )
                )
            ).scalar_one_or_none()
            if existing is not None and bool(existing.is_day_closed):
                already_closed += 1
                continue

            events = self._list_events_for_day(emp_id, work_date)
            if not events:
                no_activity += 1
                continue

            last_event = events[-1]
            et = last_event.event_type
            if et == "BREAK_OUT":
                last_event.event_type = "OUT"
                self.db.flush()
            elif et in ("IN", "BREAK_IN"):
                emp = self.db.get(Employee, emp_id)
                synthetic = AttendanceLog(
                    name=str(emp.name) if emp is not None else emp_id,
                    employee_id=emp_id,
                    timestamp=synthetic_out_dt,
                    image_path=f"close_day_{work_date.isoformat()}_{emp_id}",
                    image_data=None,
                    camera_id=None,
                    source="manual",
                    external_event_id=None,
                    event_type="OUT",
                    score=None,
                )
                self.db.add(synthetic)
                synthetic_outs += 1
                self.db.flush()
            # else: trailing OUT — already terminal, nothing to do.

            self.recompute(employee_id=emp_id, work_date=work_date)
            row = self.db.execute(
                select(DailyAttendance).where(
                    and_(
                        DailyAttendance.employee_id == emp_id,
                        DailyAttendance.work_date == work_date,
                    )
                )
            ).scalar_one_or_none()
            if row is not None:
                row.is_day_closed = True
            closed += 1

        self.db.flush()
        log.info(
            "Day close %s: closed=%d already_closed=%d no_activity=%d synthetic_outs=%d",
            work_date, closed, already_closed, no_activity, synthetic_outs,
        )
        return CloseDayResult(
            closed=closed,
            already_closed=already_closed,
            no_activity=no_activity,
            synthetic_outs=synthetic_outs,
            cutoff=synthetic_out_dt,
        )


def list_events_for_day(
    db: Session, *, work_date: date_cls, employee_id: Optional[str] = None
) -> list[AttendanceLog]:
    """Public read-side helper used by ``/api/attendance/events``.

    Returns the raw event rows (in chronological order) so the React
    dashboard can render a 'latest events' inline panel without
    duplicating the day-bound SQL.
    """
    start_utc, end_utc = _local_day_bounds_utc(work_date)
    stmt = (
        select(AttendanceLog)
        .where(
            and_(
                AttendanceLog.timestamp >= start_utc,
                AttendanceLog.timestamp <= end_utc,
                AttendanceLog.event_type.is_not(None),
            )
        )
        .order_by(AttendanceLog.timestamp.asc())
    )
    if employee_id is not None:
        stmt = stmt.where(AttendanceLog.employee_id == employee_id)
    return list(db.execute(stmt).scalars().all())
