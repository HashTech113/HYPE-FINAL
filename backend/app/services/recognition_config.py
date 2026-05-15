"""Runtime-tunable knobs for the recognition pipeline.

Stored as one row in the existing key/value ``settings`` table under the
key ``recognition_config`` — same shape as ``unknown_capture_config``.

A short in-process TTL cache (5s) keeps the per-inference DB read
cheap: the camera worker re-evaluates settings on every frame, so
without the cache a 5–10 FPS detector would slam the DB. Admin saves
are visible within 5s — fast enough that the UI feels live.

Falls back to env vars and built-in defaults if the row is missing or
malformed; the recognition pipeline must keep running even if an admin
corrupts the row.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from ..config import CAPTURE_INTERVAL_SECONDS, FACE_MATCH_THRESHOLD, FACE_MIN_QUALITY
from ..db import session_scope
from ..models import Setting

_SETTINGS_KEY = "recognition_config"
_CACHE_TTL_SECONDS = 5.0


@dataclass(frozen=True)
class RecognitionSettings:
    face_min_quality: float       # detector score floor (0..1)
    face_match_threshold: float   # cosine similarity floor for a match
    recognize_min_face_size_px: int  # min(bbox_w, bbox_h) gate before recognition
    camera_fps: int               # target detection cadence
    cooldown_seconds: int         # per-employee dedup window


def _env_defaults() -> RecognitionSettings:
    """Defaults pulled from env vars (kept as a backstop so behaviour is
    identical to before this refactor when the settings row is missing)."""
    # 1.0/CAPTURE_INTERVAL_SECONDS converts the legacy "seconds between
    # detections" to "detections per second" — a 5s legacy interval maps
    # to 0.2 FPS, which we clamp to a sensible minimum of 1.
    derived_fps = max(1, int(round(1.0 / max(0.2, float(CAPTURE_INTERVAL_SECONDS)))))
    return RecognitionSettings(
        face_min_quality=float(FACE_MIN_QUALITY),
        face_match_threshold=float(FACE_MATCH_THRESHOLD),
        recognize_min_face_size_px=0,  # disabled by default — backward compatible
        camera_fps=derived_fps,
        cooldown_seconds=5,
    )


_cache_lock = threading.Lock()
_cache: Optional[tuple[float, RecognitionSettings]] = None


def _merged(blob: dict, defaults: RecognitionSettings) -> RecognitionSettings:
    def _f(key: str, fallback: float) -> float:
        try:
            return float(blob.get(key, fallback))
        except (TypeError, ValueError):
            return fallback

    def _i(key: str, fallback: int, *, lo: int = 0) -> int:
        try:
            v = int(blob.get(key, fallback))
            return max(lo, v)
        except (TypeError, ValueError):
            return fallback

    return RecognitionSettings(
        face_min_quality=_f("face_min_quality", defaults.face_min_quality),
        face_match_threshold=_f("face_match_threshold", defaults.face_match_threshold),
        recognize_min_face_size_px=_i(
            "recognize_min_face_size_px",
            defaults.recognize_min_face_size_px,
        ),
        camera_fps=max(1, _i("camera_fps", defaults.camera_fps, lo=1)),
        cooldown_seconds=max(0, _i("cooldown_seconds", defaults.cooldown_seconds, lo=0)),
    )


def _read_uncached(session: Optional[Session]) -> RecognitionSettings:
    defaults = _env_defaults()
    own_session = False
    if session is None:
        ctx = session_scope()
        session = ctx.__enter__()
        own_session = True
    try:
        row = session.get(Setting, _SETTINGS_KEY)
        if row is None or not isinstance(row.value, dict):
            return defaults
        return _merged(row.value, defaults)
    finally:
        if own_session:
            ctx.__exit__(None, None, None)


def get_recognition_settings(session: Optional[Session] = None) -> RecognitionSettings:
    """Return the active settings, honoring the 5s in-process cache.

    Callers on the hot path (camera worker, recognition matcher) should
    use this — it adds ~one cache hit per inference, vs a full DB
    roundtrip per face.
    """
    global _cache
    now = time.monotonic()
    with _cache_lock:
        cached = _cache
        if cached is not None and (now - cached[0]) < _CACHE_TTL_SECONDS:
            return cached[1]
    settings = _read_uncached(session)
    with _cache_lock:
        _cache = (time.monotonic(), settings)
    return settings


def invalidate_cache() -> None:
    """Drop the cached settings so the next read picks up the latest row.
    Called from the PATCH endpoint after writing."""
    global _cache
    with _cache_lock:
        _cache = None


def write_recognition_settings(session: Session, patch: dict) -> RecognitionSettings:
    """Upsert the recognition_config row. Partial updates supported: only
    the keys present in ``patch`` are written; everything else keeps its
    existing value (or the env-derived default for a brand-new row)."""
    defaults = _env_defaults()
    row = session.get(Setting, _SETTINGS_KEY)
    existing: dict = {}
    if row is not None and isinstance(row.value, dict):
        existing = dict(row.value)
    # Merge with defaults first so a brand-new row gets a fully-populated
    # blob, then layer the caller's patch on top.
    merged: dict = {
        "face_min_quality": defaults.face_min_quality,
        "face_match_threshold": defaults.face_match_threshold,
        "recognize_min_face_size_px": defaults.recognize_min_face_size_px,
        "camera_fps": defaults.camera_fps,
        "cooldown_seconds": defaults.cooldown_seconds,
    }
    merged.update(existing)
    for k, v in patch.items():
        if k in merged and v is not None:
            merged[k] = v
    if row is None:
        row = Setting(key=_SETTINGS_KEY, value=merged)
        session.add(row)
    else:
        row.value = merged
    session.flush()
    invalidate_cache()
    return _merged(merged, defaults)
