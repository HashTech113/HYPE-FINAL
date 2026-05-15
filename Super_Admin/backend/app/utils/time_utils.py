from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta, tzinfo
from functools import lru_cache
from zoneinfo import ZoneInfo

from app.config import get_settings


@lru_cache
def local_tz() -> tzinfo:
    return ZoneInfo(get_settings().TIMEZONE)


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def now_local() -> datetime:
    return datetime.now(tz=local_tz())


def to_local(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(local_tz())


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=local_tz())
    return dt.astimezone(UTC)


def local_day_bounds(local_date: date) -> tuple[datetime, datetime]:
    tz = local_tz()
    start = datetime.combine(local_date, time.min, tzinfo=tz)
    end = datetime.combine(local_date + timedelta(days=1), time.min, tzinfo=tz)
    return start, end


def local_date_of(dt: datetime) -> date:
    return to_local(dt).date()
