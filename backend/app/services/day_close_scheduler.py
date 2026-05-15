"""Background day-close worker.

Wakes once a minute and runs ``DailyAttendanceService.close_day(today)``
the first time the local clock crosses ``SHIFT_END + buffer`` for a
given local day. Idempotent: the rollup row is marked ``is_day_closed``
once the close runs, so subsequent ticks find nothing to do.

Disabled by default — opt in via the env var
``DAY_CLOSE_SCHEDULER_ENABLED=1``. Manual close via
``POST /api/attendance/close-day`` works regardless of this flag.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from datetime import date as date_cls, datetime, time as time_cls, timedelta, timezone
from typing import Optional

from ..config import LOCAL_TZ_OFFSET_MIN, SHIFT_END
from ..db import session_scope

log = logging.getLogger(__name__)

# How long after SHIFT_END to wait before sealing the day. Gives any
# in-flight attendance events time to land before the synthetic OUT
# inserts kick in.
_CLOSE_BUFFER_MINUTES = 10
_TICK_SECONDS = 60.0


def _enabled() -> bool:
    return os.getenv("DAY_CLOSE_SCHEDULER_ENABLED", "0").strip().lower() in (
        "1", "true", "yes", "on",
    )


def _local_now() -> datetime:
    return datetime.now(timezone(timedelta(minutes=int(LOCAL_TZ_OFFSET_MIN))))


def _shift_end_time() -> time_cls:
    try:
        h, m = SHIFT_END.split(":", 1)
        return time_cls(hour=int(h), minute=int(m))
    except (ValueError, AttributeError):
        return time_cls(hour=18, minute=30)


class DayCloseScheduler:
    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_closed_date: Optional[date_cls] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name="day-close-scheduler", daemon=True,
        )
        self._thread.start()
        log.info("day-close scheduler started (tick=%.0fs)", _TICK_SECONDS)

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        log.info("day-close scheduler running")
        while not self._stop.wait(_TICK_SECONDS):
            try:
                self._tick()
            except Exception:
                # The scheduler must never die from a single failed close.
                log.exception("day-close tick failed (continuing)")
        log.info("day-close scheduler stopped")

    def _tick(self) -> None:
        now_local = _local_now()
        today_local = now_local.date()
        cutoff = datetime.combine(
            today_local, _shift_end_time(), tzinfo=now_local.tzinfo,
        ) + timedelta(minutes=_CLOSE_BUFFER_MINUTES)
        if now_local < cutoff:
            return  # not yet time
        if self._last_closed_date == today_local:
            return  # already closed in this process

        # Defer the heavy import + DB session creation until we actually
        # need to run a close.
        from .daily_attendance import DailyAttendanceService

        log.info("day-close scheduler closing %s (local cutoff=%s)",
                 today_local, cutoff.isoformat())
        with session_scope() as session:
            result = DailyAttendanceService(session).close_day(work_date=today_local)
        log.info(
            "day-close scheduler done date=%s closed=%d already=%d no_activity=%d synthetic=%d",
            today_local, result.closed, result.already_closed,
            result.no_activity, result.synthetic_outs,
        )
        self._last_closed_date = today_local


_singleton: Optional[DayCloseScheduler] = None
_singleton_lock = threading.Lock()


def get_scheduler() -> DayCloseScheduler:
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = DayCloseScheduler()
        return _singleton


def start_if_enabled() -> bool:
    """Convenience: start the scheduler when the env var is set.
    Returns True iff the scheduler was started."""
    if not _enabled():
        return False
    get_scheduler().start()
    return True
