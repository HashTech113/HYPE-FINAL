"""FastAPI app factory. Routers are registered from app/routers/*."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from . import upgrade
from .config import DB_PATH, FACE_RECOGNITION_ENABLED
from .db import DIALECT, init_db
from .ratelimit import limiter
from .routers import (
    admin,
    attendance,
    auth,
    cameras,
    companies,
    corrections,
    employees,
    external_attendance,
    face_images,
    faces,
    health,
    ingest,
    logs,
    recognition,
    reports,
    snapshot_admin,
    unknowns,
    users,
)
from .services.auth import seed_users_if_empty
from .services.cleanup import prune_old_snapshots, seconds_until_next_local_midnight
from .services.employees import seed_if_empty as seed_employees_if_empty
from .services.logs import snapshot_log_count

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# Exact-match origins. Production frontend + the two local Vite ports we
# actually use (5173 is Vite's default, 8080 is what this repo's dev server
# is pinned to).
DEFAULT_EXACT_ORIGINS = [
    "https://hype.camera2ai.com",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
]

# Extra origins can be added at runtime via the ALLOWED_ORIGINS env var
# (comma-separated), so adding a new frontend domain doesn't need a code
# change — just a Railway variable update + restart.
EXTRA_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()
]

# Regex backstop for preview/PR deployments (Cloudflare Pages, Vercel,
# Railway) and any *.camera2ai.com subdomain. Starlette echoes the matched
# origin back verbatim, so credentials still work.
ALLOWED_ORIGIN_REGEX = (
    r"https://.*\.pages\.dev"
    r"|https://.*\.vercel\.app"
    r"|https://.*\.up\.railway\.app"
    r"|https://.*\.workers\.dev"
    r"|https://.*\.camera2ai\.com"
    r"|http://172\.18\.\d+\.\d+(:\d+)?"
    r"|http://192\.168\.\d+\.\d+(:\d+)?"
    r"|http://10\.\d+\.\d+\.\d+(:\d+)?"
)


log = logging.getLogger(__name__)


async def _retention_loop() -> None:
    """Sleep until the next local midnight, run the snapshot retention
    cleanup, and repeat. Cancellation (on shutdown) is the only exit."""
    while True:
        delay = seconds_until_next_local_midnight()
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return
        try:
            await asyncio.to_thread(prune_old_snapshots)
        except Exception:
            log.exception("scheduled snapshot retention cleanup failed")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if DIALECT == "sqlite":
        log.info("using SQLite database at %s", DB_PATH)
    else:
        log.info("using %s database (DATABASE_URL set)", DIALECT)
    init_db()
    upgrade.run()
    seed_employees_if_empty()
    seed_users_if_empty()
    count = snapshot_log_count()
    if count == 0:
        log.warning(
            "snapshot_logs is empty — if this is production, check that "
            "DATABASE_URL points at the right database (or, when running "
            "on the SQLite fallback, that the Railway persistent volume "
            "is mounted and DATABASE_PATH is set inside it).",
        )
    else:
        log.info("snapshot_logs has %d rows", count)

    try:
        prune_old_snapshots()
    except Exception:
        log.exception("startup snapshot retention cleanup failed")
    retention_task = asyncio.create_task(_retention_loop(), name="snapshot-retention")

    # Day-close scheduler: closes the local day at SHIFT_END+buffer so
    # trailing BREAK_OUTs become OUT automatically. Disabled by default
    # (DAY_CLOSE_SCHEDULER_ENABLED=1 to enable) — manual close via
    # POST /api/attendance/close-day always works regardless.
    try:
        from .services.day_close_scheduler import start_if_enabled
        if start_if_enabled():
            log.info("day-close scheduler enabled")
        else:
            log.info("day-close scheduler disabled (set DAY_CLOSE_SCHEDULER_ENABLED=1 to enable)")
    except Exception:
        log.exception("day-close scheduler startup failed")

    # Load InsightFace + the embedding cache so the first /api/recognition
    # call doesn't pay the ~3-5s init cost. Failures are logged but don't
    # block startup — read endpoints (employees, attendance) keep working
    # even if the ML stack is broken.
    worker_manager = None
    if FACE_RECOGNITION_ENABLED:
        try:
            from .services.embedding_cache import get_embedding_cache
            from .services.face_service import get_face_service
            await asyncio.to_thread(get_face_service().load)
            await asyncio.to_thread(get_embedding_cache().load_from_db)
            log.info(
                "face engine ready (cache: %d employees, %d vectors)",
                get_embedding_cache().employee_count(),
                get_embedding_cache().size(),
            )
        except Exception:
            log.exception("face engine startup failed — recognition routes will return 503")
        # Spawn one RTSP recognition worker per active camera. Skipped
        # via RECOGNITION_WORKERS_ENABLED=0 when running the API on a
        # machine without LAN access to the cameras (so capture.py on
        # the on-prem box stays the only RTSP reader).
        if os.getenv("RECOGNITION_WORKERS_ENABLED", "1").strip().lower() not in ("0", "false", "no"):
            try:
                from .services.recognition_worker import get_worker_manager
                worker_manager = get_worker_manager()
                count = await asyncio.to_thread(worker_manager.start_all)
                log.info("recognition worker manager started (%d cameras)", count)
            except Exception:
                log.exception("recognition worker manager failed to start")
    else:
        log.info("face engine disabled (FACE_RECOGNITION_ENABLED=0)")

    try:
        yield
    finally:
        if worker_manager is not None:
            try:
                await asyncio.to_thread(worker_manager.stop_all)
            except Exception:
                log.exception("worker manager shutdown failed")
        retention_task.cancel()
        try:
            await retention_task
        except asyncio.CancelledError:
            pass


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Lightweight defaults for browser-side hardening. Doesn't override
    headers a downstream proxy already set, so a deployment behind
    nginx/cloudflare with stricter CSP rules keeps that policy."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # No CSP here — too risky to set blanket rules without knowing where
        # static assets live in this deployment. Operators add it at the
        # proxy layer if they want one.
        return response


def create_app() -> FastAPI:
    app = FastAPI(title="Camera Capture API", version="0.7.0", lifespan=lifespan)

    # Rate-limit plumbing (limits themselves are per-route, see auth router).
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(SecurityHeadersMiddleware)

    # Compress JSON / HTML / JS responses bigger than 1 KB. Typical
    # /api/employees and /api/snapshots payloads shrink 70–85% — the
    # roster JSON for 246 employees is ~75 KB raw, ~12 KB gzipped.
    # Negligible CPU cost; ignored for already-compressed binary
    # (image/jpeg, multipart MJPEG) by Starlette's heuristic.
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[*DEFAULT_EXACT_ORIGINS, *EXTRA_ORIGINS],
        allow_origin_regex=ALLOWED_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
        # Tell the browser it can cache the preflight result for 10 min.
        # Without this it sends an OPTIONS before every cross-origin
        # request — visible as the constant "OPTIONS /api/..." spam in
        # the dev log. With it, each (origin, method, headers) triple
        # is preflighted once per 10-min window.
        max_age=600,
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(faces.router)
    app.include_router(attendance.router)
    app.include_router(logs.router)
    app.include_router(ingest.router)
    app.include_router(external_attendance.router)
    app.include_router(employees.router)
    app.include_router(companies.router)
    app.include_router(face_images.router)
    app.include_router(cameras.router)
    app.include_router(corrections.router)
    app.include_router(recognition.router)
    app.include_router(reports.router)
    app.include_router(users.router)
    app.include_router(snapshot_admin.router)
    app.include_router(admin.router)
    app.include_router(unknowns.router)

    return app


app = create_app()
