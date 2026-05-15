"""Audit + seed: ensure every row in ``companies`` has an active HR user.

Iterates the ``companies`` table, finds every row that has no ``users`` row
with the same ``company_id`` and ``role='hr'`` (or whose lone HR user is
disabled), and creates / re-enables one. Username is a slug of the company
name (lowercase, alphanum-only, single underscores). Password follows the
existing ``<username>@123`` convention used by the original seed data.

Idempotent: re-running on a healthy DB is a no-op.

Usage (from backend/):
    python -m scripts.seed_missing_hr [--dry-run]
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.db import session_scope  # noqa: E402
from app.models import Company, User  # noqa: E402
from app.services import auth as auth_service  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("seed_missing_hr")

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slug(company_name: str) -> str:
    s = _SLUG_RE.sub("_", (company_name or "").lower()).strip("_")
    return s or "hr"


def _resolve_unique_username(session, base: str) -> str:
    """If ``base`` is taken, append _2, _3, ... until a free slot is found.
    Real-world conflicts are rare (one row per company name) but legacy
    seed names like ``cap`` could collide with a new ``CAP HR`` request."""
    candidate = base
    n = 2
    while session.execute(
        select(User.id).where(User.username == candidate)
    ).scalar_one_or_none() is not None:
        candidate = f"{base}_{n}"
        n += 1
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Print actions without writing to the DB.")
    args = parser.parse_args()

    created: list[tuple[str, str, str, str]] = []   # (company, username, password, action)
    reenabled: list[tuple[str, str]] = []           # (company, username)
    untouched: list[tuple[str, str]] = []           # (company, existing-username)

    with session_scope() as session:
        companies = session.execute(
            select(Company.id, Company.name).order_by(Company.name)
        ).all()

        for company_id, company_name in companies:
            # Look for ANY hr user attached to this company id, active or not.
            existing_user = session.execute(
                select(User.id, User.username, User.is_active)
                .where(User.company_id == company_id, User.role == "hr")
                .order_by(User.is_active.desc())
                .limit(1)
            ).first()

            if existing_user is not None:
                user_id, username, is_active = existing_user
                if is_active:
                    untouched.append((company_name, username))
                    continue
                # Disabled HR exists — re-enable it instead of minting a new one.
                if not args.dry_run:
                    auth_service.update_user_meta(user_id, is_active=True)
                reenabled.append((company_name, username))
                continue

            base = slug(company_name)
            password = f"{base}@123"
            if args.dry_run:
                username = base  # preview only; real one resolved at write time
                action = "DRY-RUN create"
            else:
                username = _resolve_unique_username(session, base)
                password = f"{username}@123"
                # create_user opens its own session_scope; OK to call inside ours
                # because session_scope is re-entrant via independent connections
                # for short writes. If conflicts arise, the unique check above
                # has already filtered them out.
                action = "create"
            created.append((company_name, username, password, action))

    if not args.dry_run:
        for company_name, username, password, _action in created:
            try:
                auth_service.create_user(
                    username=username,
                    password=password,
                    role="hr",
                    company=company_name,
                    display_name=f"{company_name} HR",
                )
            except ValueError as e:
                log.warning("FAILED to create %r for %r: %s", username, company_name, e)

    log.info("--- summary ---")
    log.info("companies total      : %d", len(companies))
    log.info("already had HR       : %d", len(untouched))
    log.info("re-enabled HR        : %d", len(reenabled))
    log.info("new HR created       : %d", len(created))
    if reenabled:
        log.info("--- RE-ENABLED ---")
        for company_name, username in reenabled:
            log.info("  %-32s %s", company_name, username)
    if created:
        log.info("--- NEW CREDENTIALS (save these) ---")
        log.info("  %-32s %-22s %s", "COMPANY", "USERNAME", "PASSWORD")
        for company_name, username, password, _action in created:
            log.info("  %-32s %-22s %s", company_name, username, password)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
