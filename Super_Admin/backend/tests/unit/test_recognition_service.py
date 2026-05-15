"""RecognitionService — match / no-match contract.

Wraps the matmul + threshold logic. The crash bug fixed in W0.6 is
the high-value regression target here — empty cache must NEVER raise.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.services.embedding_cache import CacheEntry, EmbeddingCache
from app.services.recognition_service import RecognitionService

pytestmark = pytest.mark.unit


def _l2(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def test_empty_cache_returns_clean_miss_no_raise() -> None:
    """Pre-fix: ranked[0] would IndexError and crash the detector
    loop, taking the camera worker down. Now it returns a None match
    cleanly."""
    cache = EmbeddingCache()
    svc = RecognitionService(cache)
    q = np.random.rand(512).astype(np.float32)
    out = svc.match(q, threshold=0.5)
    assert out.employee_id is None
    assert out.score == 0.0


def test_match_above_threshold_returns_employee() -> None:
    cache = EmbeddingCache()
    # Synthetic embeddings — just two L2-normalized vectors per
    # employee. Recognition does cosine; identical vectors → score 1.
    e1 = _l2(np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32))
    e2 = _l2(np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32))
    with cache._lock:
        cache._matrix = np.vstack([e1, e2])
        cache._ids = [101, 202]
        cache._entries = [
            CacheEntry(101, "EMP-101", "Alice", e1.reshape(1, -1)),
            CacheEntry(202, "EMP-202", "Bob", e2.reshape(1, -1)),
        ]

    svc = RecognitionService(cache)
    out = svc.match(e1, threshold=0.5)
    assert out.employee_id == 101
    assert out.score > 0.99  # identical → ~1.0


def test_match_below_threshold_returns_unknown() -> None:
    cache = EmbeddingCache()
    e1 = _l2(np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32))
    with cache._lock:
        cache._matrix = e1.reshape(1, -1)
        cache._ids = [101]
        cache._entries = [CacheEntry(101, "EMP-101", "Alice", e1.reshape(1, -1))]

    # Orthogonal query — cosine 0 — well below the 0.5 threshold.
    q = _l2(np.array([0.0, 0.0, 1.0, 0.0], dtype=np.float32))
    svc = RecognitionService(cache)
    out = svc.match(q, threshold=0.5)
    assert out.employee_id is None
    assert out.score == 0.0  # orthogonal → 0


def test_zero_vector_query_returns_clean_miss() -> None:
    """L2-normalize-by-norm of a zero vector is the only divide-by-
    zero hazard in the recognition path. We guard explicitly."""
    cache = EmbeddingCache()
    e1 = _l2(np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32))
    with cache._lock:
        cache._matrix = e1.reshape(1, -1)
        cache._ids = [101]

    svc = RecognitionService(cache)
    out = svc.match(np.zeros(4, dtype=np.float32), threshold=0.5)
    assert out.employee_id is None
    assert out.score == 0.0


def test_per_employee_max_score_used() -> None:
    """An employee with 5 vectors should be ranked by their BEST
    cosine, not the average. Otherwise enrolling many low-quality
    angles would degrade the score and lock people out."""
    cache = EmbeddingCache()
    e1 = _l2(np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32))
    e2_close = _l2(np.array([0.99, 0.1, 0.0, 0.0], dtype=np.float32))
    e2_far = _l2(np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float32))
    with cache._lock:
        # Two employees: 101 has one match-this-query embedding,
        # 202 has one close embedding and one far one.
        cache._matrix = np.vstack([e1, e2_close, e2_far])
        cache._ids = [101, 202, 202]

    svc = RecognitionService(cache)
    out = svc.match(e1, threshold=0.5)
    # 101 is the perfect match.
    assert out.employee_id == 101
    # second_best_score is the BEST score from any OTHER employee
    # (202's `e2_close` ≈ 0.99 cosine, not the diluted average).
    assert out.second_best_score > 0.95
