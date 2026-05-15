"""Attendance state machine — converts camera detections into typed events.

Mirrors the Super_Admin spec exactly:

::

    None        ──ENTRY──▶ IN
    IN          ──EXIT──▶  BREAK_OUT
    BREAK_OUT   ──ENTRY──▶ BREAK_IN
    BREAK_IN    ──EXIT──▶  BREAK_OUT     (arbitrarily many breaks)

``OUT`` is **not** reachable from any auto-transition. It is produced
only by:

* the day-close pass (which relabels the trailing ``BREAK_OUT`` to
  ``OUT`` or synthesises one at ``work_end_time`` for trailing
  ``IN`` / ``BREAK_IN``), or
* a manual admin entry via the attendance router.

This module is intentionally thin: the state machine itself is pure
logic; the only side effects are the row writes (via
``services.logs.record_capture``) and the rollup recompute (via
``services.daily_attendance.DailyAttendanceService.recompute``). Both
run inside the caller's session so the whole event is one transaction.
"""

from __future__ import annotations

import base64
import enum
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import cv2
import numpy as np
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..models import AttendanceLog, Camera as CameraModel, Employee
from . import logs as logs_service

log = logging.getLogger(__name__)


class EventType(str, enum.Enum):
    IN = "IN"
    BREAK_OUT = "BREAK_OUT"
    BREAK_IN = "BREAK_IN"
    OUT = "OUT"


