"""Request/response schemas for POST /api/external-attendance/sync."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ExternalSyncRequest(BaseModel):
    """All fields optional — calling the endpoint with an empty body pulls
    the full event list the vendor has on hand."""

    since: Optional[str] = Field(
        None,
        description=(
            "ISO timestamp (or vendor-accepted date string). Forwarded as a "
            "?since= query param — vendor-side semantics determine whether it "
            "filters by event time, by created_at, etc."
        ),
    )


class ExternalSyncResponse(BaseModel):
    """Counts for one sync run. Always returns 200 — callers can dashboard
    on ``failed`` / ``imported`` to spot regressions."""

    source: str = Field("external_api", description="Source label written to attendance_logs.source")
    requested_since: Optional[str] = Field(
        None, description="The ``since`` filter that was forwarded to the vendor."
    )
    fetched: int = Field(0, ge=0, description="Events returned by the vendor.")
    imported: int = Field(0, ge=0, description="Newly inserted attendance_logs rows.")
    skipped: int = Field(
        0,
        ge=0,
        description=(
            "Events the vendor already gave us before — dedup'd via "
            "external_event_id."
        ),
    )
    failed: int = Field(
        0,
        ge=0,
        description=(
            "Events that couldn't be imported because they were missing an id, "
            "name, timestamp, or had an unrecognized event_type."
        ),
    )
