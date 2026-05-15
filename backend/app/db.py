"""Database engine + session helpers.

Replaces the previous raw ``sqlite3`` layer with SQLAlchemy 2.x. The same
code path supports two dialects:

  * **PostgreSQL** (production / Railway) — selected when ``DATABASE_URL``
    is set. Railway's legacy ``postgres://`` prefix is rewritten to
    ``postgresql+psycopg://`` so SQLAlchemy 2 picks the psycopg v3 driver.

  * **SQLite** (local dev fallback) — used when ``DATABASE_URL`` is empty
    AND we're not running in production. WAL/synchronous PRAGMAs are
    re-applied on every connection for parity with the legacy behavior.

The production guard refuses to start with the SQLite fallback when
``APP_ENV=production`` (or Railway's own ``RAILWAY_ENVIRONMENT`` is set)
so a missing ``DATABASE_URL`` fails fast at boot rather than silently
serving an ephemeral local DB.

Public API:

  * ``Base``                      — declarative base re-exported from models
  * ``engine``                    — module-level SQLAlchemy engine
  * ``SessionLocal``              — sessionmaker bound to ``engine``
  * ``get_db()``                  — FastAPI dependency (yields a Session,
                                    auto-commits on clean exit)
  * ``session_scope()``           — context manager for non-request callers
                                    (capture loop, retention job, scripts)
  * ``init_db()``                 — idempotent ``create_all`` over every
                                    registered model
  * ``upsert_on_conflict_do_nothing(...)`` /
    ``upsert_on_conflict_do_update(...)`` — dialect-aware ``INSERT ... ON
    CONFLICT`` helpers shared by services that need real upserts.
  * ``DIALECT``                   — 'postgresql' or 'sqlite' for callers
                                    that need to branch on dialect.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Iterable, Iterator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from .config import APP_ENV, DATABASE_URL, DB_PATH
from .models import Base  # registers every model with Base.metadata on import

log = logging.getLogger(__name__)


class DBConfigError(RuntimeError):
    """Raised when the DB configuration is invalid for the current env.

    Notably: ``DATABASE_URL`` is required in production and refusing to
    silently fall back to an ephemeral SQLite file."""


def _is_production() -> bool:
    if APP_ENV == "production":
        return True
    # Railway sets RAILWAY_ENVIRONMENT to "production" / "preview" / etc.
    return bool(os.getenv("RAILWAY_ENVIRONMENT", "").strip())


def _resolve_database_url() -> str:
    """Pick the active DB URL; rewrite the postgres:// prefix Railway uses."""
    raw = (DATABASE_URL or "").strip()
    if raw:
        # Heroku/Railway-style "postgres://"; SQLAlchemy 2.x needs an explicit
        # driver. psycopg v3 is on the path (see requirements.txt).
        if raw.startswith("postgres://"):
            raw = "postgresql+psycopg://" + raw[len("postgres://"):]
        elif raw.startswith("postgresql://") and "+psycopg" not in raw.split("://", 1)[0]:
            raw = "postgresql+psycopg://" + raw[len("postgresql://"):]
        return raw
    if _is_production():
        raise DBConfigError(
            "DATABASE_URL is required in production. Refusing to start with "
            "the SQLite fallback. Set DATABASE_URL on the deploy environment."
        )
    return f"sqlite:///{DB_PATH}"


_RESOLVED_URL = _resolve_database_url()
_URL_OBJ = make_url(_RESOLVED_URL)
DIALECT: str = _URL_OBJ.get_backend_name()  # 'postgresql' or 'sqlite'


# Log only safe identifiers, never the raw URL (which carries the password).
log.info(
    "database backend dialect=%s host=%s database=%s",
    DIALECT,
    _URL_OBJ.host or "(local)",
    _URL_OBJ.database,
)


def _build_engine() -> Engine:
    if DIALECT == "sqlite":
        # check_same_thread=False so a connection can be passed across the
        # FastAPI dep + background task boundary; busy timeout (5s) replaces
        # the legacy PRAGMA busy_timeout used by the raw sqlite3 layer.
        return create_engine(
            _RESOLVED_URL,
            future=True,
            connect_args={"check_same_thread": False, "timeout": 5},
        )
    return create_engine(
        _RESOLVED_URL,
        future=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
        pool_pre_ping=True,
    )


engine: Engine = _build_engine()


