from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.constants import CameraType
from app.schemas.common import ORMModel

_ALLOWED_SCHEMES = ("rtsp://", "rtsps://", "http://", "https://")


def _validate_rtsp(v: str | None) -> str | None:
    if v is None:
        return v
    v = v.strip()
    if not v:
        raise ValueError("rtsp_url must not be empty")
    lowered = v.lower()
    if not any(lowered.startswith(s) for s in _ALLOWED_SCHEMES):
        raise ValueError(f"rtsp_url must start with one of: {', '.join(_ALLOWED_SCHEMES)}")
    return v


class CameraBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    rtsp_url: str = Field(min_length=1, max_length=1024)
    camera_type: CameraType
    location: str | None = Field(default=None, max_length=256)
    description: str | None = None

    @field_validator("rtsp_url")
    @classmethod
    def _rtsp_fmt(cls, v: str) -> str:
        return _validate_rtsp(v)  # type: ignore[return-value]


class CameraCreate(CameraBase):
    is_active: bool = True


class CameraUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    rtsp_url: str | None = Field(default=None, min_length=1, max_length=1024)
    camera_type: CameraType | None = None
    location: str | None = Field(default=None, max_length=256)
    description: str | None = None
    is_active: bool | None = None

    @field_validator("rtsp_url")
    @classmethod
    def _rtsp_fmt(cls, v: str | None) -> str | None:
        return _validate_rtsp(v)


class CameraRead(ORMModel):
    id: int
    name: str
    rtsp_url: str
    camera_type: CameraType
    location: str | None
    description: str | None
    is_active: bool
    # --- Smart-connect provenance (NULL if created via "Custom URL") ---
    brand: str | None = None
    host: str | None = None
    port: int | None = None
    username: str | None = None
    # `password` deliberately not exposed — the UI re-asks for it on
    # edit. Sending it back would invite token logging / browser
    # caching of the cleartext.
    channel: str | None = None
    stream: str | None = None
    created_at: datetime
    updated_at: datetime


class CameraHealth(BaseModel):
    id: int
    name: str
    is_active: bool
    is_running: bool
    last_heartbeat_age_seconds: float | None
    # None until a frame is actually received. The frontend uses this —
    # not `last_heartbeat_age_seconds` — to label a camera "Live", because
    # the heartbeat keeps ticking even while RTSP reads silently fail.
    last_frame_age_seconds: float | None = None
    processed_frames: int = 0
    last_error: str | None


class CameraProbeRequest(BaseModel):
    rtsp_url: str = Field(min_length=1, max_length=1024)
    timeout_ms: int = Field(default=5000, ge=500, le=30000)

    @field_validator("rtsp_url")
    @classmethod
    def _rtsp_fmt(cls, v: str) -> str:
        return _validate_rtsp(v)  # type: ignore[return-value]


class CameraProbeResult(BaseModel):
    ok: bool
    width: int | None = None
    height: int | None = None
    elapsed_ms: int
    error: str | None = None


# --- Smart-connect wizard ------------------------------------------------


class CameraStreamVariantRead(BaseModel):
    id: str
    label: str


class CameraProfileRead(BaseModel):
    """One brand entry surfaced to the wizard. The frontend uses this
    to render the brand picker, default port hint, and stream-quality
    chooser.
    """

    id: str
    name: str
    aliases: list[str] = []
    default_port: int
    default_username: str
    default_channel: str
    streams: list[CameraStreamVariantRead]
    notes: str = ""


class CameraConnectRequest(BaseModel):
    """Inputs from the wizard. Backend builds candidate URLs from the
    brand profile, probes them in order, and returns the first that
    works (or every attempt's outcome on failure).
    """

    brand: str = Field(min_length=1, max_length=64)
    host: str = Field(min_length=1, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    username: str | None = Field(default=None, max_length=128)
    password: str | None = Field(default=None, max_length=256)
    channel: str | None = Field(default=None, max_length=16)
    stream: str = Field(default="main", max_length=16)
    per_attempt_timeout_ms: int = Field(default=4000, ge=500, le=15000)


class CameraConnectAttempt(BaseModel):
    """One URL attempted during a connect, with the password masked.
    Surfaced to the UI so users can see which template variant worked
    (and which failed and why) when troubleshooting.
    """

    template_index: int
    url: str  # password-masked
    ok: bool
    elapsed_ms: int
    width: int | None = None
    height: int | None = None
    error: str | None = None


class CameraConnectResult(BaseModel):
    ok: bool
    profile_id: str
    success_url: str | None = None  # password-masked
    success_template_index: int | None = None
    width: int | None = None
    height: int | None = None
    elapsed_ms: int
    attempts: list[CameraConnectAttempt]
    error: str | None = None


class CameraSmartCreateRequest(CameraConnectRequest):
    """Smart-connect that ALSO persists on success. Combines the brand
    + connection inputs with the metadata required to create a Camera
    row (name, type, location...).
    """

    name: str = Field(min_length=1, max_length=128)
    camera_type: CameraType
    location: str | None = Field(default=None, max_length=256)
    description: str | None = None
    is_active: bool = True
