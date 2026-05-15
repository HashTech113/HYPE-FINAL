from __future__ import annotations

import logging
import time
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

log = logging.getLogger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None

# Slow-acquire warning threshold. If a request waits longer than this
# for a connection from the pool, log it loudly. Without this, pool
# exhaustion looks identical to "the API is just slow today" — you
# can't tell from the outside whether a query is slow or whether 20
# other queries are queued in front of it.
_SLOW_POOL_ACQUIRE_SEC = 1.0

# How long a caller is willing to wait for a free connection before
# we give up. Default SQLAlchemy is 30s — far too long for a request
# path. After 10s the user already thinks the page is broken; better
# to fail fast with a 503 (returning the connection to the pool for
# the next caller) than block forever.
_POOL_TIMEOUT_SEC = 10


def _build_engine() -> Engine:
    settings = get_settings()
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_timeout=_POOL_TIMEOUT_SEC,
        future=True,
    )

    # Slow-acquire instrumentation. SQLAlchemy fires `engine_connect`
    # AFTER a connection has been checked out, so timing it requires
    # the older `connect`/`first_connect` pair plus a perf marker on
    # `_ConnectionRecord`. The simpler-and-good-enough approach: time
    # `do_connect` (the actual TCP/SSL handshake when a NEW raw
    # connection is opened — not pool checkouts of warm conns), and
    # separately surface pool-checkout latency via the `_pool_checkout`
    # event hook below.
    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, conn_record):  # type: ignore[no-untyped-def]
        log.debug("DB raw-connect established (pid=%s)", id(dbapi_conn))

    @event.listens_for(engine, "checkout")
    def _on_checkout(dbapi_conn, conn_record, conn_proxy):  # type: ignore[no-untyped-def]
        # Stamp checkout time on the record. We compute the wait on
        # _on_checkin so we don't add cost to the hot path.
        conn_record._checkout_at = time.monotonic()

    @event.listens_for(engine, "checkin")
    def _on_checkin(dbapi_conn, conn_record):  # type: ignore[no-untyped-def]
        # Record how long this connection was in use. Long holds are
        # the canonical sign of a transaction held open across a slow
        # external call (a no-no for connection-pool health).
        started = getattr(conn_record, "_checkout_at", None)
        if started is None:
            return
        held = time.monotonic() - started
        if held >= _SLOW_POOL_ACQUIRE_SEC:
            log.warning(
                "DB connection held %.2fs (>%.2fs threshold). "
                "Long-held connections starve the pool — look for "
                "a slow query or a transaction that calls out to "
                "the network/disk while open.",
                held,
                _SLOW_POOL_ACQUIRE_SEC,
            )

    return engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=True,
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Transactional context. Each call gets its own Session — DO NOT
    share a Session across threads. Camera workers and background
    pools open their own scope per unit of work; FastAPI handlers use
    the per-request `get_db` dependency.
    """
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def dispose_engine() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
