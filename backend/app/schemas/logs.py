"""Response schemas for /api/attendance and /api/snapshots."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SnapshotItem(BaseModel):
    id: int
    name: str
    company: Optional[str] = None
    timestamp: str
    image_url: Optional[str] = None
    # Empty string for legacy single-camera rows (capture.py env-fallback
    # mode) and for snapshots ingested before multi-camera support landed.
    # Populated with the cameras.id once the camera is connected via the
    # admin UI and capture.py is in multi-camera mode.
    camera_id: Optional[str] = None


class SnapshotListResponse(BaseModel):
    items: list[SnapshotItem]


class BreakInterval(BaseModel):
    break_out: str
    break_in: str
    break_out_iso: str
    break_in_iso: str
    duration_seconds: int
    duration: str


class AttendanceMovementEvent(BaseModel):
    event_id: str
    movement_type: str
    timestamp: str
    timestamp_iso: str
    snapshot_url: Optional[str] = None
    snapshot_archived: bool = False
    camera_id: Optional[str] = None
    camera_name: Optional[str] = None
    confidence: Optional[float] = None


class AttendanceSummaryItem(BaseModel):
    id: str
    name: str
    company: Optional[str] = None
    date: str
    entry_time: Optional[str]
    exit_time: Optional[str]
    late_entry_minutes: int
    late_entry_seconds: int
    early_exit_minutes: int
    early_exit_seconds: int
    status: str
    total_hours: str
    total_working_hours: str
    total_break_time: str
    total_break_seconds: int
    break_details: list[BreakInterval] = []
    movement_history: list[AttendanceMovementEvent] = []
    entry_image_url: Optional[str]
    exit_image_url: Optional[str]
    entry_image_archived: bool = False
    exit_image_archived: bool = False
    missing_checkout: bool = False
    is_active: bool = False
    correction_applied: bool = False
    paid_leave: bool = False
    lop: bool = False
    wfh: bool = False


class AttendanceSummaryResponse(BaseModel):
    items: list[AttendanceSummaryItem]
