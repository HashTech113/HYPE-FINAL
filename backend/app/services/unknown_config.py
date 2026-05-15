"""Runtime-tunable knobs for the unknown-face pipeline.

Stored as a single row in the existing key/value ``settings`` table
under the key ``unknown_capture_config``. A single blob keeps related
knobs atomic (one write updates them all consistently) and avoids the
N rows the columnar Super_Admin schema used.

Callers always go through :func:`get_unknown_settings` so a missing
row (fresh install) transparently falls back to the defaults below.
The blob is *merged* with defaults on read, so adding a new knob in a
later release is backward compatible — old rows simply gain the new
default until the admin overrides it.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..models import Setting

_SETTINGS_KEY = "unknown_capture_config"


@dataclass(frozen=True)
class UnknownSettings:
    enabled: bool = True
    # Quality gate
    min_face_size_px: int = 60
    min_face_quality: float = 0.55        # detector score floor
    min_sharpness: float = 30.0           # Laplacian variance
    # Online clustering
    cluster_match_threshold: float = 0.45  # cosine similarity floor
    capture_cooldown_seconds: int = 30
    # Retention
    retention_days: int = 14


_DEFAULTS = UnknownSettings()


def _defaults_dict() -> dict:
    return {
        "enabled": _DEFAULTS.enabled,
        "min_face_size_px": _DEFAULTS.min_face_size_px,
        "min_face_quality": _DEFAULTS.min_face_quality,
        "min_sharpness": _DEFAULTS.min_sharpness,
        "cluster_match_threshold": _DEFAULTS.cluster_match_threshold,
        "capture_cooldown_seconds": _DEFAULTS.capture_cooldown_seconds,
        "retention_days": _DEFAULTS.retention_days,
    }


def get_unknown_settings(session: Session) -> UnknownSettings:
    """Read the active config, falling back to defaults for any missing
    key. Never raises on a missing or malformed row — the unknown-capture
    pipeline must keep running even if an admin somehow corrupts the
    settings row.
    """
    row = session.get(Setting, _SETTINGS_KEY)
    blob: dict = {}
    if row is not None and isinstance(row.value, dict):
        blob = row.value
    merged = _defaults_dict()
    merged.update({k: blob[k] for k in merged.keys() if k in blob})
    try:
        return UnknownSettings(
            enabled=bool(merged["enabled"]),
            min_face_size_px=int(merged["min_face_size_px"]),
            min_face_quality=float(merged["min_face_quality"]),
            min_sharpness=float(merged["min_sharpness"]),
            cluster_match_threshold=float(merged["cluster_match_threshold"]),
            capture_cooldown_seconds=int(merged["capture_cooldown_seconds"]),
            retention_days=int(merged["retention_days"]),
        )
    except (TypeError, ValueError):
        return _DEFAULTS
