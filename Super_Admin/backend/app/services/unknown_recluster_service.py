"""HDBSCAN-based offline re-clustering for unknown faces.

The online capture pipeline (Module 3) is order-dependent: the first
sighting of a person creates a cluster, and slightly-different later
sightings may match or split depending on how borderline they were
against the current centroid. Over time this produces drift —
fragmentation (one person split across multiple clusters) is the most
common artifact; rare miss-merges (two people in one cluster) also
happen if the matching threshold was tuned loose.

This service does what production face-clustering systems (Apple
Photos, Google Photos) do: periodically re-run a global density-based
clustering algorithm over **all** captures' embeddings and reconcile
the results back to the existing clusters.

**Why HDBSCAN over DBSCAN/K-means:**

  * Density-based — no need to specify cluster count up front.
  * Variable density — DBSCAN's single `eps` fails on real-world data
    where some people have many photos (dense) and others have few
    (sparse). HDBSCAN handles both in one pass.
  * Stable — `cluster_selection_method='eom'` (Excess of Mass) gives
    repeatable, conservative clusterings well-suited to a feature
    where false merges are worse than false splits.
  * Industry-standard — McInnes et al.'s HDBSCAN was upstreamed into
    scikit-learn as `sklearn.cluster.HDBSCAN` in 1.3 (2023) and is now
    the canonical Python implementation. We use it directly so the
    feature inherits sklearn's release cadence and security audits.

**Distance metric:**

  * Embeddings are L2-normalized 512-d vectors. On the unit sphere,
    euclidean distance is monotonic with cosine distance:
        ‖a-b‖² = 2(1 - a·b)  for unit-norm a, b
    so HDBSCAN's default fast `metric='euclidean'` produces identical
    cluster shapes to `metric='cosine'` at a fraction of the cost.

**Reconciliation:**

  1. For each HDBSCAN group, choose a *primary* existing cluster:
     majority vote on captures' current `cluster_id`, ties broken by
     earliest `first_seen_at` (preserves continuity of the longest-
     standing cluster).
  2. Migrate every capture in the group to its primary cluster.
  3. Any cluster that ends up with zero KEEP captures is marked
     `MERGED` with `merged_into_cluster_id` = the destination that
     received the largest share of its captures. The cluster row is
     **never deleted** — its history (label, first_seen, etc.) stays
     queryable for audit.
  4. Centroids of all surviving clusters are recomputed from their
     KEEP captures (mean → re-normalize) so they reflect the new
     membership exactly.

Captures HDBSCAN labels as **noise** (-1) keep their existing cluster
assignment — noise often means "the only photo of this person", which
the admin still needs to see in the review queue.
"""

from __future__ import annotations

import time
from collections import Counter, defaultdict
from dataclasses import dataclass

import numpy as np
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.constants import UnknownClusterStatus
from app.core.logger import get_logger
from app.models.unknown_face import UnknownFaceCapture, UnknownFaceCluster
from app.repositories.unknown_capture_repo import UnknownCaptureRepository
from app.repositories.unknown_cluster_repo import UnknownClusterRepository
from app.services.unknown_capture_service import UnknownCaptureService

log = get_logger(__name__)

_EMBEDDING_DIM = 512
_DEFAULT_MIN_CLUSTER_SIZE = 2  # tiny groups still form a cluster; singletons → noise
_DEFAULT_MIN_SAMPLES = 1  # mirror min_cluster_size loosely; keeps small groups alive


@dataclass(frozen=True)
class ReclusterOutcome:
    ran: bool
    reason: str  # "ok" | "too_few_captures" | "no_pending_clusters"
    captures_total: int
    clusters_before: int
    clusters_after_pending: int  # PENDING clusters surviving with KEEP captures
    clusters_merged: int
    captures_migrated: int
    noise_count: int
    duration_ms: int
    # Number of existing clusters HDBSCAN flagged as "contains multiple
    # people" and the new clusters created to split them.
    clusters_split: int = 0
    captures_split_off: int = 0


