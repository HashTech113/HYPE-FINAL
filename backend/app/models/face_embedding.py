"""Face embedding vectors per employee.

A 512-dim L2-normalised float32 vector produced by the InsightFace
``buffalo_l`` pipeline for each enrolled face image. The recognition
hot-path loads every active employee's embeddings into a single numpy
matrix at boot (see ``services.embedding_cache``) and computes cosine
similarity via a single matmul, so the per-frame match cost is
~O(num_employees × 512 floats) — fast even with thousands of employees.

Stored as a raw ``BLOB`` (2048 bytes) rather than a numeric array column
for portability across SQLite and PostgreSQL — every dialect supports
LargeBinary, no driver-specific UPSERT or array casting needed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Source training image, when the embedding came from a stored photo.
    # Nullable so we can also persist embeddings derived from live camera
    # frames (auto-enroll path) without inventing a synthetic image row.
    face_image_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("face_images.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    # Raw float32 vector (dim × 4 bytes). 512-dim buffalo_l = 2048 bytes.
    vector: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    dim: Mapped[int] = mapped_column(Integer, nullable=False, default=512, server_default="512")
    # Pin the model so cache rebuilds after a model swap know which rows
    # are stale and need re-extraction.
    model_name: Mapped[str] = mapped_column(
        String(64), nullable=False, default="buffalo_l", server_default="buffalo_l"
    )
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now
    )

    __table_args__ = (
        Index("idx_face_embeddings_employee_model", "employee_id", "model_name"),
    )
