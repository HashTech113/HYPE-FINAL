"""In-memory cache of every active employee's face embeddings.

Recognition is the hot path: for every detected face we compute cosine
similarity against the entire enrolled set. Pre-loading all embeddings
into a single numpy matrix and doing one ``matrix @ q`` matmul per face
is ~100× faster than running the equivalent SQL aggregation per match.

Cache invariant: ``self._matrix.shape[0] == len(self._ids)``. The two
parallel structures must always agree, otherwise recognition will map
similarities to the wrong employee_id silently. The asserts below blow
up loudly at load/delta time if the invariant ever drifts.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Optional

import numpy as np
from sqlalchemy import select

from ..db import session_scope
from ..models import Employee, FaceEmbedding

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class CacheEntry:
    employee_id: str
    employee_code: str
    employee_name: str
    vectors: np.ndarray  # (n, dim), L2-normalised


class EmbeddingCache:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: list[CacheEntry] = []
        self._matrix: Optional[np.ndarray] = None
        self._ids: list[str] = []

    @staticmethod
    def _unpack(raw: bytes, dim: int) -> np.ndarray:
        arr = np.frombuffer(raw, dtype=np.float32)
        if arr.size != dim:
            raise ValueError(f"vector size mismatch: expected {dim}, got {arr.size}")
        n = float(np.linalg.norm(arr))
        return (arr / n).astype(np.float32) if n > 0 else arr

    @staticmethod
    def pack(vec: np.ndarray) -> bytes:
        return np.ascontiguousarray(vec.astype(np.float32)).tobytes()

    def load_from_db(self) -> None:
        """Replace the entire in-memory cache with the current DB state.
        Cheap on small datasets (<10k vectors); use ``reload_employee``
        for incremental updates after a single training write."""
        with session_scope() as session:
            rows = session.execute(
                select(FaceEmbedding, Employee)
                .join(Employee, FaceEmbedding.employee_id == Employee.id)
                .where(Employee.is_active.is_(True))
            ).all()

            grouped: dict[str, list[np.ndarray]] = {}
            meta: dict[str, tuple[str, str]] = {}
            for emb, emp in rows:
                try:
                    v = self._unpack(emb.vector, int(emb.dim))
                except ValueError:
                    log.warning("Skipping corrupt embedding id=%s", emb.id)
                    continue
                grouped.setdefault(str(emp.id), []).append(v)
                meta[str(emp.id)] = (str(emp.employee_code or ""), str(emp.name or ""))

        entries: list[CacheEntry] = []
        flat_vectors: list[np.ndarray] = []
        flat_ids: list[str] = []
        for emp_id, vecs in grouped.items():
            mat = np.vstack(vecs).astype(np.float32)
            code, name = meta[emp_id]
            entries.append(CacheEntry(
                employee_id=emp_id, employee_code=code, employee_name=name, vectors=mat,
            ))
            flat_vectors.extend(vecs)
            flat_ids.extend([emp_id] * len(vecs))

        matrix = np.vstack(flat_vectors).astype(np.float32) if flat_vectors else None
        if matrix is not None:
            assert matrix.shape[0] == len(flat_ids), (
                f"cache invariant broken: matrix={matrix.shape} vs ids={len(flat_ids)}"
            )

        with self._lock:
            self._entries = entries
            self._matrix = matrix
            self._ids = flat_ids
        log.info(
            "Embedding cache loaded: %d employees, %d vectors",
            len(entries), len(flat_ids),
        )

    def reload_employee(self, employee_id: str) -> None:
        """Refresh just one employee's vectors. Called after training
        writes so a full reload (slow on big datasets) isn't required."""
        with session_scope() as session:
            rows = session.execute(
                select(FaceEmbedding, Employee)
                .join(Employee, FaceEmbedding.employee_id == Employee.id)
                .where(FaceEmbedding.employee_id == employee_id)
            ).all()

            new_vectors: list[np.ndarray] = []
            emp_meta: Optional[tuple[str, str]] = None
            for emb, emp in rows:
                try:
                    v = self._unpack(emb.vector, int(emb.dim))
                except ValueError:
                    continue
                new_vectors.append(v)
                emp_meta = (str(emp.employee_code or ""), str(emp.name or ""))

        if not new_vectors:
            self.remove_employee(employee_id)
            return

        new_mat = np.vstack(new_vectors).astype(np.float32)
        assert emp_meta is not None
        new_entry = CacheEntry(
            employee_id=employee_id,
            employee_code=emp_meta[0],
            employee_name=emp_meta[1],
            vectors=new_mat,
        )

        with self._lock:
            keep_mask = [i != employee_id for i in self._ids]
            kept_matrix = (
                self._matrix[keep_mask]
                if self._matrix is not None and self._matrix.shape[0] > 0
                else None
            )
            kept_ids = [i for i in self._ids if i != employee_id]
            if kept_matrix is None or kept_matrix.shape[0] == 0:
                merged_matrix = new_mat
            else:
                merged_matrix = np.vstack([kept_matrix, new_mat]).astype(np.float32)
            merged_ids = kept_ids + [employee_id] * len(new_vectors)
            assert merged_matrix.shape[0] == len(merged_ids)

            self._entries = [e for e in self._entries if e.employee_id != employee_id] + [new_entry]
            self._matrix = merged_matrix
            self._ids = merged_ids

        log.info(
            "Embedding cache delta: emp_id=%s vectors=%d (totals: %d employees, %d vectors)",
            employee_id, len(new_vectors), len(self._entries), len(self._ids),
        )

    def remove_employee(self, employee_id: str) -> None:
        with self._lock:
            if not any(i == employee_id for i in self._ids):
                return
            keep_mask = [i != employee_id for i in self._ids]
            kept_matrix = (
                self._matrix[keep_mask]
                if self._matrix is not None and self._matrix.shape[0] > 0
                else None
            )
            kept_ids = [i for i in self._ids if i != employee_id]
            self._entries = [e for e in self._entries if e.employee_id != employee_id]
            self._matrix = kept_matrix if kept_matrix is None or kept_matrix.shape[0] > 0 else None
            self._ids = kept_ids
        log.info("Embedding cache: removed emp_id=%s", employee_id)

    def snapshot(self) -> tuple[Optional[np.ndarray], list[str], list[CacheEntry]]:
        with self._lock:
            return self._matrix, list(self._ids), list(self._entries)

    def id_to_name_map(self) -> dict[str, str]:
        with self._lock:
            return {e.employee_id: e.employee_name for e in self._entries}

    def size(self) -> int:
        with self._lock:
            return 0 if self._matrix is None else int(self._matrix.shape[0])

    def employee_count(self) -> int:
        with self._lock:
            return len(self._entries)


_singleton_lock = threading.Lock()
_singleton: Optional[EmbeddingCache] = None


def get_embedding_cache() -> EmbeddingCache:
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = EmbeddingCache()
        return _singleton
