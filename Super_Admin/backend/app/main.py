from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.config import get_settings
from app.core.exceptions import AppError
from app.core.logger import configure_logging, get_logger
from app.core.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from app.db.session import dispose_engine
from app.services.auth_service import bootstrap_admin
from app.services.day_close_scheduler import (
    get_day_close_scheduler,
    shutdown_day_close_scheduler,
)
from app.services.embedding_cache import EmbeddingCache
from app.services.event_queue import get_pool, shutdown_all_pools
from app.services.realtime_bus import bus as realtime_bus
from app.services.settings_service import get_settings_service

# `FaceService` and `CameraManager` are imported lazily inside the
# lifespan body so an API-only deployment (Railway etc.) doesn't pay
# the multi-second InsightFace + onnxruntime + opencv import cost at
# module load. On a slow Linux container this used to push cold
# startup past the 120 s healthcheck window. Real machines (the
# on-prem Windows host where cameras live) hit the import a hair
# later than before — the difference is unmeasurable in practice.

log = get_logger(__name__)


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


# API-only mode: skip InsightFace model loading and camera worker spin-up.
# Set this on cloud deployments (Railway, Fly, etc.) where:
#   * the host has no GPU (recognition would be too slow on CPU)
#   * the RTSP cameras live on a private LAN unreachable from the cloud
# In this mode the deployment serves the read API (admin endpoints, the
# external API used by HR dashboards, attendance/event queries) but does
# NOT do any face recognition itself. The on-prem instance keeps doing
# recognition and writes to the same shared Postgres.
API_ONLY = _truthy_env("DISABLE_CAMERA_WORKERS") or _truthy_env("API_ONLY")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    log.info("Starting %s (api_only=%s)", settings.APP_NAME, API_ONLY)

    # Capture the running loop so realtime publishers can hop threads
    # safely (camera workers publish from background threads).
    realtime_bus.bind_loop(asyncio.get_running_loop())

    bootstrap_admin()
    get_settings_service().load()

    # Pre-warm the three independent worker pools regardless of mode —
    # manual event corrections still go through `attendance` from admin
    # endpoints, and eager init makes startup-time errors visible
    # immediately rather than on first event. Each pool is fully
    # isolated: saturation in one cannot affect any other.
    get_pool("attendance")
    get_pool("unknown_capture")
    get_pool("auto_enroll")

    camera_manager: CameraManager | None = None

    if API_ONLY:
        log.warning(
            "API_ONLY mode: face recognition and camera workers disabled. "
            "Endpoints depending on `camera_manager` (live preview, MJPEG, "
            "training-from-camera) will return 500. The external API and "
            "admin endpoints remain fully functional."
        )
    else:
        # Lazy import — only the on-prem (with-cameras) deployment pays
        # the InsightFace/onnxruntime/opencv import latency.
        from app.services.face_service import FaceService
        from app.workers.camera_manager import CameraManager

        face_service = FaceService()
        face_service.load()
        embedding_cache = EmbeddingCache()
        embedding_cache.load_from_db()

        camera_manager = CameraManager(
            face_service=face_service,
            embedding_cache=embedding_cache,
        )

        app.state.face_service = face_service
        app.state.embedding_cache = embedding_cache
        app.state.camera_manager = camera_manager

        camera_manager.start_all()

        # Start the daily close-day scheduler. Runs `close_day(today)`
        # automatically at `work_end_time + 30 min` so trailing
        # BREAK_OUT events get rewritten as OUT and the day is sealed
        # without an admin needing to click anything. Only relevant
        # when we're actually generating events (i.e. not API-only).
        get_day_close_scheduler().start()

    try:
        yield
    finally:
        log.info("Shutting down %s", settings.APP_NAME)
        if not API_ONLY:
            shutdown_day_close_scheduler()
        if camera_manager is not None:
            camera_manager.stop_all()
        # Drain every worker pool after camera workers stop so any in-
        # flight recognition jobs complete before we close the DB pool.
        shutdown_all_pools()
        dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
    )

    # --- Middleware stack (last registered = outermost) ---
    # 1. CORS (inner — adds CORS headers to all responses including 429)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Security headers (every response gets these)
    app.add_middleware(SecurityHeadersMiddleware)

    # 3. Request-ID + access logging (OUTERMOST so the contextvar is
    # set before any other middleware/handler logs anything, and the
    # access log line covers the full request lifetime including any
    # downstream middleware time).
    app.add_middleware(RequestIDMiddleware)

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message},
        )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/diagnostics", tags=["observability"], include_in_schema=False)
    async def diagnostics(request: Request) -> dict:
        """Operator-facing snapshot of in-process state. Faster than
        scraping Prometheus when you just need to eyeball the system
        from a terminal: pool depths, bus stats, camera worker ages,
        embedding cache size.

        Intentionally unauthenticated and intentionally read-only.
        Bind to localhost only in production deployments — the
        existing CORS_ALLOW_ORIGINS list does NOT protect this.
        """
        from app.services.event_queue import pool_depths
        from app.services.realtime_bus import bus

        cache = getattr(request.app.state, "embedding_cache", None)
        manager = getattr(request.app.state, "camera_manager", None)
        return {
            "uptime_hint": "see /metrics for ai_attendance_* gauges",
            "worker_pools": pool_depths(),
            "realtime_bus": bus.stats(),
            "embedding_cache": {
                "employees": cache.employee_count() if cache else None,
                "vectors": cache.size() if cache else None,
            },
            "camera_workers": (manager.status() if manager is not None else []),
        }

    # Prometheus metrics + periodic refresh task. Side-effects: adds
    # /metrics endpoint and starts a 10s background refresh on app
    # startup. Safe in API_ONLY deployments — refresh tolerates
    # missing camera_manager / embedding_cache state.
    from app.core.metrics import install as install_metrics

    install_metrics(app)

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
