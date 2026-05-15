from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.core.exceptions import AuthenticationError
from app.db.session import session_scope
from app.services.auth_service import AuthService
from app.services.realtime_bus import bus

log = logging.getLogger(__name__)

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.get("/stream")
async def stream(request: Request, token: str = Query(..., min_length=10)) -> StreamingResponse:
    """Server-Sent Events channel.

    EventSource cannot send Authorization headers, so the JWT is passed
    as a query string. We resolve the admin once at subscribe time and
    capture their company; messages tagged with a different `company`
    are dropped server-side so HR users only see their own tenant.
    """
    try:
        with session_scope() as db:
            admin = AuthService(db).resolve_admin(token)
            scoped_company: str | None = admin.company
    except AuthenticationError as exc:
        # `from exc` preserves the original AuthenticationError on the
        # __cause__ chain so structured logs / Sentry can show the
        # underlying reason without leaking it in the HTTP body.
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    except Exception as exc:
        log.exception("realtime: failed to resolve admin")
        raise HTTPException(status_code=401, detail="Could not authenticate") from exc

    queue = await bus.subscribe()

    async def event_generator():
        try:
            yield "retry: 3000\n\n"
            yield f"event: connected\ndata: {json.dumps({'company': scoped_company})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                except TimeoutError:
                    # Keep the connection alive through proxies.
                    yield ": ping\n\n"
                    continue
                # Filter by company if subscriber is HR-scoped.
                if scoped_company is not None:
                    try:
                        parsed = json.loads(msg)
                        msg_company = parsed.get("company")
                        if msg_company is not None and msg_company != scoped_company:
                            continue
                    except (TypeError, ValueError):
                        pass
                yield f"data: {msg}\n\n"
        finally:
            bus.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
