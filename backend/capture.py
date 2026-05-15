"""Camera → local SQLite (durable sink) → optional remote replication.

Runs on the machine with LAN access to the cameras. Pulls FaceInfo records
from each camera's API and writes them **directly** into the local DB via
``record_capture()``. The local DB is the durable outbox — even when the
remote ingest target is unreachable, captures are never lost, and
``replay_to_railway.py`` propagates them to Railway later.

Modes
-----
* **Multi-camera**: when the ``cameras`` table contains rows with
  ``connection_status='connected'``, capture spawns one worker thread per
  camera. Each worker has its own ``CameraClient``, login session, and
  in-process dedup cache. Events are tagged with ``camera_id`` so two
  cameras emitting the same SnapId don't collide on the
  ``UNIQUE(image_path)`` constraint.

* **Legacy single-camera**: when no connected cameras are found in the
  table, capture falls back to the old single-camera path driven by the
  ``CAMERA_HOST`` / ``CAMERA_USER`` / ``CAMERA_PASS`` env vars. ARP
  rediscovery (``CAMERA_MAC`` / ``CAMERA_DISCOVERY_SUBNETS``) is enabled
  only in this mode.

Optional remote replication
---------------------------
``INGEST_API_URL`` (comma-separated) lets every worker also POST each
event to remote ingest endpoints in parallel for low-latency replication.
Localhost URLs are stripped automatically because the direct DB write
covers the local backend already. ``INGEST_API_KEY`` must match the
server's ``INGEST_API_KEY`` env var; without it the remote will reject
the POST with 401.

Frame rate cap
--------------
Each worker's poll interval is at least 1.0s (configurable upward via
``CAPTURE_INTERVAL_SECONDS``), keeping CPU bounded even with many
cameras.
"""

from __future__ import annotations

import logging
import os
import queue
import signal
import sys
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlparse

import requests

from sqlalchemy import text

from app.config import CAPTURE_INTERVAL_SECONDS
from app.db import session_scope
from app.services import logs as logs_service
from app.services import snapshots
from app.services.camera import CameraClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("capture")

RECONNECT_BACKOFF_SECONDS = 5.0
# (connect, read) — short connect (fail-fast on dead host / DNS) + bounded
# read so a stalled SSL handshake or half-closed socket can never park the
# sync worker for more than INGEST_TIMEOUT_SECONDS[1] per attempt.
# A previous incident saw capture.py wedge for >70 minutes on a single
# CLOSE_WAIT socket because the old single-int timeout didn't enforce a
# read deadline cleanly.
INGEST_TIMEOUT_SECONDS: tuple[float, float] = (5.0, 15.0)
INGEST_RETRY_BACKOFF = 1.0
INGEST_RETRY_MAX = 2
SEEN_SNAP_IDS_MAX = 2000
# How far back to seed seen_ids from the local DB at startup. Anything
# older has aged out of the camera's live alarm buffer anyway.
SEEN_REWARM_HOURS = 1
# Per-worker minimum poll interval. Caps CPU at "1 frame/sec/camera"
# regardless of how aggressively CAPTURE_INTERVAL_SECONDS is tuned.
MIN_POLL_INTERVAL_SECONDS = 1.0
# Bounded queue between camera workers and the remote sync worker. If
# remote sync stalls long enough to fill this, oldest payloads are
# dropped (with a warning) — replay_to_railway.py covers them later from
# the local DB, which is the durable source of truth.
SYNC_QUEUE_MAXSIZE = 2000
# Heartbeat thread cadence + thresholds.
HEARTBEAT_INTERVAL_SECONDS = 60.0
NO_EVENT_WARN_SECONDS = 600.0   # 10 min: no faces seen — investigate camera/coverage
NO_POLL_WARN_SECONDS = 180.0    # 3 min: poll loop hasn't completed — likely stuck

