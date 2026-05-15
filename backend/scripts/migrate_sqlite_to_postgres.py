"""One-shot SQLite → PostgreSQL data migration for the Attendance Dashboard.

Usage (from the ``backend/`` directory):

    python -m scripts.migrate_sqlite_to_postgres \\
        --sqlite-path ../backend/database.db \\
        --database-url 'postgresql+psycopg://user:pw@host:5432/dbname' \\
        [--dry-run] [--batch-size 500] \\
        [--tables users,employees,cameras,attendance_logs,snapshot_logs,attendance_report_edits] \\
        [--on-conflict skip|update] [--no-backup] [--rollback-on-error] \\
        [--limit N]

What it does
------------
1. Backs up the SQLite file (``<path>.bak.<timestamp>``) unless --no-backup.
2. Verifies SQLite ``PRAGMA integrity_check``, opens the source read-only
   (``file:...?mode=ro``), pings the destination, and runs
   ``Base.metadata.create_all`` on the destination so target tables exist.
3. Copies every table in FK-respecting order with parameterized inserts
   and dialect-aware ``ON CONFLICT`` handling. ``users``, ``employees``,
   and ``cameras`` go first (no FKs), then logs and edits which reference
   ``employees.id`` via the new nullable FK column.
4. After per-table inserts, advances each BIGSERIAL/IDENTITY sequence to
   ``MAX(id)+1`` so subsequent ORM inserts don't collide on PK.
5. Prints a summary table (rows source / inserted / skipped_dup / errored,
   plus unmatched-name samples and the backup file path) and exits non-zero
   on any per-row error.

Idempotent re-runs
------------------
* ``--on-conflict skip`` (default) — re-runs are safe; rows already in PG
  are skipped via the unique index on ``image_path`` (logs), ``username``
  (users), ``id`` (PKs), or ``(name, work_date)`` (report edits).
* ``--on-conflict update`` — last-write-wins from the SQLite side. Useful
  when SQLite is the source of truth for repeated syncs.

Camera passwords
----------------
``cameras.password_encrypted`` is a Fernet token tied to ``CAMERA_SECRET_KEY``.
The token is migrated as-is — re-encryption is impossible without the
original key. If the source has any camera with a non-empty password, the
script verifies the env var matches by decrypting one row before any
writes happen, and aborts loudly on mismatch.

This script never modifies the SQLite source.
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import sqlite3
import sys
import time
from collections import Counter
from datetime import date as date_cls, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

# Make ``app.*`` importable when run as ``python -m scripts.migrate_...``
# from the ``backend/`` directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DB_PATH  # noqa: E402
from app.models import Base  # noqa: E402

log = logging.getLogger("migrate")


ALL_TABLES_IN_ORDER: tuple[str, ...] = (
    "users",
    "employees",
    "cameras",
    "attendance_logs",
    "snapshot_logs",
    "attendance_report_edits",
)


# ---- Helpers ---------------------------------------------------------------


def _normalize_database_url(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("postgres://"):
        return "postgresql+psycopg://" + raw[len("postgres://"):]
    if raw.startswith("postgresql://") and "+psycopg" not in raw.split("://", 1)[0]:
        return "postgresql+psycopg://" + raw[len("postgresql://"):]
    return raw


def _parse_iso(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        dt = value
    elif value is None or value == "":
        return None
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_date(value: Any) -> Optional[date_cls]:
    if value is None:
        return None
    if isinstance(value, date_cls):
        return value
    try:
        return date_cls.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _normalize_name(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


# ---- Per-table report ------------------------------------------------------


class TableReport:
    __slots__ = ("name", "source", "inserted", "skipped_dup", "errored", "skipped_unmatched")

    def __init__(self, name: str) -> None:
        self.name = name
        self.source = 0
        self.inserted = 0
        self.skipped_dup = 0
        self.errored = 0
        self.skipped_unmatched = 0


# ---- Pre-flight ------------------------------------------------------------


def _open_sqlite_readonly(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise SystemExit(f"FATAL: SQLite file not found: {path}")
    uri = f"file:{path.resolve()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _integrity_check(conn: sqlite3.Connection) -> None:
    result = conn.execute("PRAGMA integrity_check").fetchone()
    if not result or str(result[0]).strip().lower() != "ok":
        raise SystemExit(f"FATAL: SQLite integrity_check returned: {result[0] if result else 'no result'}")


def _verify_camera_secret_key(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT id, password_encrypted FROM cameras "
        "WHERE password_encrypted IS NOT NULL AND password_encrypted != '' LIMIT 1"
    ).fetchone()
    if row is None:
        return
    if not os.getenv("CAMERA_SECRET_KEY", "").strip():
        raise SystemExit(
            "FATAL: source has cameras with encrypted passwords but "
            "CAMERA_SECRET_KEY is not set. Migration would copy ciphertext "
            "the destination cannot decrypt."
        )
    # Decrypt one row to confirm the key matches.
    try:
        from app.services import crypto
        crypto.decrypt(row["password_encrypted"])
    except Exception as exc:
        raise SystemExit(
            "FATAL: CAMERA_SECRET_KEY does not match the key the source DB "
            f"was encrypted with — Fernet decrypt failed: {exc}. Aborting "
            "before writing anything to the destination."
        )


def _backup_sqlite(path: Path) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.name}.bak.{ts}")
    shutil.copy2(path, backup)
    log.info("backup: SQLite copied to %s", backup)
    return backup


def _ping_destination(engine: Engine) -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def _create_tables_if_missing(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)


# ---- Conflict-handling builder --------------------------------------------


def _build_insert(
    pg_session: Session,
    table_name: str,
    rows: list[dict],
    *,
    conflict_cols: Iterable[str],
    on_conflict: str,
) -> Any:
    """Build + execute an ``INSERT ... ON CONFLICT (cols) DO NOTHING|UPDATE``
    on the active dialect (always PostgreSQL for this script). Returns the
    SQLAlchemy ``Result``."""
    if not rows:
        return None
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    table = Base.metadata.tables[table_name]
    stmt = pg_insert(table).values(rows)
    cols = list(conflict_cols)
    if on_conflict == "skip":
        stmt = stmt.on_conflict_do_nothing(index_elements=cols)
    else:  # update
        update_set = {
            c.name: getattr(stmt.excluded, c.name)
            for c in table.columns
            if c.name not in cols and c.name != "id"
        }
        stmt = stmt.on_conflict_do_update(index_elements=cols, set_=update_set)
    return pg_session.execute(stmt)


def _flush_batch(
    pg_session: Session,
    table_name: str,
    batch: list[dict],
    *,
    conflict_cols: list[str],
    on_conflict: str,
    report: TableReport,
) -> None:
    """Insert ``batch`` and update ``report.inserted`` / ``report.skipped_dup``.
    On a unique-violation outside the primary conflict target (e.g. the
    partial unique index on ``external_event_id``), fall back to per-row
    insert inside savepoints so one bad row doesn't fail the whole batch.
    """
    if not batch:
        return
    try:
        result = _build_insert(
            pg_session, table_name, batch, conflict_cols=conflict_cols, on_conflict=on_conflict
        )
        rowcount = int(result.rowcount or 0)
        report.inserted += rowcount
        report.skipped_dup += max(0, len(batch) - rowcount)
        return
    except Exception as exc:
        log.warning("batch insert into %s hit exception (%s); falling back to per-row", table_name, exc)
        pg_session.rollback()

    # Per-row fallback.
    for row in batch:
        sp = pg_session.begin_nested()
        try:
            result = _build_insert(
                pg_session, table_name, [row], conflict_cols=conflict_cols, on_conflict=on_conflict
            )
            rowcount = int(result.rowcount or 0)
            sp.commit()
            if rowcount > 0:
                report.inserted += 1
            else:
                report.skipped_dup += 1
        except Exception:
            sp.rollback()
            report.errored += 1
            log.exception("per-row insert into %s failed for row=%s", table_name, _short_row(row))


def _short_row(row: dict) -> dict:
    """Return a row dict with image_data trimmed for log output."""
    out = dict(row)
    img = out.get("image_data")
    if isinstance(img, str) and len(img) > 80:
        out["image_data"] = img[:80] + f"...({len(img)} chars)"
    return out


# ---- Per-table migrations --------------------------------------------------


def _populate_lookup_tables(
    sqlite_conn: sqlite3.Connection,
    pg_session: Session,
) -> dict[str, int]:
    """Scan distinct ``company`` / ``department`` / ``shift`` strings in
    the source SQLite and ``get_or_create`` matching rows in the
    destination Postgres lookup tables. Returns ``{table: rows_created}``.
    """
    from app.services.lookups import (
        get_or_create_company_id,
        get_or_create_department_id,
        get_or_create_shift_id,
    )

    def _distinct_strings(table: str, column: str) -> list[str]:
        # Defensive PRAGMA check — older SQLite DBs may not have these columns.
        info = {r["name"] for r in sqlite_conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in info:
            return []
        rows = sqlite_conn.execute(
            f"SELECT DISTINCT {column} FROM {table} "
            f"WHERE {column} IS NOT NULL AND {column} != ''"
        ).fetchall()
        return [str(r[0]) for r in rows]

    counts: dict[str, int] = {"companies": 0, "departments": 0, "shifts": 0}

    def _seed(table: str, names: list[str], helper) -> int:
        if not names:
            return 0
        before = pg_session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
        for name in names:
            helper(pg_session, name)
        after = pg_session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
        return int(after) - int(before)

    company_names = sorted({*_distinct_strings("users", "company"), *_distinct_strings("employees", "company")})
    counts["companies"] = _seed("companies", company_names, get_or_create_company_id)
    dept_names = sorted(set(_distinct_strings("employees", "department")))
    counts["departments"] = _seed("departments", dept_names, get_or_create_department_id)
    shift_names = sorted(set(_distinct_strings("employees", "shift")))
    counts["shifts"] = _seed("shifts", shift_names, get_or_create_shift_id)
    return counts


def _build_lookup_id_map(pg_session: Session, table: str) -> dict[str, int]:
    """Map ``lower(name) -> id`` from a lookup table. Used to set the FK
    columns on users/employees during migration."""
    rows = pg_session.execute(text(f"SELECT id, name FROM {table}")).all()
    return {str(name).strip().lower(): int(rid) for rid, name in rows if name}


def _migrate_users(
    sqlite_conn: sqlite3.Connection,
    pg_session: Session,
    *,
    on_conflict: str,
    batch_size: int,
    limit: Optional[int],
    company_id_map: dict[str, int],
) -> TableReport:
    rep = TableReport("users")
    rep.source = sqlite_conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    cur = sqlite_conn.execute(
        "SELECT id, username, password_hash, role, company, display_name, "
        "avatar_url, is_active, created_at FROM users"
    )
    batch: list[dict] = []
    n = 0
    for row in cur:
        if limit is not None and n >= limit:
            break
        n += 1
        company = str(row["company"] or "")
        batch.append({
            "id": str(row["id"]),
            "username": str(row["username"]),
            "password_hash": str(row["password_hash"]),
            "role": str(row["role"]),
            "company": company,
            "company_id": company_id_map.get(company.strip().lower()) if company else None,
            "display_name": str(row["display_name"] or ""),
            "avatar_url": str(row["avatar_url"] or ""),
            "is_active": bool(row["is_active"]),
            "created_at": _parse_iso(row["created_at"]) or datetime.now(timezone.utc),
        })
        if len(batch) >= batch_size:
            _flush_batch(pg_session, "users", batch, conflict_cols=["username"], on_conflict=on_conflict, report=rep)
            batch.clear()
    _flush_batch(pg_session, "users", batch, conflict_cols=["username"], on_conflict=on_conflict, report=rep)
    return rep


def _migrate_employees(
    sqlite_conn: sqlite3.Connection,
    pg_session: Session,
    *,
    on_conflict: str,
    batch_size: int,
    limit: Optional[int],
    company_id_map: dict[str, int],
    department_id_map: dict[str, int],
    shift_id_map: dict[str, int],
) -> TableReport:
    rep = TableReport("employees")
    rep.source = sqlite_conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    cur = sqlite_conn.execute(
        "SELECT id, name, employee_id, company, department, shift, role, dob, "
        "image_url, email, mobile, salary_package FROM employees"
    )
    batch: list[dict] = []
    n = 0
    for row in cur:
        if limit is not None and n >= limit:
            break
        n += 1
        company = str(row["company"] or "")
        department = str(row["department"] or "")
        shift = str(row["shift"] or "")
        batch.append({
            "id": str(row["id"]),
            "name": str(row["name"] or ""),
            # DB column kept as ``employee_id`` (Python attr ``employee_code``).
            "employee_id": str(row["employee_id"] or ""),
            "company": company,
            "company_id": company_id_map.get(company.strip().lower()) if company else None,
            "department": department,
            "department_id": department_id_map.get(department.strip().lower()) if department else None,
            "shift": shift,
            "shift_id": shift_id_map.get(shift.strip().lower()) if shift else None,
            "role": str(row["role"] or "Employee"),
            "dob": str(row["dob"] or ""),
            "image_url": str(row["image_url"] or ""),
            "email": str(row["email"] or ""),
            "mobile": str(row["mobile"] or ""),
            "salary_package": str(row["salary_package"] or ""),
        })
        if len(batch) >= batch_size:
            _flush_batch(pg_session, "employees", batch, conflict_cols=["id"], on_conflict=on_conflict, report=rep)
            batch.clear()
    _flush_batch(pg_session, "employees", batch, conflict_cols=["id"], on_conflict=on_conflict, report=rep)
    return rep


def _migrate_cameras(
    sqlite_conn: sqlite3.Connection,
    pg_session: Session,
    *,
    on_conflict: str,
    batch_size: int,
    limit: Optional[int],
) -> TableReport:
    rep = TableReport("cameras")
    rep.source = sqlite_conn.execute("SELECT COUNT(*) FROM cameras").fetchone()[0]
    cur = sqlite_conn.execute(
        "SELECT id, name, location, ip, port, username, password_encrypted, "
        "rtsp_path, connection_status, last_checked_at, last_check_message, "
        "created_at, updated_at FROM cameras"
    )
    batch: list[dict] = []
    n = 0
    now = datetime.now(timezone.utc)
    for row in cur:
        if limit is not None and n >= limit:
            break
        n += 1
        batch.append({
            "id": str(row["id"]),
            "name": str(row["name"] or ""),
            "location": str(row["location"] or ""),
            "ip": str(row["ip"] or ""),
            "port": int(row["port"] or 554),
            "username": str(row["username"] or ""),
            "password_encrypted": str(row["password_encrypted"] or ""),
            "rtsp_path": str(row["rtsp_path"] or "/Streaming/Channels/101"),
            "connection_status": str(row["connection_status"] or "unknown"),
            "last_checked_at": _parse_iso(row["last_checked_at"]),
            "last_check_message": row["last_check_message"],
            "created_at": _parse_iso(row["created_at"]) or now,
            "updated_at": _parse_iso(row["updated_at"]) or now,
        })
        if len(batch) >= batch_size:
            _flush_batch(pg_session, "cameras", batch, conflict_cols=["id"], on_conflict=on_conflict, report=rep)
            batch.clear()
    _flush_batch(pg_session, "cameras", batch, conflict_cols=["id"], on_conflict=on_conflict, report=rep)
    return rep


def _build_employee_lookup(pg_session: Session) -> tuple[dict[str, str], dict[str, str]]:
    rows = pg_session.execute(text("SELECT id, name FROM employees")).all()
    by_lower: dict[str, str] = {}
    by_norm: dict[str, str] = {}
    for emp_id, name in rows:
        if not name:
            continue
        by_lower.setdefault(str(name).strip().lower(), str(emp_id))
        by_norm.setdefault(_normalize_name(str(name)), str(emp_id))
    return by_lower, by_norm


def _resolve_employee(
    name: Optional[str],
    by_lower: dict[str, str],
    by_norm: dict[str, str],
) -> Optional[str]:
    if not name:
        return None
    nl = str(name).strip().lower()
    if nl in by_lower:
        return by_lower[nl]
    nn = _normalize_name(str(name))
    return by_norm.get(nn)


def _migrate_attendance_logs(
    sqlite_conn: sqlite3.Connection,
    pg_session: Session,
    *,
    on_conflict: str,
    batch_size: int,
    limit: Optional[int],
    employee_by_lower: dict[str, str],
    employee_by_norm: dict[str, str],
    unmatched_counter: Counter,
) -> TableReport:
    rep = TableReport("attendance_logs")
    rep.source = sqlite_conn.execute("SELECT COUNT(*) FROM attendance_logs").fetchone()[0]
    # Detect which optional columns exist on the source (legacy DBs created
    # before the multi-source / external_event_id additions may not have
    # them). Build the SELECT defensively.
    table_info = {r["name"] for r in sqlite_conn.execute("PRAGMA table_info(attendance_logs)").fetchall()}
    cols = ["id", "name", "timestamp", "image_path"]
    optional_cols = ["image_data", "camera_id", "source", "external_event_id", "event_type"]
    cols.extend(c for c in optional_cols if c in table_info)
    select_sql = f"SELECT {', '.join(cols)} FROM attendance_logs ORDER BY id"
    cur = sqlite_conn.execute(select_sql)

    batch: list[dict] = []
    n = 0
    for row in cur:
        if limit is not None and n >= limit:
            break
        n += 1
        name = str(row["name"] or "")
        emp_id = _resolve_employee(name, employee_by_lower, employee_by_norm)
        if name and emp_id is None and name.strip().lower() != "unknown":
            unmatched_counter[name] += 1
        ts = _parse_iso(row["timestamp"])
        if ts is None:
            rep.errored += 1
            continue
        record = {
            "id": int(row["id"]),
            "name": name,
            "employee_id": emp_id,
            "timestamp": ts,
            "image_path": str(row["image_path"]),
            "image_data": row["image_data"] if "image_data" in row.keys() else None,
            "camera_id": row["camera_id"] if "camera_id" in row.keys() else None,
            "source": (row["source"] if "source" in row.keys() else None) or "local_camera",
            "external_event_id": row["external_event_id"] if "external_event_id" in row.keys() else None,
            "event_type": row["event_type"] if "event_type" in row.keys() else None,
        }
        batch.append(record)
        if len(batch) >= batch_size:
            _flush_batch(
                pg_session, "attendance_logs", batch,
                conflict_cols=["image_path"], on_conflict=on_conflict, report=rep,
            )
            batch.clear()
    _flush_batch(
        pg_session, "attendance_logs", batch,
        conflict_cols=["image_path"], on_conflict=on_conflict, report=rep,
    )
    return rep


def _migrate_snapshot_logs(
    sqlite_conn: sqlite3.Connection,
    pg_session: Session,
    *,
    on_conflict: str,
    batch_size: int,
    limit: Optional[int],
    employee_by_lower: dict[str, str],
    employee_by_norm: dict[str, str],
    unmatched_counter: Counter,
) -> TableReport:
    rep = TableReport("snapshot_logs")
    rep.source = sqlite_conn.execute("SELECT COUNT(*) FROM snapshot_logs").fetchone()[0]
    table_info = {r["name"] for r in sqlite_conn.execute("PRAGMA table_info(snapshot_logs)").fetchall()}
    cols = ["id", "name", "timestamp", "image_path"]
    optional_cols = ["image_data", "camera_id"]
    cols.extend(c for c in optional_cols if c in table_info)
    select_sql = f"SELECT {', '.join(cols)} FROM snapshot_logs ORDER BY id"
    cur = sqlite_conn.execute(select_sql)

    batch: list[dict] = []
    n = 0
    for row in cur:
        if limit is not None and n >= limit:
            break
        n += 1
        name = str(row["name"] or "")
        emp_id = _resolve_employee(name, employee_by_lower, employee_by_norm)
        if name and emp_id is None and name.strip().lower() != "unknown":
            unmatched_counter[name] += 1
        ts = _parse_iso(row["timestamp"])
        if ts is None:
            rep.errored += 1
            continue
        record = {
            "id": int(row["id"]),
            "name": name,
            "employee_id": emp_id,
            "timestamp": ts,
            "image_path": str(row["image_path"]),
            "image_data": row["image_data"] if "image_data" in row.keys() else None,
            "camera_id": row["camera_id"] if "camera_id" in row.keys() else None,
        }
        batch.append(record)
        if len(batch) >= batch_size:
            _flush_batch(
                pg_session, "snapshot_logs", batch,
                conflict_cols=["image_path"], on_conflict=on_conflict, report=rep,
            )
            batch.clear()
    _flush_batch(
        pg_session, "snapshot_logs", batch,
        conflict_cols=["image_path"], on_conflict=on_conflict, report=rep,
    )
    return rep


def _migrate_attendance_report_edits(
    sqlite_conn: sqlite3.Connection,
    pg_session: Session,
    *,
    on_conflict: str,
    batch_size: int,
    limit: Optional[int],
    employee_by_lower: dict[str, str],
    employee_by_norm: dict[str, str],
    unmatched_counter: Counter,
) -> TableReport:
    """Source: legacy ``attendance_corrections`` table on the SQLite side.
    Destination: new ``attendance_report_edits`` on PG."""
    rep = TableReport("attendance_report_edits")
    # Source table may not exist on a fresh SQLite DB.
    src_exists = sqlite_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='attendance_corrections'"
    ).fetchone() is not None
    if not src_exists:
        return rep

    rep.source = sqlite_conn.execute("SELECT COUNT(*) FROM attendance_corrections").fetchone()[0]
    cur = sqlite_conn.execute(
        "SELECT name, date, entry_iso, exit_iso, total_break_seconds, "
        "missing_checkout_resolved, note, status_override, paid_leave, lop, "
        "wfh, updated_by, updated_at FROM attendance_corrections"
    )
    batch: list[dict] = []
    n = 0
    for row in cur:
        if limit is not None and n >= limit:
            break
        n += 1
        name = str(row["name"] or "").strip()
        work_date = _parse_date(row["date"])
        if work_date is None:
            rep.errored += 1
            continue
        emp_id = _resolve_employee(name, employee_by_lower, employee_by_norm)
        if name and emp_id is None:
            unmatched_counter[name] += 1
        updated_at = _parse_iso(row["updated_at"]) or datetime.now(timezone.utc)
        record = {
            # Let BIGSERIAL assign id.
            "employee_id": emp_id,
            "name": name,
            "work_date": work_date,
            "entry_iso": _parse_iso(row["entry_iso"]),
            "exit_iso": _parse_iso(row["exit_iso"]),
            "total_break_seconds": row["total_break_seconds"],
            "missing_checkout_resolved": bool(row["missing_checkout_resolved"] or 0),
            "notes": row["note"],
            "status_override": row["status_override"],
            "paid_leave": bool(row["paid_leave"] or 0),
            "lop": bool(row["lop"] or 0),
            "wfh": bool(row["wfh"] or 0),
            "updated_by": row["updated_by"],
            "created_at": updated_at,
            "updated_at": updated_at,
        }
        batch.append(record)
        if len(batch) >= batch_size:
            _flush_batch(
                pg_session, "attendance_report_edits", batch,
                conflict_cols=["name", "work_date"], on_conflict=on_conflict, report=rep,
            )
            batch.clear()
    _flush_batch(
        pg_session, "attendance_report_edits", batch,
        conflict_cols=["name", "work_date"], on_conflict=on_conflict, report=rep,
    )
    return rep


# ---- Sequence advance ------------------------------------------------------


def _advance_sequences(pg_session: Session) -> dict[str, int]:
    """Set every BIGSERIAL/IDENTITY sequence to ``MAX(id)+1`` so future ORM
    inserts don't collide on PK with rows that were INSERTed with explicit ids.
    """
    advanced: dict[str, int] = {}
    for table in ("attendance_logs", "snapshot_logs", "attendance_report_edits"):
        pk_col = "id"
        max_id = pg_session.execute(text(f"SELECT COALESCE(MAX({pk_col}), 0) FROM {table}")).scalar_one()
        max_id = int(max_id or 0)
        # No-op when the table is empty AND the sequence was never used.
        seq = pg_session.execute(
            text(f"SELECT pg_get_serial_sequence('{table}', '{pk_col}')")
        ).scalar_one()
        if not seq:
            continue
        # ``setval(..., n, true)`` makes the next nextval() return n+1.
        pg_session.execute(
            text("SELECT setval(:seq, :val, true)"), {"seq": seq, "val": max(max_id, 1)},
        )
        advanced[table] = max_id + 1
    return advanced


# ---- Summary ---------------------------------------------------------------


def _print_summary(
    *,
    sqlite_path: Path,
    backup_path: Optional[Path],
    pg_url: str,
    started_at: float,
    reports: list[TableReport],
    advanced: dict[str, int],
    unmatched_counter: Counter,
    dry_run: bool,
) -> bool:
    elapsed = time.time() - started_at
    total_src = sum(r.source for r in reports)
    total_ins = sum(r.inserted for r in reports)
    total_dup = sum(r.skipped_dup for r in reports)
    total_err = sum(r.errored for r in reports)

    print()
    print("=" * 68)
    print(f"  Migration {'DRY-RUN ' if dry_run else ''}summary  ({datetime.now(timezone.utc).isoformat()}, {elapsed:.1f}s)")
    print("=" * 68)
    print(f"  Source:      {sqlite_path} ({sqlite_path.stat().st_size / 1024 / 1024:.1f} MB)")
    masked = make_url(pg_url).set(password="****" if make_url(pg_url).password else None)
    print(f"  Destination: {masked}")
    print()
    print("  Per-table results:")
    print(f"    {'table':<28} {'source':>9} {'inserted':>10} {'skipped_dup':>13} {'errored':>9}")
    for r in reports:
        print(f"    {r.name:<28} {r.source:>9d} {r.inserted:>10d} {r.skipped_dup:>13d} {r.errored:>9d}")
    print(f"    {'─' * 28}  {'─' * 9} {'─' * 10} {'─' * 13} {'─' * 9}")
    print(f"    {'TOTAL':<28} {total_src:>9d} {total_ins:>10d} {total_dup:>13d} {total_err:>9d}")

    if advanced:
        print()
        print("  Sequences advanced:")
        for table, val in advanced.items():
            print(f"    {table}_id_seq -> {val}")

    if unmatched_counter:
        print()
        print("  Names that did NOT resolve to an employees.id (employee_id left NULL):")
        for name, count in unmatched_counter.most_common(20):
            print(f"    {count:>4}× {name!r}")

    if backup_path:
        print()
        print(f"  Backup: {backup_path}")

    print()
    success = total_err == 0
    print(f"  Result: {'SUCCESS' if success else 'FAILURE (per-row errors > 0)'}")
    print("=" * 68)
    return success


# ---- Main ------------------------------------------------------------------


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--sqlite-path", default=os.getenv("DATABASE_PATH", str(DB_PATH)))
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", ""))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument(
        "--tables",
        default=",".join(ALL_TABLES_IN_ORDER),
        help="Comma-separated subset to migrate. Order in the list is respected.",
    )
    parser.add_argument("--on-conflict", choices=("skip", "update"), default="skip")
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--rollback-on-error", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    sqlite_path = Path(args.sqlite_path).resolve()
    pg_url = _normalize_database_url(args.database_url)
    if not pg_url:
        log.error("--database-url (or DATABASE_URL env) is required")
        return 2
    if not pg_url.startswith("postgresql"):
        log.error("--database-url must point at a PostgreSQL instance, got %s", pg_url.split("://", 1)[0])
        return 2

    log.info("source SQLite: %s", sqlite_path)
    log.info("destination Postgres host=%s db=%s", make_url(pg_url).host, make_url(pg_url).database)
    log.info("on_conflict=%s dry_run=%s batch_size=%d", args.on_conflict, args.dry_run, args.batch_size)

    sqlite_conn = _open_sqlite_readonly(sqlite_path)
    _integrity_check(sqlite_conn)

    # Cameras pre-flight (Fernet key check) BEFORE any writes.
    _verify_camera_secret_key(sqlite_conn)

    backup_path: Optional[Path] = None
    if not args.no_backup and not args.dry_run:
        backup_path = _backup_sqlite(sqlite_path)

    pg_engine = create_engine(pg_url, future=True, pool_pre_ping=True)
    _ping_destination(pg_engine)
    if not args.dry_run:
        _create_tables_if_missing(pg_engine)

    PgSession = sessionmaker(bind=pg_engine, autoflush=False, expire_on_commit=False, future=True)
    pg_session = PgSession()

    requested = [t.strip() for t in args.tables.split(",") if t.strip()]
    invalid = [t for t in requested if t not in ALL_TABLES_IN_ORDER]
    if invalid:
        log.error("unknown --tables values: %s (valid: %s)", invalid, list(ALL_TABLES_IN_ORDER))
        return 2
    # Respect the dependency-respecting global order regardless of the user's
    # listed order.
    tables_to_run = [t for t in ALL_TABLES_IN_ORDER if t in requested]

    started = time.time()
    reports: list[TableReport] = []
    unmatched: Counter = Counter()
    advanced: dict[str, int] = {}

    big_txn = None
    if args.rollback_on_error and not args.dry_run:
        big_txn = pg_session.begin()

    try:
        # Populate the company / department / shift lookup tables first so
        # the FK columns on users + employees can be set during their
        # respective migrations.
        company_id_map: dict[str, int] = {}
        department_id_map: dict[str, int] = {}
        shift_id_map: dict[str, int] = {}
        if not args.dry_run:
            if not args.rollback_on_error:
                pg_session.begin()
            lookup_counts = _populate_lookup_tables(sqlite_conn, pg_session)
            log.info("lookup tables populated counts=%s", lookup_counts)
            pg_session.flush()
            company_id_map = _build_lookup_id_map(pg_session, "companies")
            department_id_map = _build_lookup_id_map(pg_session, "departments")
            shift_id_map = _build_lookup_id_map(pg_session, "shifts")
            if not args.rollback_on_error:
                pg_session.commit()

        # Build name->id maps after employees migration for use by logs.
        employee_by_lower: dict[str, str] = {}
        employee_by_norm: dict[str, str] = {}

        for table in tables_to_run:
            log.info("starting table=%s", table)
            if not args.dry_run and not args.rollback_on_error:
                # Per-table transaction so a partial run leaves earlier
                # tables committed.
                pg_session.begin()
            if table == "users":
                rep = _migrate_users(
                    sqlite_conn, pg_session,
                    on_conflict=args.on_conflict, batch_size=args.batch_size, limit=args.limit,
                    company_id_map=company_id_map,
                )
            elif table == "employees":
                rep = _migrate_employees(
                    sqlite_conn, pg_session,
                    on_conflict=args.on_conflict, batch_size=args.batch_size, limit=args.limit,
                    company_id_map=company_id_map,
                    department_id_map=department_id_map,
                    shift_id_map=shift_id_map,
                )
                # Refresh the lookup maps now that employees are inserted.
                pg_session.flush()
                employee_by_lower, employee_by_norm = _build_employee_lookup(pg_session)
            elif table == "cameras":
                rep = _migrate_cameras(
                    sqlite_conn, pg_session,
                    on_conflict=args.on_conflict, batch_size=args.batch_size, limit=args.limit,
                )
            elif table == "attendance_logs":
                if not employee_by_lower:
                    employee_by_lower, employee_by_norm = _build_employee_lookup(pg_session)
                rep = _migrate_attendance_logs(
                    sqlite_conn, pg_session,
                    on_conflict=args.on_conflict, batch_size=args.batch_size, limit=args.limit,
                    employee_by_lower=employee_by_lower, employee_by_norm=employee_by_norm,
                    unmatched_counter=unmatched,
                )
            elif table == "snapshot_logs":
                if not employee_by_lower:
                    employee_by_lower, employee_by_norm = _build_employee_lookup(pg_session)
                rep = _migrate_snapshot_logs(
                    sqlite_conn, pg_session,
                    on_conflict=args.on_conflict, batch_size=args.batch_size, limit=args.limit,
                    employee_by_lower=employee_by_lower, employee_by_norm=employee_by_norm,
                    unmatched_counter=unmatched,
                )
            elif table == "attendance_report_edits":
                if not employee_by_lower:
                    employee_by_lower, employee_by_norm = _build_employee_lookup(pg_session)
                rep = _migrate_attendance_report_edits(
                    sqlite_conn, pg_session,
                    on_conflict=args.on_conflict, batch_size=args.batch_size, limit=args.limit,
                    employee_by_lower=employee_by_lower, employee_by_norm=employee_by_norm,
                    unmatched_counter=unmatched,
                )
            else:
                continue
            reports.append(rep)
            log.info(
                "done table=%s source=%d inserted=%d skipped_dup=%d errored=%d",
                rep.name, rep.source, rep.inserted, rep.skipped_dup, rep.errored,
            )
            if not args.dry_run and not args.rollback_on_error:
                pg_session.commit()

        # Sequence advance after every log table is in place.
        if not args.dry_run:
            advanced = _advance_sequences(pg_session)
            if not args.rollback_on_error:
                pg_session.commit()

        if args.rollback_on_error and not args.dry_run:
            assert big_txn is not None
            total_err = sum(r.errored for r in reports)
            if total_err > 0:
                big_txn.rollback()
                log.error("rolling back: %d per-row errors with --rollback-on-error", total_err)
                return 1
            big_txn.commit()

    except Exception:
        log.exception("migration failed; rolling back current transaction")
        try:
            pg_session.rollback()
        except Exception:
            pass
        return 1
    finally:
        try:
            pg_session.close()
        finally:
            sqlite_conn.close()

    success = _print_summary(
        sqlite_path=sqlite_path,
        backup_path=backup_path,
        pg_url=pg_url,
        started_at=started,
        reports=reports,
        advanced=advanced,
        unmatched_counter=unmatched,
        dry_run=args.dry_run,
    )
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
