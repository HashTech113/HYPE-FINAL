"""Response models for /api/attendance/*."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


Status = Literal[
    "Present",
    "Late",
    "Early Exit",
    "Absent",
    "WFH",
    "Paid Leave",
    "LOP",
    "Holiday",
]


class ShiftConfig(BaseModel):
    start: str               # "HH:MM" local
    end: str                 # "HH:MM" local
    late_grace_min: int
    early_exit_grace_min: int
    timezone_offset_minutes: int


class BreakIntervalRecord(BaseModel):
    break_out: str
    break_in: str
    break_out_iso: str
    break_in_iso: str
    duration_seconds: int
    duration: str


class AttendanceRecord(BaseModel):
    name: str
    date: str                              # YYYY-MM-DD (local)
    entry: Optional[str] = None            # "HH:MM:SS" (local)
    exit: Optional[str] = None             # "HH:MM:SS" (local)
    entry_iso: Optional[str] = None        # ISO 8601 with tz offset
    exit_iso: Optional[str] = None
    total_hours: str                       # "Hh Mm Ss" — "—" when absent
    total_working_hours: str               # alias of total_hours
    total_minutes: int                     # 0 when absent
    total_working_seconds: int = 0
    total_break_seconds: int = 0
    total_break_time: str = "—"
    break_details: list[BreakIntervalRecord] = []
    status: Status
    late_minutes: int
    late_seconds: int
    early_exit_minutes: int
    early_exit_seconds: int
    capture_count: int
    entry_image_url: Optional[str] = None
    exit_image_url: Optional[str] = None
    entry_image_archived: bool = False
    exit_image_archived: bool = False
    missing_checkout: bool = False
    is_active: bool = False
    correction_applied: bool = False
    paid_leave: bool = False
    lop: bool = False
    wfh: bool = False


class AttendanceDayResponse(BaseModel):
    date: str
    shift: ShiftConfig
    count: int
    items: list[AttendanceRecord]


class AttendanceRangeResponse(BaseModel):
    start: str
    end: str
    shift: ShiftConfig
    count: int
    items: list[AttendanceRecord]