_LOCALHOST_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def _is_localhost_url(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return host in _LOCALHOST_HOSTS


def _resolve_remote_targets() -> list[str]:
    raw = os.getenv("INGEST_API_URL", "").strip()
    if not raw:
        return []
    targets = [u.strip() for u in raw.split(",") if u.strip()]
    remote: list[str] = []
    for url in targets:
        if _is_localhost_url(url):
            log.info(
                "INGEST_API_URL: skipping local target %s — capture writes "
                "directly to the local DB (no HTTP round-trip needed)",
                url,
            )
            continue
        remote.append(url)
    return remote


REMOTE_TARGETS = _resolve_remote_targets()
INGEST_API_KEY = os.getenv("INGEST_API_KEY", "").strip()


# ---- background sync queue + liveness state ---------------------------------
#
# All remote sync work happens off the camera-worker threads via this queue.
# Camera workers ONLY enqueue; a single dedicated sync thread drains it. That
# way a hung POST (e.g. SSL handshake stall, half-closed socket) can never
# block frame processing or local DB writes.
#
# The local DB write happens BEFORE enqueueing, so even if we drop or fail
# remote sync we never lose data — replay_to_railway.py replays from the
# local DB on a separate loop.

_SYNC_QUEUE: "queue.Queue[dict]" = queue.Queue(maxsize=SYNC_QUEUE_MAXSIZE)
_SYNC_STATS = {"queued_total": 0, "ok": 0, "fail": 0, "dropped": 0}
_SYNC_STATS_LOCK = threading.Lock()

# Per-worker liveness state, keyed by client.label. Read by the heartbeat
# thread, written by camera workers via ``_record_heartbeat``. Times are
# ``time.monotonic()`` floats so wall-clock drift / NTP jumps can't mislead
# the warning logic.
_HEARTBEAT_LOCK = threading.Lock()
_HEARTBEAT_STATE: dict[str, dict] = {}


def _enqueue_remote(payload: dict) -> None:
    """Non-blocking handoff to the sync thread. Drops oldest on overflow.

    Never raises. Dropped events are surfaced periodically via a warning
    log; the local DB still has them, so replay covers the gap."""
    if not REMOTE_TARGETS:
        return
    try:
        _SYNC_QUEUE.put_nowait(payload)
        with _SYNC_STATS_LOCK:
            _SYNC_STATS["queued_total"] += 1
    except queue.Full:
        # Bump the dropped counter and warn periodically. Fast path: bail
        # without holding the lock past the increment.
        with _SYNC_STATS_LOCK:
            _SYNC_STATS["dropped"] += 1
            count = _SYNC_STATS["dropped"]
        # Log once per 50 drops so we don't spam during a long outage.
        if count == 1 or count % 50 == 0:
            log.warning(
                "remote sync queue full (size=%d, max=%d) — dropped %d events "
                "total; replay_to_railway.py will backfill from local DB.",
                _SYNC_QUEUE.qsize(), SYNC_QUEUE_MAXSIZE, count,
            )


def _sync_worker(stop: dict) -> None:
    """Background thread: drain ``_SYNC_QUEUE`` and POST to remotes.

    Failures here NEVER touch capture: the queue isolates camera workers
    from network state. Each iteration is wrapped in try/except so a single
    malformed payload or transient exception can't kill the thread."""
    log.info("sync-worker thread started; targets=%s", REMOTE_TARGETS or "(none)")
    session = requests.Session()
    while not stop["flag"]:
        try:
            payload = _SYNC_QUEUE.get(timeout=1.0)
        except queue.Empty:
            continue
        try:
            ok, fail = _replicate_remote(session, payload)
            with _SYNC_STATS_LOCK:
                _SYNC_STATS["ok"] += ok
                _SYNC_STATS["fail"] += fail
        except Exception:
            # Catch-all: a bug in _replicate_remote or a JSON-encode failure
            # must not take the sync thread down. Log and keep draining.
            log.exception("sync-worker: unexpected error replicating event; continuing")
            with _SYNC_STATS_LOCK:
                _SYNC_STATS["fail"] += 1
        finally:
            try:
                _SYNC_QUEUE.task_done()
            except ValueError:
                pass
    log.info("sync-worker thread exiting")


def _record_heartbeat(label: str, *, faces: int = 0, polled: bool = False) -> None:
    """Camera workers call this after every poll cycle. ``polled=True`` means
    ``client.fetch_alarms()`` returned (success or empty list). ``faces`` is
    how many events that poll yielded."""
    now = time.monotonic()
    with _HEARTBEAT_LOCK:
        s = _HEARTBEAT_STATE.setdefault(
            label,
            {
                "last_poll_ts": None,
                "last_event_ts": None,
                "polls_completed": 0,
                "events_processed": 0,
            },
        )
        if polled:
            s["last_poll_ts"] = now
            s["polls_completed"] += 1
        if faces > 0:
            s["last_event_ts"] = now
            s["events_processed"] += faces


def _heartbeat_thread(stop: dict, expected_workers: list[str]) -> None:
    """Logs a periodic liveness line for every worker + an aggregate sync
    queue line. Warns when a worker has stopped polling or stopped seeing
    events for longer than the configured thresholds.

    Runs independently of the camera workers and the sync worker, so even
    if one of them deadlocks this still ticks and surfaces the symptom."""
    log.info(
        "heartbeat thread started (interval=%.0fs, no_event_warn=%.0fs, no_poll_warn=%.0fs)",
        HEARTBEAT_INTERVAL_SECONDS, NO_EVENT_WARN_SECONDS, NO_POLL_WARN_SECONDS,
    )
    started = time.monotonic()
    while not stop["flag"]:
        now = time.monotonic()
        with _HEARTBEAT_LOCK:
            snapshot = {k: dict(v) for k, v in _HEARTBEAT_STATE.items()}
        for label in expected_workers:
            s = snapshot.get(label) or {}
            polls = int(s.get("polls_completed") or 0)
            events = int(s.get("events_processed") or 0)
            last_poll = s.get("last_poll_ts")
            last_event = s.get("last_event_ts")
            poll_age = (now - last_poll) if last_poll else (now - started)
            event_age = (now - last_event) if last_event else (now - started)
            log.info(
                "[%s] heartbeat polls=%d events=%d poll_age=%.0fs event_age=%.0fs",
                label, polls, events, poll_age, event_age,
            )
            # Only warn after the worker has had a fair chance to start polling.
            if last_poll is None and (now - started) > NO_POLL_WARN_SECONDS:
                log.warning(
                    "[%s] no successful poll since startup (%.0fs ago) — worker may "
                    "be stuck on login or DNS",
                    label, now - started,
                )
            elif last_poll is not None and poll_age > NO_POLL_WARN_SECONDS:
                log.warning(
                    "[%s] no successful poll for %.0fs — worker likely stuck "
                    "(camera unreachable / SSL hang / blocked syscall)",
                    label, poll_age,
                )
            # Idle warning: only meaningful once we've been running a while
            # AND the worker IS polling successfully (so we know the camera
            # link is alive but no faces are being seen).
            if (
                last_poll is not None
                and event_age > NO_EVENT_WARN_SECONDS
                and (now - started) > NO_EVENT_WARN_SECONDS
            ):
                log.warning(
                    "[%s] no face events for %.0fs — verify camera coverage / "
                    "that people are walking past it",
                    label, event_age,
                )
        with _SYNC_STATS_LOCK:
            stats = dict(_SYNC_STATS)
        log.info(
            "sync-queue depth=%d total_queued=%d ok=%d fail=%d dropped=%d",
            _SYNC_QUEUE.qsize(),
            stats["queued_total"], stats["ok"], stats["fail"], stats["dropped"],
        )
        # Sleep with stop polling so shutdown is responsive.
        slept = 0.0
        while slept < HEARTBEAT_INTERVAL_SECONDS and not stop["flag"]:
            chunk = min(0.5, HEARTBEAT_INTERVAL_SECONDS - slept)
            time.sleep(chunk)
            slept += chunk
    log.info("heartbeat thread exiting")


# ---- camera event extraction -----------------------------------------------

def _extract_image_b64(item: dict) -> Optional[str]:
    for field in snapshots.IMAGE_FIELDS:
        v = item.get(field)
        if isinstance(v, str) and v:
            return v
    return None


def _extract_timestamp(item: dict) -> datetime:
    for field in ("StartTime", "EndTime"):
        ts = snapshots._to_utc(item.get(field))
        if ts is not None:
            return ts
    return datetime.now(timezone.utc)


def _extract_name(item: dict) -> str:
    raw = item.get("Name")
    if not isinstance(raw, str) or not raw.strip():
        return "Unknown"
    return snapshots.sanitize_name(raw).replace("_", " ")


def _extract_snap_id(item: dict) -> Optional[str]:
    for field in ("SnapId", "Id", "GrpId"):
        v = item.get(field)
        if v is not None and str(v):
            return str(v)
    return None


# ---- remote replication ----------------------------------------------------

def _post_one(session: requests.Session, url: str, payload: dict) -> bool:
    """POST to a single target with bounded retry. Never raises."""
    headers = {"X-API-Key": INGEST_API_KEY} if INGEST_API_KEY else {}
    for attempt in range(1, INGEST_RETRY_MAX + 1):
        try:
            resp = session.post(url, json=payload, headers=headers, timeout=INGEST_TIMEOUT_SECONDS)
            if resp.status_code == 200:
                return True
            log.warning(
                "remote replicate %s returned %d (attempt %d/%d) body=%s",
                url, resp.status_code, attempt, INGEST_RETRY_MAX, resp.text[:200],
            )
        except requests.RequestException as e:
            log.warning(
                "remote replicate %s failed (attempt %d/%d): %s",
                url, attempt, INGEST_RETRY_MAX, e,
            )
        if attempt < INGEST_RETRY_MAX:
            time.sleep(INGEST_RETRY_BACKOFF * attempt)
    return False


def _replicate_remote(session: requests.Session, payload: dict) -> tuple[int, int]:
    """Fire-and-tolerate POST to every remote target. Returns (ok, fail).
    Failures are non-fatal: replay_to_railway.py covers anything missed."""
    if not REMOTE_TARGETS:
        return 0, 0
    ok = fail = 0
    for url in REMOTE_TARGETS:
        if _post_one(session, url, payload):
            ok += 1
        else:
            fail += 1
    return ok, fail


# ---- dedup cache -----------------------------------------------------------

def _seed_seen_ids(camera_id: Optional[str]) -> tuple[deque[str], set[str]]:
    """Re-warm the in-process dedup cache from the local DB so a capture
    restart doesn't re-fetch and re-write the entire camera buffer. The
    cache is **scoped to one camera** in multi-camera mode — two cameras
    can legitimately emit the same SnapId, and we don't want one worker's
    cache to dedupe another's events.

    For env-fallback (camera_id is None), we look at rows where
    ``camera_id IS NULL`` (legacy + fallback writes) so the cache rebuilds
    cleanly. The DB UNIQUE(image_path) constraint is still the real
    safety net; this is just an optimization to keep startup quiet."""
    seen_ids: deque[str] = deque(maxlen=SEEN_SNAP_IDS_MAX)
    seen_set: set[str] = set()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=SEEN_REWARM_HOURS)
    try:
        with session_scope() as session:
            if camera_id:
                rows = session.execute(
                    text(
                        "SELECT image_path FROM snapshot_logs "
                        "WHERE timestamp >= :cutoff AND camera_id = :camera_id "
                        "ORDER BY id DESC LIMIT :limit"
                    ),
                    {"cutoff": cutoff, "camera_id": camera_id, "limit": SEEN_SNAP_IDS_MAX},
                ).mappings().all()
                expected_prefix = f"ingest_{camera_id}_"
            else:
                rows = session.execute(
                    text(
                        "SELECT image_path FROM snapshot_logs "
                        "WHERE timestamp >= :cutoff AND camera_id IS NULL "
                        "ORDER BY id DESC LIMIT :limit"
                    ),
                    {"cutoff": cutoff, "limit": SEEN_SNAP_IDS_MAX},
                ).mappings().all()
                expected_prefix = "ingest_"
    except Exception:
        log.exception("seed_seen_ids: DB read failed; starting with empty cache")
        return seen_ids, seen_set
    for r in rows:
        path = r["image_path"]
        if path.startswith(expected_prefix) and path.endswith(".jpg"):
            sid = path[len(expected_prefix):-len(".jpg")]
            # Skip the content-hash form (no SnapId was available) — only
            # the bare-id form maps cleanly back to camera SnapIds.
            if "_" not in sid and sid not in seen_set:
                seen_ids.append(sid)
                seen_set.add(sid)
    return seen_ids, seen_set


