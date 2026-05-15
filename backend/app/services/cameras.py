"""Cameras CRUD + RTSP connection check + MJPEG stream proxy generator.

Storage: ``cameras`` table (PostgreSQL in prod, SQLite locally), with
passwords symmetrically encrypted at rest (services.crypto). Plaintext
passwords never leave this process — the API surfaces only a masked
RTSP URL preview, and the live stream proxy decrypts internally to open
the camera connection.
"""

from __future__ import annotations

import logging
import os
import socket
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote

# Force RTSP-over-TCP for any cv2.VideoCapture opened from this module.
# OpenCV's FFmpeg backend defaults to UDP transport, which on a typical
# LAN drops enough packets that the camera either silently refuses the
# session or returns a stream we can't decode — symptom: VideoCapture
# closes within ~200 ms with no frame. This mirrors the same setdefault
# in ``recognition_worker.py``; setting it at module-import time means
# the smart-probe endpoint doesn't depend on the worker being imported
# first. ``stimeout`` is FFmpeg's socket timeout in microseconds (5 s).
os.environ.setdefault(
    "OPENCV_FFMPEG_CAPTURE_OPTIONS",
    "rtsp_transport;tcp|stimeout;5000000",
)

from sqlalchemy import func, select

from ..db import session_scope
from ..models import Camera as CameraModel
from . import crypto

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Camera:
    id: str
    name: str
    location: str
    ip: str
    port: int
    username: str
    password_encrypted: str
    rtsp_path: str
    connection_status: str
    enable_face_ingest: bool
    auto_discovery_enabled: bool
    type: str  # "ENTRY" or "EXIT"
    last_known_ip: Optional[str]
    last_discovered_at: Optional[str]
    last_checked_at: Optional[str]
    last_check_message: Optional[str]
    created_at: str
    updated_at: str


def _iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _model_to_camera(row: CameraModel) -> Camera:
    return Camera(
        id=str(row.id),
        name=str(row.name),
        location=str(row.location or ""),
        ip=str(row.ip),
        port=int(row.port),
        username=str(row.username or ""),
        password_encrypted=str(row.password_encrypted or ""),
        rtsp_path=str(row.rtsp_path or ""),
        connection_status=str(row.connection_status or "unknown"),
        enable_face_ingest=bool(row.enable_face_ingest),
        auto_discovery_enabled=bool(row.auto_discovery_enabled),
        type=str(getattr(row, "type", None) or "ENTRY"),
        last_known_ip=row.last_known_ip,
        last_discovered_at=_iso(row.last_discovered_at),
        last_checked_at=_iso(row.last_checked_at),
        last_check_message=row.last_check_message,
        created_at=_iso(row.created_at) or "",
        updated_at=_iso(row.updated_at) or "",
    )


# ---- CRUD ------------------------------------------------------------------

def all_cameras() -> list[Camera]:
    with session_scope() as session:
        rows = session.execute(
            select(CameraModel).order_by(func.lower(CameraModel.name))
        ).scalars().all()
        return [_model_to_camera(r) for r in rows]


def connected_cameras_with_credentials() -> list[tuple[Camera, str]]:
    """Return ``(Camera, decrypted_password)`` pairs for every camera with
    ``connection_status='connected'`` AND ``enable_face_ingest=True``.

    Live-only cameras (enable_face_ingest=False) are excluded because
    capture.py speaks Uniview's HTTP face-detection API, which 404s on
    other brands. Those rows still show up in the cameras list / live
    view — they just don't get a capture worker spawned. Passwords that
    fail to decrypt (e.g. CAMERA_SECRET_KEY rotated) are skipped with a
    logged error so capture can keep running on the rest.
    """
    pairs: list[tuple[Camera, str]] = []
    for cam in all_cameras():
        if cam.connection_status != "connected":
            continue
        if not cam.enable_face_ingest:
            log.info(
                "Skipping camera %r (id=%s): live-only (enable_face_ingest=False)",
                cam.name, cam.id,
            )
            continue
        try:
            password = crypto.decrypt(cam.password_encrypted)
        except Exception as exc:
            log.error(
                "Skipping camera %r (id=%s): password decrypt failed (%s)",
                cam.name, cam.id, exc,
            )
            continue
        pairs.append((cam, password))
    return pairs


