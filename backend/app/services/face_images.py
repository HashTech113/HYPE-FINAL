"""Face training images CRUD.

Stored as base64 in the same way as ``employees.image_url`` and
``snapshot_logs.image_data`` — no filesystem to manage. The admin uploads
a multi-image reference set per employee via Settings → Employee
Management → Face Training; a future ML pipeline (or the deferred admin
backend on 8001) consumes this table to compute embeddings.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import select

from ..db import session_scope
from ..models import Employee as EmployeeModel, FaceImage

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class FaceImageRecord:
    id: int
    employee_id: str
    label: str
    image_data: str  # always returned as a data URL
    created_by: Optional[str]
    created_at: datetime


def _normalize_image(raw: str) -> str:
    """Strip the data URL prefix (if present) so we don't double-prefix on
    read. The DB stores the raw base64 payload."""
    if not raw:
        raise ValueError("image_data is empty")
    if raw.startswith("data:") and "," in raw:
        return raw.split(",", 1)[1]
    return raw


def _to_data_url(raw: str) -> str:
    """Wrap stored base64 in a JPEG data URL for direct use in <img src>.
    Older rows might already include the prefix; handle both."""
    if raw.startswith("data:"):
        return raw
    return f"data:image/jpeg;base64,{raw}"


def _to_record(row: FaceImage) -> FaceImageRecord:
    return FaceImageRecord(
        id=int(row.id),
        employee_id=str(row.employee_id),
        label=str(row.label or ""),
        image_data=_to_data_url(str(row.image_data or "")),
        created_by=str(row.created_by) if row.created_by else None,
        created_at=row.created_at,
    )


def list_for_employee(employee_id: str) -> list[FaceImageRecord]:
    """Return only face_images that still carry their inline base64
    payload. Rows whose ``image_data`` has been cleared by the post-
    training cleanup (``face_training.purge_trained_image_data``) are
    intentionally hidden so the Face Training panel reflects "pending
    uploads only" — the embeddings derived from the cleared photos
    remain in ``face_embeddings`` and continue to drive recognition.
    """
    with session_scope() as session:
        rows = session.execute(
            select(FaceImage)
            .where(FaceImage.employee_id == employee_id)
            .where(FaceImage.image_data != "")
            .order_by(FaceImage.created_at.desc(), FaceImage.id.desc())
        ).scalars().all()
        return [_to_record(r) for r in rows]


def add(
    *,
    employee_id: str,
    image_data: str,
    label: str = "",
    created_by: Optional[str] = None,
) -> FaceImageRecord:
    payload = _normalize_image(image_data)
    with session_scope() as session:
        if session.get(EmployeeModel, employee_id) is None:
            raise LookupError(f"employee {employee_id} not found")
        row = FaceImage(
            employee_id=employee_id,
            label=(label or "").strip()[:64],
            image_data=payload,
            created_by=created_by,
        )
        session.add(row)
        session.flush()
        return _to_record(row)


def delete(image_id: int) -> bool:
    with session_scope() as session:
        row = session.get(FaceImage, image_id)
        if row is None:
            return False
        session.delete(row)
        return True


def count_for_employee(employee_id: str) -> int:
    with session_scope() as session:
        return int(session.execute(
            select(__import__("sqlalchemy").func.count(FaceImage.id))
            .where(FaceImage.employee_id == employee_id)
        ).scalar_one() or 0)