# ---- per-worker poll loop --------------------------------------------------

def _process_event(
    item: dict,
    *,
    client: CameraClient,
    seen_ids: deque[str],
    seen_set: set[str],
) -> str:
    """Insert one camera event into the local DB and hand off to the sync
    queue. Returns status — one of ``queued``, ``duplicate``, ``skipped``.

    Network sync is decoupled: ``_enqueue_remote`` is non-blocking, so a
    stalled remote target can never delay the camera worker that called us.
    The local DB write happens BEFORE the enqueue, so any payload that
    drops out of the queue (overflow / sync-thread failure) is still
    durably recorded locally and will be picked up by replay_to_railway.py.
    """
    snap_id = _extract_snap_id(item)
    if snap_id and snap_id in seen_set:
        return "duplicate"

    image_b64 = _extract_image_b64(item)
    if not image_b64:
        return "skipped"

    name = _extract_name(item)
    ts_iso = _extract_timestamp(item).isoformat()
    image_path = snapshots.synthesize_image_path(
        snap_id, image_b64, ts_iso, camera_id=client.camera_id or None
    )

    try:
        stored = logs_service.record_capture(
            name=name,
            timestamp_iso=ts_iso,
            image_path=image_path,
            image_data=image_b64,
            camera_id=client.camera_id or None,
        )
    except Exception:
        log.exception(
            "[%s] local DB write failed for snap_id=%s — keeping seen_ids "
            "untouched so the next poll retries",
            client.label, snap_id,
        )
        return "skipped"

    if stored:
        log.debug("[%s] event queued (DB) snap_id=%s name=%s", client.label, snap_id, name)
        status = "queued"
    else:
        status = "duplicate"

    # Non-blocking — never blocks on the network. Failures here are silent
    # because the local DB row above is the durable record; replay covers
    # anything the sync thread drops or fails to deliver.
    _enqueue_remote({
        "name": name,
        "timestamp": ts_iso,
        "image_base64": image_b64,
        "snap_id": snap_id,
        "camera_id": client.camera_id or None,
    })

    if snap_id:
        if len(seen_ids) == seen_ids.maxlen:
            seen_set.discard(seen_ids[0])
        seen_ids.append(snap_id)
        seen_set.add(snap_id)

    return status