# Re-apply the SQLite-only PRAGMAs the legacy db.get_connection() used so
# local-dev parity stays exact (WAL journal, NORMAL synchronous, FK on).
if DIALECT == "sqlite":
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):  # noqa: D401 - SA event hook
        cursor = dbapi_conn.cursor()
        try:
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA busy_timeout = 5000")
            cursor.execute("PRAGMA foreign_keys = ON")
        finally:
            cursor.close()


SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False, future=True,
)


def get_db() -> Iterator[Session]:
    """FastAPI dependency. Auto-commits on clean exit so handlers don't have
    to call ``session.commit()`` explicitly — preserves the autocommit
    semantics the old ``isolation_level=None`` connection had."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager for code outside the request lifecycle (background
    workers, CLI scripts, retention job, seed helpers)."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Idempotent CREATE for every registered model. Replaces the legacy
    ``init_schema()`` raw-SQL bootstrap. Safe to call repeatedly."""
    Base.metadata.create_all(bind=engine)


# ---- Dialect-aware upsert helpers ------------------------------------------
#
# SQLAlchemy's core ``insert(...).values(...)`` doesn't expose ON CONFLICT
# directly — that's a dialect-specific feature on PostgreSQL and SQLite.
# These helpers wrap the right import for the active dialect so service
# code stays portable. ``index_elements`` may be a list of column names OR
# Column objects; passing names keeps service code dialect-neutral.


def _dialect_insert_stmt(model_or_table: Any) -> Any:
    if DIALECT == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        return pg_insert(model_or_table)
    if DIALECT == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        return sqlite_insert(model_or_table)
    # Fall back to ANSI insert if some other dialect is ever wired up; the
    # caller's ``on_conflict_*`` chain will raise immediately on misuse.
    from sqlalchemy import insert as ansi_insert
    return ansi_insert(model_or_table)


def upsert_on_conflict_do_nothing(
    session: Session,
    model_or_table: Any,
    values: dict | list[dict],
    *,
    index_elements: Iterable[str],
) -> Any:
    """``INSERT ... VALUES (...) ON CONFLICT (cols) DO NOTHING``.

    Returns the SQLAlchemy ``Result``. Service callers typically only need
    ``result.rowcount`` to count "actually inserted" vs "skipped duplicate"."""
    stmt = _dialect_insert_stmt(model_or_table).values(values)
    stmt = stmt.on_conflict_do_nothing(index_elements=list(index_elements))
    return session.execute(stmt)


def upsert_on_conflict_do_update(
    session: Session,
    model_or_table: Any,
    values: dict,
    *,
    index_elements: Iterable[str],
    set_: dict,
) -> Any:
    """``INSERT ... VALUES (...) ON CONFLICT (cols) DO UPDATE SET ...``.

    ``set_`` maps column name → SQLAlchemy expression (typically referring
    to ``stmt.excluded.<col>``). Mirrors the same shape on PG and SQLite —
    on both dialects ``insert(...).excluded`` is the proposed-new-row alias
    SQLAlchemy generates.
    """
    stmt = _dialect_insert_stmt(model_or_table).values(values)
    stmt = stmt.on_conflict_do_update(index_elements=list(index_elements), set_=set_)
    return session.execute(stmt)


def excluded_of(model_or_table: Any) -> Any:
    """Convenience for callers that want to build a ``set_`` dict mapping
    column names to ``excluded.<col>`` expressions. Returns the
    ``insert(table).excluded`` proxy for the active dialect."""
    return _dialect_insert_stmt(model_or_table).excluded


# ---- Backwards-compat shim --------------------------------------------------
#
# Old call sites used ``with connect() as conn: conn.execute(sql, params)``
# returning ``sqlite3.Row``-style tuples. They're rewritten to use
# ``session_scope()`` directly; this shim only exists so any straggler that
# slips through CI surfaces a loud, actionable error rather than a confusing
# import failure deep in production.


def connect():  # pragma: no cover - sentinel only
    raise RuntimeError(
        "app.db.connect() was removed in the SQLAlchemy refactor. Use "
        "app.db.session_scope() (background callers) or "
        "Depends(app.db.get_db) (FastAPI routes) instead."
    )


# Optional helper exposed for callers that just want the configured URL
# without re-parsing.
def database_url() -> str:
    return _RESOLVED_URL


# Re-export Base so ``from app.db import Base`` keeps working for any
# external tools or scripts.
__all__ = [
    "Base",
    "DIALECT",
    "DBConfigError",
    "SessionLocal",
    "engine",
    "get_db",
    "session_scope",
    "init_db",
    "upsert_on_conflict_do_nothing",
    "upsert_on_conflict_do_update",
    "excluded_of",
    "database_url",
]