class CameraType(str, enum.Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"


# Single source of truth for what a camera-triggered detection becomes.
# Keyed on (current_state, camera_type). Missing entries explicitly
# represent "no valid transition" and the caller drops the event.
STATE_TRANSITIONS: dict[tuple[Optional[EventType], CameraType], EventType] = {
    (None, CameraType.ENTRY): EventType.IN,
    (EventType.IN, CameraType.EXIT): EventType.BREAK_OUT,
    (EventType.BREAK_OUT, CameraType.ENTRY): EventType.BREAK_IN,
    (EventType.BREAK_IN, CameraType.EXIT): EventType.BREAK_OUT,
}

# OUT is terminal — once set for the day, no more auto-events fire.
TERMINAL_STATES: frozenset[EventType] = frozenset({EventType.OUT})


@dataclass(frozen=True)
class AutoEventOutcome:
    created: bool
    reason: str  # "ok" | "employee_not_found_or_inactive" | "day_closed" | "invalid_transition_from_X_via_Y"
    event_type: Optional[EventType]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _local_day_bounds_utc(at: datetime, tz_offset_min: int) -> tuple[datetime, datetime]:
    """Return UTC datetimes spanning the local calendar day containing ``at``.

    Uses a fixed UTC offset (read from ``LOCAL_TZ_OFFSET_MIN`` by the
    caller) so DST jumps in regions with one don't introduce off-by-one
    rollover bugs. India / Sri Lanka / most of the regions this product
    runs in use a fixed-offset TZ.
    """
    local_tz = timezone(timedelta(minutes=tz_offset_min))
    local = at.astimezone(local_tz)
    start_local = local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local.replace(hour=23, minute=59, second=59, microsecond=999_999)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


class AttendanceStateMachine:
    """Per-session helper. Construct one per DB session (same pattern
    as ``UnknownCaptureService`` and other services in this package).
    """

    def __init__(self, db: Session, *, tz_offset_min: int) -> None:
        self.db = db
        self.tz_offset_min = int(tz_offset_min)

    # ------------------------------------------------------------------
    # Public entry — called by the recognition worker after a match
    # ------------------------------------------------------------------

    def process_auto_event(
        self,
        *,
        employee_id: str,
        employee_name: str,
        camera_id: str,
        captured_at: Optional[datetime] = None,
        bbox: tuple[int, int, int, int],
        frame_bgr: Optional[np.ndarray],
        score: Optional[float],
    ) -> AutoEventOutcome:
        """Drive one detection through the state machine.

        Steps:
        1. Resolve the camera's ``type`` (ENTRY/EXIT).
        2. Look up the employee's current state (latest typed event today).
        3. Apply ``STATE_TRANSITIONS``; bail with a reason on a miss.
        4. Encode the face crop as base64 JPEG so it lands in
           ``attendance_logs.image_data`` + ``snapshot_logs.image_data``
           (the columns the existing reports/Live view already render from).
        5. Hand to ``logs.record_capture`` with the resolved ``event_type``
           + ``score``.
        6. Trigger the rollup recompute for (employee_id, local_date).

        Returns ``AutoEventOutcome`` instead of raising on predictable
        rejects so the camera worker can log + continue without dropping
        the surrounding inference batch.
        """
        at = captured_at or _utc_now()

        # 1. Camera type
        cam = self.db.get(CameraModel, camera_id)
        if cam is None:
            return AutoEventOutcome(False, "camera_not_found", None)
        try:
            cam_type = CameraType(str(cam.type or "ENTRY"))
        except ValueError:
            cam_type = CameraType.ENTRY

        # 2. Employee active?
        emp = self.db.get(Employee, employee_id)
        if emp is None or not bool(getattr(emp, "is_active", True)):
            return AutoEventOutcome(False, "employee_not_found_or_inactive", None)

        # 3. State machine
        current = self._current_state(employee_id, at)
        if current in TERMINAL_STATES:
            return AutoEventOutcome(False, "day_closed", None)
        next_type = STATE_TRANSITIONS.get((current, cam_type))
        if next_type is None:
            return AutoEventOutcome(
                False,
                f"invalid_transition_from_{current.value if current else 'NONE'}_via_{cam_type.value}",
                None,
            )

        # 4. Encode crop (best-effort — falls back to no image_data)
        image_b64: Optional[str] = None
        if frame_bgr is not None and bbox is not None:
            try:
                crop = _crop_face(frame_bgr, bbox)
                ok_enc, jpg = cv2.imencode(".jpg", crop, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if ok_enc:
                    image_b64 = base64.b64encode(jpg.tobytes()).decode("ascii")
            except Exception:
                log.exception("attendance_state: crop encode failed")

        # 5. Record row — record_capture handles the UNIQUE(image_path)
        # idempotency + writes both snapshot_logs and attendance_logs.
        ts_iso = at.astimezone(timezone.utc).isoformat()
        image_path = (
            f"recog_cam_{camera_id}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}.jpg"
        )
        stored = logs_service.record_capture(
            name=employee_name or employee_id,
            timestamp_iso=ts_iso,
            image_path=image_path,
            image_data=image_b64,
            camera_id=camera_id,
            score=float(score) if score is not None else None,
            event_type=next_type.value,
        )
        if not stored:
            # Duplicate image_path — almost certainly a redundant call in
            # the same millisecond. Surface as a no-op without erroring.
            return AutoEventOutcome(False, "duplicate", next_type)

        # 6. Rollup recompute for the local day of this event. Done in a
        # nested import so the state-machine module stays import-cheap.
        try:
            from .daily_attendance import DailyAttendanceService
            local_date = at.astimezone(
                timezone(timedelta(minutes=self.tz_offset_min))
            ).date()
            DailyAttendanceService(self.db).recompute(
                employee_id=employee_id,
                work_date=local_date,
            )
        except Exception:
            # Rollup failure must NEVER take down the recognition loop.
            # The raw row is already written; the rollup is recomputed
            # on the next event or on /api/attendance/recompute.
            log.exception("rollup recompute failed after event")

        log.info(
            "Auto event employee=%s name=%s type=%s camera=%s cam_type=%s score=%.3f",
            employee_id, employee_name, next_type.value, camera_id, cam_type.value,
            float(score) if score is not None else 0.0,
        )
        return AutoEventOutcome(True, "ok", next_type)

    # ------------------------------------------------------------------
    # State lookup
    # ------------------------------------------------------------------

    def _current_state(self, employee_id: str, at_time: datetime) -> Optional[EventType]:
        """Latest typed event for this employee on the local day of
        ``at_time``. Untyped rows (event_type IS NULL) are ignored —
        those are camera detections written before the FSM was wired up
        and shouldn't drive the state machine.
        """
        day_start_utc, day_end_utc = _local_day_bounds_utc(at_time, self.tz_offset_min)
        row = self.db.execute(
            select(AttendanceLog)
            .where(
                AttendanceLog.employee_id == employee_id,
                AttendanceLog.timestamp >= day_start_utc,
                AttendanceLog.timestamp <= day_end_utc,
                AttendanceLog.event_type.is_not(None),
            )
            .order_by(desc(AttendanceLog.timestamp))
            .limit(1)
        ).scalar_one_or_none()
        if row is None or row.event_type is None:
            return None
        try:
            return EventType(str(row.event_type))
        except ValueError:
            return None


def _crop_face(frame: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    """Pad a face bbox by a small ratio and clamp to the frame. Lifted
    from the recognition_worker so attendance event snapshots line up
    visually with the live-view crops."""
    if frame.size == 0:
        return frame
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = bbox
    bw = max(1, x2 - x1)
    bh = max(1, y2 - y1)
    px = int(bw * 0.25)
    py = int(bh * 0.25)
    x1c = max(0, int(x1) - px)
    y1c = max(0, int(y1) - py)
    x2c = min(w, int(x2) + px)
    y2c = min(h, int(y2) + py)
    if x2c <= x1c or y2c <= y1c:
        return frame
    return frame[y1c:y2c, x1c:x2c].copy()
