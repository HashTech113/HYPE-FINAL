from __future__ import annotations

from sqlalchemy import Boolean, Enum as SAEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import CameraType
from app.core.secrets import EncryptedString
from app.db.base import Base, TimestampMixin


class Camera(Base, TimestampMixin):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    # `rtsp_url` is the resolved/working URL the workers actually open.
    # When the row was created via the smart-connect wizard it's
    # auto-generated from `brand` + `host` + ... below; when created via
    # the "Custom RTSP URL" path the user pasted it directly.
    rtsp_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    camera_type: Mapped[CameraType] = mapped_column(
        SAEnum(CameraType, name="camera_type"), nullable=False, index=True
    )
    location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    # --- Smart-connect provenance ---
    # When the wizard built the rtsp_url, we keep the inputs so:
    #   * The edit dialog can pre-fill them.
    #   * The user can re-resolve after a password change without
    #     hand-editing the URL.
    #   * Future tooling can audit which firmware family is in use.
    # All NULL when the row was created via the "Custom RTSP URL" path.
    #
    # Password is stored plaintext for now — same exposure level as the
    # rtsp_url that already embeds it. Encrypting these properly needs a
    # KMS / Fernet key story; tracked as a follow-up.
    brand: Mapped[str | None] = mapped_column(String(64), nullable=True)
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # Encrypted at rest via Fernet when CAMERA_SECRET_KEY is set;
    # passthrough plaintext when it isn't (with a startup warning).
    # Storage column is widened to 512 chars in migration 0013 to
    # accommodate Fernet's base64 expansion (~1.4× + 64-byte header).
    # Defense-in-depth note: rtsp_url ALSO embeds this password — full
    # protection requires a follow-up that re-derives rtsp_url from
    # decomposed fields on each worker spin-up.
    password: Mapped[str | None] = mapped_column(EncryptedString(512), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(16), nullable=True)
    stream: Mapped[str | None] = mapped_column(String(16), nullable=True)
