"""Cameras router — CRUD, connection-check, and MJPEG stream proxy.

All CRUD/check endpoints require the admin role. The MJPEG stream uses a
separate short-lived stream token (5 min, scoped to camera_id) so that
``<img>`` tags — which can't send Authorization headers — can authenticate
via query string without exposing the long-lived JWT.
"""

from __future__ import annotations

import logging
import os
import time

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..config import JWT_ALGORITHM, JWT_SECRET
from ..dependencies import require_admin
from ..schemas.cameras import (
    CameraCheckRequest,
    CameraCheckResponse,
    CameraCreate,
    CameraHealth,
    CameraHealthListResponse,
    CameraListResponse,
    CameraOut,
    CameraRediscoverResponse,
    CameraSmartProbeAttempt,
    CameraSmartProbeRequest,
    CameraSmartProbeResponse,
    CameraUpdate,
    StreamTokenResponse,
)
from ..services import cameras as cameras_service
from ..services import crypto

log = logging.getLogger(__name__)

router = APIRouter(tags=["cameras"], prefix="/api/cameras")

STREAM_TOKEN_TTL_SECONDS = 300  # 5 min — refreshed by the frontend
STREAM_TOKEN_SCOPE = "camera-stream"


def _workers_enabled() -> bool:
    raw = os.getenv("RECOGNITION_WORKERS_ENABLED", "1").strip().lower()
    return raw not in ("0", "false", "no")


def _refresh_workers() -> None:
    if not _workers_enabled():
        return
    try:
        from ..services.recognition_worker import get_worker_manager
        count = get_worker_manager().start_all()
        log.info("recognition workers refreshed (%d cameras)", count)
    except Exception:
        # Camera CRUD should still succeed even if worker refresh fails.
        log.exception("failed to refresh recognition workers")


def _serialize(cam: cameras_service.Camera) -> CameraOut:
    return CameraOut(
        id=cam.id,
        name=cam.name,
        location=cam.location,
        ip=cam.ip,
        port=cam.port,
        username=cam.username,
        rtsp_path=cam.rtsp_path,
        rtsp_url_preview=cameras_service.masked_rtsp_url(cam),
        connection_status=cam.connection_status,
        enable_face_ingest=cam.enable_face_ingest,
        auto_discovery_enabled=cam.auto_discovery_enabled,
        type=cam.type if cam.type in ("ENTRY", "EXIT") else "ENTRY",
        last_known_ip=cam.last_known_ip,
        last_discovered_at=cam.last_discovered_at,
        last_checked_at=cam.last_checked_at,
        last_check_message=cam.last_check_message,
        created_at=cam.created_at,
        updated_at=cam.updated_at,
    )


@router.get(
    "",
    response_model=CameraListResponse,
    dependencies=[Depends(require_admin)],
)
def list_cameras(response: Response) -> CameraListResponse:
    # Same short browser cache as /api/employees — repeat polls within
    # 5 s come straight from the local cache, eliminating the matching
    # OPTIONS + GET round-trip from the dev log.
    response.headers["Cache-Control"] = "private, max-age=5"
    return CameraListResponse(items=[_serialize(c) for c in cameras_service.all_cameras()])


