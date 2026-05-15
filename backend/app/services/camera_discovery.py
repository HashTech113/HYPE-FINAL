"""Locate the camera on the LAN when its DHCP-assigned IP changes.

The camera's IP rotates because it's a DHCP client; its MAC is stable.
We use the kernel's ARP table (`/proc/net/arp`) as the source of truth
and seed it via a quick parallel TCP-SYN sweep when needed.

Resolution order:
1. If ``CAMERA_MAC`` is set and present in the live ARP cache, validate
   that IP via ``POST /API/Web/Login`` and return on success.
2. Otherwise probe the candidate /24 subnets (~250 hosts × N subnets,
   parallel, ~1-2 s total). The kernel populates ARP for each host that
   replies. Re-walk the cache afterwards.
3. Filter cache entries by ``CAMERA_MAC`` (if set) or by known Hikvision
   MAC OUIs (if not). Validate each candidate with a login probe; first
   success wins.

"Valid" = HTTP 200 with an ``X-csrftoken`` response header. Anything else
is rejected so we don't accidentally pick another HTTP service on the LAN.
"""

from __future__ import annotations

import logging
import socket
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, Optional

import requests
from requests.auth import HTTPDigestAuth

log = logging.getLogger(__name__)

# Hikvision OUI prefixes — used as a coarse filter when CAMERA_MAC isn't
# pinned. Not exhaustive; expand as new firmware ships.
HIKVISION_OUIS: tuple[str, ...] = (
    "38:24:f1", "f4:4e:e3", "d4:5e:89", "c0:56:e3", "c0:51:7e",
    "28:57:be", "44:19:b6", "bc:ad:28", "b8:b5:dc",
    "5c:c5:d4", "00:40:48", "4c:bd:8f",
)


def _parse_arp_table() -> list[tuple[str, str]]:
    """Read `/proc/net/arp` → [(ip, mac_lower), ...]; skip incomplete rows."""
    try:
        with open("/proc/net/arp") as f:
            lines = f.readlines()
    except OSError:
        return []
    rows: list[tuple[str, str]] = []
    for line in lines[1:]:  # header
        parts = line.split()
        if len(parts) < 4:
            continue
        ip, flags, mac = parts[0], parts[2], parts[3].lower()
        if mac == "00:00:00:00:00:00" or flags == "0x0":
            continue
        rows.append((ip, mac))
    return rows


def _populate_arp_for_subnet(
    subnet_prefix: str, *, port: int = 80, timeout: float = 0.25
) -> None:
    """Send a quick TCP connect to every host in <prefix>.0/24 in parallel.

    The connect almost always fails — we don't care. The ARP request the
    kernel sends *before* the SYN is what fills `/proc/net/arp`, which is
    all we want.
    """

    def probe(host: int) -> None:
        ip = f"{subnet_prefix}.{host}"
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                try:
                    sock.connect((ip, port))
                except OSError:
                    pass
        except OSError:
            pass

    with ThreadPoolExecutor(max_workers=64) as pool:
        list(pool.map(probe, range(1, 255)))


def _validate_login(
    ip: str, user: str, password: str, *, timeout: float = 4.0
) -> bool:
    try:
        resp = requests.post(
            f"http://{ip}/API/Web/Login",
            json={"data": {}},
            auth=HTTPDigestAuth(user, password),
            timeout=timeout,
        )
    except requests.RequestException:
        return False
    return resp.status_code == 200 and bool(resp.headers.get("X-csrftoken"))


def discover_camera(
    *,
    user: str,
    password: str,
    expected_mac: Optional[str] = None,
    subnet_prefixes: Iterable[str] = ("172.18.10", "172.18.11"),
) -> Optional[str]:
    """Return the camera's current IP, or None if no Hikvision-like host
    on the LAN passes a login probe.

    ``expected_mac`` is an optional pin — if set, ONLY hosts with that MAC
    are validated. Without it, every host whose MAC starts with a known
    Hikvision OUI is tried. Format is the standard ``aa:bb:cc:dd:ee:ff``,
    case-insensitive.
    """
    mac_norm = (expected_mac or "").strip().lower() or None
    subnets = tuple(subnet_prefixes)

    # Phase 1: cheap pass over whatever's already in the kernel's ARP cache.
    if mac_norm:
        for ip, mac in _parse_arp_table():
            if mac == mac_norm and _validate_login(ip, user, password):
                log.info("camera discovery: matched MAC %s at %s (cached ARP)", mac, ip)
                return ip

    # Phase 2: seed ARP for each candidate subnet, then walk the cache.
    for prefix in subnets:
        log.info("camera discovery: probing subnet %s.0/24", prefix)
        _populate_arp_for_subnet(prefix)

    candidates: list[tuple[str, str]] = []
    for ip, mac in _parse_arp_table():
        if mac_norm:
            if mac == mac_norm:
                candidates.append((ip, mac))
        else:
            if any(mac.startswith(oui) for oui in HIKVISION_OUIS):
                candidates.append((ip, mac))

    for ip, mac in candidates:
        if _validate_login(ip, user, password):
            log.info("camera discovery: validated %s (MAC %s)", ip, mac)
            return ip

    log.warning(
        "camera discovery: no camera found across subnets=%s mac_pin=%s candidates=%d",
        subnets, mac_norm or "(none — OUI filter)", len(candidates),
    )
    return None