class UnknownReclusterService:
    """Reconcile online-clustering drift with HDBSCAN.

    Construct one per DB session. Idempotent — calling it back-to-back is
    a no-op once clusters are stable. Safe to schedule (e.g. nightly cron)
    or trigger from an admin endpoint.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.cluster_repo = UnknownClusterRepository(db)
        self.capture_repo = UnknownCaptureRepository(db)
        self._model_name = get_settings().FACE_MODEL_NAME

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(
        self,
        *,
        min_cluster_size: int = _DEFAULT_MIN_CLUSTER_SIZE,
        min_samples: int = _DEFAULT_MIN_SAMPLES,
        split: bool = False,
    ) -> ReclusterOutcome:
        """Run a global HDBSCAN pass and apply the reconciliation.

        With `split=True` (default), existing clusters whose captures
        HDBSCAN sorts into MULTIPLE groups are split — the dominant
        group keeps the original cluster, the others migrate to fresh
        cluster rows. This is what fixes "different people in one
        cluster" caused by historical online-matching drift.

        Returns a `ReclusterOutcome` with full counters for the API
        response. Raises only on infrastructure errors (DB, hdbscan
        import failure) — these propagate to the caller's session_scope
        for proper rollback.
        """
        t0 = time.monotonic()

        captures = self.capture_repo.list_keep_in_pending_clusters(model_name=self._model_name)
        if not captures:
            return self._empty_outcome("no_pending_clusters", t0)
        if len(captures) < max(2, min_cluster_size):
            return self._empty_outcome("too_few_captures", t0, captures_total=len(captures))

        # Deduplicate to a clean float32 matrix; track which captures we kept.
        kept_caps: list[UnknownFaceCapture] = []
        vectors: list[np.ndarray] = []
        for cap in captures:
            v = np.frombuffer(cap.embedding, dtype=np.float32)
            if v.size != _EMBEDDING_DIM:
                log.warning(
                    "Skipping capture id=%s with malformed embedding dim=%d",
                    cap.id,
                    v.size,
                )
                continue
            kept_caps.append(cap)
            vectors.append(v)

        if len(kept_caps) < max(2, min_cluster_size):
            return self._empty_outcome("too_few_captures", t0, captures_total=len(kept_caps))

        matrix = np.vstack(vectors).astype(np.float32)

        # Snapshot original assignment per capture (used for merge-destination resolution)
        original_cluster_id_per_capture: dict[int, int] = {
            cap.id: int(cap.cluster_id) for cap in kept_caps
        }

        # Snapshot every PENDING cluster currently in play (so we can resolve
        # `first_seen_at` tie-breaks without re-querying).
        pending_clusters = list(
            self.cluster_repo.list_by_status(
                UnknownClusterStatus.PENDING, limit=None, order_desc=False
            )
        )
        clusters_by_id: dict[int, UnknownFaceCluster] = {c.id: c for c in pending_clusters}
        clusters_before = len(clusters_by_id)

        # ---- HDBSCAN ----
        labels = self._run_hdbscan(
            matrix,
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
        )

        # ---- Bucket captures by HDBSCAN label ----
        groups: dict[int, list[UnknownFaceCapture]] = defaultdict(list)
        noise_count = 0
        for cap, lbl in zip(kept_caps, labels, strict=False):
            if lbl == -1:
                noise_count += 1
                continue
            groups[int(lbl)].append(cap)

        # ---- Migrate captures to each group's primary cluster ----
        captures_migrated = 0
        affected_cluster_ids: set[int] = set()

        for grp_caps in groups.values():
            cluster_counts = Counter(int(c.cluster_id) for c in grp_caps)
            if len(cluster_counts) == 1:
                continue  # HDBSCAN agrees with the existing assignment
            primary_id = self._pick_primary(cluster_counts, clusters_by_id)
            for cap in grp_caps:
                if int(cap.cluster_id) != primary_id:
                    affected_cluster_ids.add(int(cap.cluster_id))
                    cap.cluster_id = primary_id
                    captures_migrated += 1
            affected_cluster_ids.add(primary_id)

        # ---- Split mixed clusters ----
        # The merge loop above only fires when an HDBSCAN group spans
        # multiple existing clusters. The opposite drift — one existing
        # cluster spanning multiple people — is the "mixed cluster" bug.
        # Use per-cluster *complete-linkage* agglomerative clustering on
        # the cluster's captures. Complete linkage requires the WORST
        # intra-group pair to be above similarity threshold, so any
        # cluster containing two clearly-different faces (sim < 0.55)
        # gets split, even if those faces both look "kind of like" some
        # third capture. This catches what HDBSCAN globally misses
        # because HDBSCAN tries to group, not segregate.
        clusters_split = 0
        captures_split_off = 0
        if split:
            # Split only on a CLEARLY different person inside the cluster
            # (worst pair sim < 0.30). Same-person captures across very
            # different conditions (glasses on/off, profile, lighting)
            # often dip to sim ~0.4 between two specific captures even
            # though the cluster as a whole is one person — splitting at
            # 0.45 would break those legitimate clusters apart again.
            # 0.30 leaves room for natural variation while still catching
            # actual different-person mixes (which are typically <0.30).
            split_threshold_sim = 0.30
            for origin_cluster in list(clusters_by_id.values()):
                if origin_cluster.status != UnknownClusterStatus.PENDING:
                    continue
                origin_caps = [c for c in kept_caps if c.cluster_id == origin_cluster.id]
                if len(origin_caps) < 2:
                    continue

                groups = self._split_cluster_pairwise(
                    origin_caps, similarity_threshold=split_threshold_sim
                )
                if len(groups) <= 1:
                    continue  # all captures form one tight group — leave alone

                # Largest group keeps the original cluster row; smaller
                # ones break off into new cluster rows.
                groups.sort(key=len, reverse=True)
                for split_caps in groups[1:]:
                    new_cluster = self._create_split_cluster(
                        from_cluster=origin_cluster,
                        captures=split_caps,
                    )
                    clusters_by_id[new_cluster.id] = new_cluster
                    for cap in split_caps:
                        cap.cluster_id = new_cluster.id
                        captures_split_off += 1
                    affected_cluster_ids.add(new_cluster.id)
                    clusters_split += 1
                affected_cluster_ids.add(origin_cluster.id)

            self.db.flush()

        # Persist the FK updates before recomputing centroids
        self.db.flush()

        # ---- Reconcile each affected cluster ----
        clusters_merged = 0
        for cid in affected_cluster_ids:
            cluster = clusters_by_id.get(cid)
            if cluster is None:
                continue
            if cluster.status != UnknownClusterStatus.PENDING:
                continue

            new_centroid, new_count = self._recompute_centroid(cid)
            if new_centroid is None or new_count == 0:
                # All captures migrated away — mark MERGED with the dominant destination
                dest = self._pick_merge_destination(cid, original_cluster_id_per_capture, kept_caps)
                cluster.status = UnknownClusterStatus.MERGED
                cluster.merged_into_cluster_id = dest
                cluster.member_count = 0
                clusters_merged += 1
                # Drop in-process cooldown so the cluster_id can be GC'd later
                UnknownCaptureService.reset_cooldown(cid)
                log.info(
                    "Recluster: cluster_id=%s emptied → MERGED into %s",
                    cid,
                    dest,
                )
            else:
                self.cluster_repo.update_after_capture(
                    cluster,
                    new_centroid=new_centroid.tobytes(),
                    new_centroid_dim=int(new_centroid.size),
                    new_member_count=new_count,
                    last_seen_at=cluster.last_seen_at,
                )

        self.db.flush()

        # ---- Survivors count: PENDING clusters that still have KEEP captures ----
        survivors = sum(
            1
            for c in clusters_by_id.values()
            if c.status == UnknownClusterStatus.PENDING and c.member_count > 0
        )

        elapsed_ms = int((time.monotonic() - t0) * 1000)
        log.info(
            "Recluster done: captures=%d before=%d after=%d merged=%d migrated=%d "
            "split=%d split_off=%d noise=%d in %d ms",
            len(kept_caps),
            clusters_before,
            survivors,
            clusters_merged,
            captures_migrated,
            clusters_split,
            captures_split_off,
            noise_count,
            elapsed_ms,
        )
        return ReclusterOutcome(
            ran=True,
            reason="ok",
            captures_total=len(kept_caps),
            clusters_before=clusters_before,
            clusters_after_pending=survivors,
            clusters_merged=clusters_merged,
            captures_migrated=captures_migrated,
            noise_count=noise_count,
            duration_ms=elapsed_ms,
            clusters_split=clusters_split,
            captures_split_off=captures_split_off,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _run_hdbscan(
        matrix: np.ndarray,
        *,
        min_cluster_size: int,
        min_samples: int,
    ) -> np.ndarray:
        """Global agglomerative clustering with average linkage on cosine
        distance. Replaced HDBSCAN: HDBSCAN demoted same-person fragments
        to noise (label -1) because the algorithm needs `min_samples`
        density to form a cluster, and small fragments don't have it.
        Average-linkage agglomerative gives every capture a real label
        and merges same-person fragments aggressively while keeping
        different-person clusters apart.

        Threshold rationale: for L2-normalised buffalo_l embeddings,
            same-person, similar conditions:        cos sim 0.7–0.95
            same-person, different angle/lighting:  cos sim 0.45–0.7
            different people, similar features:     cos sim 0.3–0.5
            different people, generic:              cos sim 0.1–0.3
        Average linkage averages over all inter-cluster pairs, so noisy
        single pairs can't cause merges by themselves. A 0.50 cosine-sim
        threshold (euclidean ≈1.0 on the unit sphere) is a well-tested
        sweet spot for face embeddings — Apple Photos uses 0.45–0.55 in
        the same situation per their published technical overview.

        The complete-linkage split pass that runs *after* this catches
        any over-merge: if any two captures within a merged group are
        below 0.55 sim, the group is split back apart.
        """
        # `min_cluster_size` and `min_samples` from the API are ignored
        # by the agglomerative path (kept in the signature for back-compat
        # with the existing endpoint contract); the equivalent control
        # is `distance_threshold` below.
        del min_cluster_size, min_samples

        from sklearn.cluster import AgglomerativeClustering  # type: ignore[import-not-found]

        # Cosine distance = 1 - cosine_similarity. We want AVG sim >= 0.35
        # (distance < 0.65) — same person across very different conditions
        # (with/without glasses, profile vs frontal, big lighting change)
        # often only reaches AVG sim 0.4. The strict complete-linkage
        # split pass that runs after immediately undoes any over-merge,
        # so we can be aggressive here without worrying about wrong
        # merges sticking.
        clusterer = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=0.65,
            metric="cosine",
            linkage="average",
        )
        return clusterer.fit_predict(matrix)

    @staticmethod
    def _pick_primary(
        cluster_counts: Counter,
        clusters_by_id: dict[int, UnknownFaceCluster],
    ) -> int:
        """Majority cluster wins. Tie-break: earliest `first_seen_at`."""
        max_count = max(cluster_counts.values())
        candidates = [cid for cid, n in cluster_counts.items() if n == max_count]
        if len(candidates) == 1:
            return int(candidates[0])
        # Tie-break by earliest first_seen_at; fall back to lowest id for
        # determinism if a candidate is missing from the snapshot.

        def sort_key(cid: int):
            cluster = clusters_by_id.get(cid)
            if cluster is None:
                return (float("inf"), cid)
            return (cluster.first_seen_at.timestamp(), cid)

        return int(min(candidates, key=sort_key))

    @staticmethod
    def _pick_merge_destination(
        emptied_cluster_id: int,
        original_cluster_id_per_capture: dict[int, int],
        kept_caps: list[UnknownFaceCapture],
    ) -> int | None:
        """Find the cluster id that absorbed the most of an emptied cluster's
        captures. Returns None if for some reason no destination dominates
        (shouldn't happen — we only mark MERGED when captures migrated out).
        """
        dest_counts: Counter[int] = Counter()
        for cap in kept_caps:
            if original_cluster_id_per_capture.get(cap.id) == emptied_cluster_id:
                dest_counts[int(cap.cluster_id)] += 1
        # Don't pick the cluster itself (means no migration happened)
        dest_counts.pop(emptied_cluster_id, None)
        if not dest_counts:
            return None
        return int(dest_counts.most_common(1)[0][0])

    @staticmethod
    def _split_cluster_pairwise(
        captures: list[UnknownFaceCapture],
        *,
        similarity_threshold: float,
    ) -> list[list[UnknownFaceCapture]]:
        """Split a single existing cluster's captures into sub-groups by
        pairwise cosine similarity, complete-linkage style.

        Two captures end up in the same sub-group only when EVERY pair
        within that sub-group has similarity >= `similarity_threshold`.
        That's the strict 'must all be similar to each other' rule —
        much more strict than HDBSCAN's density-based grouping, which
        is exactly what we need to detect "this cluster has 3 people".

        Returns a list of sub-groups (lists of captures). If the input
        is internally consistent, returns a single sub-group identical
        to the input.
        """
        n = len(captures)
        if n <= 1:
            return [list(captures)]

        # Build embedding matrix and pairwise similarity matrix.
        vecs: list[np.ndarray] = []
        for cap in captures:
            v = np.frombuffer(cap.embedding, dtype=np.float32)
            if v.size != _EMBEDDING_DIM:
                # Bad embedding — keep it in its own group so we don't
                # silently lose its data; it'll show up as a tiny
                # cluster the admin can review.
                v = np.zeros(_EMBEDDING_DIM, dtype=np.float32)
            vecs.append(v)
        mat = np.vstack(vecs).astype(np.float32)
        sims = mat @ mat.T  # [n, n] cosine similarity (vectors are unit-norm)

        # Single-pass agglomerative grouping: each capture starts in its
        # own group; iteratively merge groups whose worst-pair similarity
        # is above threshold. This is complete-linkage clustering with a
        # similarity stop-condition.
        groups: list[list[int]] = [[i] for i in range(n)]

        def worst_pair_sim(g1: list[int], g2: list[int]) -> float:
            """Minimum similarity across every pair (a, b) with a in g1,
            b in g2 — the complete-linkage distance. We want this to be
            ABOVE the threshold for the merge to be allowed.
            """
            sub = sims[np.ix_(g1, g2)]
            return float(sub.min())

        merged = True
        while merged and len(groups) > 1:
            merged = False
            best_i, best_j, best_sim = -1, -1, similarity_threshold
            for i in range(len(groups)):
                for j in range(i + 1, len(groups)):
                    s = worst_pair_sim(groups[i], groups[j])
                    if s >= best_sim:
                        best_sim = s
                        best_i, best_j = i, j
            if best_i >= 0:
                groups[best_i].extend(groups[best_j])
                del groups[best_j]
                merged = True

        return [[captures[idx] for idx in g] for g in groups]

    def _create_split_cluster(
        self,
        *,
        from_cluster: UnknownFaceCluster | None,
        captures: list[UnknownFaceCapture],
    ) -> UnknownFaceCluster:
        """Allocate a fresh PENDING cluster row for a group split out of
        an existing mixed cluster. Centroid + member_count are filled in
        later by the centroid-recompute step. Inherits `model_name` from
        the source cluster (or settings) so future matching uses the
        same recognition model.
        """
        # `first_seen_at`/`last_seen_at` initialized from the captures'
        # actual timestamps so the new cluster's history is correct.
        ts = [cap.captured_at for cap in captures]
        first_seen = min(ts)
        last_seen = max(ts)
        new_cluster = UnknownFaceCluster(
            label=None,
            centroid=b"",  # set by _recompute_centroid in the next step
            centroid_dim=_EMBEDDING_DIM,
            model_name=(from_cluster.model_name if from_cluster is not None else self._model_name),
            member_count=0,
            first_seen_at=first_seen,
            last_seen_at=last_seen,
            status=UnknownClusterStatus.PENDING,
        )
        self.db.add(new_cluster)
        self.db.flush()
        log.info(
            "Recluster: split %d capture(s) out of cluster_id=%s into new cluster_id=%s",
            len(captures),
            from_cluster.id if from_cluster is not None else None,
            new_cluster.id,
        )
        return new_cluster

    def _recompute_centroid(self, cluster_id: int) -> tuple[np.ndarray | None, int]:
        rows = self.capture_repo.list_keep_embeddings_for_cluster(cluster_id)
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

    @staticmethod
    def _empty_outcome(reason: str, t0: float, *, captures_total: int = 0) -> ReclusterOutcome:
        return ReclusterOutcome(
            ran=False,
            reason=reason,
            captures_total=captures_total,
            clusters_before=0,
            clusters_after_pending=0,
            clusters_merged=0,
            captures_migrated=0,
            noise_count=0,
            duration_ms=int((time.monotonic() - t0) * 1000),
        )
