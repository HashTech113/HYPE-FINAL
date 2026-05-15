"""Unknown-face clustering tables.

Two-row design ported from the Super_Admin reference implementation,
adapted to the current backend's conventions:

* No external ``TimestampMixin`` — ``created_at`` / ``updated_at`` are
  inlined here.
* ``promoted_employee_id`` is a ``String(64)`` FK to ``employees.id``
  (this backend uses UUID-style employee ids, not integers).

``UnknownFaceCluster`` = one uniquely-identified unknown person.
``UnknownFaceCapture`` = one face crop assigned to a cluster.

The capture row carries its 512-d L2-normalized float32 embedding as a
raw LargeBinary blob, mirroring ``face_embeddings.vector`` exactly —
the recognition path can then reuse those bytes verbatim when a cluster
gets promoted to an employee.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UnknownClusterStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROMOTED = "PROMOTED"
    IGNORED = "IGNORED"
    MERGED = "MERGED"


class UnknownCaptureStatus(str, enum.Enum):
    KEEP = "KEEP"
    DISCARDED = "DISCARDED"


class UnknownFaceCluster(Base):
    __tablename__ = "unknown_face_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    centroid: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    centroid_dim: Mapped[int] = mapped_column(Integer, nullable=False, default=512)
    model_name: Mapped[str] = mapped_column(
        String(64), nullable=False, default="buffalo_l", server_default="buffalo_l"
    )
    member_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[UnknownClusterStatus] = mapped_column(
        SAEnum(UnknownClusterStatus, name="unknown_cluster_status"),
        nullable=False,
        default=UnknownClusterStatus.PENDING,
    )
    promoted_employee_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    merged_into_cluster_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey(
            "unknown_face_clusters.id",
            ondelete="SET NULL",
            name="fk_unknown_clusters_merged_into",
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now,
    )

    captures: Mapped[list["UnknownFaceCapture"]] = relationship(
        back_populates="cluster",
        cascade="all, delete-orphan",
        order_by="UnknownFaceCapture.captured_at.desc()",
    )

    __table_args__ = (
        Index(
            "ix_unknown_face_clusters_status_last_seen",
            "status",
            "last_seen_at",
        ),
        Index("ix_unknown_face_clusters_last_seen", "last_seen_at"),
        Index("ix_unknown_face_clusters_status", "status"),
        Index("ix_unknown_face_clusters_promoted_emp", "promoted_employee_id"),
    )


class UnknownFaceCapture(Base):
    __tablename__ = "unknown_face_captures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cluster_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("unknown_face_clusters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    embedding: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    embedding_dim: Mapped[int] = mapped_column(Integer, nullable=False, default=512)
    model_name: Mapped[str] = mapped_column(
        String(64), nullable=False, default="buffalo_l", server_default="buffalo_l"
    )
    camera_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("cameras.id", ondelete="SET NULL"),
        nullable=True,
    )
    bbox_x: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_y: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_w: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_h: Mapped[int] = mapped_column(Integer, nullable=False)
    det_score: Mapped[float] = mapped_column(Float, nullable=False)
    sharpness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    status: Mapped[UnknownCaptureStatus] = mapped_column(
        SAEnum(UnknownCaptureStatus, name="unknown_capture_status"),
        nullable=False,
        default=UnknownCaptureStatus.KEEP,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now
    )

    cluster: Mapped["UnknownFaceCluster"] = relationship(back_populates="captures")

    __table_args__ = (
        Index(
            "ix_unknown_face_captures_cluster_time",
            "cluster_id",
            "captured_at",
        ),
        Index(
            "ix_unknown_face_captures_cluster_status",
            "cluster_id",
            "status",
        ),
    )
