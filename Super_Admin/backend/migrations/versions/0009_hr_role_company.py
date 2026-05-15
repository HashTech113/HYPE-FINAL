"""add HR role + admins.company for multi-tenant HR dashboard

Revision ID: 0009_hr_role_company
Revises: 0008_clustering_accuracy
Create Date: 2026-04-29
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_hr_role_company"
down_revision = "0008_clustering_accuracy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add HR to the admin_role enum (Postgres needs ALTER TYPE ... ADD VALUE).
    # Run outside a transaction block — Postgres doesn't allow ADD VALUE
    # inside one before commit, even with ALTER TYPE ... ADD VALUE IF NOT EXISTS.
    op.execute("COMMIT")
    op.execute("ALTER TYPE admin_role ADD VALUE IF NOT EXISTS 'HR'")

    op.add_column(
        "admins",
        sa.Column("company", sa.String(length=128), nullable=True),
    )
    op.create_index("ix_admins_company", "admins", ["company"])


def downgrade() -> None:
    op.drop_index("ix_admins_company", table_name="admins")
    op.drop_column("admins", "company")
    # Postgres has no DROP VALUE for enums — the HR value stays. Harmless
    # since downgrade only runs in dev environments.
