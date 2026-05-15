"""Face training images per employee.

A reference set the admin uploads via Settings → Employee Management →
Face Training. There is no embedding/training step in this backend right
now; the images are stored as base64 in the same way as ``employees.
image_url`` and ``snapshot_logs.image_data`` so behaviour stays
consistent across the codebase. A future ML pipeline (or the deferred
admin backend) can read this table to build embeddings.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FaceImage(Base):
    __tablename__ = "face_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Optional human label, e.g. "front" / "left" / "right" / free text. May be
    # empty when the admin just bulk-uploaded a set without naming each one.
    label: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    # Base64-encoded JPEG/PNG (with or without the data URL prefix; the API
    # normalizes to a data URL on read).
    image_data: Mapped[str] = mapped_column(Text, nullable=False)
    # The admin who uploaded this image (FK soft-link by id; we don't
    # constrain it because the User table id format isn't a guaranteed FK
    # target across deployments, and admins may be deleted without losing
    # the historical upload record).
    created_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now
    )

    __table_args__ = (
        Index("idx_face_images_employee_created", "employee_id", "created_at"),
    )
