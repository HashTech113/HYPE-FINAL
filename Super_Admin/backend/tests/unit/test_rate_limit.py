"""EndpointRateLimiter — sliding-window per-IP guard.

Used on /auth/login, /auth/change-password, /cameras/preview*, and
now /employees/{id}/image. A regression here either DDoSes the
service (limiter too loose) or locks legit users out (too strict).
"""

from __future__ import annotations

import time
from unittest.mock import Mock

import pytest

from app.core.rate_limit import (
    EndpointRateLimiter,
    RateLimitError,
)

pytestmark = pytest.mark.unit


def _request(ip: str = "1.2.3.4") -> Mock:
    """Stand-in for a FastAPI Request — only `request.client.host` is
    consulted by the limiter."""
    req = Mock()
    req.client = Mock()
    req.client.host = ip
    return req


def test_first_request_passes() -> None:
    rl = EndpointRateLimiter(max_calls=3, window_seconds=60)
    rl(_request())  # no raise


def test_passes_until_limit_exceeded() -> None:
    rl = EndpointRateLimiter(max_calls=3, window_seconds=60)
    for _ in range(3):
        rl(_request())
    with pytest.raises(RateLimitError):
        rl(_request())


def test_window_resets_after_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    """After the window passes, the budget refills."""
    rl = EndpointRateLimiter(max_calls=2, window_seconds=10)

    fake_now = [1000.0]

    def fake_monotonic() -> float:
        return fake_now[0]

    monkeypatch.setattr(time, "monotonic", fake_monotonic)
    rl(_request())
    rl(_request())
    with pytest.raises(RateLimitError):
        rl(_request())

    # Jump past the window.
    fake_now[0] += 11.0
    # Now allowed again.
    rl(_request())


def test_per_ip_independent_budgets() -> None:
    """One client's traffic must not deny another's. Per-key
    bookkeeping is the whole point of this limiter."""
    rl = EndpointRateLimiter(max_calls=2, window_seconds=60)
    rl(_request("1.1.1.1"))
    rl(_request("1.1.1.1"))
    # First IP exhausted.
    with pytest.raises(RateLimitError):
        rl(_request("1.1.1.1"))
    # Different IP still allowed.
    rl(_request("2.2.2.2"))
    rl(_request("2.2.2.2"))


def test_missing_client_host_falls_back_to_unknown() -> None:
    """A request with no client (e.g. mid-test, no transport) must
    not crash the limiter — bucket all such requests under 'unknown'."""
    rl = EndpointRateLimiter(max_calls=2, window_seconds=60)
    req = Mock()
    req.client = None  # type: ignore[assignment]
    rl(req)
    rl(req)
    with pytest.raises(RateLimitError):
        rl(req)
