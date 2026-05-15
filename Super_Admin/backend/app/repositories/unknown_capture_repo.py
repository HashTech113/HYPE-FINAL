from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, func, select

from app.core.constants import UnknownCaptureStatus, UnknownClusterStatus
from app.models.unknown_face import UnknownFaceCapture, UnknownFaceCluster
from app.repositories.base_repo import BaseRepository


class UnknownCaptureRepository(BaseRepository[UnknownFaceCapture]):
    model = UnknownFaceCapture

    # ------------------------------------------------------------------
    # Centroid recomputation — pull every KEEP embedding for a cluster
    # ------------------------------------------------------------------

    def list_keep_embeddings_for_cluster(self, cluster_id: int) -> list[tuple[bytes, int]]:
        """Return `(embedding_bytes, embedding_dim)` for every KEEP capture in
        the cluster, ordered oldest-first so callers can deterministically
        identify the oldest member when enforcing per-cluster caps.
        """
        stmt = (
            select(UnknownFaceCapture.embedding, UnknownFaceCapture.embedding_dim)
            .where(
                and_(
                    UnknownFaceCapture.cluster_id == cluster_id,
                    UnknownFaceCapture.status == UnknownCaptureStatus.KEEP,
                )
            )
            .order_by(UnknownFaceCapture.captured_at.asc())
        )
        return [(bytes(r[0]), int(r[1])) for r in self.db.execute(stmt).all()]

    def list_keep_quality_ranked(self, cluster_id: int) -> list[UnknownFaceCapture]:
        """Highest-quality KEEP captures first — used by the promotion
        service to pick the best images when training a new employee.
        Ordered by `det_score` desc, then `sharpness_score` desc as a
        tie-break.
        """
        stmt = (
            select(UnknownFaceCapture)
            .where(
                and_(
                    UnknownFaceCapture.cluster_id == cluster_id,
                    UnknownFaceCapture.status == UnknownCaptureStatus.KEEP,
                )
            )
            .order_by(
                UnknownFaceCapture.det_score.desc(),
                UnknownFaceCapture.sharpness_score.desc(),
            )
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_keep_for_cluster(
        self, cluster_id: int, *, order_desc: bool = True
    ) -> list[UnknownFaceCapture]:
        order_col = (
            UnknownFaceCapture.captured_at.desc()
            if order_desc
            else UnknownFaceCapture.captured_at.asc()
        )
        stmt = (
            select(UnknownFaceCapture)
            .where(
                and_(
                    UnknownFaceCapture.cluster_id == cluster_id,
                    UnknownFaceCapture.status == UnknownCaptureStatus.KEEP,
                )
            )
            .order_by(order_col)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_all_for_cluster(self, cluster_id: int) -> list[UnknownFaceCapture]:
        stmt = (
            select(UnknownFaceCapture)
            .where(UnknownFaceCapture.cluster_id == cluster_id)
            .order_by(UnknownFaceCapture.captured_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_oldest_keep(self, cluster_id: int) -> UnknownFaceCapture | None:
        stmt = (
            select(UnknownFaceCapture)
            .where(
                and_(
                    UnknownFaceCapture.cluster_id == cluster_id,
                    UnknownFaceCapture.status == UnknownCaptureStatus.KEEP,
                )
            )
            .order_by(UnknownFaceCapture.captured_at.asc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def count_keep_for_cluster(self, cluster_id: int) -> int:
        stmt = select(func.count(UnknownFaceCapture.id)).where(
            and_(
                UnknownFaceCapture.cluster_id == cluster_id,
                UnknownFaceCapture.status == UnknownCaptureStatus.KEEP,
            )
        )
        return int(self.db.execute(stmt).scalar_one())

    def count_total(self, *, only_keep: bool = False) -> int:
        stmt = select(func.count(UnknownFaceCapture.id))
        if only_keep:
            stmt = stmt.where(UnknownFaceCapture.status == UnknownCaptureStatus.KEEP)
        return int(self.db.execute(stmt).scalar_one())

    def count_older_than(self, cutoff: datetime) -> int:
        stmt = select(func.count(UnknownFaceCapture.id)).where(
            UnknownFaceCapture.captured_at < cutoff
        )
        return int(self.db.execute(stmt).scalar_one())

    def list_keep_in_pending_clusters(
        self,
        *,
        model_name: str,
        recent_clusters_limit: int | None = None,
    ) -> list[UnknownFaceCapture]:
        """Every KEEP capture from every PENDING cluster — input for the
        global re-cluster pass and the per-frame "is this a known
        unknown" match.

        `recent_clusters_limit`:
          When set (typically passed by the per-frame matcher), limit
          the result to captures from the N most-recently-active
          pending clusters (ordered by latest_capture_at desc).
          Without this cap, a deployment that's been running for
          weeks accumulates thousands of pending clusters and the
          per-frame match becomes O(N) over all of them — at 4
          cameras × 5 fps × N captures, the matmul + DB fetch
          becomes the dominant CPU cost. Bounding to the most recent
          ~200 clusters preserves correctness (older clusters are
          almost never the right answer for a fresh face) while
          keeping match cost flat regardless of total cluster count.
        """
        if recent_clusters_limit is not None and recent_clusters_limit > 0:
            # Two-step: pick the most-recently-touched pending cluster
            # ids first, then fetch their captures. Avoids a pathological
            # join-then-limit plan.
            recent_stmt = (
                select(UnknownFaceCluster.id)
                .where(UnknownFaceCluster.status == UnknownClusterStatus.PENDING)
                .order_by(UnknownFaceCluster.last_seen_at.desc().nulls_last())
                .limit(recent_clusters_limit)
            )
            cluster_ids = [int(r) for r in self.db.execute(recent_stmt).scalars().all()]
            if not cluster_ids:
                return []
            stmt = (
                select(UnknownFaceCapture)
                .where(
                    and_(
                        UnknownFaceCapture.status == UnknownCaptureStatus.KEEP,
                        UnknownFaceCapture.model_name == model_name,
                        UnknownFaceCapture.cluster_id.in_(cluster_ids),
                    )
                )
                .order_by(
                    UnknownFaceCapture.cluster_id.asc(),
                    UnknownFaceCapture.captured_at.asc(),
                )
            )
            return list(self.db.execute(stmt).scalars().all())

        stmt = (
            select(UnknownFaceCapture)
            .join(
                UnknownFaceCluster,
                UnknownFaceCluster.id == UnknownFaceCapture.cluster_id,
            )
            .where(
                and_(
                    UnknownFaceCapture.status == UnknownCaptureStatus.KEEP,
                    UnknownFaceCluster.status == UnknownClusterStatus.PENDING,
                    UnknownFaceCapture.model_name == model_name,
                )
            )
            .order_by(
                UnknownFaceCapture.cluster_id.asc(),
                UnknownFaceCapture.captured_at.asc(),
            )
        )
        return list(self.db.execute(stmt).scalars().all())
