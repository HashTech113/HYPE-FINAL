"""Company / branch lookup table.

Replaces the free-text ``company`` string repeated across ``users`` and
``employees`` rows. ``users.company_id`` and ``employees.company_id`` are
nullable FKs with ``ON DELETE SET NULL`` so deleting a stale company
doesn't cascade into operational tables.

The legacy ``company`` TEXT columns on ``users`` and ``employees`` are
kept for one release as transitional compat shims (see ``app.upgrade``).
A follow-up commit will drop them once the FKs are confirmed
authoritative in production.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now,
    )