def get_by_id(camera_id: str) -> Optional[Camera]:
    with session_scope() as session:
        row = session.get(CameraModel, camera_id)
        return _model_to_camera(row) if row else None


def create(
    *,
    name: str,
    location: str,
    ip: str,
    port: int,
    username: str,
    password: str,
    rtsp_path: str,
    enable_face_ingest: Optional[bool] = None,
    auto_discovery_enabled: Optional[bool] = None,
    type: Optional[str] = None,
) -> Camera:
    """Create a new camera row.

    ``enable_face_ingest`` and ``auto_discovery_enabled`` are None when
    the caller wants the model defaults (True / False respectively). The
    frontend's Add Camera dialog sends explicit values so the user's
    toggles in the form are honored at create-time.

    ``type`` is ``ENTRY`` or ``EXIT``; defaults to ``ENTRY`` so existing
    callers keep working unchanged.
    """
    new_id = f"cam-{uuid.uuid4().hex[:10]}"
    pw_enc = crypto.encrypt(password)
    extra: dict = {}
    if enable_face_ingest is not None:
        extra["enable_face_ingest"] = enable_face_ingest
    if auto_discovery_enabled is not None:
        extra["auto_discovery_enabled"] = auto_discovery_enabled
    if type is not None:
        if type not in ("ENTRY", "EXIT"):
            raise ValueError(f"invalid camera type: {type!r}")
        extra["type"] = type
    with session_scope() as session:
        session.add(
            CameraModel(
                id=new_id,
                name=name,
                location=location,
                ip=ip,
                port=port,
                username=username,
                password_encrypted=pw_enc,
                rtsp_path=rtsp_path,
                connection_status="unknown",
                **extra,
            )
        )
        session.flush()
        row = session.get(CameraModel, new_id)
        assert row is not None
        cam = _model_to_camera(row)
        log.info(
            "camera created id=%s name=%r type=%s rtsp=%s face_ingest=%s",
            cam.id, cam.name, cam.type, masked_rtsp_url(cam), cam.enable_face_ingest,
        )
        return cam


def update(
    camera_id: str,
    *,
    name: Optional[str] = None,
    location: Optional[str] = None,
    ip: Optional[str] = None,
    port: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    rtsp_path: Optional[str] = None,
    enable_face_ingest: Optional[bool] = None,
    auto_discovery_enabled: Optional[bool] = None,
    type: Optional[str] = None,
) -> Optional[Camera]:
    with session_scope() as session:
        row = session.get(CameraModel, camera_id)
        if row is None:
            return None
        if name is not None:
            row.name = name
        if location is not None:
            row.location = location
        if ip is not None:
            row.ip = ip
        if port is not None:
            row.port = port
        if username is not None:
            row.username = username
        # Empty/None password = leave existing one untouched (so the operator
        # can edit the form without re-entering the password every time).
        if password is not None and password != "":
            row.password_encrypted = crypto.encrypt(password)
        if rtsp_path is not None:
            row.rtsp_path = rtsp_path
        if enable_face_ingest is not None:
            row.enable_face_ingest = enable_face_ingest
        if auto_discovery_enabled is not None:
            row.auto_discovery_enabled = auto_discovery_enabled
        if type is not None:
            if type not in ("ENTRY", "EXIT"):
                raise ValueError(f"invalid camera type: {type!r}")
            row.type = type
        # ``onupdate`` on the model bumps updated_at automatically.
        session.flush()
        cam = _model_to_camera(row)
        log.info(
            "camera updated id=%s name=%r type=%s rtsp=%s",
            cam.id, cam.name, cam.type, masked_rtsp_url(cam),
        )
        return cam


