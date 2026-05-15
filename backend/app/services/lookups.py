"""Get-or-create helpers for the company / department / shift lookup tables.

Used by:
* ``services.employees`` and ``services.auth`` when creating or updating
  rows that reference these lookups.
* ``app.upgrade`` when backfilling FK columns from legacy string columns.
* ``scripts.migrate_sqlite_to_postgres`` when populating the destination
  PG instance from the legacy SQLite source.

The pattern is the same for all three: trim the input, treat empty as
"no lookup needed" (returns ``None``), look up by name (case-insensitive),
INSERT if missing, return the row id. Duplicates are guarded by the
``UNIQUE(name)`` constraint on every lookup table — a concurrent INSERT
that loses the race surfaces as an IntegrityError; the helper retries the
SELECT once and returns the now-existing id.
"""

from __future__ import annotations

from typing import Any, Optional, Type

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Company, Department, Shift


def _normalize(name: str) -> str:
    return " ".join((name or "").strip().split())


# Canonical company naming across the product. Keys are lowercase/normalized
# variants seen in legacy imports, manual edits, or historical seeds.
COMPANY_NAME_ALIASES: dict[str, str] = {
    # Legacy/demo placeholders that should resolve to the real tenant.
    "branch a": "WAWU",
    "branch b": "WAWU",
    "branch c": "WAWU",
    "startup televison": "Startup TV",
    "startup television": "Startup TV",
    "startup tv": "Startup TV",
    "startup park": "Startup Park",
    "startup school": "Startup School",
    "sib": "Study in Bengaluru",
    "franchisify": "Franchisify",
    "rent your hr": "Rent Your HR",
    "ceo2": "CEO Square",
    "ique ventures": "iQue Ventures",
    "ique cap - delhi team": "iQue CAP - Delhi Team",
    "ique cap - blr team": "iQue CAP - BLR Team",
    "ique cap - kl team": "iQue CAP - KL Team",
    "ique cap - mh team": "iQue CAP - MH Team",
    "ique cap - mp": "iQue CAP - MP Team",
    "ique cap - andra pradesh": "iQue CAP - AP Team",
    "ique cap - andhra pradesh": "iQue CAP - AP Team",
    "ique cap - tn team": "iQue CAP - TN Team",
    "ique cap punjab": "iQue CAP - Punjab Team",
    "ique cap - punjab team": "iQue CAP - Punjab Team",
    "iquecap - core team": "iQue CAP - Core Team",
    "skill univ": "Skill Univ",
    "moonbliss": "Moon Bliss",
    "incubenation": "Incubenation",
    "ceo square": "CEO Square",
    "karumitra": "Karu Mitra",
    "karu miyta": "Karu Mitra",
}


def normalize_company_name(name: str) -> str:
    canonical = _normalize(name)
    if not canonical:
        return canonical
    return COMPANY_NAME_ALIASES.get(canonical.lower(), canonical)


def _get_or_create(session: Session, model: Type[Any], name: str) -> Optional[int]:
    canonical = _normalize(name)
    if model is Company:
        canonical = normalize_company_name(canonical)
    if not canonical:
        return None
    # Case-insensitive lookup so "WAWU" and "wawu" don't get duplicate rows
    # if both spellings appear in seed/legacy data.
    row_id = session.execute(
        select(model.id).where(func.lower(model.name) == canonical.lower())
    ).scalar_one_or_none()
    if row_id is not None:
        return int(row_id)
    new_row = model(name=canonical)
    session.add(new_row)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        # Another transaction won the race — re-read.
        row_id = session.execute(
            select(model.id).where(func.lower(model.name) == canonical.lower())
        ).scalar_one_or_none()
        if row_id is not None:
            return int(row_id)
        raise
    return int(new_row.id)


def get_or_create_company_id(session: Session, name: str) -> Optional[int]:
    return _get_or_create(session, Company, name)


def get_or_create_department_id(session: Session, name: str) -> Optional[int]:
    return _get_or_create(session, Department, name)


def get_or_create_shift_id(session: Session, name: str) -> Optional[int]:
    return _get_or_create(session, Shift, name)
