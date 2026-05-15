"""Shared slowapi Limiter instance.

Lives in its own module so both ``app.main`` (which wires the middleware
and exception handler) and route modules (which decorate handlers with
``@limiter.limit(...)``) can import the same instance without a circular
``app.main`` dependency.

Default limits: none (no global throttle). Per-route limits are applied
explicitly with the ``@limiter.limit("5/minute")`` decorator on the
sensitive endpoints (login, change-password) so the rest of the API
keeps its current unthrottled behaviour.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=[])
