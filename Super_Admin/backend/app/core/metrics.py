"""Prometheus metrics surface.

Two flavors of metrics exist in this app:

  * AUTOMATIC HTTP metrics — request count, latency, in-flight,
    response size — emitted by `prometheus-fastapi-instrumentator`.
    Exposed at GET `/metrics` (no auth — standard Prom convention,
    scrapers run inside the trust boundary).

  * MANUAL operational gauges/counters — worker pool depths, last
    frame age per camera, embedding cache size, realtime drop
    counter, RTSP reconnect count. Updated by a periodic refresh
    task whose only job is to read in-process state into Prom
    primitives (no extra contention added to the hot paths).

Adding a new metric:
  1. Declare it as a module-level Gauge/Counter/Histogram with a
     stable name + labels (renaming = breaking change for dashboards).
  2. Update it from the periodic refresh in `_periodic_refresh()`,
     OR call `.inc()` / `.set()` from the hot-path producer if the
     update is event-driven and cheap.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from prometheus_client import Counter, Gauge

if TYPE_CHECKING:
    from fastapi import FastAPI

log = logging.getLogger(__name__)


# --- Worker pools --------------------------------------------------------

worker_pool_depth = Gauge(
    "ai_attendance_worker_pool_depth",
    "Current number of jobs queued in each background worker pool.",
    ["pool"],
)
worker_pool_capacity = Gauge(
    "ai_attendance_worker_pool_capacity",
    "Configured maximum queue size for each background worker pool.",
    ["pool"],
)

# --- Camera workers ------------------------------------------------------

camera_worker_running = Gauge(
    "ai_attendance_camera_worker_running",
    "1 if the camera worker thread is alive, 0 otherwise.",
    ["camera_id", "camera_name"],
)
camera_last_frame_age_seconds = Gauge(
    "ai_attendance_camera_last_frame_age_seconds",
    "Seconds since this camera last produced a frame. Stale > a few "
    "seconds = the camera is not actually streaming.",
    ["camera_id", "camera_name"],
)
camera_last_detector_tick_age_seconds = Gauge(
    "ai_attendance_camera_last_detector_tick_age_seconds",
    "Seconds since the per-camera detector loop last ran. Watches for "
    "the 'reader-fine-detector-stuck' deadlock that the reader-only "
    "heartbeat misses.",
    ["camera_id", "camera_name"],
)
camera_processed_frames_total = Gauge(
    "ai_attendance_camera_processed_frames_total",
    "Cumulative count of frames this worker has processed.",
    ["camera_id", "camera_name"],
)
camera_events_generated_total = Gauge(
    "ai_attendance_camera_events_generated_total",
    "Cumulative count of attendance events this worker has produced.",
    ["camera_id", "camera_name"],
)

# --- Embedding cache -----------------------------------------------------

embedding_cache_employees = Gauge(
    "ai_attendance_embedding_cache_employees",
    "Number of employees currently loaded in the recognition cache.",
)
embedding_cache_vectors = Gauge(
    "ai_attendance_embedding_cache_vectors",
    "Number of face embedding vectors currently loaded.",
)

# --- Realtime bus --------------------------------------------------------

realtime_subscribers = Gauge(
    "ai_attendance_realtime_subscribers",
    "Number of active SSE subscribers connected to the realtime bus.",
)
realtime_drops_total = Counter(
    "ai_attendance_realtime_drops_total",
    "Cumulative count of realtime messages dropped due to slow consumers.",
)

# --- DB --------------------------------------------------------------

db_pool_size = Gauge(
    "ai_attendance_db_pool_size",
    "Current SQLAlchemy QueuePool size (idle + checked-out).",
)
db_pool_checked_out = Gauge(
    "ai_attendance_db_pool_checked_out",
    "Connections currently checked out (in use).",
)


# Snapshot of last-observed bus drop count so we can `Counter.inc(delta)`
# correctly even though the bus exposes a cumulative number.
_last_bus_drops: int = 0


def install(app: FastAPI) -> None:
    """Wire HTTP metrics middleware and start the periodic refresh.

    Idempotent: safe to call once per process. The refresh task is
    bound to the FastAPI lifespan so it stops cleanly on shutdown.
    """
    from prometheus_fastapi_instrumentator import Instrumentator

    instrumentator = Instrumentator(
        # Don't record metrics for /metrics itself (would be silly +
        # would inflate the request count for every scrape).
        excluded_handlers=["/metrics", "/health"],
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
    )
    instrumentator.instrument(app).expose(
        app,
        endpoint="/metrics",
        include_in_schema=False,
        tags=["observability"],
    )

    @app.on_event("startup")
    async def _start_refresh() -> None:  # pragma: no cover — wiring
        loop = asyncio.get_event_loop()
        app.state._metrics_task = loop.create_task(_periodic_refresh(app))

    @app.on_event("shutdown")
    async def _stop_refresh() -> None:  # pragma: no cover — wiring
        task = getattr(app.state, "_metrics_task", None)
        if task is not None:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass


async def _periodic_refresh(app: FastAPI) -> None:
    """Pulls in-process state into Prom gauges every 10s.

    Failure isolation: any exception in here is logged and the loop
    continues — losing one refresh tick is fine, but the loop must
    NEVER die (otherwise metrics silently freeze). Sleep is
    cancellable so shutdown is fast.
    """
    while True:
        try:
            await asyncio.sleep(10.0)
            _refresh_once(app)
        except asyncio.CancelledError:
            return
        except Exception:
            log.exception("metrics refresh tick raised; will retry")


def _refresh_once(app: FastAPI) -> None:
    # Late imports — these modules pull in heavy deps, and the
    # metrics module shouldn't add to import-time cost.
    from app.db.session import get_engine
    from app.services.event_queue import _POOLS  # type: ignore[attr-defined]
    from app.services.realtime_bus import bus

    # Worker pools
    for name, pool in _POOLS.items():
        worker_pool_depth.labels(pool=name).set(pool.depth())
        worker_pool_capacity.labels(pool=name).set(pool.capacity)

    # Camera workers (only present when not in API_ONLY mode)
    manager = getattr(app.state, "camera_manager", None)
    if manager is not None:
        for status in manager.status():
            labels = {
                "camera_id": str(status["camera_id"]),
                "camera_name": status.get("camera_name", "?"),
            }
            camera_worker_running.labels(**labels).set(1 if status["is_running"] else 0)
            frame_age = status.get("last_frame_age_seconds")
            camera_last_frame_age_seconds.labels(**labels).set(
                frame_age if frame_age is not None else -1.0
            )
            tick_age = status.get("last_detector_tick_age_seconds")
            if tick_age is not None:
                camera_last_detector_tick_age_seconds.labels(**labels).set(tick_age)
            camera_processed_frames_total.labels(**labels).set(status.get("processed_frames", 0))
            camera_events_generated_total.labels(**labels).set(status.get("events_generated", 0))

    # Embedding cache
    cache = getattr(app.state, "embedding_cache", None)
    if cache is not None:
        embedding_cache_employees.set(cache.employee_count())
        embedding_cache_vectors.set(cache.size())

    # Realtime bus
    bus_stats = bus.stats()
    realtime_subscribers.set(bus_stats["subscribers"])
    global _last_bus_drops
    delta = max(0, bus_stats["drops_total"] - _last_bus_drops)
    if delta > 0:
        realtime_drops_total.inc(delta)
    _last_bus_drops = bus_stats["drops_total"]

    # DB pool — read directly from SQLAlchemy's pool object.
    try:
        pool = get_engine().pool
        if hasattr(pool, "size"):
            db_pool_size.set(pool.size())  # type: ignore[attr-defined]
        if hasattr(pool, "checkedout"):
            db_pool_checked_out.set(pool.checkedout())  # type: ignore[attr-defined]
    except Exception:
        # Pool may not be initialized yet, or the dialect may not
        # expose these methods — non-fatal.
        pass
