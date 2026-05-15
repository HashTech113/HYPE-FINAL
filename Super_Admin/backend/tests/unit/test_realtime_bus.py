"""RealtimeBus — failure isolation between subscribers.

The bus is a critical liveness path: an in-process pub/sub from
camera workers / API handlers to SSE clients. A single misbehaving
subscriber must not affect siblings.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.services.realtime_bus import RealtimeBus

pytestmark = pytest.mark.unit


@pytest.fixture
async def bus_with_loop() -> RealtimeBus:
    bus = RealtimeBus()
    bus.bind_loop(asyncio.get_event_loop())
    return bus


def test_publish_with_no_subscribers_is_noop() -> None:
    bus = RealtimeBus()
    # No loop bound, no subscribers — must not raise.
    bus.publish("test", payload="x")
    assert bus.stats()["drops_total"] == 0


@pytest.mark.asyncio
async def test_publish_delivers_to_all_subscribers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sanity: a normal publish reaches every subscribed queue."""
    pytest.importorskip("pytest_asyncio", reason="asyncio test fixture")

    bus = RealtimeBus()
    bus.bind_loop(asyncio.get_running_loop())

    q1 = await bus.subscribe()
    q2 = await bus.subscribe()
    bus.publish("attendance_event", employee_id=1)
    await asyncio.sleep(0)  # let call_soon_threadsafe drain

    msg1 = await asyncio.wait_for(q1.get(), timeout=1.0)
    msg2 = await asyncio.wait_for(q2.get(), timeout=1.0)
    assert json.loads(msg1)["topic"] == "attendance_event"
    assert json.loads(msg2)["topic"] == "attendance_event"


def test_stats_snapshot_shape() -> None:
    bus = RealtimeBus()
    s = bus.stats()
    assert {"subscribers", "drops_total", "drops_per_subscriber"}.issubset(s)
    assert s["subscribers"] == 0
    assert s["drops_total"] == 0
    assert s["drops_per_subscriber"] == {}


def test_record_drop_increments_counters() -> None:
    """Direct test of the drop bookkeeping — guards against regressions
    where a refactor stops counting."""
    bus = RealtimeBus()
    fake_sub_id = 12345
    bus._record_drop(fake_sub_id)
    bus._record_drop(fake_sub_id)
    bus._record_drop(99999)

    s = bus.stats()
    assert s["drops_total"] == 3
    assert s["drops_per_subscriber"][fake_sub_id] == 2
    assert s["drops_per_subscriber"][99999] == 1


def test_unsubscribe_clears_per_subscriber_drop_counter() -> None:
    """Drop counters keyed on `id(queue)` — unsubscribing should
    clean up so we don't leak unbounded memory in the stats dict
    over a long uptime with many short-lived subscribers."""
    bus = RealtimeBus()
    q: asyncio.Queue = asyncio.Queue()
    bus._subscribers.add(q)
    bus._record_drop(id(q))
    assert id(q) in bus.stats()["drops_per_subscriber"]
    bus.unsubscribe(q)
    assert id(q) not in bus.stats()["drops_per_subscriber"]


def test_publish_with_unserializable_payload_logs_no_raise() -> None:
    """A publisher passing something json doesn't know how to encode
    must NOT crash — we want to lose ONE message, not crash the
    whole subsystem."""
    bus = RealtimeBus()
    bus.bind_loop(asyncio.new_event_loop())

    class Unserializable:
        pass

    # Should not raise.
    bus.publish("topic", payload=Unserializable())
    # No subscribers to check, but the fact that we didn't raise IS
    # the assertion. Drops_total stays 0 because nothing was delivered.
    assert bus.stats()["drops_total"] == 0
