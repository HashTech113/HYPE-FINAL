"""Pydantic schemas for /api/cameras."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

CameraType = Literal["ENTRY", "EXIT"]


class CameraOut(BaseModel):
    id: str
    name: str
    location: str
    ip: str
    port: int
    username: str
    rtsp_path: str
    rtsp_url_preview: str  # masked; never includes the password
    connection_status: str
    enable_face_ingest: bool
    auto_discovery_enabled: bool
    type: CameraType = "ENTRY"
    last_known_ip: Optional[str]
    last_discovered_at: Optional[str]
    last_checked_at: Optional[str]
    last_check_message: Optional[str]
    created_at: str
    updated_at: str


class CameraCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    location: str = Field("", max_length=256)
    ip: str = Field(..., min_length=1, max_length=64)
    port: int = Field(554, ge=1, le=65535)
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=256)
    rtsp_path: str = Field("/Streaming/Channels/101", min_length=1, max_length=256)
    # Both flags are optional at create-time. When omitted, the model
    # defaults (face_ingest=True, auto_discovery=False) apply, preserving
    # the pre-toggle behavior. The frontend form sends explicit values so
    # the user's choice in the Add Camera dialog is honored.
    enable_face_ingest: Optional[bool] = None
    auto_discovery_enabled: Optional[bool] = None
    # ENTRY (default) or EXIT. Drives the attendance state machine —
    # see services.attendance_state.STATE_TRANSITIONS.
    type: Optional[CameraType] = None


class CameraUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    location: Optional[str] = Field(None, max_length=256)
    ip: Optional[str] = Field(None, min_length=1, max_length=64)
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = Field(None, min_length=1, max_length=128)
    # Empty / None = leave the existing password unchanged.
    password: Optional[str] = Field(None, max_length=256)
    rtsp_path: Optional[str] = Field(None, min_length=1, max_length=256)
    enable_face_ingest: Optional[bool] = None
    auto_discovery_enabled: Optional[bool] = None
    type: Optional[CameraType] = None


class CameraCheckRequest(BaseModel):
    """Form-time check — uses values being typed without saving a row."""
    ip: str = Field(..., min_length=1, max_length=64)
    port: int = Field(554, ge=1, le=65535)
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=256)
    rtsp_path: str = Field("/Streaming/Channels/101", min_length=1, max_length=256)


class CameraCheckResponse(BaseModel):
    ok: bool
    message: str
    latency_ms: int


class CameraListResponse(BaseModel):
    items: list[CameraOut]


class StreamTokenResponse(BaseModel):
    token: str
    expires_in: int


class CameraRediscoverResponse(BaseModel):
    """Result of a manual auto-discovery sweep for one DB-backed camera.

    ``previous_ip`` and ``new_ip`` are equal when discovery confirmed the
    saved IP is still correct (still useful — signals the camera is alive
    on the LAN). ``new_ip`` is None when no Uniview host on the camera's
    /24 passed the login probe."""
    ok: bool
    message: str
    previous_ip: str
    new_ip: Optional[str]


# ---- Worker health --------------------------------------------------------

CameraBrand = Literal["hikvision", "cp_plus", "dahua", "axis", "generic"]


class CameraHealth(BaseModel):
    """Live worker state for one camera.

    A row exists per camera whether or not a recognition worker is running
    — when no worker is up, ``is_running=False`` and the frame-age fields
    are ``None``. Use ``last_frame_age_seconds`` (not ``is_running``) to
    decide whether the stream is actually "live": a worker keeps heart-
    beating its loop even while RTSP reads silently fail.
    """
    id: str
    name: str
    is_running: bool
    last_frame_age_seconds: Optional[float]
    last_match_age_seconds: Optional[float]
    processed_frames: int
    faces_detected: int
    matches_recorded: int
    last_error: Optional[str]
    backoff_seconds: float
    enable_face_ingest: bool
    connection_status: str


class CameraHealthListResponse(BaseModel):
    items: list[CameraHealth]


# ---- Smart probe ----------------------------------------------------------


class CameraSmartProbeRequest(BaseModel):
    """Try every RTSP-path template for a brand against one host/credentials.

    Stops at the first template that returns a frame; otherwise returns a
    per-attempt audit trail so the operator can see which paths were tried
    and why they failed. The winning ``rtsp_path`` is returned for the
    operator to persist via the standard CRUD — no row is written here.
    """
    brand: CameraBrand
    ip: str = Field(..., min_length=1, max_length=64)
    port: int = Field(554, ge=1, le=65535)
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=256)
    per_attempt_timeout_s: float = Field(4.0, ge=1.0, le=15.0)


class CameraSmartProbeAttempt(BaseModel):
    template_index: int
    rtsp_path: str
    rtsp_url_masked: str  # password redacted
    ok: bool
    elapsed_ms: int
    width: Optional[int]
    height: Optional[int]
    error: Optional[str]


class CameraSmartProbeResponse(BaseModel):
    ok: bool
    brand: CameraBrand
    success_template_index: Optional[int]
    success_rtsp_path: Optional[str]
    width: Optional[int]
    height: Optional[int]
    elapsed_ms: int
    attempts: list[CameraSmartProbeAttempt]
    error: Optional[str]
