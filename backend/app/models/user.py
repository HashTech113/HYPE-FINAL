"""User model — backs the ``users`` table.

Identity for the dashboard's login / role checks. Stores only the bcrypt
hash; the plaintext password never lives in the DB. The role CHECK
constraint is enforced at the DB level to keep bad role values out even if
a service-layer validator regresses.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    # Free-text ``company`` is the legacy denormalized column; ``company_id``
    # is the canonical FK to ``companies.id``. Both stay in sync via the
    # service layer for one release; a follow-up commit will drop the string.
    company: Mapped[str] = mapped_column(String(128), nullable=False, default="", server_default="")
    company_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    display_name: Mapped[str] = mapped_column(String(128), nullable=False, default="", server_default="")
    avatar_url: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)

    __table_args__ = (
        CheckConstraint("role IN ('admin','hr')", name="ck_users_role"),
    )
