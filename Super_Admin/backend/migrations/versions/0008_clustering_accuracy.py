"""tighten unknown_cluster_match_threshold 0.55 -> 0.62

Lenient online clustering (0.55 cosine similarity) was placing different
people in the same PENDING cluster. 0.62 errs toward "different person"
on borderline matches — more clusters created up-front, which the
periodic HDBSCAN re-cluster pass will merge back into single people
when there are enough samples to do it confidently.

Revision ID: 0008_clustering_accuracy
Revises: 0007_employee_dob_and_quality
Create Date: 2026-04-28
"""
from __future__ import annotations

from alembic import op

revision = "0008_clustering_accuracy"
down_revision = "0007_employee_dob_and_quality"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE attendance_settings "
        "SET unknown_cluster_match_threshold = "
        "GREATEST(unknown_cluster_match_threshold, 0.62)"
    )
    op.alter_column(
        "attendance_settings",
        "unknown_cluster_match_threshold",
        server_default="0.62",
    )


def downgrade() -> None:
    op.alter_column(
        "attendance_settings",
        "unknown_cluster_match_threshold",
        server_default="0.55",
    )
