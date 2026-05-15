"""POST /api/external-attendance/sync — pulls events from the third-party
attendance API and merges them into ``attendance_logs`` alongside local
camera rows.

Auth: admin only. Calling this is a write operation that mutates the roster
of attendance events; HR users read but don't reconcile.

Idempotency: dedup is by ``external_event_id`` via a partial unique index
on ``attendance_logs.external_event_id``. Re-running the sync after a
partial outage just re-imports the missing rows.

Configuration: see ``services.external_attendance.is_configured``. When
either the URL or key env var is missing the endpoint returns 503 rather
than silently doing nothing — same fail-closed posture as ``/api/ingest``.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import require_admin
from ..schemas.external import ExternalSyncRequest, ExternalSyncResponse
from ..services import external_attendance, logs as logs_service

log = logging.getLogger(__name__)

router = APIRouter(tags=["external_attendance"], dependencies=[Depends(require_admin)])


@router.post(
    "/api/external-attendance/sync",
    response_model=ExternalSyncResponse,
)
def sync_external_attendance(
    payload: Optional[ExternalSyncRequest] = None,
) -> ExternalSyncResponse:
    """Trigger a one-shot import from the external attendance API.

    The whole call is wrapped so any single bad event (missing id, bogus
    timestamp, weird event_type) just bumps ``failed`` and the rest of the
    batch keeps going. Network errors are absorbed by the service layer
    and produce ``fetched=0`` here."""
    if not external_attendance.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "External attendance API is not configured on this server "
                "(set EXTERNAL_ATTENDANCE_API_URL and EXTERNAL_ATTENDANCE_API_KEY)."
            ),
        )

    since = payload.since if payload else None
    events = external_attendance.fetch_events(since=since)
    fetched = len(events)
    imported = skipped = failed = 0

    for ev in events:
        try:
            external_id = external_attendance.extract_event_id(ev)
            name = external_attendance.extract_employee_name(ev)
            timestamp = external_attendance.extract_timestamp(ev)
            event_type = external_attendance.extract_event_type(ev)
            if not (external_id and name and timestamp and event_type):
                # Only log the first few problematic events at WARNING — past
                # that we drop to DEBUG so a malformed feed doesn't spam logs.
                if failed < 5:
                    log.warning(
                        "external sync: skipping malformed event "
                        "(id=%r name=%r ts=%r type=%r)",
                        external_id, name, timestamp, ev.get("event_type") or ev.get("type"),
                    )
                else:
                    log.debug(
                        "external sync: skipping malformed event "
                        "(id=%r name=%r ts=%r)",
                        external_id, name, timestamp,
                    )
                failed += 1
                continue
            stored = logs_service.record_external_event(
                name=name,
                timestamp_iso=timestamp,
                external_event_id=external_id,
                event_type=event_type,
            )
            if stored:
                imported += 1
            else:
                skipped += 1
        except Exception:
            # Defensive — a programmer error in a normalizer must not abort
            # the whole sync. Count it as failed and move on.
            log.exception("external sync: unexpected error processing event %r", ev)
            failed += 1

    log.info(
        "external sync complete: since=%s fetched=%d imported=%d skipped=%d failed=%d",
        since, fetched, imported, skipped, failed,
    )
    return ExternalSyncResponse(
        requested_since=since,
        fetched=fetched,
        imported=imported,
        skipped=skipped,
        failed=failed,
    )