def record_rediscovery(camera_id: str, *, new_ip: str) -> Optional[Camera]:
    """Persist a successful auto-rediscovery transition for a single camera.

    Atomically: stores the prior ``ip`` as ``last_known_ip``, swaps in the
    newly-discovered ``new_ip``, and stamps ``last_discovered_at`` to now.
    Returns the refreshed Camera, or None if the row vanished mid-call.
    Caller is responsible for ensuring ``new_ip`` was already validated
    against the camera (Uniview login probe) — this function trusts its
    input and never re-validates.
    """
    now = datetime.now(timezone.utc)
    with session_scope() as session:
        row = session.get(CameraModel, camera_id)
        if row is None:
            return None
        if row.ip != new_ip:
            row.last_known_ip = row.ip
            row.ip = new_ip
        row.last_discovered_at = now
        # Bumping connection_status here would race the worker's own
        # subsequent login probe — leave that to update_status() so we
        # don't paper over a failed post-rediscovery validation.
        session.flush()
        return _model_to_camera(row)


def delete(camera_id: str) -> bool:
    with session_scope() as session:
        row = session.get(CameraModel, camera_id)
        if row is None:
            return False
        name = row.name
        session.delete(row)
        log.info("camera deleted id=%s name=%r", camera_id, name)
        return True


def update_status(camera_id: str, *, status: str, message: str) -> None:
    now = datetime.now(timezone.utc)
    with session_scope() as session:
        row = session.get(CameraModel, camera_id)
        if row is None:
            return
        row.connection_status = status
        row.last_checked_at = now
        row.last_check_message = message
        log.info(
            "camera status id=%s name=%r status=%s msg=%s",
            camera_id, row.name, status, message,
        )


# ---- RTSP URL helpers ------------------------------------------------------

def build_rtsp_url(
    *,
    ip: str,
    port: int,
    username: str,
    password: str,
    rtsp_path: str,
) -> str:
    """Full credentialed RTSP URL — used internally to open the stream.
    URL-encodes credentials so symbols like '@' and ':' don't break parsing."""
    path = rtsp_path if rtsp_path.startswith("/") else f"/{rtsp_path}"
    if username:
        creds = f"{quote(username, safe='')}:{quote(password, safe='')}@"
    else:
        creds = ""
    return f"rtsp://{creds}{ip}:{port}{path}"


def build_rtsp_url_for_camera(cam: Camera) -> str:
    return build_rtsp_url(
        ip=cam.ip,
        port=cam.port,
        username=cam.username,
        password=crypto.decrypt(cam.password_encrypted),
        rtsp_path=cam.rtsp_path,
    )


def masked_rtsp_url(cam: Camera) -> str:
    """Credential-less preview, safe to return to the frontend."""
    path = cam.rtsp_path if cam.rtsp_path.startswith("/") else f"/{cam.rtsp_path}"
    if cam.username:
        return f"rtsp://{cam.username}:****@{cam.ip}:{cam.port}{path}"
    return f"rtsp://{cam.ip}:{cam.port}{path}"


# ---- Connection check ------------------------------------------------------

def _tcp_reachable(host: str, port: int, timeout_s: float = 3.0) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True, "TCP reachable"
    except socket.gaierror:
        return False, "Could not resolve hostname — check the IP"
    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        return False, f"Camera unreachable: {exc.__class__.__name__}"