def _worker_loop(client: CameraClient, stop: dict) -> None:
    """Long-running poll loop for a single camera. Runs until ``stop['flag']``
    is set by the signal handler.

    Remote sync runs on a separate thread; this loop only touches the camera
    HTTP API and the local DB, plus a non-blocking enqueue. Every successful
    poll cycle (faces or empty) records a heartbeat so an external observer
    (the heartbeat thread) can tell whether the worker is healthy."""
    log.info(
        "[%s] worker starting (id=%s, location=%s)",
        client.label, client.camera_id or "(legacy)", client.camera_location or "—",
    )
    seen_ids, seen_set = _seed_seen_ids(client.camera_id or None)
    log.info("[%s] seeded seen_ids cache with %d recent snap_ids", client.label, len(seen_set))

    poll_interval = max(MIN_POLL_INTERVAL_SECONDS, CAPTURE_INTERVAL_SECONDS)
    # Pre-register so the heartbeat thread sees this label even before the
    # first poll completes — useful for "stuck on login" warnings.
    _record_heartbeat(client.label)

    while not stop["flag"]:
        try:
            faces = client.fetch_alarms()
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            log.warning("[%s] Camera HTTP error %s — re-logging in", client.label, status)
            client.invalidate()
            time.sleep(RECONNECT_BACKOFF_SECONDS)
            continue
        except requests.RequestException as e:
            log.warning("[%s] Camera request failed: %s — retrying", client.label, e)
            client.invalidate()
            time.sleep(RECONNECT_BACKOFF_SECONDS)
            continue
        except Exception:
            log.exception("[%s] Camera iteration failed (continuing)", client.label)
            client.invalidate()
            time.sleep(RECONNECT_BACKOFF_SECONDS)
            continue

        n_faces = len(faces)
        queued = duplicate = skipped = 0
        for item in faces:
            try:
                status = _process_event(
                    item, client=client, seen_ids=seen_ids, seen_set=seen_set,
                )
            except Exception:
                # Defensive: a bug in extraction / enqueue must not crash the
                # poll loop. Local DB writes inside _process_event already
                # have their own try/except.
                log.exception("[%s] _process_event crashed; skipping item", client.label)
                skipped += 1
                continue
            if status == "queued":
                queued += 1
            elif status == "duplicate":
                duplicate += 1
            else:
                skipped += 1

        # Record heartbeat AFTER processing so faces is the count we actually
        # tried to handle, not the count fetched.
        _record_heartbeat(client.label, faces=queued, polled=True)

        if n_faces:
            log.info(
                "[%s] poll faces=%d queued=%d duplicate=%d skipped=%d sync_qsize=%d",
                client.label, n_faces, queued, duplicate, skipped, _SYNC_QUEUE.qsize(),
            )

        # `time.sleep` is interruptible by signals on Linux/macOS; capped so
        # workers don't oversleep when SIGTERM arrives mid-cycle.
        slept = 0.0
        while slept < poll_interval and not stop["flag"]:
            chunk = min(0.5, poll_interval - slept)
            time.sleep(chunk)
            slept += chunk

    log.info("[%s] worker exiting", client.label)


