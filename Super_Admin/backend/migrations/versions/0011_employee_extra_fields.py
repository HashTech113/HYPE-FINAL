"""extend employees with salary, shift window, and profile image

Adds columns:
  - salary_package  Numeric(12, 2)  — annual CTC, currency-neutral
  - shift_start     Time             — local-clock start of work shift
  - shift_end       Time             — local-clock end of work shift
  - image_path      String(255)      — relative path under STORAGE_ROOT

All four are nullable so existing rows remain valid without backfill.

Revision ID: 0011_employee_extra_fields
Revises: 0010_api_keys
Create Date: 2026-05-08
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_employee_extra_fields"
down_revision = "0010_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column("salary_package", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "employees",
        sa.Column("shift_start", sa.Time(timezone=False), nullable=True),
    )
    op.add_column(
        "employees",
        sa.Column("shift_end", sa.Time(timezone=False), nullable=True),
    )
    op.add_column(
        "employees",
        sa.Column("image_path", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("employees", "image_path")
    op.drop_column("employees", "shift_end")
    op.drop_column("employees", "shift_start")
    op.drop_column("employees", "salary_package")
