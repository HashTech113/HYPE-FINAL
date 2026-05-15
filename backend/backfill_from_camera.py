"""Scheduled camera-history backfill worker.

Every ``BACKFILL_INTERVAL_SECONDS`` (default 300s = 5 min), scan the
camera's persistent SnapedFaces index over ``[now - BACKFILL_WINDOW, now]``
(default 30 min) and ingest anything missing from snapshot_logs. This
closes any gap left by the live ``capture.py`` stream — capture restarts,
network blips, brief camera unavailability, etc.

The worker runs as its own supervised process so a crash cannot drag down
live capture or the API. Camera errors trigger a re-login; DB writes are
idempotent via the same UNIQUE(image_path) constraint that ingest uses.
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta, timezone

from app.services import camera_backfill
from app.services.camera import CameraClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("backfill")

BACKFILL_INTERVAL_SECONDS = float(os.getenv("BACKFILL_INTERVAL_SECONDS", "300"))
BACKFILL_WINDOW_SECONDS = float(os.getenv("BACKFILL_WINDOW_SECONDS", "1800"))
ERROR_BACKOFF_SECONDS = float(os.getenv("BACKFILL_ERROR_BACKOFF_SECONDS", "30"))
# How often to refresh the MatchedFaceId → name map. Names rarely change
# and the lookup is expensive (full SnapedFaces scan), so an hour is fine.
FACE_MAP_TTL_SECONDS = float(os.getenv("FACE_MAP_TTL_SECONDS", "3600"))


def _interruptible_sleep(seconds: float, stop: dict) -> None:
    """time.sleep() that exits early when SIGTERM/SIGINT is received."""
    end = time.monotonic() + seconds
    while not stop["flag"]:
        remaining = end - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(1.0, remaining))


def run() -> int:
    stop = {"flag": False}

    def _handle(signum, _frame):
        log.info("Received signal %s — shutting down backfill worker", signum)
        stop["flag"] = True

    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)

    log.info(
        "scheduled backfill: every %.0fs over [now - %.0fs, now]",
        BACKFILL_INTERVAL_SECONDS, BACKFILL_WINDOW_SECONDS,
    )

    camera = CameraClient()
    face_id_map: dict[int, str] = {}
    last_map_refresh = 0.0

    while not stop["flag"]:
        cycle_start = time.monotonic()

        if cycle_start - last_map_refresh > FACE_MAP_TTL_SECONDS:
            try:
                face_id_map = camera_backfill.build_face_id_name_map(camera)
                last_map_refresh = cycle_start
            except Exception:
                log.exception(
                    "face_id_name_map refresh failed (continuing with %d-entry stale map)",
                    len(face_id_map),
                )
                camera.invalidate()

        end_utc = datetime.now(timezone.utc)
        start_utc = end_utc - timedelta(seconds=BACKFILL_WINDOW_SECONDS)
        log.info("backfill started window=%s→%s", start_utc.isoformat(), end_utc.isoformat())
        try:
            summary = camera_backfill.backfill_window(
                camera, start_utc, end_utc, face_id_map=face_id_map,
            )
        except Exception:
            log.exception("backfill cycle failed; backing off then retrying")
            camera.invalidate()
            _interruptible_sleep(ERROR_BACKOFF_SECONDS, stop)
            continue

        log.info(
            "backfill completed camera=%d added=%d already=%d failed=%d unmapped=%s",
            summary.get("camera_count", 0),
            summary.get("added", 0),
            summary.get("already_present", 0),
            summary.get("failed", 0),
            summary.get("unmapped_face_ids", {}),
        )

        elapsed = time.monotonic() - cycle_start
        sleep_for = max(10.0, BACKFILL_INTERVAL_SECONDS - elapsed)
        _interruptible_sleep(sleep_for, stop)

    log.info("backfill loop exited")
    return 0


if __name__ == "__main__":
    sys.exit(run())
