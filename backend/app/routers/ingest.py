"""POST /api/ingest — receives captures pushed by capture.py."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import require_admin_or_hr, require_api_key
from ..schemas.ingest import IngestRequest, IngestResponse
from ..services import logs as logs_service
from ..services.snapshots import normalize_timestamp_iso, synthesize_image_path

log = logging.getLogger(__name__)

router = APIRouter(tags=["ingest"])

# Anything older than this is flagged "stale" — tuned to a few multiples of
# the expected capture cadence so brief pauses don't trip the alarm.
INGEST_STALE_THRESHOLD_SECONDS = 120


@router.post(
    "/api/ingest",
    response_model=IngestResponse,
    dependencies=[Depends(require_api_key)],
)
def ingest(payload: IngestRequest) -> IngestResponse:
    try:
        timestamp_iso = normalize_timestamp_iso(payload.timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    image_path = synthesize_image_path(
        payload.snap_id,
        payload.image_base64,
        timestamp_iso,
        camera_id=payload.camera_id,
    )

    stored = logs_service.record_capture(
        name=payload.name.strip(),
        timestamp_iso=timestamp_iso,
        image_path=image_path,
        image_data=payload.image_base64,
        camera_id=payload.camera_id,
    )
    if not stored:
        log.info("ingest dedup: duplicate skipped image_path=%s name=%s", image_path, payload.name)
    return IngestResponse(status="ok", stored=stored)


class IngestLastSeenResponse(BaseModel):
    last_seen: Optional[str]
    seconds_ago: Optional[int]
    stale: bool
    threshold_seconds: int


@router.get(
    "/api/ingest/last-seen",
    response_model=IngestLastSeenResponse,
    dependencies=[Depends(require_admin_or_hr)],
)
def ingest_last_seen() -> IngestLastSeenResponse:
    last = logs_service.snapshot_last_timestamp()
    if not last:
        return IngestLastSeenResponse(
            last_seen=None,
            seconds_ago=None,
            stale=True,
            threshold_seconds=INGEST_STALE_THRESHOLD_SECONDS,
        )
    try:
        dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
    except ValueError:
        return IngestLastSeenResponse(
            last_seen=last,
            seconds_ago=None,
            stale=True,
            threshold_seconds=INGEST_STALE_THRESHOLD_SECONDS,
        )
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    seconds_ago = max(0, int((datetime.now(timezone.utc) - dt).total_seconds()))
    return IngestLastSeenResponse(
        last_seen=dt.astimezone(timezone.utc).isoformat(),
        seconds_ago=seconds_ago,
        stale=seconds_ago > INGEST_STALE_THRESHOLD_SECONDS,
        threshold_seconds=INGEST_STALE_THRESHOLD_SECONDS,
    )
