"""widen cameras.password from 256 to 512 chars for Fernet encryption

Fernet ciphertext is base64 URL-safe encoded with a fixed 32-byte
header and a per-message HMAC, so a typical 32-char plaintext expands
to ~100 chars on disk. The previous 256-char column would still fit
most realistic passwords, but pinned us against the wall — a 64-char
password (vault-generated, common in enterprise installs) would
overflow at ~150 chars + Fernet padding. 512 leaves comfortable
headroom for any realistic password length.

Backward compat:
  Existing plaintext rows are untouched. The application's
  EncryptedString TypeDecorator detects "looks like Fernet" via the
  "gAAAA" prefix on read and falls back to passthrough for legacy
  rows. Rows naturally migrate to ciphertext as they're updated.

Revision ID: 0013_camera_password_encrypted
Revises: 0012_camera_connection_fields
Create Date: 2026-05-09
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0013_camera_password_encrypted"
down_revision = "0012_camera_connection_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # `existing_type` lets Postgres do an ALTER COLUMN TYPE without a
    # full table rewrite (only metadata changes when growing a varchar).
    op.alter_column(
        "cameras",
        "password",
        existing_type=sa.String(length=256),
        type_=sa.String(length=512),
        existing_nullable=True,
    )


def downgrade() -> None:
    # Down-migration would truncate any rows whose ciphertext exceeds
    # 256 chars — those rows would become unreadable. Refuse rather
    # than silently corrupt data; an operator who really needs to
    # downgrade can re-encrypt all rows under a key that produces
    # shorter tokens (impossible) or revert to plaintext via SQL.
    raise NotImplementedError(
        "Refusing to shrink cameras.password from 512→256: encrypted "
        "rows may exceed 256 chars and would be silently truncated. "
        "Decrypt rows manually before downgrading."
    )
