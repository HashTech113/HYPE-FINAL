"""Liveness + snapshot count + active DB dialect.

The ``database`` field is the public way to confirm whether a deploy is
running on PostgreSQL (production) or the SQLite fallback (local /
unconfigured Railway). It never includes credentials — only the dialect
name and, for SQLite, the file path so operators can verify which file
Railway is bind-mounting.
"""

from __future__ import annotations

from fastapi import APIRouter

from ..config import DB_PATH
from ..db import DIALECT
from ..services.logs import snapshot_log_count

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health() -> dict:
    payload: dict = {
        "status": "ok",
        "snapshot_count": snapshot_log_count(),
        "database": DIALECT,
    }
    if DIALECT == "sqlite":
        payload["db_path"] = str(DB_PATH)
    return payload
