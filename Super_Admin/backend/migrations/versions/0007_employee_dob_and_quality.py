"""add employees.dob + bump face_min_quality default 0.50 -> 0.60

Revision ID: 0007_employee_dob_and_quality
Revises: 0006_recognize_size_and_company
Create Date: 2026-04-28
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_employee_dob_and_quality"
down_revision = "0006_recognize_size_and_company"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("employees", sa.Column("dob", sa.Date(), nullable=True))

    # Tighten face detection slightly. RetinaNet inside buffalo_l
    # occasionally produces high-confidence false positives at det_score
    # 0.5–0.59 (logos, fabric patterns, blurry posters); 0.60 is a
    # well-tested threshold that keeps real faces and drops most noise.
    op.execute(
        "UPDATE attendance_settings "
        "SET face_min_quality = GREATEST(face_min_quality, 0.60)"
    )
    op.alter_column(
        "attendance_settings",
        "face_min_quality",
        server_default="0.60",
    )


def downgrade() -> None:
    op.alter_column(
        "attendance_settings",
        "face_min_quality",
        server_default="0.50",
    )
    op.drop_column("employees", "dob")
