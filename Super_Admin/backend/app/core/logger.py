"""Logging setup.

Two output formats are supported, selected by the `LOG_FORMAT` env var:

  - `text` (default) — human-readable single-line records with timestamp,
    level, logger name, and message. Good for local dev and `tail -f`.
  - `json` — one JSON object per line, suitable for ingestion by a log
    aggregator (Loki, ELK, Datadog, CloudWatch). Adds the request_id
    contextvar and a small set of standard fields.

Cross-cutting context:
  Every log line emitted while a FastAPI request is in flight (or
  while a background worker has bound a request_id) automatically
  includes that ID — no need to pass it explicitly. The middleware
  in `app.core.middleware` populates the contextvar at request entry.
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from app.config import get_settings

_CONFIGURED = False

# Cross-thread / cross-task context. ContextVars are the right
# primitive — they propagate through `await` boundaries AND through
# `loop.run_in_threadpool` calls (FastAPI uses this for sync deps).
# `request_id` lets us trace one HTTP request across every log line
# it produces, including any background job it kicks off that we've
# arranged to copy the value into.
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
# Optional secondary context — free-form key/value pairs the caller
# wants attached to every emitted log within the current task. Used
# sparingly (heavy use makes log diffs noisy).
log_context_var: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "log_context", default=None
)


# --- Formatters ----------------------------------------------------------


class _ContextInjectingFilter(logging.Filter):
    """Adds `request_id` and any current `log_context` dict onto every
    LogRecord. Runs before the formatter so both text and JSON
    outputs see the enriched record.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        ctx = log_context_var.get()
        if ctx:
            for k, v in ctx.items():
                # Don't clobber the standard LogRecord attrs.
                if not hasattr(record, k):
                    setattr(record, k, v)
        return True


class _JsonFormatter(logging.Formatter):
    """One JSON object per line. Stable field order so logs diff cleanly."""

    # The standard LogRecord attributes we DON'T want to dump as
    # extras (they're either redundant or noisy).
    _SKIP = frozenset(
        {
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "msg",
            "message",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
            "taskName",
            # We surface these explicitly below.
            "levelname",
            "request_id",
        }
    )

    def format(self, record: logging.LogRecord) -> str:
        out: dict[str, Any] = {
            "ts": _isoformat(record.created),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        # Any extras the caller attached via `log_context_var` or
        # `logger.info(..., extra={...})` come along.
        for k, v in record.__dict__.items():
            if k in self._SKIP or k.startswith("_"):
                continue
            if k in out:
                continue
            try:
                json.dumps(v)
                out[k] = v
            except (TypeError, ValueError):
                out[k] = repr(v)
        if record.exc_info:
            out["exc"] = self.formatException(record.exc_info)
        return json.dumps(out, ensure_ascii=False)


def _isoformat(epoch: float) -> str:
    # ISO-8601 UTC with millisecond precision. Standard log-aggregator
    # input format; lexicographically sortable.
    t = time.gmtime(epoch)
    ms = int((epoch - int(epoch)) * 1000)
    return f"{time.strftime('%Y-%m-%dT%H:%M:%S', t)}.{ms:03d}Z"


# --- Configure once -------------------------------------------------------


def configure_logging() -> None:
    """Idempotent. Safe to call multiple times — only the first call
    actually wires handlers."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    fmt_choice = (getattr(settings, "LOG_FORMAT", None) or "text").lower()
    if fmt_choice == "json":
        formatter: logging.Formatter = _JsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt=("%(asctime)s | %(levelname)-8s | %(name)s | [req=%(request_id)s] %(message)s"),
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    context_filter = _ContextInjectingFilter()

    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL.upper())
    root.handlers.clear()
    root.addFilter(context_filter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(context_filter)
    root.addHandler(stream_handler)

    file_handler = RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(context_filter)
    root.addHandler(file_handler)

    for noisy in ("uvicorn.access", "sqlalchemy.engine", "insightface", "onnxruntime"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
