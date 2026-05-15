"""Snapshot image retention.

Images live as base64 in the ``image_data`` column on ``snapshot_logs`` and
``attendance_logs``. To keep the DB from growing unbounded, this module
nulls out ``image_data`` on rows older than yesterday — except the first
ENTRY and final EXIT capture per (name, local_date), which we keep so the
attendance summary can still render entry/exit thumbnails.

Retention rule:
    today           — keep all images
    yesterday       — keep all images
    older           — keep first + last image per (employee, local date);
                      NULL out image_data on the rest

Attendance rows themselves are never deleted; only ``image_data`` is
cleared. The job is idempotent: the WHERE clause skips rows that were
already pruned, so re-running it is a no-op.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date as date_cls, datetime, time, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import bindparam, text

from ..config import LOCAL_TZ_OFFSET_MIN
from ..db import session_scope

log = logging.getLogger(__name__)

_TABLES = ("snapshot_logs", "attendance_logs")
_UPDATE_CHUNK = 500
_UNKNOWN_NAME = "unknown"


def _local_tz() -> timezone:
    return timezone(timedelta(minutes=LOCAL_TZ_OFFSET_MIN))


def today_local() -> date_cls:
    return datetime.now(timezone.utc).astimezone(_local_tz()).date()


def _local_midnight_utc(local_date: date_cls) -> datetime:
    midnight_local = datetime.combine(local_date, time(0, 0), tzinfo=_local_tz())
    return midnight_local.astimezone(timezone.utc)


def _parse_utc(value: Any) -> Optional[datetime]:
    """Parse a row's timestamp column into a UTC datetime. Accepts both
    string (SQLite) and datetime (Postgres) — SA returns whichever the
    underlying driver provides for the configured DateTime(timezone=True)."""
    if isinstance(value, datetime):
        dt = value
    elif value is None:
        return None
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _is_unknown(name_key: str) -> bool:
    return not name_key or name_key == _UNKNOWN_NAME


def _normalize_name_key(name: str) -> str:
    """Group key used to pair captures into entry/exit. Mirrors
    ``services.attendance._normalize_name`` lowercased, so cleanup keeps
    the exact same first/last rows that the reports query selects."""
    return " ".join((name or "").strip().split()).lower()


def prune_old_snapshots() -> dict[str, int]:
    """Apply the retention rule. Returns the number of rows whose
    ``image_data`` was cleared, per table.

    Safety guarantees enforced here:
      * the FIRST capture per (employee, local date) keeps its image_data
      * the FINAL capture per (employee, local date) keeps its image_data
      * attendance_logs / snapshot_logs ROWS are never deleted — only the
        ``image_data`` column is nulled out for non-required rows
      * unknown faces have no entry/exit semantics, so we clear all of theirs
    """
    today = today_local()
    yesterday = today - timedelta(days=1)
    # Anything strictly older than the start of `yesterday` (local) is in scope.
    cutoff_utc = _local_midnight_utc(yesterday)
    tz = _local_tz()

    summary: dict[str, int] = {}
    for table in _TABLES:
        with session_scope() as session:
            rows = session.execute(
                text(
                    f"SELECT id, name, timestamp FROM {table} "
                    f"WHERE image_data IS NOT NULL AND timestamp < :cutoff"
                ),
                {"cutoff": cutoff_utc},
            ).mappings().all()

            groups: dict[tuple[str, date_cls], list[tuple[datetime, int]]] = defaultdict(list)
            display_name: dict[tuple[str, date_cls], str] = {}
            for r in rows:
                ts = _parse_utc(r["timestamp"])
                if ts is None:
                    continue
                local_date = ts.astimezone(tz).date()
                # Defensive: a row whose UTC ts < cutoff but whose local date
                # still falls on `yesterday` (or later) should not be pruned.
                if local_date >= yesterday:
                    continue
                key = (_normalize_name_key(r["name"]), local_date)
                groups[key].append((ts, r["id"]))
                display_name.setdefault(key, r["name"])

            ids_to_clear: list[int] = []
            kept_ids: list[tuple[str, date_cls, int, int]] = []
            for (name_key, _date), items in groups.items():
                items.sort(key=lambda x: (x[0], x[1]))
                if _is_unknown(name_key):
                    # Unknown faces have no entry/exit semantics — drop all.
                    ids_to_clear.extend(_id for _, _id in items)
                    log.info(
                        "retention[%s]: unknown face on %s — clearing %d images "
                        "(no entry/exit semantics)",
                        table, _date.isoformat(), len(items),
                    )
                    continue
                first_id = items[0][1]
                last_id = items[-1][1]
                keep_ids = {first_id, last_id}
                kept_ids.append((display_name[(name_key, _date)], _date, first_id, last_id))
                cleared_for_group = [_id for _, _id in items if _id not in keep_ids]
                ids_to_clear.extend(cleared_for_group)
                log.info(
                    "retention[%s]: %s on %s — keeping entry id=%d + exit id=%d, "
                    "clearing %d middle images",
                    table,
                    display_name[(name_key, _date)],
                    _date.isoformat(),
                    first_id,
                    last_id,
                    len(cleared_for_group),
                )

            cleared = 0
            update_stmt = text(
                f"UPDATE {table} SET image_data = NULL WHERE id IN :ids"
            ).bindparams(bindparam("ids", expanding=True))
            for i in range(0, len(ids_to_clear), _UPDATE_CHUNK):
                chunk = ids_to_clear[i : i + _UPDATE_CHUNK]
                if not chunk:
                    continue
                session.execute(update_stmt, {"ids": chunk})
                cleared += len(chunk)
            summary[table] = cleared

            log.info(
                "retention[%s] summary: scanned %d candidate rows older than %s "
                "(local), kept %d (entry+exit) image rows across %d employee-days, "
                "cleared image_data on %d rows; attendance rows were not deleted",
                table,
                len(rows),
                yesterday.isoformat(),
                len(kept_ids) * 2,
                len(kept_ids),
                cleared,
            )
    return summary


def snapshot_storage_stats() -> dict:
    """Quick summary the admin Settings → Snapshots panel renders: total
    rows in each capture table, how many still hold image data, and the
    approximate byte size that data is consuming.

    The byte size is the sum of base64 string lengths across image_data
    columns — close enough to disk usage for an at-a-glance view without
    needing platform-specific page-size math.
    """
    out: dict = {"tables": {}, "totalRows": 0, "totalRowsWithImage": 0, "totalBytes": 0}
    with session_scope() as session:
        for table in _TABLES:
            row = session.execute(
                text(
                    f"SELECT COUNT(*) AS n_total, "
                    f"SUM(CASE WHEN image_data IS NOT NULL THEN 1 ELSE 0 END) AS n_with, "
                    f"COALESCE(SUM(LENGTH(image_data)), 0) AS bytes "
                    f"FROM {table}"
                ),
            ).mappings().one()
            n_total = int(row["n_total"] or 0)
            n_with = int(row["n_with"] or 0)
            n_bytes = int(row["bytes"] or 0)
            out["tables"][table] = {
                "rows": n_total,
                "rowsWithImage": n_with,
                "approxBytes": n_bytes,
            }
            out["totalRows"] += n_total
            out["totalRowsWithImage"] += n_with
            out["totalBytes"] += n_bytes

        first = session.execute(
            text("SELECT MIN(timestamp) FROM snapshot_logs WHERE image_data IS NOT NULL")
        ).scalar_one_or_none()
        out["oldestImageTimestamp"] = (
            first.isoformat() if isinstance(first, datetime) else (str(first) if first else None)
        )
    return out


def purge_image_data_before(cutoff_date: date_cls) -> dict[str, int]:
    """Force-NULL ``image_data`` on every capture row whose timestamp is
    strictly before the start of ``cutoff_date`` (local). Unlike the
    nightly prune, this does NOT preserve entry/exit thumbnails — the
    admin is explicitly asking to free space.

    Rows themselves are never deleted; only image_data is cleared so the
    attendance summary can still account for the event (without a thumb).
    Returns rows-cleared per table.
    """
    cutoff_utc = _local_midnight_utc(cutoff_date)
    out: dict[str, int] = {}
    with session_scope() as session:
        for table in _TABLES:
            result = session.execute(
                text(
                    f"UPDATE {table} SET image_data = NULL "
                    f"WHERE image_data IS NOT NULL AND timestamp < :cutoff"
                ),
                {"cutoff": cutoff_utc},
            )
            cleared = int(result.rowcount or 0)
            out[table] = cleared
            log.info(
                "manual purge[%s] cleared image_data on %d rows older than %s",
                table, cleared, cutoff_date.isoformat(),
            )
    return out


def seconds_until_next_local_midnight() -> float:
    """Seconds from now until 00:00:30 local on the next local day. The 30s
    cushion makes sure the cleanup runs *after* the date boundary rather
    than racing it."""
    tz = _local_tz()
    now_local = datetime.now(timezone.utc).astimezone(tz)
    next_day = (now_local + timedelta(days=1)).date()
    next_run_local = datetime.combine(next_day, time(0, 0, 30), tzinfo=tz)
    delta = (next_run_local - now_local).total_seconds()
    return max(60.0, delta)
