"""extend cameras with smart-connect provenance fields

Adds nullable columns describing the inputs the smart-connect wizard
used to build the resolved `rtsp_url`:

  brand     String(64)   — profile id from camera_profiles catalog
  host      String(255)  — IP or hostname
  port      Integer
  username  String(128)
  password  String(256)  — plaintext (same exposure as rtsp_url)
  channel   String(16)
  stream    String(16)   — "main" | "sub"

All nullable so existing rows (which only have `rtsp_url`) stay valid
without backfill. The next time the user edits one of those rows the
form invites them to re-enter inputs and the columns get populated.

Revision ID: 0012_camera_connection_fields
Revises: 0011_employee_extra_fields
Create Date: 2026-05-09
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012_camera_connection_fields"
down_revision = "0011_employee_extra_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cameras", sa.Column("brand", sa.String(length=64), nullable=True))
    op.add_column("cameras", sa.Column("host", sa.String(length=255), nullable=True))
    op.add_column("cameras", sa.Column("port", sa.Integer(), nullable=True))
    op.add_column("cameras", sa.Column("username", sa.String(length=128), nullable=True))
    op.add_column("cameras", sa.Column("password", sa.String(length=256), nullable=True))
    op.add_column("cameras", sa.Column("channel", sa.String(length=16), nullable=True))
    op.add_column("cameras", sa.Column("stream", sa.String(length=16), nullable=True))


def downgrade() -> None:
    op.drop_column("cameras", "stream")
    op.drop_column("cameras", "channel")
    op.drop_column("cameras", "password")
    op.drop_column("cameras", "username")
    op.drop_column("cameras", "port")
    op.drop_column("cameras", "host")
    op.drop_column("cameras", "brand")