@router.post(
    "",
    response_model=CameraOut,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_camera(payload: CameraCreate) -> CameraOut:
    cam = cameras_service.create(
        name=payload.name.strip(),
        location=payload.location.strip(),
        ip=payload.ip.strip(),
        port=payload.port,
        username=payload.username.strip(),
        password=payload.password,
        rtsp_path=(payload.rtsp_path.strip() or "/Streaming/Channels/101"),
        enable_face_ingest=payload.enable_face_ingest,
        auto_discovery_enabled=payload.auto_discovery_enabled,
        type=payload.type,
    )
    # Run an immediate connection check so the new row carries a real status
    # rather than 'unknown'.
    ok, msg, _ = cameras_service.check_connection(
        ip=cam.ip,
        port=cam.port,
        username=cam.username,
        password=payload.password,
        rtsp_path=cam.rtsp_path,
    )
    cameras_service.update_status(
        cam.id, status="connected" if ok else "failed", message=msg
    )
    _refresh_workers()
    refreshed = cameras_service.get_by_id(cam.id)
    assert refreshed is not None
    return _serialize(refreshed)


@router.get(
    "/health",
    response_model=CameraHealthListResponse,
    dependencies=[Depends(require_admin)],
)
def cameras_health() -> CameraHealthListResponse:
    """Live per-camera worker state.

    Combines every row in the ``cameras`` table with the
    recognition-worker manager's in-memory status. Cameras that have no
    worker spawned (live-only, disconnected, or face-ingest disabled)
    still appear with ``is_running=False`` and ``None`` frame-age — so
    the frontend can lay out the same grid as the cameras list.
    """
    import time
    from ..services.recognition_worker import get_worker_manager

    statuses = {s.camera_id: s for s in get_worker_manager().status_all()}
    now = time.monotonic()
    items: list[CameraHealth] = []
    for cam in cameras_service.all_cameras():
        st = statuses.get(cam.id)
        if st is not None:
            last_frame_age = (
                round(now - st.last_frame_at, 2)
                if st.last_frame_at is not None else None
            )
            last_match_age = (
                round(now - st.last_match_at, 2)
                if st.last_match_at is not None else None
            )
            items.append(CameraHealth(
                id=cam.id, name=cam.name,
                is_running=bool(st.running),
                last_frame_age_seconds=last_frame_age,
                last_match_age_seconds=last_match_age,
                processed_frames=int(st.frames_read),
                faces_detected=int(st.faces_detected),
                matches_recorded=int(st.matches_recorded),
                last_error=st.last_error,
                backoff_seconds=float(st.backoff_seconds),
                enable_face_ingest=cam.enable_face_ingest,
                connection_status=cam.connection_status,
            ))
        else:
            items.append(CameraHealth(
                id=cam.id, name=cam.name,
                is_running=False,
                last_frame_age_seconds=None,
                last_match_age_seconds=None,
                processed_frames=0,
                faces_detected=0,
                matches_recorded=0,
                last_error=None,
                backoff_seconds=0.0,
                enable_face_ingest=cam.enable_face_ingest,
                connection_status=cam.connection_status,
            ))
    return CameraHealthListResponse(items=items)


@router.post(
    "/smart-probe",
    response_model=CameraSmartProbeResponse,
    dependencies=[Depends(require_admin)],
)
def smart_probe(payload: CameraSmartProbeRequest) -> CameraSmartProbeResponse:
    """Multi-template RTSP probe for a single host + credentials.

    Returns the first templated path that returned a frame, plus the
    full audit trail (each attempt's URL, elapsed time, and reason on
    failure). No row is written — the operator persists the winning
    ``rtsp_path`` via the normal create/update endpoints.
    """
    result = cameras_service.smart_probe(
        brand=payload.brand,
        ip=payload.ip.strip(),
        port=payload.port,
        username=payload.username.strip(),
        password=payload.password,
        per_attempt_timeout_s=payload.per_attempt_timeout_s,
    )
    return CameraSmartProbeResponse(
        ok=result.ok,
        brand=payload.brand,
        success_template_index=result.success_template_index,
        success_rtsp_path=result.success_rtsp_path,
        width=result.width,
        height=result.height,
        elapsed_ms=result.elapsed_ms,
        attempts=[
            CameraSmartProbeAttempt(
                template_index=a.template_index,
                rtsp_path=a.rtsp_path,
                rtsp_url_masked=a.rtsp_url_masked,
                ok=a.ok,
                elapsed_ms=a.elapsed_ms,
                width=a.width,
                height=a.height,
                error=a.error,
            )
            for a in result.attempts
        ],
        error=result.error,
    )


@router.post(
    "/check",
    response_model=CameraCheckResponse,
    dependencies=[Depends(require_admin)],
)
def check_pre_save(payload: CameraCheckRequest) -> CameraCheckResponse:
    """Connection check against form values before saving — no DB row written."""
    ok, msg, latency = cameras_service.check_connection(
        ip=payload.ip.strip(),
        port=payload.port,
        username=payload.username.strip(),
        password=payload.password,
        rtsp_path=payload.rtsp_path.strip(),
    )
    return CameraCheckResponse(ok=ok, message=msg, latency_ms=latency)


@router.get(
    "/{camera_id}",
    response_model=CameraOut,
    dependencies=[Depends(require_admin)],
)
def get_camera(camera_id: str) -> CameraOut:
    cam = cameras_service.get_by_id(camera_id)
    if cam is None:
        raise HTTPException(status_code=404, detail=f"camera not found: {camera_id}")
    return _serialize(cam)


@router.put(
    "/{camera_id}",
    response_model=CameraOut,
    dependencies=[Depends(require_admin)],
)
def update_camera(camera_id: str, payload: CameraUpdate) -> CameraOut:
    cam = cameras_service.update(
        camera_id,
        name=payload.name.strip() if payload.name else None,
        location=payload.location.strip() if payload.location is not None else None,
        ip=payload.ip.strip() if payload.ip else None,
        port=payload.port,
        username=payload.username.strip() if payload.username else None,
        password=payload.password if payload.password else None,
        rtsp_path=payload.rtsp_path.strip() if payload.rtsp_path else None,
        enable_face_ingest=payload.enable_face_ingest,
        auto_discovery_enabled=payload.auto_discovery_enabled,
        type=payload.type,
    )
    if cam is None:
        raise HTTPException(status_code=404, detail=f"camera not found: {camera_id}")
    _refresh_workers()
    return _serialize(cam)


@router.delete("/{camera_id}", dependencies=[Depends(require_admin)])
def delete_camera(camera_id: str) -> dict:
    if not cameras_service.delete(camera_id):
        raise HTTPException(status_code=404, detail=f"camera not found: {camera_id}")
    _refresh_workers()
    return {"status": "deleted", "id": camera_id}


@router.post(
    "/{camera_id}/check",
    response_model=CameraCheckResponse,
    dependencies=[Depends(require_admin)],
)
def check_existing(camera_id: str) -> CameraCheckResponse:
    cam = cameras_service.get_by_id(camera_id)
    if cam is None:
        raise HTTPException(status_code=404, detail=f"camera not found: {camera_id}")
    ok, msg, latency = cameras_service.check_connection(
        ip=cam.ip,
        port=cam.port,
        username=cam.username,
        password=crypto.decrypt(cam.password_encrypted),
        rtsp_path=cam.rtsp_path,
    )
    cameras_service.update_status(
        camera_id, status="connected" if ok else "failed", message=msg
    )
    _refresh_workers()
    return CameraCheckResponse(ok=ok, message=msg, latency_ms=latency)


@router.post(
    "/{camera_id}/rediscover",
    response_model=CameraRediscoverResponse,
    dependencies=[Depends(require_admin)],
)
def rediscover(camera_id: str) -> CameraRediscoverResponse:
    """Manually trigger an auto-discovery sweep for one camera.

    Only enabled when the row has ``auto_discovery_enabled=True``. Scans
    the camera's current /24 subnet, validates candidates via Uniview
    ``/API/Web/Login`` against the saved credentials, and on success
    persists the new IP (recording ``last_known_ip``/``last_discovered_at``).
    Workers running against the camera will pick up the new IP on their
    next iteration; the in-memory ``CameraClient._base_url`` is also
    refreshed transparently when ``_rediscover()`` runs there.
    """
    cam = cameras_service.get_by_id(camera_id)
    if cam is None:
        raise HTTPException(status_code=404, detail=f"camera not found: {camera_id}")
    if not cam.auto_discovery_enabled:
        raise HTTPException(
            status_code=409,
            detail="auto_discovery_enabled=False; toggle it on before rediscovering",
        )

    # Late import: discovery is a heavy module (ThreadPoolExecutor, ARP
    # parsing) and we only need it on this code path.
    from ..services.camera_discovery import discover_camera

    parts = cam.ip.split(".")
    if len(parts) != 4 or not all(p.isdigit() for p in parts):
        raise HTTPException(
            status_code=400,
            detail=f"camera ip {cam.ip!r} is not an IPv4 address; cannot derive subnet",
        )
    prefix = ".".join(parts[:3])
    password = crypto.decrypt(cam.password_encrypted)
    new_ip = discover_camera(
        user=cam.username,
        password=password,
        expected_mac=None,
        subnet_prefixes=(prefix,),
    )
    if not new_ip:
        return CameraRediscoverResponse(
            ok=False,
            message=f"No Uniview camera on {prefix}.0/24 accepted the saved credentials",
            previous_ip=cam.ip,
            new_ip=None,
        )
    if new_ip == cam.ip:
        # Stamp last_discovered_at so the UI shows a fresh probe even
        # when the IP didn't change — useful liveness signal.
        cameras_service.record_rediscovery(camera_id, new_ip=new_ip)
        return CameraRediscoverResponse(
            ok=True,
            message="Camera still reachable at the saved IP",
            previous_ip=cam.ip,
            new_ip=new_ip,
        )
    cameras_service.record_rediscovery(camera_id, new_ip=new_ip)
    log.info(
        "camera %s (%s) rediscovered: %s -> %s", camera_id, cam.name, cam.ip, new_ip,
    )
    _refresh_workers()
    return CameraRediscoverResponse(
        ok=True,
        message=f"IP updated: {cam.ip} -> {new_ip}",
        previous_ip=cam.ip,
        new_ip=new_ip,
    )


@router.post(
    "/{camera_id}/stream-token",
    response_model=StreamTokenResponse,
    dependencies=[Depends(require_admin)],
)
def stream_token(camera_id: str) -> StreamTokenResponse:
    """Issue a short-lived token for embedding in <img src> for the MJPEG
    stream. Scoped to camera_id and 5-minute TTL so leakage is bounded."""
    cam = cameras_service.get_by_id(camera_id)
    if cam is None:
        raise HTTPException(status_code=404, detail=f"camera not found: {camera_id}")
    now = int(time.time())
    payload = {
        "scope": STREAM_TOKEN_SCOPE,
        "cam": camera_id,
        "iat": now,
        "exp": now + STREAM_TOKEN_TTL_SECONDS,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return StreamTokenResponse(token=token, expires_in=STREAM_TOKEN_TTL_SECONDS)


@router.get("/{camera_id}/stream")
def stream(camera_id: str, token: str = Query(...)) -> StreamingResponse:
    """MJPEG proxy. Auth via short-lived ``?token=`` because <img> tags
    can't set Authorization headers. The actual RTSP credentials are
    decrypted server-side and never leave this process."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Stream token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid stream token")
    if payload.get("scope") != STREAM_TOKEN_SCOPE or payload.get("cam") != camera_id:
        raise HTTPException(status_code=403, detail="Token not scoped to this camera")

    cam = cameras_service.get_by_id(camera_id)
    if cam is None:
        raise HTTPException(status_code=404, detail=f"camera not found: {camera_id}")

    rtsp_url = cameras_service.build_rtsp_url_for_camera(cam)
    # Passing ``camera_id`` lets the streamer serve the recognition
    # worker's pre-annotated frames (with face boxes + names) instead of
    # opening a second RTSP read. Falls back to direct RTSP when the
    # worker isn't running for this camera.
    return StreamingResponse(
        cameras_service.mjpeg_stream(rtsp_url, camera_id=camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# ---------------------------------------------------------------------------
# Live detection JSON
# ---------------------------------------------------------------------------


class LiveDetection(BaseModel):
    bbox: list[int]
    name: str
    employee_id: str | None
    score: float
    matched: bool


class LiveDetectionsResponse(BaseModel):
    detections: list[LiveDetection]
    captured_at: float | None  # monotonic seconds (relative); None if no pass yet
    age_seconds: float | None  # how long ago the inference pass ran


@router.get(
    "/{camera_id}/detections",
    response_model=LiveDetectionsResponse,
    dependencies=[Depends(require_admin)],
)
def live_detections(camera_id: str) -> LiveDetectionsResponse:
    """Structured detections from the most recent inference pass for this
    camera. Reads from the worker's in-memory state — no DB hit, no RTSP
    open. Used by the React Live View to show ``Alice · 74%`` rows next
    to the MJPEG tile.

    Returns an empty list when the worker isn't running yet or hasn't
    completed its first inference. ``captured_at`` is ``time.monotonic()``
    on the server (relative, not wall-clock) so clients can detect
    staleness via ``age_seconds``.
    """
    cam = cameras_service.get_by_id(camera_id)
    if cam is None:
        raise HTTPException(status_code=404, detail=f"camera not found: {camera_id}")
    try:
        from ..services.recognition_worker import get_worker_manager
        worker = get_worker_manager().get_worker(camera_id)
    except Exception:
        log.exception("live_detections: worker lookup failed")
        worker = None
    if worker is None:
        return LiveDetectionsResponse(detections=[], captured_at=None, age_seconds=None)
    detections, captured_at = worker.latest_detections()
    age = (time.monotonic() - captured_at) if captured_at is not None else None
    return LiveDetectionsResponse(
        detections=[LiveDetection(**d) for d in detections],
        captured_at=captured_at,
        age_seconds=age,
    )
