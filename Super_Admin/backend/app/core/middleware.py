from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logger import get_logger, request_id_var

log = get_logger(__name__)

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}

# Header callers can supply to correlate THEIR client trace with our
# server trace. We accept it on the way in and echo it back on the
# way out — same name as Heroku/Cloudflare/AWS-LB conventions.
_REQUEST_ID_HEADER = "X-Request-ID"

# Cap the inbound ID length so a malicious client can't write a
# multi-megabyte string into our logs by setting a giant header.
_MAX_REQUEST_ID_LEN = 64


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject standard security headers into every HTTP response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Per-request correlation ID + access log line.

    Behavior:
      1. Read `X-Request-ID` from the inbound request. If absent or
         malformed, generate a fresh UUID4.
      2. Bind it to the `request_id_var` contextvar so every `log.*`
         call inside the request automatically tags with it.
      3. Time the request, emit a single structured access log line
         on completion (success OR exception).
      4. Echo the ID back to the client via the same header so an
         end user reporting "I got an error at 14:23" can also share
         the request ID and we can pull every related log line in
         one query.

    Why this is its own middleware (rather than folded into the
    security one): the contextvar MUST be set before any business
    code runs, and it must be unset (token reset) on the way out so
    a recycled worker thread doesn't carry a stale value into the
    next request. Two responsibilities, two middlewares.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = self._extract_or_generate(request)
        token = request_id_var.set(rid)
        start = time.perf_counter()
        status_code: int | None = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers[_REQUEST_ID_HEADER] = rid
            return response
        except Exception:
            # Re-raise so FastAPI's exception handler chain runs;
            # we just want the access log line to land first.
            status_code = 500
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            # One line per request — the full HTTP-access trail. JSON
            # formatter converts this into structured fields; text
            # formatter renders the message inline.
            log.info(
                "%s %s -> %s (%.1fms)",
                request.method,
                request.url.path,
                status_code if status_code is not None else "—",
                elapsed_ms,
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "http_status": status_code,
                    "duration_ms": round(elapsed_ms, 1),
                    "client_ip": request.client.host if request.client else None,
                },
            )
            request_id_var.reset(token)

    @staticmethod
    def _extract_or_generate(request: Request) -> str:
        candidate = request.headers.get(_REQUEST_ID_HEADER, "").strip()
        if not candidate or len(candidate) > _MAX_REQUEST_ID_LEN:
            return uuid.uuid4().hex
        # Sanitize: only allow ASCII alnum + a few punctuation chars.
        # Anything weirder is replaced rather than rejected, so a
        # broken-but-well-meaning client still gets correlation.
        if not all(c.isalnum() or c in "-_." for c in candidate):
            return uuid.uuid4().hex
        return candidate
