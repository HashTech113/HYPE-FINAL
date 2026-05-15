"""External attendance API adapter.

Pulls events / daily summaries / today's stats from a third-party HR system
configured via two env vars:

    EXTERNAL_ATTENDANCE_API_URL   base URL, no trailing slash
    EXTERNAL_ATTENDANCE_API_KEY   shared secret, sent as ``X-API-Key`` header

Both live only on the backend / Railway side. The frontend never sees them.

All HTTP calls use a bounded ``(connect, read)`` timeout so a slow vendor
can't hang the request handler. Failures are caught and logged — the caller
gets an empty list / falsy value rather than an exception, so the sync
endpoint can return a clean count of what was imported instead of 500ing.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import requests

from ..config import EXTERNAL_ATTENDANCE_API_KEY, EXTERNAL_ATTENDANCE_API_URL

log = logging.getLogger(__name__)

# (connect, read) seconds. Short connect: dead host / DNS / firewall fails fast.
# Bounded read: vendor that accepts the connection but stalls on the response
# body still releases our worker after 15s.
EXTERNAL_TIMEOUT_SECONDS: tuple[float, float] = (5.0, 15.0)

ALLOWED_EVENT_TYPES: frozenset[str] = frozenset({"IN", "OUT", "BREAK_OUT", "BREAK_IN"})

# Map common vendor spellings → our four canonical types. Anything not
# resolvable is treated as a malformed event and skipped (with a debug log).
_EVENT_TYPE_ALIASES: dict[str, str] = {
    "IN": "IN",
    "CHECK_IN": "IN",
    "CHECKIN": "IN",
    "ENTRY": "IN",
    "PUNCH_IN": "IN",
    "CLOCK_IN": "IN",
    "OUT": "OUT",
    "CHECK_OUT": "OUT",
    "CHECKOUT": "OUT",
    "EXIT": "OUT",
    "PUNCH_OUT": "OUT",
    "CLOCK_OUT": "OUT",
    "BREAK_OUT": "BREAK_OUT",
    "BREAK_START": "BREAK_OUT",
    "BREAK_BEGIN": "BREAK_OUT",
    "BREAKOUT": "BREAK_OUT",
    "BREAK_IN": "BREAK_IN",
    "BREAK_END": "BREAK_IN",
    "BREAKIN": "BREAK_IN",
    "RESUME": "BREAK_IN",
}


def is_configured() -> bool:
    """True iff both URL and key are present. Callers (notably the sync
    endpoint) should short-circuit on False to surface a clean 503 rather
    than attempting a request to ``''``."""
    return bool(EXTERNAL_ATTENDANCE_API_URL and EXTERNAL_ATTENDANCE_API_KEY)


def _headers() -> dict[str, str]:
    return {"X-API-Key": EXTERNAL_ATTENDANCE_API_KEY, "Accept": "application/json"}


def _normalize_list_payload(data: Any) -> list[dict]:
    """Accept either ``[ … ]`` or ``{"items": […]}`` / ``{"events": […]}``
    shapes. Anything else logs a warning and returns an empty list — the
    caller treats that as "vendor returned nothing usable", not a 500."""
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("items", "events", "data", "results"):
            inner = data.get(key)
            if isinstance(inner, list):
                return [item for item in inner if isinstance(item, dict)]
    log.warning("external API returned unexpected JSON shape: %r", type(data).__name__)
    return []


def _get(path: str, params: Optional[dict] = None) -> Any:
    """Wrapped GET. Returns parsed JSON on 2xx, ``None`` on any failure
    (network / non-JSON / non-2xx). Never raises."""
    if not is_configured():
        log.warning(
            "external attendance API not configured; "
            "set EXTERNAL_ATTENDANCE_API_URL and EXTERNAL_ATTENDANCE_API_KEY"
        )
        return None
    url = f"{EXTERNAL_ATTENDANCE_API_URL}{path}"
    try:
        resp = requests.get(
            url,
            headers=_headers(),
            params=params or None,
            timeout=EXTERNAL_TIMEOUT_SECONDS,
        )
    except requests.RequestException as e:
        log.error("external GET %s failed: %s", url, e)
        return None
    if resp.status_code != 200:
        # Truncate body in case vendor returned a huge HTML error page.
        log.error(
            "external GET %s returned %d: %s",
            url, resp.status_code, resp.text[:300],
        )
        return None
    try:
        return resp.json()
    except ValueError as e:
        log.error("external GET %s returned non-JSON body: %s", url, e)
        return None


def fetch_events(since: Optional[str] = None) -> list[dict]:
    """``GET /external/events`` — list of attendance events the vendor
    has recorded. Optional ``since`` ISO timestamp narrows the window.

    Returns ``[]`` on any error so the caller can keep counts clean."""
    params: dict[str, str] = {}
    if since:
        params["since"] = since
    data = _get("/external/events", params)
    if data is None:
        return []
    return _normalize_list_payload(data)


def fetch_daily(date: str) -> list[dict]:
    """``GET /external/daily?date=YYYY-MM-DD`` — vendor's already-aggregated
    daily roster. We don't currently merge this into the per-day summary
    builder (that one rebuilds from events) but it's exposed for ad-hoc
    diagnostics / future use."""
    data = _get("/external/daily", {"date": date})
    if data is None:
        return []
    return _normalize_list_payload(data)


def fetch_stats_today() -> Optional[dict]:
    """``GET /external/stats/today`` — vendor's "summary stats" object.
    Shape is vendor-specific so we just return the parsed dict (or None)."""
    data = _get("/external/stats/today")
    if isinstance(data, dict):
        return data
    return None


def normalize_event_type(raw: Any) -> Optional[str]:
    """Map vendor event-type strings to one of IN / OUT / BREAK_OUT / BREAK_IN.
    Returns None when the value is missing or unrecognized — callers should
    skip events that fail to normalize (they can't be classified as entry
    or exit)."""
    if raw is None:
        return None
    s = str(raw).strip().upper().replace("-", "_").replace(" ", "_")
    if not s:
        return None
    return _EVENT_TYPE_ALIASES.get(s) or (s if s in ALLOWED_EVENT_TYPES else None)


def extract_event_id(item: dict) -> Optional[str]:
    """Best-effort scan for the vendor's event id under any of the common
    key spellings. Without an id we can't dedup, so the caller should skip
    the event."""
    for key in ("id", "event_id", "external_id", "uuid", "punch_id"):
        v = item.get(key)
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def extract_employee_name(item: dict) -> Optional[str]:
    for key in ("employee_name", "name", "full_name", "display_name"):
        v = item.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def extract_timestamp(item: dict) -> Optional[str]:
    for key in ("timestamp", "event_time", "occurred_at", "time", "punch_time"):
        v = item.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def extract_event_type(item: dict) -> Optional[str]:
    """Looks up the event-type field under common names and normalizes it."""
    for key in ("event_type", "type", "punch_type", "action"):
        if key in item:
            normalized = normalize_event_type(item.get(key))
            if normalized:
                return normalized
    return None
