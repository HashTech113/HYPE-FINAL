"""Shared helpers used by the capture → ingest pipeline.

The DB is the single source of truth for captures (image bytes live inline
as base64 in ``snapshot_logs.image_data``). This module no longer reads or
writes the filesystem — it only exposes the dataclass and the name/timestamp
helpers that ``capture.py`` uses to build ingest payloads.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ..config import LOCAL_TZ_OFFSET_MIN

log = logging.getLogger(__name__)

NAME_SAFE_RE = re.compile(r"[^A-Za-z0-9]+")

# Image field preference: captured-face, body, enrolled-face, background.
IMAGE_FIELDS = ("Image2", "Image3", "Image1", "Image4")


def synthesize_image_path(
    snap_id: Optional[str],
    image_b64: str,
    timestamp_iso: str,
    *,
    camera_id: Optional[str] = None,
) -> str:
    """Stable per-capture identifier used as the UNIQUE dedup key in
    snapshot_logs/attendance_logs. Prefer the camera's SnapId; fall back
    to a content-addressed hash so re-ingesting the same bytes dedups.

    When ``camera_id`` is supplied (multi-camera mode) it's woven into the
    path so two cameras emitting the same SnapId don't collide on the
    UNIQUE(image_path) constraint. Legacy single-camera captures keep the
    old ``ingest_<snap_id>.jpg`` shape so existing rows stay valid."""
    prefix = f"ingest_{camera_id}_" if camera_id else "ingest_"
    if snap_id:
        return f"{prefix}{snap_id}.jpg"
    digest = hashlib.sha1(image_b64.encode("ascii", errors="ignore")).hexdigest()[:16]
    return f"{prefix}{timestamp_iso.replace(':', '').replace('-', '')}_{digest}.jpg"


def normalize_timestamp_iso(value: Any) -> str:
    """Coerce a timestamp value (epoch seconds, ISO string, or datetime)
    into a UTC ISO-8601 string. Raises ValueError on failure."""
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"timestamp must be ISO8601, got {value!r}") from exc
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    else:
        raise ValueError(f"unsupported timestamp type: {type(value).__name__}")
    return dt.astimezone(timezone.utc).isoformat()


@dataclass
class Snapshot:
    filename: str
    name: str
    entry: datetime
    exit: datetime
    image_data: Optional[str] = None
    camera_id: Optional[str] = None
    camera_name: Optional[str] = None
    score: Optional[float] = None


def sanitize_name(name: str) -> str:
    cleaned = NAME_SAFE_RE.sub("_", name.strip()).strip("_")
    return cleaned[:32] or "Unknown"


def _epoch_local_to_utc(value: float) -> datetime:
    """The camera uses a non-standard "local-time seconds since 1970" epoch
    (the number represents IST on the camera's clock). Re-interpret it as
    such and return true UTC by subtracting the local offset.
    """
    as_if_utc = datetime.fromtimestamp(value, tz=timezone.utc)
    return as_if_utc - timedelta(minutes=LOCAL_TZ_OFFSET_MIN)


def _to_utc(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return _epoch_local_to_utc(float(value))
        if isinstance(value, str):
            v = value.strip()
            if v.isdigit():
                return _epoch_local_to_utc(float(v))
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00")).astimezone(timezone.utc)
            except ValueError:
                local_tz = timezone(timedelta(minutes=LOCAL_TZ_OFFSET_MIN))
                local_dt = datetime.strptime(v, "%Y-%m-%d %H:%M:%S").replace(tzinfo=local_tz)
                return local_dt.astimezone(timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None
    return None
