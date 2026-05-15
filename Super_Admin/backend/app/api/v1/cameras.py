from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.deps import (
    get_camera_manager,
    get_current_admin,
    get_db,
    require_roles,
)
from app.config import get_settings
from app.core.constants import Role
from app.core.exceptions import (
    AlreadyExistsError,
    AuthenticationError,
    NotFoundError,
)
from app.core.logger import get_logger
from app.core.rate_limit import preview_rate_limit
from app.core.security import decode_token
from app.models.admin import Admin
from app.models.camera import Camera
from app.repositories.camera_repo import CameraRepository
from app.schemas.camera import (
    CameraConnectAttempt,
    CameraConnectRequest,
    CameraConnectResult,
    CameraCreate,
    CameraHealth,
    CameraProbeRequest,
    CameraProbeResult,
    CameraProfileRead,
    CameraRead,
    CameraSmartCreateRequest,
    CameraStreamVariantRead,
    CameraUpdate,
)
from app.services.auth_service import AuthService
from app.services.camera_connector import smart_connect
from app.services.camera_profiles import list_profiles
from app.services.realtime_bus import bus as realtime_bus
from app.workers.camera_manager import CameraManager
from app.workers.rtsp_probe import probe_rtsp

router = APIRouter(prefix="/cameras", tags=["cameras"])
log = get_logger(__name__)


