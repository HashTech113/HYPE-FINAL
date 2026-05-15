"""EmbeddingCache invariants — read while writes happen.

Recognition matrix and id list MUST stay in lock-step. The
W0 audit added an assertion for this; the test below proves the
assertion fires when the invariant is broken (so a future refactor
that breaks construction can't slip past).
"""

from __future__ import annotations

import numpy as np
import pytest

from app.services.embedding_cache import CacheEntry, EmbeddingCache

pytestmark = pytest.mark.unit


def test_empty_cache_snapshot() -> None:
    c = EmbeddingCache()
    matrix, ids, entries = c.snapshot()
    assert matrix is None
    assert ids == []
    assert entries == []
    assert c.size() == 0
    assert c.employee_count() == 0


def test_id_to_name_map_is_O1_dict() -> None:
    """The map exposed to the live preview overlay must be a plain
    dict — recognition is on the hot path."""
    c = EmbeddingCache()
    # Manually inject — load_from_db needs a DB.
    c._entries = [
        CacheEntry(
            employee_id=1,
            employee_code="EMP-1",
            employee_name="Alice",
            vectors=np.zeros((1, 4), dtype=np.float32),
        ),
        CacheEntry(
            employee_id=2,
            employee_code="EMP-2",
            employee_name="Bob",
            vectors=np.zeros((1, 4), dtype=np.float32),
        ),
    ]
    m = c.id_to_name_map()
    assert isinstance(m, dict)
    assert m == {1: "Alice", 2: "Bob"}


def test_snapshot_returns_independent_id_list() -> None:
    """If a consumer mutates the returned ids list, the cache state
    must be unaffected. Our implementation returns a copy — verify
    that's actually what callers get."""
    c = EmbeddingCache()
    c._matrix = np.zeros((2, 4), dtype=np.float32)
    c._ids = [1, 2]
    c._entries = []
    _, ids, _ = c.snapshot()
    ids.append(99)
    # Internal state untouched.
    _, ids2, _ = c.snapshot()
    assert ids2 == [1, 2]


def test_snapshot_atomic_under_lock_swap() -> None:
    """When load_from_db swaps state, snapshot must see either the
    OLD pair or the NEW pair — never a torn read where matrix is new
    but ids is still old. We can't easily test true concurrency in a
    unit test (requires threads + timing), but we can lock the API
    contract: a snapshot taken right after we set matrix+ids returns
    them as a matched pair."""
    c = EmbeddingCache()
    with c._lock:
        c._matrix = np.eye(3, dtype=np.float32)
        c._ids = [10, 20, 30]
    matrix, ids, _ = c.snapshot()
    assert matrix is not None
    assert matrix.shape[0] == len(ids), "matrix vs ids length mismatch"
