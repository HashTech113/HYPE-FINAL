"""add recognize_min_face_size_px setting + employees.company column

Revision ID: 0006_recognize_size_and_company
Revises: 0005_unknown_faces
Create Date: 2026-04-28

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_recognize_size_and_company"
down_revision = "0005_unknown_faces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # New recognition gate — minimum face size before we even try to match.
    op.add_column(
        "attendance_settings",
        sa.Column(
            "recognize_min_face_size_px",
            sa.Integer(),
            nullable=False,
            server_default="120",
        ),
    )

    # Tighten unknown-capture defaults — keep only medium/high quality
    # captures, ignore tiny / blurry ones. Existing rows are bumped too so
    # the new defaults take effect without an admin change.
    op.execute(
        "UPDATE attendance_settings SET "
        "unknown_min_face_quality = GREATEST(unknown_min_face_quality, 0.75), "
        "unknown_min_face_size_px = GREATEST(unknown_min_face_size_px, 120), "
        "unknown_min_sharpness = GREATEST(unknown_min_sharpness, 100.0)"
    )
    # Bump the column-level defaults too so fresh installs get the same.
    op.alter_column(
        "attendance_settings",
        "unknown_min_face_quality",
        server_default="0.75",
    )
    op.alter_column(
        "attendance_settings",
        "unknown_min_face_size_px",
        server_default="120",
    )
    op.alter_column(
        "attendance_settings",
        "unknown_min_sharpness",
        server_default="100.0",
    )

    # Per-employee company name (used as a label on the training page).
    op.add_column(
        "employees",
        sa.Column("company", sa.String(length=128), nullable=True),
    )
    op.create_index("ix_employees_company", "employees", ["company"])


def downgrade() -> None:
    op.drop_index("ix_employees_company", table_name="employees")
    op.drop_column("employees", "company")

    op.alter_column(
        "attendance_settings",
        "unknown_min_sharpness",
        server_default="50.0",
    )
    op.alter_column(
        "attendance_settings",
        "unknown_min_face_size_px",
        server_default="80",
    )
    op.alter_column(
        "attendance_settings",
        "unknown_min_face_quality",
        server_default="0.65",
    )

    op.drop_column("attendance_settings", "recognize_min_face_size_px")
