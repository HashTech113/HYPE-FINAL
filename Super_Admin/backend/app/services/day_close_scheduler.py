from __future__ import annotations

import threading
from datetime import date, datetime, time as dtime, timedelta

from app.core.logger import get_logger
from app.db.session import session_scope
from app.repositories.daily_attendance_repo import DailyAttendanceRepository
from app.services.daily_attendance_service import DailyAttendanceService
from app.services.settings_service import get_settings_service
from app.utils.time_utils import now_local

log = get_logger(__name__)

# Office hours policy: 18:30 is a hard cutoff, no grace.
# Anyone whose last event today is BREAK_OUT gets that converted to
# OUT in place; anyone still showing as IN or BREAK_IN gets a
# synthetic OUT inserted at exactly 18:30. The scheduler ticks every
# 60 s, so the actual close runs at the first tick at-or-after
# work_end_time (within ~60 s of sharp).
_CLOSE_DELAY_MINUTES: int = 0

# How often the scheduler wakes up to check whether it's time to close.
# Every minute is plenty — close-day is a once-a-day event.
_TICK_SECONDS: float = 60.0

# Default end-of-workday when the runtime setting is unset. Mirrors
# the office hours documented elsewhere in the codebase.
_DEFAULT_WORK_END = dtime(hour=18, minute=30)


class DayCloseScheduler:
    """Runs `DailyAttendanceService.close_day(today)` automatically at
    `work_end_time + 30min` every day.

    Without this the only way for a day to close (and trailing
    BREAK_OUT events to be rewritten as OUT) was an admin clicking
    "Close Day" on the dashboard. Employees who left after 18:30
    showed as INCOMPLETE in reports until someone remembered.

    The scheduler is:
      • idempotent — calling close_day on an already-closed day is a
        cheap no-op, and we also gate locally with `_last_closed_date`
        so we don't hammer the DB every minute past 19:00.
      • settings-aware — reads `work_end_time` fresh on each tick so
        admins who change office hours from the UI take effect on the
        next loop iteration.
      • robust to backend restarts — if the system was off all day and
        boots at 21:00, the very first tick detects "past close time,
        not yet closed for today" and closes immediately.
    """

    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_closed_date: date | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()

        # One-shot backfill: close every past day that still has
        # unclosed daily-attendance rows. Catches up after a downtime
        # period or initial deployment without admins manually closing
        # each missed day.
        try:
            self._backfill_unclosed_past_days()
        except Exception:
            log.exception("DayCloseScheduler backfill failed")

        self._thread = threading.Thread(target=self._loop, name="day-close-scheduler", daemon=True)
        self._thread.start()
        log.info(
            "DayCloseScheduler started (close_at = work_end_time + %d min)",
            _CLOSE_DELAY_MINUTES,
        )

    def _backfill_unclosed_past_days(self) -> None:
        """Find every past day with at least one unclosed daily-attendance
        row and close it. Today is left to the scheduler loop (which
        will close it on the first tick if we're already past
        work_end_time)."""
        from sqlalchemy import distinct, select

        from app.models.daily_attendance import DailyAttendance

        today = now_local().date()
        with session_scope() as db:
            stmt = (
                select(distinct(DailyAttendance.work_date))
                .where(
                    DailyAttendance.is_day_closed.is_(False),
                    DailyAttendance.work_date < today,
                )
                .order_by(DailyAttendance.work_date.asc())
            )
            past_dates: list[date] = list(db.execute(stmt).scalars().all())

        if not past_dates:
            log.info("DayCloseScheduler: no unclosed past days to backfill")
            return

        log.info(
            "DayCloseScheduler: backfilling %d unclosed past day(s): %s",
            len(past_dates),
            ", ".join(d.isoformat() for d in past_dates),
        )
        for d in past_dates:
            try:
                with session_scope() as db:
                    result = DailyAttendanceService(db).close_day(d)
                log.info(
                    "Backfill closed %s: closed=%d already=%d synthetic_outs=%d",
                    d,
                    result.closed,
                    result.already_closed,
                    # CloseDayResult doesn't expose synthetic_outs directly,
                    # log it via the close-day function's own log line.
                    0,
                )
            except Exception:
                log.exception("Backfill close failed for %s", d)

    def stop(self) -> None:
        self._stop.set()
        t = self._thread
        if t is not None:
            t.join(timeout=5.0)
            self._thread = None

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._maybe_close()
            except Exception:
                log.exception("DayCloseScheduler tick error")
            if self._stop.wait(_TICK_SECONDS):
                return

    def _maybe_close(self) -> None:
        now = now_local()
        today = now.date()
        end = self._effective_work_end()
        close_at = now.replace(
            hour=end.hour, minute=end.minute, second=0, microsecond=0
        ) + timedelta(minutes=_CLOSE_DELAY_MINUTES)

        if now < close_at:
            return  # work day still in progress
        if self._last_closed_date == today:
            return  # we already closed today this process

        # The day to close depends on whether we're past close time
        # of TODAY or close time of YESTERDAY. If `now < end_of_today`
        # but we got here, the close_at window must be for yesterday.
        # `_compute_close_target` resolves that.
        target_date = self._compute_close_target(now, end)

        with session_scope() as db:
            existing = DailyAttendanceRepository(db).list_by_date(target_date)
            if existing and all(row.is_day_closed for row in existing):
                # Someone (admin manually, or a previous run) already
                # closed it. Mark as done so we don't keep checking.
                self._last_closed_date = target_date
                return
            result = DailyAttendanceService(db).close_day(target_date)
        log.info(
            "Auto-closed day %s: closed=%d already=%d no_activity=%d",
            target_date,
            result.closed,
            result.already_closed,
            result.no_activity,
        )
        self._last_closed_date = target_date

    @staticmethod
    def _effective_work_end() -> dtime:
        try:
            snap = get_settings_service().get()
        except Exception:
            return _DEFAULT_WORK_END
        return snap.work_end_time or _DEFAULT_WORK_END

    @staticmethod
    def _compute_close_target(now: datetime, end: dtime) -> date:
        """Decide which calendar date this closure is for.

        If we're past `end` of today, the target is today.
        If we crossed midnight before the scheduler woke (e.g. system
        restart at 02:00), the target is yesterday — its close was
        missed and we want to flush it now.
        """
        today = now.date()
        end_today = now.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
        if now >= end_today:
            return today
        return today - timedelta(days=1)


_INSTANCE: DayCloseScheduler | None = None
_LOCK = threading.Lock()


def get_day_close_scheduler() -> DayCloseScheduler:
    global _INSTANCE
    with _LOCK:
        if _INSTANCE is None:
            _INSTANCE = DayCloseScheduler()
        return _INSTANCE


def shutdown_day_close_scheduler() -> None:
    global _INSTANCE
    with _LOCK:
        if _INSTANCE is not None:
            _INSTANCE.stop()
            _INSTANCE = None
