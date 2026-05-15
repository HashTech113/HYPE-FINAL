from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from typing import Any

log = logging.getLogger(__name__)


class RealtimeBus:
    """In-process pub/sub bridge from backend writes to SSE subscribers.

    Publishers (attendance service, employee endpoints, camera workers)
    call `publish(kind, **payload)` synchronously from any thread. Each
    SSE subscriber owns an asyncio.Queue; messages are scheduled onto
    the captured event loop with `call_soon_threadsafe` so cross-thread
    publishes are safe.

    Payloads optionally include `company` so the SSE endpoint can drop
    irrelevant updates for HR users scoped to a single company.

    Failure isolation:
      A misbehaving subscriber (slow consumer, closed event loop, dead
      queue) is contained — its failure must NOT affect delivery to
      other subscribers, and we never lose unrelated subscriber state
      because one publish raised. Drops are counted and rate-limited
      logged so we can see when consumers are losing messages instead
      of silently degrading.
    """

    # How often (max) to log dropped-message warnings, regardless of
    # how many drops happened in between. Avoids log floods when a
    # subscriber is permanently slow.
    _DROP_LOG_INTERVAL_SEC = 30.0

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        # Per-subscriber drop counter, plus aggregate stats. The lock
        # protects increment/read since publishers are multi-threaded
        # but subscribers run on the single event loop.
        self._stats_lock = threading.Lock()
        self._drops_total: int = 0
        self._drops_per_subscriber: dict[int, int] = {}
        self._last_drop_log_at: float = 0.0

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=512)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)
        with self._stats_lock:
            self._drops_per_subscriber.pop(id(queue), None)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    def stats(self) -> dict[str, Any]:
        """Snapshot of bus health for /diagnostics endpoints. Cheap."""
        with self._stats_lock:
            return {
                "subscribers": len(self._subscribers),
                "drops_total": self._drops_total,
                "drops_per_subscriber": dict(self._drops_per_subscriber),
            }

    def publish(self, topic: str, **payload: Any) -> None:
        if self._loop is None or not self._subscribers:
            return
        try:
            payload_clean = {k: v for k, v in payload.items() if v is not None}
            msg = json.dumps({"topic": topic, **payload_clean}, default=str)
        except (TypeError, ValueError):
            log.exception("realtime_bus: could not serialize %s payload", topic)
            return
        # Iterate a SNAPSHOT of subscribers so concurrent (un)subscribe
        # can't mutate the set under us. Each subscriber's failure is
        # caught individually so one bad consumer can't starve siblings.
        dead: list[asyncio.Queue] = []
        for queue in list(self._subscribers):
            try:
                self._loop.call_soon_threadsafe(self._safe_put, queue, msg, id(queue))
            except RuntimeError:
                # Loop closed mid-publish, OR call_soon_threadsafe
                # rejected (rare on shutdown). Mark for removal.
                dead.append(queue)
            except Exception:
                # Should never happen — call_soon_threadsafe shouldn't
                # raise anything else — but if a future Python adds
                # new error types, don't let one subscriber's bug
                # prevent us from delivering to the rest.
                log.exception("realtime_bus: unexpected scheduling error for subscriber")
                dead.append(queue)
        for q in dead:
            self._subscribers.discard(q)

    def _safe_put(self, queue: asyncio.Queue, msg: str, sub_id: int) -> None:
        """Deliver `msg` to one subscriber. Called on the event loop.
        Drops oldest on overflow (slow-consumer policy) and increments
        the per-subscriber drop counter.
        """
        try:
            queue.put_nowait(msg)
            return
        except asyncio.QueueFull:
            # Slow consumer — drop oldest, push newest, count it.
            try:
                queue.get_nowait()
                queue.put_nowait(msg)
            except Exception:
                # Even drop-and-replace failed (queue closed?). Count
                # as drop and move on; never raise from here — this
                # runs on the event loop and an exception would be
                # logged as "task exception was never retrieved" and
                # leave the subscriber set in an undefined state.
                pass
            self._record_drop(sub_id)
        except Exception:
            # Any other exception (queue closed, etc.) is treated as
            # a drop. Same justification as above.
            log.exception("realtime_bus: put_nowait raised unexpectedly")
            self._record_drop(sub_id)

    def _record_drop(self, sub_id: int) -> None:
        with self._stats_lock:
            self._drops_total += 1
            self._drops_per_subscriber[sub_id] = self._drops_per_subscriber.get(sub_id, 0) + 1
            now = time.monotonic()
            if now - self._last_drop_log_at >= self._DROP_LOG_INTERVAL_SEC:
                self._last_drop_log_at = now
                log.warning(
                    "realtime_bus: dropping messages — total=%d, slowest_subscriber=%d msgs",
                    self._drops_total,
                    max(self._drops_per_subscriber.values(), default=0),
                )


bus = RealtimeBus()
