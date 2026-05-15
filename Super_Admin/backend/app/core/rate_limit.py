import time
from collections import defaultdict
from threading import Lock

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.exceptions import AppError

# ---------------------------------------------------------------------------
# Global rate limiter (enforced via SlowAPIMiddleware on every request)
# ---------------------------------------------------------------------------
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
    storage_uri="memory://",
)


# ---------------------------------------------------------------------------
# Per-endpoint rate limiter — usable as a FastAPI Depends() dependency.
#
# Why not @limiter.limit()?  slowapi's decorator breaks FastAPI's signature
# inspection when `from __future__ import annotations` is active (the
# wrapper loses the deferred type hints, so Pydantic body params get
# misread as query params).  A callable dependency avoids this entirely.
# ---------------------------------------------------------------------------
class RateLimitError(AppError):
    status_code = 429
    code = "rate_limit_exceeded"


class EndpointRateLimiter:
    """Simple in-memory per-IP rate limiter, callable as a FastAPI dependency."""

    def __init__(self, max_calls: int, window_seconds: int) -> None:
        self._max = max_calls
        self._window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def __call__(self, request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        with self._lock:
            cutoff = now - self._window
            timestamps = self._hits[key] = [t for t in self._hits[key] if t > cutoff]
            if len(timestamps) >= self._max:
                raise RateLimitError(f"Too many requests. Limit: {self._max} per {self._window}s.")
            timestamps.append(now)


# Pre-built limiters for sensitive endpoints
login_rate_limit = EndpointRateLimiter(max_calls=5, window_seconds=60)
password_rate_limit = EndpointRateLimiter(max_calls=5, window_seconds=60)
preview_rate_limit = EndpointRateLimiter(max_calls=600, window_seconds=60)
# Employee-image GET. Authenticated users only (the route is JWT-gated)
# but defends against an authenticated-but-malicious client enumerating
# employee IDs to crawl the photo gallery from disk. 120/min is well
# above any honest dashboard load (one image per row × ~50 employees
# loaded once per page open = ~50 reqs/page, far under the limit).
employee_image_rate_limit = EndpointRateLimiter(max_calls=120, window_seconds=60)
