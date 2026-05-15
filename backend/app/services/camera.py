"""
Camera HTTP client.

Thin wrapper around `requests` that handles the Login → X-csrftoken →
`/API/AI/processAlarm/Get` (live) and `/API/AI/SnapedFaces/Search` +
`GetByIndex` (historical backfill) flows.

Each ``CameraClient`` instance is scoped to one camera. Construct with no
args to use the legacy ``CAMERA_*`` env config (which also enables ARP
rediscovery if the camera's DHCP lease rotates), or pass ``host``,
``user``, ``password`` explicitly to bind to a specific camera from the
``cameras`` table — multi-camera capture spawns one client per row.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import requests
from requests.auth import HTTPDigestAuth

from ..config import (
    CAMERA_BASE_URL,
    CAMERA_DISCOVERY_SUBNETS,
    CAMERA_MAC,
    CAMERA_PASS,
    CAMERA_USER,
    REQUEST_TIMEOUT_SECONDS,
)
from .camera_discovery import discover_camera

log = logging.getLogger(__name__)


class CameraClient:
    """Keeps a logged-in session; transparently re-logs in when the camera 401s.

    The base URL lives on the instance so the legacy env-driven client can
    swap in a freshly-discovered IP if the camera's DHCP lease rotates
    (see ``_rediscover``). DB-backed cameras have a stable IP edited via
    the admin UI, so they skip rediscovery.
    """

    def __init__(
        self,
        *,
        host: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        camera_id: str = "",
        camera_name: str = "",
        camera_location: str = "",
        auto_discovery_enabled: bool = False,
    ) -> None:
        # ``host=None`` means "use the legacy env config" — preserves the
        # previous single-camera behavior for the env-fallback code path.
        self._session: Optional[requests.Session] = None
        if host:
            self._base_url = f"http://{host}"
            self._user = user or CAMERA_USER
            self._password = password if password is not None else CAMERA_PASS
            # DB cameras opt in explicitly per-row. When the row carries
            # auto_discovery_enabled=True we sweep the SAME /24 the camera
            # currently lives on and persist any successful match back to
            # the DB. Default False keeps static-IP DB cameras strictly
            # fixed (matches the column default).
            self._enable_rediscovery = bool(auto_discovery_enabled)
            self._persist_rediscovery = bool(auto_discovery_enabled and camera_id)
        else:
            self._base_url = CAMERA_BASE_URL
            self._user = CAMERA_USER
            self._password = CAMERA_PASS
            # Legacy env-driven client uses the .env-pinned MAC + subnet
            # list and does NOT persist anywhere — there's no DB row to
            # update.
            self._enable_rediscovery = True
            self._persist_rediscovery = False
        # Identity tags, only used to enrich log messages and ingest payloads.
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.camera_location = camera_location

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def label(self) -> str:
        """Short human label for log lines: name when known, falling back to host."""
        return self.camera_name or self._base_url

    def _login(self) -> requests.Session:
        log.info("[%s] Logging into camera at %s", self.label, self._base_url)
        session = requests.Session()
        try:
            resp = session.post(
                f"{self._base_url}/API/Web/Login",
                json={"data": {}},
                auth=HTTPDigestAuth(self._user, self._password),
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.ReadTimeout:
            log.warning(
                "[%s] Camera login timed out after %.1fs at %s",
                self.label, REQUEST_TIMEOUT_SECONDS, self._base_url,
            )
            self._rediscover()
            raise
        except (requests.ConnectTimeout, requests.ConnectionError):
            # Connect-level failure is the classic "DHCP rotated the IP"
            # signal: we can't even reach the host. Rediscovery is only
            # meaningful for the legacy env client (which has the MAC pin
            # configured); DB cameras skip it.
            log.warning("[%s] Camera login could not connect to %s", self.label, self._base_url)
            self._rediscover()
            raise
        except requests.RequestException:
            log.warning("[%s] Camera login request failed at %s", self.label, self._base_url)
            raise
        if resp.status_code != 200:
            raise RuntimeError(f"[{self.label}] Login failed: {resp.status_code} {resp.text[:200]}")
        token = resp.headers.get("X-csrftoken")
        if not token:
            raise RuntimeError(f"[{self.label}] Login response missing X-csrftoken header")
        session.headers.update({"X-csrftoken": token, "Content-Type": "application/json"})
        log.info("[%s] Camera login succeeded; X-csrftoken received", self.label)
        return session

    def _current_subnet_prefix(self) -> Optional[str]:
        """Derive ``a.b.c`` from ``http://a.b.c.d`` for DB-camera rediscovery.

        DB cameras don't get to sweep the global CAMERA_DISCOVERY_SUBNETS
        list — they're constrained to the /24 they're currently on. Returns
        None if the current URL doesn't look like a numeric IPv4 host
        (e.g. someone configured a DNS name)."""
        host = self._base_url.replace("http://", "", 1).split(":", 1)[0]
        parts = host.split(".")
        if len(parts) != 4 or not all(p.isdigit() for p in parts):
            return None
        return ".".join(parts[:3])

    def _rediscover(self) -> None:
        """Look up the camera's current IP via ARP, validate it with the
        Uniview login probe, and (for DB-backed cameras) persist the new IP
        atomically. No-op when rediscovery is disabled for this client or
        when discovery turns up nothing."""
        if not self._enable_rediscovery:
            return

        # DB-camera path: scan only the camera's own /24, no MAC pin
        # (saved username/password identifies it via the Uniview API).
        # Legacy env path: use the global pinned-MAC + multi-subnet config.
        if self._persist_rediscovery:
            prefix = self._current_subnet_prefix()
            if prefix is None:
                log.warning(
                    "[%s] auto-discovery: current host %r is not an IPv4 "
                    "address; cannot derive subnet to scan", self.label, self._base_url,
                )
                return
            subnets: tuple[str, ...] = (prefix,)
            mac_pin: Optional[str] = None
        else:
            subnets = CAMERA_DISCOVERY_SUBNETS
            mac_pin = CAMERA_MAC or None

        new_ip = discover_camera(
            user=self._user,
            password=self._password,
            expected_mac=mac_pin,
            subnet_prefixes=subnets,
        )
        if not new_ip:
            return
        candidate = f"http://{new_ip}"
        if candidate == self._base_url:
            return
        log.info(
            "[%s] Camera rediscovered: %s -> %s (subnets=%s pin=%s)",
            self.label, self._base_url, candidate, subnets,
            mac_pin or "(none — login probe)",
        )
        self._base_url = candidate

        # Persist the IP change so the live-view router, the API, and the
        # next worker spawn all agree with the running worker. Late import
        # to avoid a service-layer cycle at module load.
        if self._persist_rediscovery:
            try:
                from . import cameras as cameras_service  # late import: avoid cycle
                cameras_service.record_rediscovery(self.camera_id, new_ip=new_ip)
                log.info(
                    "[%s] auto-discovery: persisted new IP %s to DB (camera_id=%s)",
                    self.label, new_ip, self.camera_id,
                )
            except Exception:
                # Worker keeps running with the in-memory ip even if the
                # DB write fails; we just won't survive a process restart.
                log.exception(
                    "[%s] auto-discovery: failed to persist new IP %s to DB",
                    self.label, new_ip,
                )

    def _ensure_session(self) -> requests.Session:
        if self._session is None:
            self._session = self._login()
        return self._session

    def invalidate(self) -> None:
        self._session = None

    def fetch_alarms(self) -> list[dict]:
        """
        Return the current `data.FaceInfo[]` list.

        Some firmware builds appear to hold `processAlarm/Get` open briefly when
        there are no live events to return. In that case a read timeout should be
        treated as an empty poll, not as a dead session that forces a re-login.
        """
        session = self._ensure_session()
        try:
            resp = session.post(
                f"{self._base_url}/API/AI/processAlarm/Get",
                json={},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.ReadTimeout:
            log.info(
                "processAlarm/Get timed out after %.1fs; treating as no live events",
                REQUEST_TIMEOUT_SECONDS,
            )
            return []
        if resp.status_code >= 400:
            log.warning(
                "processAlarm/Get %s rejected — response=%s",
                resp.status_code,
                resp.text[:500],
            )
        resp.raise_for_status()
        data = resp.json().get("data", {}) or {}
        faces = data.get("FaceInfo")
        if isinstance(faces, list):
            log.info("processAlarm/Get succeeded; FaceInfo count=%d", len(faces))
        return faces if isinstance(faces, list) else []

    def search_history(
        self,
        start_local: datetime,
        end_local: datetime,
        similarity: int = 70,
    ) -> int:
        """Initiate a SnapedFaces search over the given local-time window.

        The camera uses this call to seed an internal cursor; actual rows are
        fetched via ``get_snaped_by_index``. Returns the total match count.
        """
        session = self._ensure_session()
        payload = {
            "msgType": "AI_searchSnapedFaces",
            "data": {
                "MsgId": None,
                "StartTime": start_local.strftime("%Y-%m-%d %H:%M:%S"),
                "EndTime": end_local.strftime("%Y-%m-%d %H:%M:%S"),
                "Similarity": similarity,
                "Engine": 0,
            },
        }
        resp = session.post(
            f"{self._base_url}/API/AI/SnapedFaces/Search",
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {}) or {}
        total = int(data.get("Count") or 0)
        log.info(
            "SnapedFaces/Search %s→%s total=%d",
            payload["data"]["StartTime"],
            payload["data"]["EndTime"],
            total,
        )
        return total

    def get_snaped_by_index(
        self,
        start_index: int,
        count: int,
        *,
        with_face_image: bool = True,
        matched_only: bool = True,
    ) -> list[dict]:
        """Page through the current SnapedFaces cursor. Call after search_history."""
        session = self._ensure_session()
        payload = {
            "data": {
                "MsgId": None,
                "Engine": 0,
                "MatchedFaces": 1 if matched_only else 0,
                "StartIndex": start_index,
                "Count": count,
                "SimpleInfo": 0,
                "WithFaceImage": 1 if with_face_image else 0,
                "WithBodyImage": 0,
                "WithBackgroud": 0,
                "WithFeature": 0,
            }
        }
        resp = session.post(
            f"{self._base_url}/API/AI/SnapedFaces/GetByIndex",
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {}) or {}
        rows = data.get("SnapedFaceInfo")
        return rows if isinstance(rows, list) else []