@router.get("", response_model=list[CameraRead])
def list_cameras(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> list[CameraRead]:
    return [CameraRead.model_validate(c) for c in CameraRepository(db).list_all()]


@router.get("/health", response_model=list[CameraHealth])
def cameras_health(
    db: Session = Depends(get_db),
    manager: CameraManager = Depends(get_camera_manager),
    _: Admin = Depends(get_current_admin),
) -> list[CameraHealth]:
    statuses = {s["camera_id"]: s for s in manager.status()}
    result: list[CameraHealth] = []
    for cam in CameraRepository(db).list_all():
        s = statuses.get(cam.id)
        result.append(
            CameraHealth(
                id=cam.id,
                name=cam.name,
                is_active=cam.is_active,
                is_running=bool(s and s["is_running"]),
                last_heartbeat_age_seconds=s["last_heartbeat_age_seconds"] if s else None,
                last_frame_age_seconds=s["last_frame_age_seconds"] if s else None,
                processed_frames=int(s["processed_frames"]) if s else 0,
                last_error=s["last_error"] if s else None,
            )
        )
    return result


@router.post("/probe", response_model=CameraProbeResult)
async def probe_camera(
    payload: CameraProbeRequest,
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
) -> CameraProbeResult:
    outcome = await run_in_threadpool(probe_rtsp, payload.rtsp_url, timeout_ms=payload.timeout_ms)
    return CameraProbeResult(
        ok=outcome.ok,
        width=outcome.width,
        height=outcome.height,
        elapsed_ms=outcome.elapsed_ms,
        error=outcome.error,
    )


# --- Smart-connect wizard --------------------------------------------------
#
# Two endpoints power the wizard:
#
#   GET  /cameras/profiles  — the brand catalog. Frontend renders a
#                             searchable dropdown from this. Cached
#                             aggressively because the catalog is
#                             baked into the binary.
#   POST /cameras/connect   — try every URL template the brand profile
#                             generates against the supplied IP/creds,
#                             return the first that returns a frame
#                             (and a per-attempt audit trail).
#   POST /cameras/smart     — same as /connect but also persists a new
#                             Camera row on success, so the user
#                             experiences a single "Connect & Save"
#                             button instead of two phases.
#
# The legacy POST /cameras (raw rtsp_url) and POST /cameras/probe stay
# in place — they're the "Custom RTSP URL" escape hatch for cameras
# the catalog doesn't yet cover.


@router.get("/profiles", response_model=list[CameraProfileRead])
def list_camera_profiles(
    _: Admin = Depends(get_current_admin),
) -> list[CameraProfileRead]:
    return [
        CameraProfileRead(
            id=p.id,
            name=p.name,
            aliases=list(p.aliases),
            default_port=p.default_port,
            default_username=p.default_username,
            default_channel=p.default_channel,
            streams=[CameraStreamVariantRead(id=s.id, label=s.label) for s in p.streams],
            notes=p.notes,
        )
        for p in list_profiles()
    ]


def _connect_to_schema(result) -> CameraConnectResult:
    return CameraConnectResult(
        ok=result.ok,
        profile_id=result.profile_id,
        # Always return the redacted form to clients — passwords must
        # never round-trip through the API in cleartext.
        success_url=(
            next(
                (
                    a.redacted_url
                    for a in result.attempts
                    if a.template_index == result.success_template_index
                ),
                None,
            )
            if result.success_template_index is not None
            else None
        ),
        success_template_index=result.success_template_index,
        width=result.width,
        height=result.height,
        elapsed_ms=result.elapsed_ms,
        attempts=[
            CameraConnectAttempt(
                template_index=a.template_index,
                url=a.redacted_url,
                ok=a.outcome.ok,
                elapsed_ms=a.outcome.elapsed_ms,
                width=a.outcome.width,
                height=a.outcome.height,
                error=a.outcome.error,
            )
            for a in result.attempts
        ],
        error=result.error,
    )


@router.post("/connect", response_model=CameraConnectResult)
async def connect_camera(
    payload: CameraConnectRequest,
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
) -> CameraConnectResult:
    """Smart-connect dry run. Tries the brand's URL templates and
    returns which (if any) work — does NOT save anything. Used by the
    wizard's "Test connection" button.
    """
    result = await run_in_threadpool(
        smart_connect,
        profile_id=payload.brand,
        host=payload.host,
        port=payload.port,
        username=payload.username,
        password=payload.password,
        channel=payload.channel,
        stream_id=payload.stream,
        per_attempt_timeout_ms=payload.per_attempt_timeout_ms,
    )
    return _connect_to_schema(result)


@router.post("/smart", response_model=CameraRead, status_code=201)
async def smart_create_camera(
    payload: CameraSmartCreateRequest,
    db: Session = Depends(get_db),
    manager: CameraManager = Depends(get_camera_manager),
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
) -> CameraRead:
    """Smart-connect AND save in one call. On success persists a
    Camera row with both the resolved `rtsp_url` and the smart-connect
    inputs (so the edit dialog can pre-fill them later). Fails with
    422 (no DB write) if no URL template works.
    """
    repo = CameraRepository(db)
    if repo.get_by_name(payload.name) is not None:
        raise AlreadyExistsError(f"Camera '{payload.name}' already exists")

    result = await run_in_threadpool(
        smart_connect,
        profile_id=payload.brand,
        host=payload.host,
        port=payload.port,
        username=payload.username,
        password=payload.password,
        channel=payload.channel,
        stream_id=payload.stream,
        per_attempt_timeout_ms=payload.per_attempt_timeout_ms,
    )
    if not result.ok or not result.success_url:
        # Surface the same diagnostic shape the /connect endpoint uses
        # but as a 422 so the UI knows to render error UI rather than
        # close the dialog. We embed the redacted attempts in the
        # error body so the user can see what we tried.
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail={
                "error": "smart_connect_failed",
                "message": result.error or "No URL template returned a frame",
                "attempts": [
                    {
                        "template_index": a.template_index,
                        "url": a.redacted_url,
                        "ok": a.outcome.ok,
                        "elapsed_ms": a.outcome.elapsed_ms,
                        "error": a.outcome.error,
                    }
                    for a in result.attempts
                ],
            },
        )

    cam = Camera(
        name=payload.name,
        rtsp_url=result.success_url,
        camera_type=payload.camera_type,
        location=payload.location,
        description=payload.description,
        is_active=payload.is_active,
        brand=payload.brand,
        host=payload.host,
        port=payload.port,
        username=payload.username,
        password=payload.password,
        channel=payload.channel,
        stream=payload.stream,
    )
    repo.add(cam)
    db.commit()
    realtime_bus.publish("camera", kind="created", camera_id=cam.id)
    response = CameraRead.model_validate(cam)
    if cam.is_active:
        try:
            manager.restart(cam.id)
        except Exception:
            log.exception("Failed to start worker for new camera id=%s", cam.id)
    return response


@router.get("/{camera_id}", response_model=CameraRead)
def get_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> CameraRead:
    cam = CameraRepository(db).get(camera_id)
    if cam is None:
        raise NotFoundError(f"Camera {camera_id} not found")
    return CameraRead.model_validate(cam)


@router.post("", response_model=CameraRead, status_code=201)
def create_camera(
    payload: CameraCreate,
    db: Session = Depends(get_db),
    manager: CameraManager = Depends(get_camera_manager),
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
) -> CameraRead:
    repo = CameraRepository(db)
    if repo.get_by_name(payload.name) is not None:
        raise AlreadyExistsError(f"Camera '{payload.name}' already exists")
    cam = Camera(
        name=payload.name,
        rtsp_url=payload.rtsp_url,
        camera_type=payload.camera_type,
        location=payload.location,
        description=payload.description,
        is_active=payload.is_active,
    )
    repo.add(cam)
    db.commit()
    realtime_bus.publish("camera", kind="created", camera_id=cam.id)
    response = CameraRead.model_validate(cam)
    if cam.is_active:
        try:
            manager.restart(cam.id)
        except Exception:
            log.exception("Failed to start worker for new camera id=%s", cam.id)
    return response


