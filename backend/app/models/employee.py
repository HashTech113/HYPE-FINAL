"""Employee directory.

The DB column ``employee_id`` holds the human-facing employee code (e.g.
"E0023"); the Python attribute is named ``employee_code`` so the term
``employee_id`` is free for FKs to ``employees.id`` on the log tables.
``UniqueConstraint`` on (employee_id, company) lets the same code live
across companies but never collide within one.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Python attr `employee_code` — DB column kept as `employee_id` so existing
    # API payloads, JSON seed, and migration paths don't have to change.
    employee_code: Mapped[str] = mapped_column(
        "employee_id", String(64), nullable=False, default="", server_default=""
    )
    # Free-text ``company`` / ``department`` / ``shift`` are the legacy
    # denormalized columns; the ``*_id`` FK columns below are the canonical
    # references to the lookup tables. Both stay in sync via the service
    # layer for one release; a follow-up commit will drop the strings once
    # the FKs are confirmed authoritative.
    company: Mapped[str] = mapped_column(String(128), nullable=False, default="", server_default="")
    company_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    department: Mapped[str] = mapped_column(String(128), nullable=False, default="", server_default="")
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    shift: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    shift_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    role: Mapped[str] = mapped_column(String(64), nullable=False, default="Employee", server_default="Employee")
    dob: Mapped[str] = mapped_column(String(32), nullable=False, default="", server_default="")
    image_url: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="", server_default="")
    mobile: Mapped[str] = mapped_column(String(32), nullable=False, default="", server_default="")
    salary_package: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1", index=True,
    )

    __table_args__ = (
        UniqueConstraint("employee_id", "company", name="uq_employees_code_per_company"),
        Index("idx_employees_name", "name"),
        # Standalone index on the employee code (DB column is named
        # ``employee_id`` for legacy reasons; Python attr is ``employee_code``).
        # Faster than the composite uq_employees_code_per_company when looking
        # up by code alone.
        Index("idx_employees_employee_code", "employee_id"),
    )