# ---- mode selection --------------------------------------------------------

def _load_db_workers() -> list[CameraClient]:
    """Load every camera with ``connection_status='connected'`` and return
    a configured ``CameraClient`` for each. Empty list (and a logged
    reason) when the table is empty, no rows are connected, or
    CAMERA_SECRET_KEY isn't set so passwords can't be decrypted."""
    try:
        from app.services.cameras import connected_cameras_with_credentials
    except Exception:
        log.exception("could not import cameras service; falling back to legacy mode")
        return []

    try:
        pairs = connected_cameras_with_credentials()
    except Exception as exc:
        # Most likely cause: CAMERA_SECRET_KEY is unset. Surface clearly.
        log.error("could not load cameras from DB: %s", exc)
        return []

    clients: list[CameraClient] = []
    for cam, password in pairs:
        clients.append(
            CameraClient(
                host=cam.ip,
                user=cam.username,
                password=password,
                camera_id=cam.id,
                camera_name=cam.name,
                camera_location=cam.location,
                auto_discovery_enabled=cam.auto_discovery_enabled,
            )
        )
    return clients


def run() -> int:
    stop = {"flag": False}

    def _handle_signal(signum, _frame):
        log.info("Received signal %s — shutting down", signum)
        stop["flag"] = True

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    if REMOTE_TARGETS:
        log.info("local DB write enabled; remote replication targets=%s", REMOTE_TARGETS)
        if not INGEST_API_KEY:
            log.warning(
                "INGEST_API_KEY is unset — remote /api/ingest calls will be "
                "rejected with 401. Set INGEST_API_KEY to the same value as "
                "the server-side env var."
            )
    else:
        log.info(
            "local DB write enabled; no remote replication (INGEST_API_URL unset). "
            "replay_to_railway.py will sync to Railway out-of-band."
        )

    db_clients = _load_db_workers()
    if db_clients:
        log.info("Multi-camera mode: %d connected cameras loaded from DB", len(db_clients))
        for c in db_clients:
            log.info(
                "  - %s @ %s [%s] (camera_id=%s)",
                c.camera_name or "(unnamed)", c.base_url,
                c.camera_location or "no location", c.camera_id,
            )
        return _run_workers(db_clients, stop)

    log.info("Legacy single-camera mode: no connected cameras in DB, falling back to env config")
    legacy = CameraClient()  # env-driven defaults; rediscovery enabled
    return _run_workers([legacy], stop)