@router.patch("/{camera_id}", response_model=CameraRead)
def update_camera(
    camera_id: int,
    payload: CameraUpdate,
    db: Session = Depends(get_db),
    manager: CameraManager = Depends(get_camera_manager),
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
) -> CameraRead:
    repo = CameraRepository(db)
    cam = repo.get(camera_id)
    if cam is None:
        raise NotFoundError(f"Camera {camera_id} not found")

    data = payload.model_dump(exclude_unset=True)
    new_name = data.get("name")
    if new_name is not None and new_name != cam.name:
        clash = repo.get_by_name(new_name)
        if clash is not None and clash.id != cam.id:
            raise AlreadyExistsError(f"Camera '{new_name}' already exists")

    repo.update(cam, data)
    db.commit()
    realtime_bus.publish("camera", kind="updated", camera_id=cam.id)
    response = CameraRead.model_validate(cam)
    try:
        manager.restart(camera_id)
    except Exception:
        log.exception("Failed to restart worker after camera update id=%s", camera_id)
    return response


@router.delete("/{camera_id}", status_code=204, response_model=None)
def delete_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    manager: CameraManager = Depends(get_camera_manager),
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN)),
) -> None:
    repo = CameraRepository(db)
    cam = repo.get(camera_id)
    if cam is None:
        raise NotFoundError(f"Camera {camera_id} not found")
    cam.is_active = False
    db.commit()
    realtime_bus.publish("camera", kind="deactivated", camera_id=cam.id)
    try:
        manager.restart(camera_id)
    except Exception:
        log.exception("Failed to stop worker on delete id=%s", camera_id)


@router.post("/{camera_id}/restart", status_code=204, response_model=None)
def restart_camera(
    camera_id: int,
    manager: CameraManager = Depends(get_camera_manager),
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
) -> None:
    manager.restart(camera_id)


