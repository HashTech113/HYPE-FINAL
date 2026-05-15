from __future__ import annotations

import threading
from dataclasses import dataclass

import numpy as np

from app.core.logger import get_logger
from app.db.session import session_scope
from app.repositories.embedding_repo import EmbeddingRepository

log = get_logger(__name__)


@dataclass(frozen=True)
class CacheEntry:
    employee_id: int
    employee_code: str
    employee_name: str
    vectors: np.ndarray  # shape (n, dim), L2-normalized


class EmbeddingCache:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: list[CacheEntry] = []
        self._matrix: np.ndarray | None = None
        self._ids: list[int] = []

    @staticmethod
    def _unpack(vec: bytes, dim: int) -> np.ndarray:
        arr = np.frombuffer(vec, dtype=np.float32)
        if arr.size != dim:
            raise ValueError(f"Vector size mismatch: expected {dim}, got {arr.size}")
        n = np.linalg.norm(arr)
        return arr / n if n > 0 else arr

    @staticmethod
    def pack(vec: np.ndarray) -> bytes:
        return np.ascontiguousarray(vec.astype(np.float32)).tobytes()

    def load_from_db(self) -> None:
        with session_scope() as db:
            repo = EmbeddingRepository(db)
            rows = repo.list_active_with_employee()

        grouped: dict[int, list[np.ndarray]] = {}
        meta: dict[int, tuple[str, str]] = {}
        for emb, emp, _img in rows:
            try:
                v = self._unpack(emb.vector, emb.dim)
            except ValueError:
                log.warning("Skipping corrupt embedding id=%s", emb.id)
                continue
            grouped.setdefault(emp.id, []).append(v)
            meta[emp.id] = (emp.employee_code, emp.name)

        entries: list[CacheEntry] = []
        flat_vectors: list[np.ndarray] = []
        flat_ids: list[int] = []
        for emp_id, vecs in grouped.items():
            mat = np.vstack(vecs).astype(np.float32)
            code, name = meta[emp_id]
            entries.append(
                CacheEntry(employee_id=emp_id, employee_code=code, employee_name=name, vectors=mat)
            )
            flat_vectors.extend(vecs)
            flat_ids.extend([emp_id] * len(vecs))

        matrix = np.vstack(flat_vectors).astype(np.float32) if flat_vectors else None

        # Invariant: the matrix's row count MUST equal the length of
        # the parallel ids list. Recognition does `matrix @ q` then
        # `zip(ids, sims)` — a length mismatch silently maps the wrong
        # employee_id to each similarity, which would corrupt
        # attendance. Assert here so any future regression in the
        # construction logic above blows up loudly at load time
        # instead of producing wrong identities for hours.
        if matrix is not None:
            assert matrix.shape[0] == len(flat_ids), (
                f"embedding cache invariant broken: matrix={matrix.shape} vs ids={len(flat_ids)}"
            )

        with self._lock:
            self._entries = entries
            self._matrix = matrix
            self._ids = flat_ids
        log.info("Embedding cache loaded: %d employees, %d vectors", len(entries), len(flat_ids))

    def snapshot(self) -> tuple[np.ndarray | None, list[int], list[CacheEntry]]:
        with self._lock:
            return self._matrix, list(self._ids), list(self._entries)

    def reload_employee(self, employee_id: int) -> None:
        """Refresh JUST this employee's vectors in the cache.

        Replaces the previous full-table `load_from_db()` call that
        every training event used to do. With 14 employees and 168
        vectors the old approach took 14s on Railway DB; with 10k
        employees it would have been minutes. The delta query reads
        only the rows for `employee_id` (typically <20 rows) and
        splices them into the in-memory matrix under the lock.

        Idempotent. If the employee no longer has any embeddings (all
        deleted), this method behaves like `remove_employee`.
        """
        with session_scope() as db:
            repo = EmbeddingRepository(db)
            rows = repo.list_active_for_employee(employee_id)

        new_vectors: list[np.ndarray] = []
        emp_meta: tuple[str, str] | None = None
        for emb, emp, _img in rows:
            try:
                v = self._unpack(emb.vector, emb.dim)
            except ValueError:
                log.warning("Skipping corrupt embedding id=%s", emb.id)
                continue
            new_vectors.append(v)
            emp_meta = (emp.employee_code, emp.name)

        if not new_vectors:
            # Employee has no remaining embeddings — treat as a remove.
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
            # Drop old rows for this employee from the flat structures.
            keep_mask = [i != employee_id for i in self._ids]
            kept_matrix = (
                self._matrix[keep_mask]
                if self._matrix is not None and self._matrix.shape[0] > 0
                else None
            )
            kept_ids = [i for i in self._ids if i != employee_id]
            # Append fresh rows.
            if kept_matrix is None or kept_matrix.shape[0] == 0:
                merged_matrix = new_mat
            else:
                merged_matrix = np.vstack([kept_matrix, new_mat]).astype(np.float32)
            merged_ids = kept_ids + [employee_id] * len(new_vectors)
            assert merged_matrix.shape[0] == len(merged_ids)

            # Update entries list — replace if present, else append.
            new_entries = [e for e in self._entries if e.employee_id != employee_id]
            new_entries.append(new_entry)

            self._entries = new_entries
            self._matrix = merged_matrix
            self._ids = merged_ids

        log.info(
            "Embedding cache delta: emp_id=%s vectors=%d (cache totals: %d employees, %d vectors)",
            employee_id,
            len(new_vectors),
            len(self._entries),
            len(self._ids),
        )

    def remove_employee(self, employee_id: int) -> None:
        """Drop an employee's vectors from the cache without touching
        the DB. Used when all of an employee's embeddings are deleted
        or when the employee is deactivated.
        """
        with self._lock:
            if not any(i == employee_id for i in self._ids):
                return  # already absent — idempotent
            keep_mask = [i != employee_id for i in self._ids]
            kept_matrix = (
                self._matrix[keep_mask]
                if self._matrix is not None and self._matrix.shape[0] > 0
                else None
            )
            kept_ids = [i for i in self._ids if i != employee_id]
            assert kept_matrix is None or kept_matrix.shape[0] == len(kept_ids)
            self._entries = [e for e in self._entries if e.employee_id != employee_id]
            self._matrix = kept_matrix if kept_matrix is None or kept_matrix.shape[0] > 0 else None
            self._ids = kept_ids
        log.info("Embedding cache: removed emp_id=%s", employee_id)

    def id_to_name_map(self) -> dict[int, str]:
        """O(1) employee_id -> display name lookup for the live preview
        overlay. Iterating the entries list every face was O(N) per
        detection — small for a tiny office, but pile that on top of
        20 detections/sec × 4 cameras at scale and it shows up.
        """
        with self._lock:
            return {e.employee_id: e.employee_name for e in self._entries}

    def size(self) -> int:
        with self._lock:
            return 0 if self._matrix is None else int(self._matrix.shape[0])

    def employee_count(self) -> int:
        with self._lock:
            return len(self._entries)