def check_connection(
    *,
    ip: str,
    port: int,
    username: str,
    password: str,
    rtsp_path: str,
    timeout_s: float = 8.0,
) -> tuple[bool, str, int]:
    """Open the RTSP stream, read one frame, return (ok, message, latency_ms).

    Bounded by ``timeout_s`` since cv2.VideoCapture can hang for ~60s on a
    bad URL. The probe runs in a daemon thread; if it overshoots the timeout
    we abandon it (the OpenCV capture releases when its local ref is GC'd).
    """
    started = time.monotonic()

    # Cheap reachability gate — avoids the heavier RTSP probe when the host
    # isn't even responding on the RTSP port.
    ok, msg = _tcp_reachable(ip, port, timeout_s=3.0)
    if not ok:
        return False, msg, int((time.monotonic() - started) * 1000)

    rtsp_url = build_rtsp_url(
        ip=ip, port=port, username=username, password=password, rtsp_path=rtsp_path
    )
    result: dict = {"ok": False, "msg": "Connection timed out"}

    def _attempt() -> None:
        try:
            import cv2
        except Exception as exc:
            result["msg"] = f"OpenCV unavailable: {exc}"
            return
        cap = None
        try:
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                result["msg"] = "Could not open RTSP stream — check IP, port, and path"
                return
            ret, _frame = cap.read()
            if ret:
                result["ok"] = True
                result["msg"] = "Connected"
            else:
                result["msg"] = "Stream opened but no frame received — check credentials"
        except Exception as exc:
            result["msg"] = f"Connection error: {exc}"
        finally:
            if cap is not None:
                cap.release()

    masked_url = _masked_rtsp_url(ip=ip, port=port, username=username, rtsp_path=rtsp_path)
    log.info("test_connection: probing %s", masked_url)
    t = threading.Thread(target=_attempt, daemon=True, name=f"rtsp-check-{ip}")
    t.start()
    t.join(timeout=timeout_s)
    latency_ms = int((time.monotonic() - started) * 1000)
    if t.is_alive():
        log.warning("test_connection: timeout after %dms on %s", latency_ms, masked_url)
        return False, "Connection timed out", latency_ms
    ok = bool(result["ok"])
    msg = str(result["msg"])
    log.info(
        "test_connection: result ok=%s latency=%dms msg=%s url=%s",
        ok, latency_ms, msg, masked_url,
    )
    return ok, msg, latency_ms


# ---- Smart probe (multi-template) -----------------------------------------

# Per-brand RTSP path candidates, tried in order. The first template that
# returns a frame wins. Each list is curated for the common firmware
# variants we've seen in the field; ``generic`` doubles as a fallback for
# unknown brands when the operator misidentifies the camera. Sub-streams
# (lower resolution) are tried after main streams because some cameras
# refuse main-stream concurrent reads but happily serve the sub-stream.
SMART_PROBE_TEMPLATES: dict[str, list[str]] = {
    "hikvision": [
        "/Streaming/Channels/101",
        "/Streaming/Channels/102",
        "/Streaming/Channels/1",
        "/h264_stream",
        "/h264",
        "/ch1/main/av_stream",
    ],
    # CP Plus ships at least three firmware families: Dahua-derived
    # (/cam/realmonitor — most common), Hikvision-derived (/Streaming/...),
    # and a third group using /live or /stream paths on older models.
    # We probe all three because rebrands swap silently between model years.
    "cp_plus": [
        "/cam/realmonitor?channel=1&subtype=0",
        "/cam/realmonitor?channel=1&subtype=1",
        "/Streaming/Channels/101",
        "/Streaming/Channels/102",
        "/live",
        "/h264",
        "/stream1",
        "/stream2",
        "/onvif1",
    ],
    "dahua": [
        "/cam/realmonitor?channel=1&subtype=0",
        "/cam/realmonitor?channel=1&subtype=1",
        "/live",
    ],
    "axis": [
        "/axis-media/media.amp",
        "/axis-media/media.amp?streamprofile=Quality",
    ],
    "generic": [
        "/Streaming/Channels/101",
        "/cam/realmonitor?channel=1&subtype=0",
        "/cam/realmonitor?channel=1&subtype=1",
        "/axis-media/media.amp",
        "/live",
        "/stream1",
        "/h264",
        "/onvif1",
    ],
}


@dataclass(frozen=True)
class ProbeAttempt:
    template_index: int
    rtsp_path: str
    rtsp_url_masked: str
    ok: bool
    elapsed_ms: int
    width: Optional[int]
    height: Optional[int]
    error: Optional[str]


@dataclass(frozen=True)
class SmartProbeResult:
    ok: bool
    success_template_index: Optional[int]
    success_rtsp_path: Optional[str]
    width: Optional[int]
    height: Optional[int]
    elapsed_ms: int
    attempts: list[ProbeAttempt]
    error: Optional[str]


def _masked_rtsp_url(*, ip: str, port: int, username: str, rtsp_path: str) -> str:
    path = rtsp_path if rtsp_path.startswith("/") else f"/{rtsp_path}"
    creds = f"{username}:****@" if username else ""
    return f"rtsp://{creds}{ip}:{port}{path}"


