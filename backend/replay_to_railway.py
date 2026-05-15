"""Backfill local snapshot_logs + employees to a remote ingest URL.

Usage:
    # one-shot
    python replay_to_railway.py --target <URL>

    # continuous loop (re-scan every 300s, auto-heal any gaps)
    python replay_to_railway.py --target <URL> --loop 300

Two tables get synced on every pass:

1. snapshot_logs — append-only; the remote's UNIQUE(image_path) makes it
   idempotent. We derive snap_id from the local image_path so the remote
   reconstructs the same image_path and dedup works end-to-end.

2. employees — one-way local → remote upsert: POST if id not present,
   PUT if fields differ, skip if identical. Local is source of truth;
   edits made only on the deployed side will be overwritten within one
   loop pass. Deletions never propagate (safer). Disable with
   --no-sync-employees.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import requests
from sqlalchemy import text

from app.db import session_scope

INGEST_API_KEY = os.getenv("INGEST_API_KEY", "").strip()
_INGEST_HEADERS = {"X-API-Key": INGEST_API_KEY} if INGEST_API_KEY else {}


def extract_snap_id(image_path: str, camera_id: str | None = None) -> str | None:
    """Recover the camera-side SnapId from the local image_path so the remote
    server reconstructs the same path. Multi-camera rows use the form
    ``ingest_<camera_id>_<snap_id>.jpg``; legacy rows use ``ingest_<snap_id>.jpg``.
    Content-hash paths (no SnapId at capture time) contain extra underscores
    and we return None to let the remote rebuild from the image bytes."""
    if not (image_path.startswith("ingest_") and image_path.endswith(".jpg")):
        return None
    raw = image_path[len("ingest_"):-len(".jpg")]
    if camera_id and raw.startswith(f"{camera_id}_"):
        raw = raw[len(camera_id) + 1:]
    # Bare-id form is alphanumeric without separators; anything containing
    # '_' is a timestamp+content-hash path and cannot be turned back into a
    # SnapId. Returning None makes the remote use the same content hash.
    if "_" in raw:
        return None
    return raw


RETRY_MAX = 3
RETRY_BACKOFF = 2.0


def post_with_retry(session: requests.Session, url: str, payload: dict, timeout: float) -> tuple[bool, bool]:
    """Returns (ok, stored). On transient 5xx / network error retries up to RETRY_MAX."""
    for attempt in range(1, RETRY_MAX + 1):
        try:
            resp = session.post(url, json=payload, headers=_INGEST_HEADERS, timeout=timeout)
        except requests.RequestException:
            if attempt < RETRY_MAX:
                time.sleep(RETRY_BACKOFF * attempt)
                continue
            return False, False
        if resp.status_code == 200:
            return True, bool(resp.json().get("stored"))
        if 500 <= resp.status_code < 600 and attempt < RETRY_MAX:
            time.sleep(RETRY_BACKOFF * attempt)
            continue
        return False, False
    return False, False


def replay_once(target: str, timeout: float, sleep_between: float) -> tuple[int, int, int]:
    with session_scope() as db_session:
        rows = db_session.execute(
            text(
                "SELECT name, timestamp, image_path, image_data, camera_id FROM snapshot_logs "
                "WHERE image_data IS NOT NULL AND image_data != '' "
                "ORDER BY id ASC"
            )
        ).mappings().all()

    total = len(rows)
    print(f"replaying {total} rows to {target}", flush=True)

    session = requests.Session()
    stored = skipped = failed = 0
    for i, row in enumerate(rows, 1):
        cam_id = row["camera_id"]
        ts = row["timestamp"]
        # SA returns either a datetime (PostgreSQL) or an ISO string (SQLite)
        # for the configured DateTime(timezone=True) column. Normalize so the
        # ingest payload is always a JSON-safe ISO string.
        ts_iso = ts.isoformat() if hasattr(ts, "isoformat") else str(ts or "")
        payload = {
            "name": row["name"],
            "timestamp": ts_iso,
            "image_base64": row["image_data"],
            "snap_id": extract_snap_id(row["image_path"], cam_id),
            "camera_id": cam_id,
        }
        ok, was_stored = post_with_retry(session, target, payload, timeout)
        if not ok:
            failed += 1
        elif was_stored:
            stored += 1
        else:
            skipped += 1
        if i % 100 == 0 or i == total:
            print(f"[{i}/{total}] stored={stored} skipped={skipped} failed={failed}", flush=True)
        time.sleep(sleep_between)

    print(f"pass complete — stored={stored} skipped={skipped} failed={failed}", flush=True)
    return stored, skipped, failed


def _derive_remote_base(ingest_url: str) -> str:
    base = ingest_url.rstrip("/")
    suffix = "/api/ingest"
    if base.endswith(suffix):
        base = base[: -len(suffix)]
    return base


def _employee_matches_remote(emp, remote: dict) -> bool:
    return (
        remote.get("name", "") == emp.name
        and remote.get("employeeId", "") == emp.employee_id
        and (remote.get("company") or "") == (emp.company or "")
        and (remote.get("department") or "") == (emp.department or "")
        and (remote.get("shift") or "") == (emp.shift or "")
        and (remote.get("role") or "Employee") == (emp.role or "Employee")
        and (remote.get("dob") or "") == (emp.dob or "")
    )


def _login_for_employees(remote_base: str, timeout: float) -> str | None:
    """Acquire an admin JWT via REPLAY_USERNAME / REPLAY_PASSWORD env vars.
    Returns None if creds aren't configured or login fails — caller must
    skip the employee sync in that case."""
    username = os.getenv("REPLAY_USERNAME", "").strip()
    password = os.getenv("REPLAY_PASSWORD", "")
    if not username or not password:
        return None
    try:
        resp = requests.post(
            f"{remote_base}/api/auth/login",
            json={"username": username, "password": password},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        print(f"employees: login request failed: {exc}", flush=True)
        return None
    if resp.status_code != 200:
        print(
            f"employees: login HTTP {resp.status_code} (check REPLAY_USERNAME / "
            f"REPLAY_PASSWORD): {resp.text[:200]}",
            flush=True,
        )
        return None
    return resp.json().get("access_token")


def sync_employees_once(remote_base: str, timeout: float) -> tuple[int, int, int]:
    """One-way local → remote upsert. Returns (upserted, skipped, failed).

    Requires admin auth on the remote (employees endpoints are protected).
    Provide credentials via REPLAY_USERNAME / REPLAY_PASSWORD env vars."""
    from app.services import employees as employees_service

    token = _login_for_employees(remote_base, timeout)
    if not token:
        print(
            "employees: skipping sync — set REPLAY_USERNAME and REPLAY_PASSWORD "
            "env vars to an admin account on the remote, or pass "
            "--no-sync-employees to silence this.",
            flush=True,
        )
        return 0, 0, 0

    auth_headers = {"Authorization": f"Bearer {token}"}
    local = employees_service.all_employees()
    session = requests.Session()

    try:
        resp = session.get(f"{remote_base}/api/employees", headers=auth_headers, timeout=timeout)
        resp.raise_for_status()
        remote_map = {e["id"]: e for e in resp.json().get("items", [])}
    except requests.RequestException as exc:
        print(f"employees: remote fetch failed: {exc}", flush=True)
        return 0, 0, 1

    upserted = skipped = failed = 0
    for emp in local:
        payload = {
            "name": emp.name,
            "employeeId": emp.employee_id,
            "company": emp.company,
            "department": emp.department,
            "shift": emp.shift,
            "role": emp.role,
            "dob": emp.dob or "",
        }
        try:
            if emp.id not in remote_map:
                resp = session.post(
                    f"{remote_base}/api/employees",
                    json={**payload, "id": emp.id},
                    headers=auth_headers,
                    timeout=timeout,
                )
                if resp.status_code in (200, 201):
                    upserted += 1
                else:
                    failed += 1
                    print(
                        f"employees POST {emp.id} HTTP {resp.status_code}: {resp.text[:200]}",
                        flush=True,
                    )
            elif not _employee_matches_remote(emp, remote_map[emp.id]):
                resp = session.put(
                    f"{remote_base}/api/employees/{emp.id}",
                    json=payload,
                    headers=auth_headers,
                    timeout=timeout,
                )
                if resp.status_code == 200:
                    upserted += 1
                else:
                    failed += 1
                    print(
                        f"employees PUT {emp.id} HTTP {resp.status_code}: {resp.text[:200]}",
                        flush=True,
                    )
            else:
                skipped += 1
        except requests.RequestException as exc:
            failed += 1
            print(f"employees {emp.id} failed: {exc}", flush=True)

    print(
        f"employees sync — upserted={upserted} skipped={skipped} failed={failed}",
        flush=True,
    )
    return upserted, skipped, failed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Remote /api/ingest URL")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--sleep", type=float, default=0.05, help="Seconds between posts")
    parser.add_argument("--loop", type=float, default=0.0,
                        help="If >0, run forever — sleep this many seconds between passes. "
                             "Most rows will be skipped (already present); only new/missing "
                             "rows get inserted.")
    parser.add_argument("--no-sync-employees", action="store_true",
                        help="Disable the one-way employees upsert (local → remote).")
    args = parser.parse_args()

    remote_base = _derive_remote_base(args.target)
    sync_employees = not args.no_sync_employees

    def _one_pass() -> int:
        _, _, snap_failed = replay_once(args.target, args.timeout, args.sleep)
        emp_failed = 0
        if sync_employees:
            _, _, emp_failed = sync_employees_once(remote_base, args.timeout)
        return snap_failed + emp_failed

    if args.loop <= 0:
        return 0 if _one_pass() == 0 else 1

    print(f"loop mode: pass every {args.loop}s (employees sync={'on' if sync_employees else 'off'})", flush=True)
    while True:
        try:
            _one_pass()
        except Exception as exc:
            print(f"pass crashed: {exc}", flush=True)
        time.sleep(args.loop)


if __name__ == "__main__":
    sys.exit(main())
