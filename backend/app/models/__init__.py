"""ORM model package.

Importing this package registers every model with ``Base.metadata`` so
``Base.metadata.create_all(engine)`` (called from ``app.db.init_db``)
sees them all.
"""

from __future__ import annotations

from ._base import Base
from .api_key import ApiKey
from .attendance import AttendanceLog, AttendanceReportEdit, SnapshotLog
from .camera import Camera
from .company import Company
from .daily_attendance import DailyAttendance
from .department import Department
from .employee import Employee
from .face_embedding import FaceEmbedding
from .face_image import FaceImage
from .setting import Setting
from .shift import Shift
from .unknown_face import (
    UnknownCaptureStatus,
    UnknownClusterStatus,
    UnknownFaceCapture,
    UnknownFaceCluster,
)
from .user import User

__all__ = [
    "Base",
    "User",
    "Employee",
    "Camera",
    "Company",
    "Department",
    "FaceEmbedding",
    "FaceImage",
    "Shift",
    "AttendanceLog",
    "SnapshotLog",
    "AttendanceReportEdit",
    "Setting",
    "ApiKey",
    "DailyAttendance",
    "UnknownFaceCluster",
    "UnknownFaceCapture",
    "UnknownClusterStatus",
    "UnknownCaptureStatus",
]