def _single_probe(
    *,
    ip: str,
    port: int,
    username: str,
    password: str,
    rtsp_path: str,
    timeout_s: float,
) -> ProbeAttempt:
    """One templated attempt — runs the same check_connection probe but also
    captures frame dimensions when the read succeeds.

    Implementation mirrors :func:`check_connection` but reads frame width /
    height from the capture before releasing it. Kept separate to avoid
    threading two return shapes through the existing call sites.
    """
    started = time.monotonic()
    rtsp_url = build_rtsp_url(
        ip=ip, port=port, username=username, password=password, rtsp_path=rtsp_path,
    )
    masked = _masked_rtsp_url(ip=ip, port=port, username=username, rtsp_path=rtsp_path)
    result: dict = {
        "ok": False, "msg": "Connection timed out",
        "width": None, "height": None,
    }

    def _attempt() -> None:
        try:
            import cv2
        except Exception as exc:
            result["msg"] = f"OpenCV unavailable: {exc}"
            return
        cap = None
        try:
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                result["msg"] = "Could not open RTSP stream"
                return
            ret, frame = cap.read()
            if ret:
                result["ok"] = True
                result["msg"] = None
                if frame is not None and hasattr(frame, "shape") and len(frame.shape) >= 2:
                    result["height"] = int(frame.shape[0])
                    result["width"] = int(frame.shape[1])
            else:
                result["msg"] = "Stream opened but no frame received"
        except Exception as exc:
            result["msg"] = f"{exc.__class__.__name__}: {exc}"
        finally:
            if cap is not None:
                cap.release()

    t = threading.Thread(target=_attempt, daemon=True, name=f"rtsp-probe-{ip}")
    t.start()
    t.join(timeout=timeout_s)
    elapsed_ms = int((time.monotonic() - started) * 1000)
    if t.is_alive():
        return ProbeAttempt(
            template_index=-1, rtsp_path=rtsp_path, rtsp_url_masked=masked,
            ok=False, elapsed_ms=elapsed_ms,
            width=None, height=None,
            error="Probe timed out",
        )
    return ProbeAttempt(
        template_index=-1, rtsp_path=rtsp_path, rtsp_url_masked=masked,
        ok=bool(result["ok"]), elapsed_ms=elapsed_ms,
        width=result.get("width"), height=result.get("height"),
        error=None if result["ok"] else str(result["msg"] or "Probe failed"),
    )


def _onvif_discover_rtsp_paths(
    *,
    ip: str,
    username: str,
    password: str,
) -> tuple[list[str], Optional[str]]:
    """Ask the camera over ONVIF for its actual stream URIs.

    Returns ``(paths, error_msg)``. ``paths`` is the list of RTSP paths the
    camera advertises (one per media profile, main + sub streams typically);
    ``error_msg`` is set when discovery itself failed (ONVIF not enabled,
    auth rejected, etc.) and explains *why*. A camera that doesn't speak
    ONVIF at all (very rare in 2024+) returns ``([], <reason>)``.

    Implementation notes:
    * ``adjust_time=True`` — most cameras enforce a ±5 s WSSE timestamp
      window. We've seen real cameras drift several minutes; without this
      ONVIF auth fails with "Wsse authorized time check failed."
    * SSL verification is disabled — every camera ships a self-signed cert
      on HTTPS, and onvif-zeep auto-follows the HTTP→HTTPS redirect.
    * We probe on port 80 only; non-standard ONVIF ports (8000, 8080, etc.)
      are uncommon and not worth the timeout cost in the hot path.
    """
    try:
        from onvif import ONVIFCamera
        from zeep.transports import Transport
        import requests
        import urllib3
    except ImportError:
        return [], "onvif-zeep not installed on the backend"

    urllib3.disable_warnings()
    session = requests.Session()
    session.verify = False
    try:
        transport = Transport(session=session, timeout=6)
        cam = ONVIFCamera(
            ip, 80, username, password,
            adjust_time=True, transport=transport,
        )
        media = cam.create_media_service()
        profiles = media.GetProfiles()
        if not profiles:
            return [], "Camera exposes no ONVIF media profiles"
        paths: list[str] = []
        for prof in profiles:
            req = media.create_type("GetStreamUri")
            req.ProfileToken = prof.token
            req.StreamSetup = {
                "Stream": "RTP-Unicast",
                "Transport": {"Protocol": "RTSP"},
            }
            try:
                resp = media.GetStreamUri(req)
            except Exception:
                continue
            uri = str(getattr(resp, "Uri", "") or "")
            # Strip scheme+credentials+host so we can re-build with our own
            # creds. The ONVIF URI may be ``rtsp://host:port/path?query``
            # without auth — we want just ``/path?query``.
            if uri.lower().startswith("rtsp://"):
                rest = uri[len("rtsp://"):]
                slash = rest.find("/")
                path = rest[slash:] if slash >= 0 else "/"
                if path not in paths:
                    paths.append(path)
        return paths, None if paths else "ONVIF returned profiles but no RTSP URIs"
    except Exception as exc:
        msg = str(exc) or exc.__class__.__name__
        if "Wsse" in msg or "time check" in msg.lower():
            msg = f"ONVIF auth/time-sync failed: {msg}"
        return [], f"ONVIF: {msg[:160]}"


