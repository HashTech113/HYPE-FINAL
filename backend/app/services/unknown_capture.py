"""Unknown-face capture + online clustering.

Invoked from ``recognition_worker.py`` whenever a detected face fails
to match an enrolled employee. Decides:

  1. **Whether to keep it** — quality gate (size, det_score, sharpness).
  2. **Which cluster it belongs to** — k-NN match against every KEEP
     capture in every PENDING cluster (sub-millisecond matmul, with a
     5-second TTL cache so a 20 fps detection rate doesn't slam the DB).
  3. **Cooldown** — one capture per cluster per
     ``capture_cooldown_seconds`` so a person standing in front of a
     camera doesn't fill the cluster with dozens of near-identical
     crops.
  4. **Persist** — write the JPG to disk, insert the capture row, cap
     each cluster at ``_PER_CLUSTER_KEEP_CAP`` KEEP captures, then
     recompute the L2-normalized centroid.

Anti-drift design: matching is against individual captures (with a
"corroboration" rule: a cluster of ≥2 captures needs ≥2 hits above
threshold), not centroids. A single moving centroid would drift as
captures accumulated and create the "two different people, one cluster"
bug.

Ported from the Super_Admin reference implementation. Queries are
inlined here rather than going through a repository layer to match the
rest of this backend's services package.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar, Optional

import numpy as np
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..config import UNKNOWNS_DIR
from ..models import UnknownCaptureStatus, UnknownClusterStatus
from ..models import UnknownFaceCapture, UnknownFaceCluster
from .face_quality import (
    FaceQualityMetrics,
    QualityThresholds,
    measure_and_evaluate,
)
from .face_service import DetectedFace
from .image_utils import crop_bbox, write_jpeg
from .unknown_config import UnknownSettings, get_unknown_settings

log = logging.getLogger(__name__)

_EMBEDDING_DIM = 512
_MODEL_NAME = "buffalo_l"
_PER_CLUSTER_KEEP_CAP = 30
_CROP_PAD_RATIO = 0.25
_JPEG_QUALITY = 88
# Per-frame match search bound — only the 50 most-recently-active
# PENDING clusters are considered. Anything older is almost never the
# right home for a fresh face, and bounding the IN-list keeps the
# per-frame query in milliseconds even after weeks of accumulated state.
_PER_FRAME_CLUSTER_LIMIT = 50
# Match-input TTL — collapse N detections/sec into 1 DB query / N sec.
_MATCH_CACHE_TTL_SECONDS = 5.0


@dataclass(frozen=True)
class UnknownCaptureOutcome:
    accepted: bool
    reason: str
    cluster_id: Optional[int]
    capture_id: Optional[int]
    cluster_was_new: bool
    match_score: float
    metrics: Optional[FaceQualityMetrics]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UnknownCaptureService:
    """One instance per DB session (same lifetime pattern as other services
    in this package). Cooldown and the match-input cache are class-level so
    they're shared across instances + threads.
    """

    _cooldown_lock: ClassVar[threading.Lock] = threading.Lock()
    _last_capture_monotonic: ClassVar[dict[int, float]] = {}

    _match_cache_lock: ClassVar[threading.Lock] = threading.Lock()
    _match_cache: ClassVar[
        Optional[tuple[float, Optional[np.ndarray], list[int], dict[int, int]]]
    ] = None

    @classmethod
    def invalidate_match_cache(cls) -> None:
        """Force the next match call to re-query the DB. Call after any
        write that affects PENDING-cluster KEEP captures."""
        with cls._match_cache_lock:
            cls._match_cache = None

    @classmethod
    def reset_cooldown(cls, cluster_id: int) -> None:
        with cls._cooldown_lock:
            cls._last_capture_monotonic.pop(cluster_id, None)

    @classmethod
    def clear_cooldowns(cls) -> None:
        with cls._cooldown_lock:
            cls._last_capture_monotonic.clear()

    def __init__(self, db: Session) -> None:
        self.db = db
        self._unknowns_dir = Path(UNKNOWNS_DIR)

    # ------------------------------------------------------------------
    # Public entry point — called from the recognition worker.
    # ------------------------------------------------------------------

    def maybe_capture(
        self,
        *,
        face: DetectedFace,
        frame_bgr: np.ndarray,
        camera_id: Optional[int],
        captured_at: Optional[datetime] = None,
    ) -> UnknownCaptureOutcome:
        """Try to capture and cluster one unmatched face.

        Predictable rejections (disabled / quality fail / cooldown /
        malformed embedding) return an outcome dataclass. Infrastructure
        errors (DB, disk I/O) propagate so the caller's surrounding
        transaction can roll back cleanly.
        """
        ts = captured_at or _utc_now()
        return self._process(face=face, frame_bgr=frame_bgr, camera_id=camera_id, captured_at=ts)

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    def _process(
        self,
        *,
        face: DetectedFace,
        frame_bgr: np.ndarray,
        camera_id: Optional[int],
        captured_at: datetime,
    ) -> UnknownCaptureOutcome:
        settings = get_unknown_settings(self.db)
        if not settings.enabled:
            return UnknownCaptureOutcome(False, "disabled", None, None, False, 0.0, None)

        # 1) Quality gate
        thresholds = QualityThresholds(
            min_face_size_px=settings.min_face_size_px,
            min_det_score=settings.min_face_quality,
            min_sharpness=settings.min_sharpness,
        )
        verdict = measure_and_evaluate(
            frame_bgr=frame_bgr,
            bbox=face.bbox,
            kps=face.kps,
            det_score=face.det_score,
            thresholds=thresholds,
        )
        if not verdict.accepted:
            return UnknownCaptureOutcome(
                False, f"quality:{verdict.reason}", None, None, False, 0.0, verdict.metrics
            )

        # 2) Normalize embedding
        emb = self._normalize(face.embedding)
        if emb is None:
            return UnknownCaptureOutcome(
                False, "error:zero_norm_embedding", None, None, False, 0.0, verdict.metrics
            )

        # 3) Find best matching PENDING cluster
        match_id, match_score = self._find_best_match(emb, settings.cluster_match_threshold)

        cluster_was_new = False
        if match_id is None:
            cluster = self._create_cluster(emb=emb, captured_at=captured_at)
            cluster_was_new = True
        else:
            cluster = self.db.get(UnknownFaceCluster, match_id)
            if cluster is None:
                # Race: cluster was removed between match and load. Fall back
                # to a fresh cluster so we don't drop the face.
                cluster = self._create_cluster(emb=emb, captured_at=captured_at)
                cluster_was_new = True

        # 4) Per-cluster cooldown — skipped for brand-new clusters since
        # we want their first capture to land.
        if not cluster_was_new and not self._cooldown_allow(
            cluster.id, settings.capture_cooldown_seconds
        ):
            return UnknownCaptureOutcome(
                False, "cooldown", cluster.id, None, False, match_score, verdict.metrics
            )

        # 5) Crop + write JPEG
        out_path = self._build_path(cluster.id, captured_at)
        crop = crop_bbox(frame_bgr, face.bbox, pad=_CROP_PAD_RATIO)
        if crop.size == 0:
            crop = frame_bgr
        write_jpeg(out_path, crop, quality=_JPEG_QUALITY)

        # 6) Insert capture row
        x1, y1, x2, y2 = face.bbox
        capture = UnknownFaceCapture(
            cluster_id=cluster.id,
            file_path=str(out_path),
            embedding=emb.tobytes(),
            embedding_dim=int(emb.size),
            model_name=_MODEL_NAME,
            camera_id=camera_id,
            bbox_x=int(x1),
            bbox_y=int(y1),
            bbox_w=int(x2 - x1),
            bbox_h=int(y2 - y1),
            det_score=float(face.det_score),
            sharpness_score=float(verdict.metrics.sharpness),
            captured_at=captured_at,
            status=UnknownCaptureStatus.KEEP,
        )
        self.db.add(capture)
        self.db.flush()

        # 7) Per-cluster cap — demote oldest KEEP if over
        self._enforce_per_cluster_cap(cluster.id)

        # 8) Recompute centroid + counters
        new_centroid, new_count = self._recompute_centroid(cluster.id)
        if new_centroid is not None:
            cluster.centroid = new_centroid.tobytes()
            cluster.centroid_dim = int(new_centroid.size)
            cluster.member_count = new_count
            cluster.last_seen_at = captured_at
            self.db.flush()

        # 9) Bookkeeping
        self._cooldown_set(cluster.id)
        self.invalidate_match_cache()

        log.info(
            "Unknown captured cluster_id=%s capture_id=%s new=%s match_score=%.3f cam=%s",
            cluster.id, capture.id, cluster_was_new, match_score, camera_id,
        )
        return UnknownCaptureOutcome(
            accepted=True,
            reason="ok",
            cluster_id=cluster.id,
            capture_id=capture.id,
            cluster_was_new=cluster_was_new,
            match_score=match_score,
            metrics=verdict.metrics,
        )

    # ------------------------------------------------------------------
    # Matching helpers
    # ------------------------------------------------------------------

    def _find_best_match(self, query: np.ndarray, threshold: float) -> tuple[Optional[int], float]:
        """K-NN against individual KEEP captures, with corroboration.

        Anti-drift rule: a cluster of ≥2 captures needs at least 2 hits
        above ``threshold`` to win. A single-capture cluster can match
        on one hit so newly-created clusters can grow.
        """
        matrix, cluster_ids, cluster_total = self._load_match_input()
        if matrix is None or matrix.shape[0] == 0:
            return None, 0.0

        sims = matrix @ query

        cluster_hits: dict[int, list[float]] = {}
        for cid, s in zip(cluster_ids, sims, strict=False):
            if float(s) >= threshold:
                cluster_hits.setdefault(cid, []).append(float(s))

        if not cluster_hits:
            return None, float(sims.max())

        best_cluster: Optional[int] = None
        best_score: float = -1.0
        for cid, hit_sims in cluster_hits.items():
            required = 1 if cluster_total[cid] == 1 else 2
            if len(hit_sims) < required:
                continue
            top = sorted(hit_sims, reverse=True)[:3]
            score = sum(top) / len(top)
            if score > best_score:
                best_score = score
                best_cluster = cid

        if best_cluster is None:
            return None, float(sims.max())
        return best_cluster, best_score

    def _load_match_input(
        self,
    ) -> tuple[Optional[np.ndarray], list[int], dict[int, int]]:
        """Return ``(matrix, cluster_ids_per_row, total_per_cluster)``.

        Honors a class-level TTL cache to amortise the DB roundtrip
        across many detections.
        """
        now = time.monotonic()
        with self._match_cache_lock:
            cached = self._match_cache
            if cached is not None and (now - cached[0]) < _MATCH_CACHE_TTL_SECONDS:
                _, m, ids, totals = cached
                return m, ids, dict(totals)

        # Two-step query so the planner doesn't fall into a pathological
        # join-then-limit plan: recent PENDING cluster ids first, then
        # their KEEP captures.
        recent_ids = [
            int(r) for r in self.db.execute(
                select(UnknownFaceCluster.id)
                .where(UnknownFaceCluster.status == UnknownClusterStatus.PENDING)
                .order_by(UnknownFaceCluster.last_seen_at.desc())
                .limit(_PER_FRAME_CLUSTER_LIMIT)
            ).scalars().all()
        ]
        if not recent_ids:
            with self._match_cache_lock:
                UnknownCaptureService._match_cache = (time.monotonic(), None, [], {})
            return None, [], {}

        captures = self.db.execute(
            select(UnknownFaceCapture)
            .where(
                and_(
                    UnknownFaceCapture.status == UnknownCaptureStatus.KEEP,
                    UnknownFaceCapture.model_name == _MODEL_NAME,
                    UnknownFaceCapture.cluster_id.in_(recent_ids),
                )
            )
            .order_by(
                UnknownFaceCapture.cluster_id.asc(),
                UnknownFaceCapture.captured_at.asc(),
            )
        ).scalars().all()

        cluster_ids: list[int] = []
        vectors: list[np.ndarray] = []
        cluster_total: dict[int, int] = {}
        for cap in captures:
            if int(cap.embedding_dim) != _EMBEDDING_DIM:
                continue
            try:
                vec = np.frombuffer(cap.embedding, dtype=np.float32)
            except (TypeError, ValueError):
                continue
            if vec.size != _EMBEDDING_DIM:
                continue
            cid = int(cap.cluster_id)
            cluster_ids.append(cid)
            vectors.append(vec)
            cluster_total[cid] = cluster_total.get(cid, 0) + 1

        matrix = np.vstack(vectors).astype(np.float32) if vectors else None

        with self._match_cache_lock:
            UnknownCaptureService._match_cache = (
                time.monotonic(), matrix, cluster_ids, dict(cluster_total),
            )
        return matrix, cluster_ids, cluster_total

    # ------------------------------------------------------------------
    # Cluster lifecycle
    # ------------------------------------------------------------------

    def _create_cluster(self, *, emb: np.ndarray, captured_at: datetime) -> UnknownFaceCluster:
        cluster = UnknownFaceCluster(
            label=None,
            centroid=emb.tobytes(),
            centroid_dim=int(emb.size),
            model_name=_MODEL_NAME,
            member_count=0,
            first_seen_at=captured_at,
            last_seen_at=captured_at,
            status=UnknownClusterStatus.PENDING,
        )
        self.db.add(cluster)
        self.db.flush()
        return cluster

    def _enforce_per_cluster_cap(self, cluster_id: int) -> None:
        count = int(
            self.db.execute(
                select(func.count(UnknownFaceCapture.id)).where(
                    and_(
                        UnknownFaceCapture.cluster_id == cluster_id,
                        UnknownFaceCapture.status == UnknownCaptureStatus.KEEP,
                    )
                )
            ).scalar_one()
        )
        if count <= _PER_CLUSTER_KEEP_CAP:
            return
        oldest = self.db.execute(
            select(UnknownFaceCapture)
            .where(
                and_(
                    UnknownFaceCapture.cluster_id == cluster_id,
                    UnknownFaceCapture.status == UnknownCaptureStatus.KEEP,
                )
            )
            .order_by(UnknownFaceCapture.captured_at.asc())
            .limit(1)
        ).scalar_one_or_none()
        if oldest is None:
            return
        oldest.status = UnknownCaptureStatus.DISCARDED
        self.db.flush()

    def _recompute_centroid(self, cluster_id: int) -> tuple[Optional[np.ndarray], int]:
        rows = self.db.execute(
            select(UnknownFaceCapture.embedding, UnknownFaceCapture.embedding_dim)
            .where(
                and_(
                    UnknownFaceCapture.cluster_id == cluster_id,
                    UnknownFaceCapture.status == UnknownCaptureStatus.KEEP,
                )
            )
            .order_by(UnknownFaceCapture.captured_at.asc())
        ).all()
        if not rows:
            return None, 0
        vectors: list[np.ndarray] = []
        for blob, dim in rows:
            arr = np.frombuffer(blob, dtype=np.float32)
            if arr.size != dim or arr.size != _EMBEDDING_DIM:
                continue
            vectors.append(arr)
        if not vectors:
            return None, 0
        mat = np.vstack(vectors).astype(np.float32)
        mean = mat.mean(axis=0)
        n = float(np.linalg.norm(mean))
        if n <= 0.0:
            return None, len(vectors)
        return (mean / n).astype(np.float32), len(vectors)

    # ------------------------------------------------------------------
    # External-facing helper for the router's per-capture delete
    # ------------------------------------------------------------------

    def demote_capture_and_recompute(
        self,
        *,
        capture: UnknownFaceCapture,
        cluster_id: int,
    ) -> None:
        """Mark one capture DISCARDED and rebuild its cluster's centroid.

        If the cluster ends up empty (every KEEP demoted), it's moved
        to IGNORED so it stops being matched against new faces.
        """
        capture.status = UnknownCaptureStatus.DISCARDED
        self.db.flush()

        cluster = self.db.get(UnknownFaceCluster, cluster_id)
        if cluster is None:
            return

        new_centroid, new_count = self._recompute_centroid(cluster_id)
        if new_centroid is None or new_count == 0:
            cluster.status = UnknownClusterStatus.IGNORED
            cluster.member_count = 0
            self.db.flush()
            self.reset_cooldown(cluster_id)
            self.invalidate_match_cache()
            return

        cluster.centroid = new_centroid.tobytes()
        cluster.centroid_dim = int(new_centroid.size)
        cluster.member_count = new_count
        self.db.flush()
        self.invalidate_match_cache()

    # ------------------------------------------------------------------
    # Cooldown bookkeeping
    # ------------------------------------------------------------------

    def _cooldown_allow(self, cluster_id: int, cooldown_seconds: int) -> bool:
        if cooldown_seconds <= 0:
            return True
        now = time.monotonic()
        with self._cooldown_lock:
            last = self._last_capture_monotonic.get(cluster_id)
            return last is None or (now - last) >= float(cooldown_seconds)

    def _cooldown_set(self, cluster_id: int) -> None:
        now = time.monotonic()
        with self._cooldown_lock:
            self._last_capture_monotonic[cluster_id] = now

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(vec: np.ndarray) -> Optional[np.ndarray]:
        v = np.asarray(vec, dtype=np.float32).ravel()
        if v.size != _EMBEDDING_DIM:
            return None
        n = float(np.linalg.norm(v))
        if n <= 0.0:
            return None
        return (v / n).astype(np.float32)

    def _build_path(self, cluster_id: int, captured_at: datetime) -> Path:
        # Storage layout: ``<UNKNOWNS_DIR>/cluster_<id>/<YYYYMMDD-HHMMSS>_<uuid>.jpg``
        local_ts = captured_at.astimezone() if captured_at.tzinfo else captured_at
        filename = f"{local_ts.strftime('%Y%m%d-%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
        return self._unknowns_dir / f"cluster_{cluster_id}" / filename


__all__ = [
    "UnknownCaptureService",
    "UnknownCaptureOutcome",
    "UnknownSettings",
]
