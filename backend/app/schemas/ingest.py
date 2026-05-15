"""Request/response schemas for POST /api/ingest."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Recognized face name, or 'Unknown'")
    timestamp: str = Field(..., description="ISO8601 timestamp, UTC preferred")
    image_base64: str = Field(..., min_length=1, description="Base64-encoded JPEG (no data-URL prefix)")
    snap_id: Optional[str] = Field(None, description="Camera-side unique id, used for dedup")
    camera_id: Optional[str] = Field(
        None,
        description="Source camera's id from the cameras table. Optional — omitted in env-fallback mode.",
    )


class IngestResponse(BaseModel):
    status: str
    stored: bool
