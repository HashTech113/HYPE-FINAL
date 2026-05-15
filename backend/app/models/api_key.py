"""API key registry.

Stores hashed API keys (never plaintext) for inbound integrations such as
the camera ingest endpoint and any future external callers. Each row
carries a scope (``"ingest"``, ``"admin"``, etc.), an active flag, and
optional expiry / revocation timestamps so keys can be rotated without
restarting the service.

Today the camera ingest endpoint validates against the ``INGEST_API_KEY``
env var directly (see ``app.config``); this table is the next step. When
a request is migrated to use this table, the lookup is:

    SELECT id, scope, is_active, expires_at, revoked_at
      FROM api_keys
     WHERE key_hash = bcrypt_or_hmac(presented_key)

Plaintext keys are issued ONCE at creation time and never returned by
any endpoint thereafter; only the hash lives in the DB.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    # Hash only — issuance flow returns the plaintext to the operator once
    # and discards it. Suitable for sha256 / hmac / bcrypt depending on the
    # consumer; the column is wide enough for any of them.
    key_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    scope: Mapped[str] = mapped_column(String(32), nullable=False, default="ingest", server_default="ingest")
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1", index=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now,
    )
