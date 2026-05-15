"""Company catalog CRUD for the Settings → Edit Companies admin panel.

Reads/writes the ``companies`` table and keeps the legacy denormalized
``company`` strings on ``employees`` and ``users`` in sync, so HR scoping
(which compares lowercased ``user.company`` against ``employee.company``)
keeps working after a rename.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import func, select, update

from ..db import session_scope
from ..models import Company, Employee, User
from .lookups import normalize_company_name

log = logging.getLogger(__name__)


class CompanyNameError(ValueError):
    """Bad input — empty name, or duplicate of another company."""


class CompanyHasEmployeesError(RuntimeError):
    """Tried to delete a company that still has employees attached."""

    def __init__(self, count: int):
        super().__init__(f"company still has {count} employee(s)")
        self.count = count


def _normalize(name: str) -> str:
    return normalize_company_name(name)


def list_with_counts() -> list[dict]:
    """Return every company with its current employee count, ordered by name.

    Now also surfaces the linked HR account (``hr_user_id``, ``hr_username``)
    so the Edit Companies panel can show one row per company with the HR
    account inline — no separate Users panel hop. When a company has more
    than one HR user we pick the lowest username alphabetically; that's
    deterministic and matches what an admin would see if they sorted the
    Users panel by username.
    """
    with session_scope() as session:
        rows = session.execute(
            select(
                Company.id,
                Company.name,
                func.count(Employee.id).label("employee_count"),
            )
            .outerjoin(Employee, Employee.company_id == Company.id)
            .group_by(Company.id, Company.name)
            .order_by(func.lower(Company.name))
        ).all()
        # Pull every HR user that is attached to a company in one shot,
        # then collapse to the alphabetically-first username per company.
        hr_by_company: dict[int, dict] = {}
        for u in session.execute(
            select(User.id, User.username, User.company_id, User.is_active)
            .where(User.company_id.is_not(None), User.role == "hr")
            .order_by(User.company_id, func.lower(User.username))
        ).all():
            cid = int(u.company_id)
            if cid not in hr_by_company:
                hr_by_company[cid] = {
                    "id": str(u.id),
                    "username": u.username,
                    "is_active": bool(u.is_active),
                }
        return [
            {
                "id": int(r.id),
                "name": r.name,
                "employee_count": int(r.employee_count or 0),
                "has_users": int(r.id) in hr_by_company,
                "hr_user_id": hr_by_company.get(int(r.id), {}).get("id"),
                "hr_username": hr_by_company.get(int(r.id), {}).get("username"),
                "hr_user_active": hr_by_company.get(int(r.id), {}).get("is_active"),
            }
            for r in rows
        ]


def rename(company_id: int, new_name: str) -> dict:
    """Rename a company; cascade the name change into the denormalized
    ``company`` columns on ``employees`` and ``users`` so HR scoping
    keeps matching by string.

    Raises:
        LookupError if no company with that id exists.
        CompanyNameError if the new name is empty or collides with
        another company (case-insensitive).
    """
    canonical = _normalize(new_name)
    if not canonical:
        raise CompanyNameError("name cannot be empty")

    with session_scope() as session:
        row = session.get(Company, company_id)
        if row is None:
            raise LookupError(f"company {company_id} not found")

        # Uniqueness check across other companies (case-insensitive). Reusing
        # the same name with different casing is allowed.
        clash = session.execute(
            select(Company.id).where(
                func.lower(Company.name) == canonical.lower(),
                Company.id != company_id,
            )
        ).scalar_one_or_none()
        if clash is not None:
            raise CompanyNameError(f"another company is already named {canonical!r}")

        old_name = row.name
        if old_name == canonical:
            return {
                "id": int(row.id),
                "name": row.name,
                "employee_count": int(
                    session.execute(
                        select(func.count(Employee.id)).where(
                            Employee.company_id == company_id
                        )
                    ).scalar_one() or 0
                ),
                "has_users": session.execute(
                    select(func.count(User.id)).where(User.company_id == company_id)
                ).scalar_one() > 0,
            }

        row.name = canonical

        emp_updated = session.execute(
            update(Employee)
            .where(Employee.company_id == company_id)
            .values(company=canonical)
        ).rowcount or 0
        usr_updated = session.execute(
            update(User)
            .where(User.company_id == company_id)
            .values(company=canonical)
        ).rowcount or 0

        log.info(
            "company rename id=%d %r -> %r (employees=%d, users=%d)",
            company_id, old_name, canonical, emp_updated, usr_updated,
        )

        return {
            "id": int(row.id),
            "name": row.name,
            "employee_count": int(emp_updated),
            "has_users": bool(usr_updated),
        }


def delete(company_id: int) -> int:
    """Delete a company. Refuses if any employees are still attached
    (caller should reassign first). Users with this company_id get their
    FK set to NULL by the existing ``ON DELETE SET NULL`` constraint —
    we additionally clear the denormalized ``company`` string so the HR
    scope doesn't keep matching the now-deleted name.

    Returns the number of HR users whose ``company`` field was cleared.

    Raises:
        LookupError if no company with that id exists.
        CompanyHasEmployeesError if any employees still reference it.
    """
    with session_scope() as session:
        row = session.get(Company, company_id)
        if row is None:
            raise LookupError(f"company {company_id} not found")

        employee_count = int(
            session.execute(
                select(func.count(Employee.id)).where(Employee.company_id == company_id)
            ).scalar_one() or 0
        )
        if employee_count > 0:
            raise CompanyHasEmployeesError(employee_count)

        # Clear denormalized strings on HR users before drop. The FK itself
        # is set NULL by the schema's ON DELETE SET NULL.
        users_cleared = session.execute(
            update(User)
            .where(User.company_id == company_id)
            .values(company="")
        ).rowcount or 0

        session.delete(row)
        log.info(
            "company delete id=%d %r (cleared company string on %d HR user(s))",
            company_id, row.name, users_cleared,
        )
        return int(users_cleared)


def get_by_id(company_id: int) -> Optional[dict]:
    with session_scope() as session:
        row = session.get(Company, company_id)
        if row is None:
            return None
        count = int(
            session.execute(
                select(func.count(Employee.id)).where(Employee.company_id == company_id)
            ).scalar_one() or 0
        )
        has_users = (
            session.execute(
                select(func.count(User.id)).where(User.company_id == company_id)
            ).scalar_one() or 0
        ) > 0
        return {
            "id": int(row.id),
            "name": row.name,
            "employee_count": count,
            "has_users": bool(has_users),
        }
