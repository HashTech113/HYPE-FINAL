"""Backfill missing snapshot_logs rows from the camera's history.

Live capture goes through `capture.py` + processAlarm/Get. That stream can
drop events if capture.py crashes or the local backend is unreachable. This
service closes the gap by querying the camera's persistent SnapedFaces index
over a time window and re-posting anything we don't already have.

The only awkward bit is `MatchedFaceId → name`. The camera doesn't expose a
name lookup via any of the AddedFaces / FDGroup endpoints on this firmware
(all return empty on 172.18.11.62). Instead we *learn* the map by
cross-referencing: for SnapIds we already have locally (recorded by live
processAlarm, so we know the name), we know their MatchedFaceId from the
camera's SnapedFaces response. Majority vote gives a stable mapping.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Iterable, Iterator, Optional

from sqlalchemy import bindparam, text

from ..config import LOCAL_TZ_OFFSET_MIN
from ..db import session_scope
from . import logs as logs_service
from . import snapshots as snapshots_mod
from .camera import CameraClient

log = logging.getLogger(__name__)

PAGE_SIZE = 100
DEFAULT_LEARN_LOOKBACK_DAYS = 7


def _local_tz() -> timezone:
    return timezone(timedelta(minutes=LOCAL_TZ_OFFSET_MIN))


def _utc_to_local(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_local_tz())


def _iterate_search_results(
    camera: CameraClient, total: int, *, with_face_image: bool
) -> Iterator[dict]:
    """Yield every SnapedFaceInfo row by paging through the active cursor."""
    fetched = 0
    while fetched < total:
        batch = camera.get_snaped_by_index(
            fetched,
            min(PAGE_SIZE, total - fetched),
            with_face_image=with_face_image,
        )
        if not batch:
            break
        for row in batch:
            yield row
        fetched += len(batch)
        if len(batch) < PAGE_SIZE:
            break


def _extract_snap_id_from_image_path(image_path: str) -> Optional[int]:
    if not image_path.startswith("ingest_") or not image_path.endswith(".jpg"):
        return None
    raw = image_path[len("ingest_") : -len(".jpg")]
    try:
        return int(raw)
    except ValueError:
        return None


def build_face_id_name_map(
    camera: CameraClient,
    *,
    lookback_days: int = DEFAULT_LEARN_LOOKBACK_DAYS,
) -> dict[int, str]:
    """Learn MatchedFaceId → canonical name by joining SnapedFaces ∩ snapshot_logs."""
    end_local = datetime.now(_local_tz())
    start_local = end_local - timedelta(days=lookback_days)

    total = camera.search_history(start_local, end_local)
    if total == 0:
        log.info("face_id_name_map: camera returned 0 rows; map is empty")
        return {}

    cam_snap_to_face: dict[int, int] = {}
    for row in _iterate_search_results(camera, total, with_face_image=False):
        snap_id = row.get("SnapId")
        face_id = row.get("MatchedFaceId")
        if isinstance(snap_id, int) and isinstance(face_id, int) and face_id > 0:
            cam_snap_to_face[snap_id] = face_id

    if not cam_snap_to_face:
        return {}

    image_paths = [f"ingest_{sid}.jpg" for sid in cam_snap_to_face]
    with session_scope() as session:
        rows = session.execute(
            text(
                "SELECT image_path, name FROM snapshot_logs "
                "WHERE image_path IN :paths"
            ).bindparams(bindparam("paths", expanding=True)),
            {"paths": image_paths},
        ).mappings().all()

    votes: dict[int, Counter] = {}
    for r in rows:
        sid = _extract_snap_id_from_image_path(r["image_path"])
        if sid is None:
            continue
        face_id = cam_snap_to_face.get(sid)
        if face_id is None:
            continue
        votes.setdefault(face_id, Counter())[r["name"]] += 1

    result: dict[int, str] = {}
    for face_id, counter in votes.items():
        name, _count = counter.most_common(1)[0]
        result[face_id] = name

    log.info(
        "face_id_name_map built from %d cam rows × %d local matches → %d ids: %s",
        len(cam_snap_to_face),
        len(rows),
        len(result),
        result,
    )
    return result


def _existing_image_paths() -> set[str]:
    with session_scope() as session:
        return {
            r[0]
            for r in session.execute(text("SELECT image_path FROM snapshot_logs")).all()
        }


def backfill_window(
    camera: CameraClient,
    start_utc: datetime,
    end_utc: datetime,
    *,
    dry_run: bool = False,
    face_id_map: Optional[dict[int, str]] = None,
) -> dict:
    """Scan camera history in [start_utc, end_utc] and ingest any rows not in
    snapshot_logs. Idempotent via image_path. Returns a summary dict.
    """
    if face_id_map is None:
        face_id_map = build_face_id_name_map(camera)

    start_local = _utc_to_local(start_utc)
    end_local = _utc_to_local(end_utc)

    total = camera.search_history(start_local, end_local)
    summary: dict = {
        "window_utc": {"start": start_utc.isoformat(), "end": end_utc.isoformat()},
        "window_local": {"start": start_local.isoformat(), "end": end_local.isoformat()},
        "camera_count": total,
        "already_present": 0,
        "added": 0,
        "unmapped_face_ids": {},
        "failed": 0,
        "dry_run": dry_run,
        "face_id_map": face_id_map,
    }
    if total == 0:
        return summary

    existing = _existing_image_paths()
    unmapped: Counter = Counter()

    for row in _iterate_search_results(camera, total, with_face_image=True):
        snap_id = row.get("SnapId")
        if not isinstance(snap_id, int):
            summary["failed"] += 1
            continue

        image_path = f"ingest_{snap_id}.jpg"
        if image_path in existing:
            summary["already_present"] += 1
            continue

        face_image = row.get("FaceImage")
        if not isinstance(face_image, str) or not face_image:
            summary["failed"] += 1
            continue

        face_id = row.get("MatchedFaceId") or 0
        name = face_id_map.get(int(face_id)) if face_id else None
        if not name:
            unmapped[int(face_id)] += 1
            continue

        ts_utc = snapshots_mod._to_utc(row.get("StartTime"))
        if ts_utc is None:
            summary["failed"] += 1
            continue

        if dry_run:
            summary["added"] += 1
            continue

        stored = logs_service.record_capture(
            name=name,
            timestamp_iso=ts_utc.isoformat(),
            image_path=image_path,
            image_data=face_image,
        )
        if stored:
            summary["added"] += 1
            existing.add(image_path)
        else:
            summary["already_present"] += 1

    summary["unmapped_face_ids"] = dict(unmapped)
    return summary
