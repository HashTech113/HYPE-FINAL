"""Camera registry.

Passwords are stored as Fernet-encrypted ciphertext (``services.crypto``)
and never returned to the frontend. The CHECK on ``connection_status``
mirrors the original SQLite schema so legacy rows survive migration.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    location: Mapped[str] = mapped_column(String(128), nullable=False, default="", server_default="")
    ip: Mapped[str] = mapped_column(String(64), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=554, server_default="554")
    username: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    password_encrypted: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    rtsp_path: Mapped[str] = mapped_column(
        String(255), nullable=False,
        default="/Streaming/Channels/101", server_default="/Streaming/Channels/101",
    )
    connection_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="unknown", server_default="unknown", index=True,
    )
    # Direction the camera covers. Drives the attendance state machine:
    #   ENTRY camera → IN / BREAK_IN
    #   EXIT camera  → BREAK_OUT (or OUT once day-close runs)
    # Stored as a small string + CHECK constraint to match the rest of this
    # model's style. Defaults to ENTRY so a fresh install or an existing
    # camera without a configured direction still behaves like the legacy
    # "always treat detections as entries" pipeline.
    type: Mapped[str] = mapped_column(
        String(8), nullable=False, default="ENTRY", server_default="ENTRY", index=True,
    )
    # When False, capture.py skips this camera entirely — used for brands that
    # don't speak Uniview's face-detection HTTP API (Hikvision/CP Plus/Dahua).
    # Live-view (RTSP/MJPEG) still works regardless, since that path is
    # vendor-agnostic. Default True preserves legacy behavior for existing rows.
    enable_face_ingest: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1",
    )
    # Auto-rediscovery for WiFi/DHCP cameras whose IP rotates. When True,
    # CameraClient sweeps the camera's /24 subnet on login failure, validates
    # candidates by Uniview ``/API/Web/Login`` against the saved credentials,
    # and on success persists the new IP here (with ``last_known_ip`` /
    # ``last_discovered_at`` recording the transition). Default False keeps
    # static-IP cameras strictly fixed.
    auto_discovery_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0",
    )
    last_known_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_discovered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_check_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now,
    )

    __table_args__ = (
        CheckConstraint(
            "connection_status IN ('unknown','connected','failed')",
            name="ck_cameras_status",
        ),
        CheckConstraint(
            "type IN ('ENTRY','EXIT')",
            name="ck_cameras_type",
        ),
    )
