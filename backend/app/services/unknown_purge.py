"""Retention sweep for unknown-face clusters.

Hard-deletes IGNORED and MERGED clusters whose ``last_seen_at`` is
older than the configured retention window (default 14 days, tunable
via the runtime ``unknown_retention_days`` setting). Pass
``include_promoted=True`` to also reclaim disk for PROMOTED clusters
whose captures have already been migrated to the employee's training
images.

**PENDING clusters are never touched** — they're still in the admin's
review queue.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..config import UNKNOWNS_DIR
from ..models import UnknownClusterStatus, UnknownFaceCapture, UnknownFaceCluster
from .unknown_capture import UnknownCaptureService
from .unknown_config import get_unknown_settings

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class PurgeOutcome:
    cutoff: datetime
    clusters_examined: int
    clusters_deleted: int
    captures_deleted: int
    files_deleted: int
    bytes_freed: int


class UnknownPurgeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def purge(
        self,
        *,
        max_age_days: Optional[int] = None,
        include_promoted: bool = False,
    ) -> PurgeOutcome:
        settings = get_unknown_settings(self.db)
        days = int(max_age_days) if max_age_days is not None else int(settings.retention_days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        statuses: list[UnknownClusterStatus] = [
            UnknownClusterStatus.IGNORED,
            UnknownClusterStatus.MERGED,
        ]
        if include_promoted:
            statuses.append(UnknownClusterStatus.PROMOTED)

        candidates = self._list_for_purge(statuses=statuses, max_last_seen=cutoff)

        clusters_deleted = 0
        captures_deleted = 0
        files_deleted = 0
        bytes_freed = 0

        unknowns_root = Path(UNKNOWNS_DIR)

        for cluster in candidates:
            captures = self.db.execute(
                select(UnknownFaceCapture).where(UnknownFaceCapture.cluster_id == cluster.id)
            ).scalars().all()
            for cap in captures:
                p = Path(cap.file_path)
                if p.exists():
                    try:
                        size = p.stat().st_size
                        p.unlink()
                        files_deleted += 1
                        bytes_freed += size
                    except OSError as exc:
                        log.warning("Failed to remove capture file %s: %s", p, exc)
                self.db.delete(cap)
                captures_deleted += 1

            cluster_dir = unknowns_root / f"cluster_{cluster.id}"
            if cluster_dir.exists():
                try:
                    shutil.rmtree(cluster_dir, ignore_errors=True)
                except OSError as exc:
                    log.warning("Failed to remove cluster dir %s: %s", cluster_dir, exc)

            UnknownCaptureService.reset_cooldown(cluster.id)
            self.db.delete(cluster)
            clusters_deleted += 1

        self.db.flush()
        UnknownCaptureService.invalidate_match_cache()
        log.info(
            "Unknowns purge: cutoff=%s examined=%d clusters=%d captures=%d files=%d bytes=%d",
            cutoff.isoformat(), len(candidates), clusters_deleted, captures_deleted,
            files_deleted, bytes_freed,
        )
        return PurgeOutcome(
            cutoff=cutoff,
            clusters_examined=len(candidates),
            clusters_deleted=clusters_deleted,
            captures_deleted=captures_deleted,
            files_deleted=files_deleted,
            bytes_freed=bytes_freed,
        )

    def _list_for_purge(
        self,
        *,
        statuses: Iterable[UnknownClusterStatus],
        max_last_seen: datetime,
    ) -> list[UnknownFaceCluster]:
        statuses_list = list(statuses)
        if not statuses_list:
            return []
        rows = self.db.execute(
            select(UnknownFaceCluster)
            .where(
                and_(
                    UnknownFaceCluster.status.in_(statuses_list),
                    UnknownFaceCluster.last_seen_at < max_last_seen,
                )
            )
            .order_by(UnknownFaceCluster.last_seen_at.asc())
        ).scalars().all()
        return list(rows)