def _run_workers(clients: list[CameraClient], stop: dict) -> int:
    worker_threads: list[threading.Thread] = []
    expected_labels = [c.label for c in clients]

    # Auxiliary threads start FIRST so the heartbeat is logging from the
    # very first second — even if a camera-worker stalls on initial login,
    # the heartbeat will surface the symptom.
    aux_threads: list[threading.Thread] = []
    if REMOTE_TARGETS:
        sync_t = threading.Thread(
            target=_sync_worker, args=(stop,), daemon=True, name="sync-worker",
        )
        sync_t.start()
        aux_threads.append(sync_t)
    else:
        log.info("sync-worker not started (no REMOTE_TARGETS configured)")

    hb_t = threading.Thread(
        target=_heartbeat_thread,
        args=(stop, expected_labels),
        daemon=True,
        name="heartbeat",
    )
    hb_t.start()
    aux_threads.append(hb_t)

    for client in clients:
        name = f"capture-{client.camera_id or 'legacy'}"
        t = threading.Thread(target=_worker_loop, args=(client, stop), daemon=True, name=name)
        t.start()
        worker_threads.append(t)

    # Park the main thread until shutdown. We poll instead of join() so the
    # signal handler can trip stop['flag'] without first having to wake one
    # specific thread. Aux threads are not part of the liveness check —
    # capture is "alive" as long as at least one camera worker is alive;
    # the heartbeat / sync threads exiting unexpectedly is logged but
    # doesn't terminate the process.
    try:
        while not stop["flag"] and any(t.is_alive() for t in worker_threads):
            time.sleep(0.5)
    finally:
        stop["flag"] = True
        for t in worker_threads:
            t.join(timeout=RECONNECT_BACKOFF_SECONDS + 1.0)
        for t in aux_threads:
            t.join(timeout=2.0)

    log.info("Capture loop exited")
    return 0


if __name__ == "__main__":
    sys.exit(run())
