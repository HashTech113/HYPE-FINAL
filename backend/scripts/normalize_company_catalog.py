"""Normalize existing company names in DB to canonical display names.

Usage (from backend/):
    python -m scripts.normalize_company_catalog
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from sqlalchemy import func, select, update

# Make the script runnable as a module from backend/.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.db import session_scope  # noqa: E402
from app.models import Company, Employee, User  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("normalize_company_catalog")


RENAME_MAP: dict[str, str] = {
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
    "ique cap - mh team": "iQue CAP - MH Team",
    "ique cap - kl team": "iQue CAP - KL Team",
    "ique cap - blr team": "iQue CAP - BLR Team",
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


def _normalize(name: str) -> str:
    return " ".join((name or "").strip().split())


def main() -> None:
    merged_companies = 0
    renamed_companies = 0
    employee_rows_updated = 0
    user_rows_updated = 0

    with session_scope() as session:
        for old_variant, canonical in RENAME_MAP.items():
            old_lc = _normalize(old_variant).lower()
            canonical = _normalize(canonical)
            if not canonical:
                continue

            source_rows = session.execute(
                select(Company).where(func.lower(Company.name) == old_lc)
            ).scalars().all()
            if not source_rows:
                # Still normalize denormalized columns even if lookup row isn't present.
                emp_fix = session.execute(
                    update(Employee)
                    .where(func.lower(Employee.company) == old_lc)
                    .values(company=canonical)
                ).rowcount or 0
                usr_fix = session.execute(
                    update(User)
                    .where(func.lower(User.company) == old_lc)
                    .values(company=canonical)
                ).rowcount or 0
                employee_rows_updated += int(emp_fix)
                user_rows_updated += int(usr_fix)
                continue

            target_row = session.execute(
                select(Company).where(func.lower(Company.name) == canonical.lower())
            ).scalar_one_or_none()

            for source_row in source_rows:
                if target_row and source_row.id != target_row.id:
                    # Merge source company into existing canonical row.
                    emp_fk = session.execute(
                        update(Employee)
                        .where(Employee.company_id == source_row.id)
                        .values(company_id=target_row.id, company=canonical)
                    ).rowcount or 0
                    usr_fk = session.execute(
                        update(User)
                        .where(User.company_id == source_row.id)
                        .values(company_id=target_row.id, company=canonical)
                    ).rowcount or 0
                    session.delete(source_row)
                    merged_companies += 1
                    employee_rows_updated += int(emp_fk)
                    user_rows_updated += int(usr_fk)
                    continue

                # In-place rename if canonical row does not already exist.
                if source_row.name != canonical:
                    source_row.name = canonical
                    renamed_companies += 1

                emp_fix = session.execute(
                    update(Employee)
                    .where(Employee.company_id == source_row.id)
                    .values(company=canonical)
                ).rowcount or 0
                usr_fix = session.execute(
                    update(User)
                    .where(User.company_id == source_row.id)
                    .values(company=canonical)
                ).rowcount or 0
                employee_rows_updated += int(emp_fix)
                user_rows_updated += int(usr_fix)

            # Also normalize any denormalized strings that may exist independent
            # of FK links (legacy rows, partial migrations, etc.).
            emp_fix_text = session.execute(
                update(Employee)
                .where(func.lower(Employee.company) == old_lc)
                .values(company=canonical)
            ).rowcount or 0
            usr_fix_text = session.execute(
                update(User)
                .where(func.lower(User.company) == old_lc)
                .values(company=canonical)
            ).rowcount or 0
            employee_rows_updated += int(emp_fix_text)
            user_rows_updated += int(usr_fix_text)

    log.info(
        "company normalization complete: renamed=%d merged=%d employees_updated=%d users_updated=%d",
        renamed_companies,
        merged_companies,
        employee_rows_updated,
        user_rows_updated,
    )


if __name__ == "__main__":
    main()
