"""Generic key/value settings store.

Single-row-per-key. ``value`` is JSON so callers can stash structured
config (shift schedule, retention windows, feature toggles) without
schema churn. Resolves to JSONB on Postgres and TEXT on SQLite via
SQLAlchemy's ``JSON`` type affinity.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now,
    )
