"""Shift lookup table.

Currently just (id, name) — the existing data stores shift as a free
string on employees with values like "9:30-18:30", "10-19", etc.
``start_time`` / ``end_time`` columns can be added later if reports
start needing per-shift schedule data; right now the global shift
config in ``app.config`` (SHIFT_START / SHIFT_END) drives all reports.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now,
    )
