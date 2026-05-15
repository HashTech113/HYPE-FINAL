from __future__ import annotations

import queue
import threading
from collections.abc import Callable

from app.core.logger import get_logger

log = get_logger(__name__)

Job = Callable[[], None]


class WorkerPool:
    """Named, isolated background worker pool.

    Each pool owns its own queue, its own worker thread(s), and its own
    lifecycle. Saturation, worker death, or job exceptions in one pool
    cannot affect any other pool — the camera workers split their
    background work across multiple pools so that a flood of low-value
    jobs (e.g. unknown-face captures when many unenrolled people are on
    camera) cannot starve high-value jobs (recognized-employee
    attendance writes).

    The detector hot path must NEVER block on background work, so when
    a pool's queue is full the new job is dropped with a warning rather
    than blocked. Producers can react (e.g. the attendance path resets
    its cooldown so the next frame retries).

    Multiple worker threads only help for I/O-bound jobs (DB writes,
    snapshot file writes) where the GIL is released during syscalls;
    they buy nothing for CPU-bound work.
    """

    def __init__(self, name: str, workers: int = 1, capacity: int = 512) -> None:
        self.name = name
        self.capacity = capacity
        self._queue: queue.Queue[Job | None] = queue.Queue(maxsize=capacity)
        self._stop = threading.Event()
        self._threads = [
            threading.Thread(
                target=self._loop,
                name=f"{name}-{i}",
                daemon=True,
            )
            for i in range(max(1, workers))
        ]
        for t in self._threads:
            t.start()
        log.info(
            "WorkerPool %s started (workers=%d, capacity=%d)",
            name,
            len(self._threads),
            capacity,
        )

    def submit(self, fn: Job) -> bool:
        """Enqueue a job. Returns False if the pool's queue is full."""
        try:
            self._queue.put_nowait(fn)
            return True
        except queue.Full:
            log.warning(
                "WorkerPool %s queue full (capacity %d) — dropping job",
                self.name,
                self.capacity,
            )
            return False

    def stop(self) -> None:
        self._stop.set()
        # One sentinel per worker so each thread wakes and exits.
        for _ in self._threads:
            try:
                self._queue.put_nowait(None)
            except queue.Full:
                pass
        for t in self._threads:
            t.join(timeout=5.0)

    def depth(self) -> int:
        return self._queue.qsize()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                fn = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue
            if fn is None:
                break
            try:
                fn()
            except Exception:
                log.exception("WorkerPool %s job raised", self.name)


# --- Pool registry --------------------------------------------------------
# Independent pools per job type. A pool is created lazily on first
# `get_pool(name)`; subsequent calls return the same instance. The
# defaults below are tuned for the camera worker's job mix:
#
#   attendance       — high priority, must not be dropped under load.
#                      2 threads for I/O parallelism (DB write +
#                      snapshot file write) and a roomy queue so a
#                      brief I/O blip can't lose an actual punch-in.
#   unknown_capture  — bursty when many unenrolled people are visible.
#                      Drops are acceptable; the next frame re-attempts.
#                      Isolated from attendance so this burst can't
#                      block a recognized employee event.
#   auto_enroll      — best-effort embedding refresh after a
#                      high-confidence match. Lowest priority, smallest
#                      queue.
_POOL_DEFAULTS: dict[str, dict[str, int]] = {
    # `workers=1` for attendance is deliberate: the recompute() pipeline
    # reads-then-writes the daily_attendance row for an employee/date,
    # and the field-update phase is not safe for concurrent writes to
    # the same employee/day. Scaling beyond 1 would need either
    # per-employee `SELECT ... FOR UPDATE` row locking or a per-employee
    # in-process lock — leaving that for later. The roomy capacity
    # ensures a brief I/O blip can never cause us to drop an actual
    # punch-in.
    "attendance": {"workers": 1, "capacity": 1024},
    "unknown_capture": {"workers": 1, "capacity": 256},
    "auto_enroll": {"workers": 1, "capacity": 64},
}

_POOLS: dict[str, WorkerPool] = {}
_LOCK = threading.Lock()


def get_pool(name: str) -> WorkerPool:
    """Get-or-create a named pool. First call uses the defaults from
    `_POOL_DEFAULTS` (or workers=1, capacity=512 for unrecognized names);
    subsequent calls return the existing pool unchanged.
    """
    with _LOCK:
        pool = _POOLS.get(name)
        if pool is None:
            cfg = _POOL_DEFAULTS.get(name, {"workers": 1, "capacity": 512})
            pool = WorkerPool(name, **cfg)
            _POOLS[name] = pool
        return pool


def shutdown_all_pools() -> None:
    """Stop every pool created in this process. Called from the FastAPI
    lifespan exit so background threads release their DB sessions before
    the engine is disposed.
    """
    with _LOCK:
        pools = list(_POOLS.values())
        _POOLS.clear()
    for p in pools:
        p.stop()


def pool_depths() -> dict[str, int]:
    """Snapshot of current queue depth per pool. Useful for /health
    diagnostics and for spotting saturation before it causes drops.
    """
    with _LOCK:
        return {name: p.depth() for name, p in _POOLS.items()}