@router.get("/{camera_id}/preview.jpg", response_class=Response)
def camera_preview(
    camera_id: int,
    annotated: bool = Query(True),
    max_age_seconds: float = Query(10.0, ge=0.5, le=120.0),
    quality: int = Query(80, ge=30, le=95),
    max_width: int | None = Query(None, ge=160, le=3840),
    token: str | None = Query(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    manager: CameraManager = Depends(get_camera_manager),
    _rate: None = Depends(preview_rate_limit),
) -> Response:
    """Return the most recent frame from this camera as a JPEG, with
    face-detection bounding boxes drawn on top by default.
    Used by the `/live` page's polling-based tile refresh — each <img>
    re-fetches this URL with a cache-busting query param every 80 ms,
    which is far more robust than long-lived multipart streams (no
    connection-cap exhaustion when navigating between pages).

    Auth: JWT cryptographic verify only — no DB lookup. With 4 cameras
    polling at ~12 fps each, the previous per-request `SELECT * FROM
    admins` (~50 round-trips/sec) was contending with the recognition
    pipeline's writes for the SQLAlchemy connection pool, which froze
    the live tile for seconds whenever a face was detected. JWTs are
    self-signed and time-bounded; a deactivated admin's token still
    streams previews until the JWT expires, but every other endpoint
    re-validates against the DB so they can't actually do anything.

    Bearer either via standard `Authorization: Bearer …` header OR a
    `?token=` query param (required because <img> tags can't set
    headers).
    """
    bearer: str | None = None
    if credentials and credentials.credentials:
        bearer = credentials.credentials
    if bearer is None and token:
        bearer = token.strip() or None
    if bearer is None:
        raise AuthenticationError("Missing bearer token")
    payload_jwt = decode_token(bearer)
    if payload_jwt.get("type") != "access" or payload_jwt.get("sub") is None:
        raise AuthenticationError("Invalid token")

    payload = manager.get_preview_jpeg(
        camera_id,
        annotated=annotated,
        max_age_seconds=max_age_seconds,
        quality=quality,
        max_width=max_width,
    )
    if payload is None:
        raise NotFoundError(f"No recent frame from camera {camera_id}")
    return Response(
        content=payload,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-store"},
    )


_MJPEG_BOUNDARY = "aifrm"


@router.get("/{camera_id}/preview.mjpg")
async def camera_preview_mjpeg(
    camera_id: int,
    request: Request,
    token: str = Query(..., min_length=1, description="JWT (same as bearer)"),
    fps: int | None = Query(None, ge=1, le=30),
    annotated: bool = Query(True),
    quality: int | None = Query(None, ge=30, le=95),
    max_width: int | None = Query(None, ge=160, le=3840),
    db: Session = Depends(get_db),
    manager: CameraManager = Depends(get_camera_manager),
) -> StreamingResponse:
    """Live MJPEG stream for the dashboard's Live tile.

    Uses `multipart/x-mixed-replace` so a single long-lived connection
    pushes one JPEG per fresh frame produced by the worker — no per-frame
    HTTP overhead, no client-side polling jitter.

    Auth via `?token=` because <img src="…"> can't set headers. The token
    is the same JWT issued by `/auth/login`. The browser auto-reconnects
    if the connection drops, so the frontend doesn't have to.

    All tunables (fps, quality, max_width) default to PREVIEW_* config
    values so a single config change rolls out across every Live tile.
    """
    # Auth (same JWT as bearer; no role gate beyond `is_active`).
    AuthService(db).resolve_admin(token)

    settings = get_settings()
    eff_fps = int(fps if fps is not None else settings.PREVIEW_DEFAULT_FPS)
    eff_quality = int(quality if quality is not None else settings.PREVIEW_DEFAULT_QUALITY)
    eff_max_width = int(max_width if max_width is not None else settings.PREVIEW_MAX_WIDTH)

    # The previous implementation slept up to `1/eff_fps` seconds before
    # every yield to clamp output to the requested fps. With the new
    # seq-based wait, that was pure dead time on the hot path — the
    # worker already publishes at the configured `camera_fps` and
    # `wait_preview_jpeg` blocks until the next fresh seq, so we yield
    # exactly once per produced frame with zero idle sleep.
    #
    # `eff_fps` survives only as a *cap* enforced lazily: if the worker
    # is publishing significantly faster than the client requested, we
    # subsample by skipping intermediate seqs (the seq-wait returns the
    # latest, never an old one). For production CCTV — where camera_fps
    # is the rate-limiter — this branch is never taken.
    min_interval = 1.0 / float(eff_fps)
    boundary = _MJPEG_BOUNDARY

    async def producer():
        loop = asyncio.get_event_loop()
        last_seq = 0
        last_yield_at = 0.0
        consecutive_stale = 0

        # Send the most recent cached frame IMMEDIATELY on connect so the
        # browser's <img> has pixels to paint within the first network
        # round-trip — no black-tile gap while we wait for the next worker
        # publish (worst case ~67 ms at camera_fps=15, but during a brief
        # camera hiccup that gap can stretch to seconds and looks broken).
        priming = await run_in_threadpool(
            manager.get_preview_jpeg,
            camera_id,
            annotated=annotated,
            max_age_seconds=10.0,
            quality=eff_quality,
            max_width=eff_max_width,
        )
        if priming is not None:
            header = (
                f"--{boundary}\r\n"
                f"Content-Type: image/jpeg\r\n"
                f"Content-Length: {len(priming)}\r\n\r\n"
            ).encode("ascii")
            yield header + priming + b"\r\n"
            last_yield_at = loop.time()

        while True:
            if await request.is_disconnected():
                break

            result = await run_in_threadpool(
                manager.wait_preview_jpeg,
                camera_id,
                last_seen_seq=last_seq,
                annotated=annotated,
                quality=eff_quality,
                max_width=eff_max_width,
                max_wait_seconds=2.0,
                max_age_seconds=10.0,
            )
            if result is None:
                # No fresh frame in 2s — TCP keepalive holds the socket
                # open; browsers tolerate gaps fine. We don't yield an
                # invalid empty part (some clients drop the connection
                # when they see one).
                consecutive_stale += 1
                if consecutive_stale > 30:
                    # ~60s without a frame — let the client reconnect to
                    # rebuild state on whatever worker is now live.
                    break
                continue
            consecutive_stale = 0

            jpeg, new_seq = result
            last_seq = new_seq
            header = (
                f"--{boundary}\r\nContent-Type: image/jpeg\r\nContent-Length: {len(jpeg)}\r\n\r\n"
            ).encode("ascii")
            yield header + jpeg + b"\r\n"

            # Lazy throttle: only slow down if the worker is publishing
            # faster than the requested cap.
            now = loop.time()
            elapsed = now - last_yield_at if last_yield_at else min_interval
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            last_yield_at = now

    headers = {
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
        # Disable response buffering on reverse proxies (nginx, etc.)
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        producer(),
        media_type=f"multipart/x-mixed-replace; boundary={boundary}",
        headers=headers,
    )
