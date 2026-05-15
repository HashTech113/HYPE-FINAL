"""Attendance + snapshot logs and the report-edit override table.

`name` is kept denormalized on every log row because face recognition
emits names that don't always resolve to an Employee yet (Unknown,
new-hire-not-yet-enrolled, mis-recognized variants). A nullable
`employee_id` FK with `ON DELETE SET NULL` is added alongside `name` so
recognized rows are joinable while unrecognized rows still land in the DB.

`AttendanceReportEdit` replaces the legacy `attendance_corrections` table:
surrogate `id` PK + nullable employee FK, with `(name, work_date)` kept as
the unique upsert key so partial-name rows (employee_id IS NULL) still
dedupe correctly across re-runs.
"""

from __future__ import annotations

from datetime import date as date_cls, datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    image_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    camera_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("cameras.id", ondelete="SET NULL"),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(
        String(32), nullable=False,
        default="local_camera", server_default="local_camera",
    )
    external_event_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    event_type: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    # Recognition confidence (cosine similarity 0..1). NULL on rows
    # written by external/manual sources or legacy rows from before the
    # column was added.
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "source IN ('local_camera','external_api','manual')",
            name="ck_attendance_source",
        ),
        # event_type may be NULL for camera presence ticks (which aren't typed
        # punches); typed values must be one of the four punch types.
        CheckConstraint(
            "event_type IS NULL OR event_type IN ('IN','OUT','BREAK_OUT','BREAK_IN')",
            name="ck_attendance_event_type",
        ),
        Index("idx_attendance_logs_name", "name"),
        Index("idx_attendance_logs_employee_id", "employee_id"),
        Index("idx_attendance_logs_timestamp", "timestamp"),
        Index("idx_attendance_logs_source", "source"),
        Index("idx_attendance_logs_camera_id", "camera_id"),
        Index("idx_attendance_logs_employee_timestamp", "employee_id", "timestamp"),
        # Partial unique on external_event_id — one row per external punch.
        # postgresql_where + sqlite_where keeps both dialects happy.
        Index(
            "uq_attendance_logs_external_event_id",
            "external_event_id",
            unique=True,
            postgresql_where=text("external_event_id IS NOT NULL"),
            sqlite_where=text("external_event_id IS NOT NULL"),
        ),
    )


class SnapshotLog(Base):
    __tablename__ = "snapshot_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    image_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    camera_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("cameras.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Recognition confidence (cosine similarity 0..1). NULL on rows
    # written by ingest/external paths and legacy rows.
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("idx_snapshot_logs_name", "name"),
        Index("idx_snapshot_logs_employee_id", "employee_id"),
        Index("idx_snapshot_logs_timestamp", "timestamp"),
        Index("idx_snapshot_logs_camera_id", "camera_id"),
    )


# Whitelist of allowed status_override values, mirrored at the CHECK level
# below. Kept in sync with services.corrections.ALLOWED_STATUS_OVERRIDES.
_ALLOWED_STATUS_OVERRIDES_SQL = (
    "status_override IS NULL OR status_override IN "
    "('Present','Late','Early Exit','Absent','WFH','Paid Leave','LOP','Holiday')"
)


class AttendanceReportEdit(Base):
    """HR/Admin overrides applied on top of auto-computed attendance records.

    Renamed from the legacy ``attendance_corrections`` table. The original
    composite PK ``(name, date)`` becomes a UNIQUE constraint so the row
    has a real surrogate ``id`` for FK targets, while existing upsert
    semantics ("one row per employee per day") are preserved.
    """

    __tablename__ = "attendance_report_edits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    work_date: Mapped[date_cls] = mapped_column(Date, nullable=False)
    entry_iso: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    exit_iso: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_break_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    missing_checkout_resolved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0",
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status_override: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    paid_leave: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    lop: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    wfh: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    updated_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now,
    )

    __table_args__ = (
        UniqueConstraint("name", "work_date", name="uq_report_edit_name_date"),
        CheckConstraint(_ALLOWED_STATUS_OVERRIDES_SQL, name="ck_report_edit_status"),
        Index("idx_report_edit_employee_date", "employee_id", "work_date"),
        Index("idx_report_edit_work_date", "work_date"),
    )
