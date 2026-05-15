from __future__ import annotations

from datetime import date, time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Numeric, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.attendance_event import AttendanceEvent
    from app.models.daily_attendance import DailyAttendance
    from app.models.face_embedding import EmployeeFaceEmbedding
    from app.models.face_image import EmployeeFaceImage


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # `designation` is the canonical role column. The HR-facing UI labels
    # it "Role" — same data, friendlier wording — so we don't carry two
    # parallel columns that drift apart.
    designation: Mapped[str | None] = mapped_column(String(128), nullable=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    company: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    join_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Annual CTC (or whatever currency unit the deployment uses). Numeric
    # rather than Float so we never lose precision on round-trips.
    salary_package: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    # Shift window stored as two `TIME WITHOUT TIME ZONE` columns so we
    # can compare/aggregate in SQL (e.g. "who is on the morning shift")
    # without parsing strings. Display layer renders them as 12-hour
    # "9:00 AM – 6:00 PM"; storage stays neutral.
    shift_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    shift_end: Mapped[time | None] = mapped_column(Time, nullable=True)
    # Relative path under STORAGE_ROOT for the employee profile photo.
    # Path-only (not bytes) keeps the row tiny and lets us serve via the
    # existing static-file pipeline. Always normalized to forward slashes.
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    @property
    def has_image(self) -> bool:
        # Cheap derived flag exposed in EmployeeRead so the UI can decide
        # whether to render the avatar without us leaking the storage
        # path. The actual existence check happens in the GET endpoint.
        return bool(self.image_path)

    face_images: Mapped[list[EmployeeFaceImage]] = relationship(
        back_populates="employee", cascade="all, delete-orphan", lazy="selectin"
    )
    face_embeddings: Mapped[list[EmployeeFaceEmbedding]] = relationship(
        back_populates="employee", cascade="all, delete-orphan", lazy="selectin"
    )
    events: Mapped[list[AttendanceEvent]] = relationship(back_populates="employee")
    daily_records: Mapped[list[DailyAttendance]] = relationship(back_populates="employee")
