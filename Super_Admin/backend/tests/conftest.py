"""Shared pytest fixtures.

Test-time environment isolation:
  Several modules (config, security, secrets) read env vars on import
  or via lru_cache. We set the minimum required env BEFORE importing
  any app code so tests don't depend on the developer's `.env`.
"""

from __future__ import annotations

import os

# Set BEFORE any `app.*` import.
os.environ.setdefault(
    "DATABASE_URL",
    # SQLite in-memory by default — unit tests must not touch a real
    # postgres. Integration tests override this.
    "sqlite+pysqlite:///:memory:",
)
os.environ.setdefault(
    "JWT_SECRET_KEY",
    # Long-enough deterministic test key — never used in production.
    "test-secret-do-not-use-in-prod-9d1e3871a9d3d1eb85e7f0113b3791b5",
)

import pytest


@pytest.fixture
def fernet_key() -> str:
    """A throwaway Fernet key, regenerated per test so leakage between
    tests is impossible. Use this whenever you need to test the
    encrypted-mode paths of `SecretCipher`.
    """
    from cryptography.fernet import Fernet

    return Fernet.generate_key().decode("ascii")