def smart_probe(
    *,
    brand: str,
    ip: str,
    port: int,
    username: str,
    password: str,
    per_attempt_timeout_s: float = 4.0,
) -> SmartProbeResult:
    """Try every brand-template against the host until one returns a frame.

    On exhausting the brand's template list without a hit, we fall back to
    **ONVIF discovery** — asking the camera directly for its stream URIs
    via the standard ``GetStreamUri`` RPC. This catches cameras with
    custom RTSP paths (CP-UNC series and similar OEM rebrands) that no
    static template list could cover.

    Short-circuits on first success — the audit trail only contains the
    paths that were actually attempted. Returns every attempt (templates
    + any ONVIF-discovered paths) on failure so the operator can see
    exactly which paths the camera rejected.
    """
    started = time.monotonic()
    templates = SMART_PROBE_TEMPLATES.get(brand) or SMART_PROBE_TEMPLATES["generic"]

    # TCP-reachability gate up front — every template against an unreachable
    # host would otherwise eat the full per-attempt timeout for no gain.
    tcp_ok, tcp_msg = _tcp_reachable(ip, port, timeout_s=3.0)
    if not tcp_ok:
        elapsed_ms = int((time.monotonic() - started) * 1000)
        return SmartProbeResult(
            ok=False,
            success_template_index=None, success_rtsp_path=None,
            width=None, height=None,
            elapsed_ms=elapsed_ms, attempts=[],
            error=tcp_msg,
        )

    attempts: list[ProbeAttempt] = []

    def _try_path(idx: int, rtsp_path: str) -> Optional[ProbeAttempt]:
        raw = _single_probe(
            ip=ip, port=port, username=username, password=password,
            rtsp_path=rtsp_path, timeout_s=per_attempt_timeout_s,
        )
        attempt = ProbeAttempt(
            template_index=idx,
            rtsp_path=raw.rtsp_path,
            rtsp_url_masked=raw.rtsp_url_masked,
            ok=raw.ok,
            elapsed_ms=raw.elapsed_ms,
            width=raw.width,
            height=raw.height,
            error=raw.error,
        )
        attempts.append(attempt)
        return attempt if attempt.ok else None

    # Phase 1: brand templates (fast path).
    for idx, rtsp_path in enumerate(templates):
        hit = _try_path(idx, rtsp_path)
        if hit is not None:
            elapsed_ms = int((time.monotonic() - started) * 1000)
            return SmartProbeResult(
                ok=True,
                success_template_index=idx,
                success_rtsp_path=hit.rtsp_path,
                width=hit.width, height=hit.height,
                elapsed_ms=elapsed_ms, attempts=attempts,
                error=None,
            )

    # Phase 2: ONVIF discovery fallback. Most modern IP cameras speak
    # ONVIF even when their RTSP path is custom — asking the camera for
    # its own URI is more reliable than guessing.
    log.info("smart_probe: %d templates exhausted; trying ONVIF discovery", len(templates))
    discovered, onvif_err = _onvif_discover_rtsp_paths(
        ip=ip, username=username, password=password,
    )
    next_idx = len(templates)
    for offset, rtsp_path in enumerate(discovered):
        # Skip if we already attempted this path in phase 1 — no point
        # double-probing the same URL.
        if any(a.rtsp_path == rtsp_path for a in attempts):
            continue
        hit = _try_path(next_idx + offset, rtsp_path)
        if hit is not None:
            elapsed_ms = int((time.monotonic() - started) * 1000)
            return SmartProbeResult(
                ok=True,
                success_template_index=hit.template_index,
                success_rtsp_path=hit.rtsp_path,
                width=hit.width, height=hit.height,
                elapsed_ms=elapsed_ms, attempts=attempts,
                error=None,
            )

    elapsed_ms = int((time.monotonic() - started) * 1000)
    if discovered:
        err = "ONVIF discovered paths but none returned a frame — see attempt audit for details"
    elif onvif_err:
        err = f"No template returned a frame; ONVIF fallback also failed ({onvif_err})"
    else:
        err = "No template returned a frame — see attempt audit for details"
    return SmartProbeResult(
        ok=False,
        success_template_index=None, success_rtsp_path=None,
        width=None, height=None,
        elapsed_ms=elapsed_ms, attempts=attempts,
        error=err,
    )


# ---- MJPEG generator -------------------------------------------------------

def _yield_mjpeg_chunk(chunk: bytes) -> bytes:
    """Wrap a single JPEG in the multipart-MJPEG framing the browser expects."""
    return (
        b"--frame\r\n"
        b"Content-Type: image/jpeg\r\n"
        b"Content-Length: " + str(len(chunk)).encode() + b"\r\n\r\n"
        + chunk + b"\r\n"
    )


def mjpeg_stream(
    rtsp_url: str,
    *,
    camera_id: Optional[str] = None,
    target_fps: int = 20,
    jpeg_quality: int = 70,
):
    """Yield multipart MJPEG bytes for FastAPI's StreamingResponse.

    When ``camera_id`` is set AND the recognition worker for that
    camera is publishing annotated frames into the shared
    :mod:`live_frames` buffer, this serves those frames directly — the
    operator sees bounding boxes + employee names overlaid in real
    time, with no duplicate RTSP read and no duplicate inference.

    Fallback: when no recent annotated frame is in the buffer (worker
    not running, just started, crashed, or this is a live-only camera),
    we open the RTSP socket ourselves and yield raw frames at
    ``target_fps``. The fallback is the original behavior and is
    selected per-request so existing call sites that omit
    ``camera_id`` keep working unchanged.
    """
    try:
        import cv2
    except Exception:
        log.exception("cv2 unavailable; cannot stream")
        return

    # Late import to avoid a service-layer cycle at module load.
    from . import live_frames

    # Path A: annotated frames from the recognition worker.
    if camera_id and live_frames.has_recent(camera_id):
        period = 1.0 / max(1, target_fps)
        next_at = time.monotonic()
        # We keep streaming from the cache as long as a fresh frame is
        # available. If the worker dies mid-stream the cache will go
        # stale within ``STALE_AFTER_SECONDS`` — at that point we break
        # out and the client will reconnect (or we could fall through
        # to direct RTSP, but that risks the camera vendor capping
        # concurrent RTSP sessions).
        while True:
            now = time.monotonic()
            if now < next_at:
                time.sleep(next_at - now)
            next_at = time.monotonic() + period
            frame = live_frames.get_fresh(camera_id)
            if frame is None:
                log.info(
                    "mjpeg_stream: live_frames buffer for %s went stale; closing",
                    camera_id,
                )
                return
            yield _yield_mjpeg_chunk(frame.jpeg_bytes)

    # Path B: original behavior — open our own RTSP socket.
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        log.warning("mjpeg_stream: could not open RTSP stream")
        return

    period = 1.0 / max(1, target_fps)
    next_at = time.monotonic()
    try:
        while True:
            now = time.monotonic()
            if now < next_at:
                time.sleep(next_at - now)
            next_at = time.monotonic() + period

            ret, frame = cap.read()
            if not ret:
                time.sleep(0.2)
                continue

            ok, jpeg = cv2.imencode(
                ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
            )
            if not ok:
                continue
            yield _yield_mjpeg_chunk(jpeg.tobytes())
    finally:
        cap.release()
