"""Employee directory — name/company mapping consumed by routers.

Backed by the ``employees`` table via SQLAlchemy. On first boot, an empty
table is seeded from ``backend/data/employees.json`` so the roster is
never accidentally blank after a fresh deploy. Edits go through
create/update/delete; all writes persist to the configured database
(PostgreSQL in production, SQLite locally).

The Python attribute on the ORM model is ``employee_code``, mapped to the
underlying DB column ``employee_id`` so existing API payloads stay
unchanged. The public ``Employee`` dataclass continues to expose
``employee_id`` for the same reason.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from sqlalchemy import func, inspect, select, text

from ..db import session_scope
from ..models import Employee as EmployeeModel
from .lookups import (
    get_or_create_company_id,
    get_or_create_department_id,
    get_or_create_shift_id,
)

log = logging.getLogger(__name__)

_SEED_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "employees.json"
_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class Employee:
    id: str
    name: str
    employee_id: str
    company: str
    department: str
    shift: str
    role: str
    dob: str = ""
    image_url: str = ""
    email: str = ""
    mobile: str = ""
    salary_package: str = ""


def _model_to_employee(row: EmployeeModel) -> Employee:
    return Employee(
        id=str(row.id),
        name=str(row.name or ""),
        employee_id=str(row.employee_code or ""),
        company=str(row.company or ""),
        department=str(row.department or ""),
        shift=str(row.shift or ""),
        role=str(row.role or "Employee"),
        dob=str(row.dob or ""),
        image_url=str(row.image_url or ""),
        email=str(row.email or ""),
        mobile=str(row.mobile or ""),
        salary_package=str(row.salary_package or ""),
    )


def all_employees() -> list[Employee]:
    with session_scope() as session:
        rows = session.execute(
            select(EmployeeModel).order_by(func.lower(EmployeeModel.name))
        ).scalars().all()
        return [_model_to_employee(r) for r in rows]


def get_by_id(employee_id: str) -> Optional[Employee]:
    with session_scope() as session:
        row = session.get(EmployeeModel, employee_id)
        return _model_to_employee(row) if row else None


def create(
    *,
    id: str,
    name: str,
    employee_id: str,
    company: str = "",
    department: str = "",
    shift: str = "",
    role: str = "Employee",
    dob: str = "",
    image_url: str = "",
    email: str = "",
    mobile: str = "",
    salary_package: str = "",
) -> Employee:
    with session_scope() as session:
        # Lookup-or-create the FK targets so the normalized columns stay
        # consistent with the legacy denormalized strings.
        company_id = get_or_create_company_id(session, company) if company else None
        department_id = (
            get_or_create_department_id(session, department) if department else None
        )
        shift_id = get_or_create_shift_id(session, shift) if shift else None
        session.add(
            EmployeeModel(
                id=id,
                name=name,
                employee_code=employee_id,
                company=company,
                company_id=company_id,
                department=department,
                department_id=department_id,
                shift=shift,
                shift_id=shift_id,
                role=role,
                dob=dob,
                image_url=image_url,
                email=email,
                mobile=mobile,
                salary_package=salary_package,
            )
        )
        session.flush()
        row = session.get(EmployeeModel, id)
        assert row is not None, "created employee should load back"
        return _model_to_employee(row)


_UPDATABLE_COLUMNS = {
    "name", "employee_id", "company", "department", "shift", "role", "dob", "image_url",
    "email", "mobile", "salary_package",
}


# Map public attribute name -> ORM attribute name. ``employee_id`` is the
# only one that differs.
_PUBLIC_TO_MODEL_ATTR = {
    "name": "name",
    "employee_id": "employee_code",
    "company": "company",
    "department": "department",
    "shift": "shift",
    "role": "role",
    "dob": "dob",
    "image_url": "image_url",
    "email": "email",
    "mobile": "mobile",
    "salary_package": "salary_package",
}


def update(employee_id: str, patch: dict) -> Optional[Employee]:
    fields = [(k, v) for k, v in patch.items() if k in _UPDATABLE_COLUMNS and v is not None]
    if not fields:
        return get_by_id(employee_id)

    # Always run the rename pass on save so historical log spellings stay
    # aligned with the current canonical employee name — including variant
    # spellings the camera/recognizer may have inserted since the last save
    # (e.g. "Akhil c v" alongside "Akhil C V"). All writes commit together;
    # on any failure, nothing changes.
    with session_scope() as session:
        row = session.get(EmployeeModel, employee_id)
        if row is None:
            return None

        old_name = str(row.name or "")
        # Snapshot the roster BEFORE the rename so fuzzy-match can tell apart
        # variants belonging to THIS employee from similar names owned by
        # someone else.
        employees_before: list[Employee] = [
            _model_to_employee(r)
            for r in session.execute(select(EmployeeModel)).scalars().all()
        ]

        for public_key, value in fields:
            setattr(row, _PUBLIC_TO_MODEL_ATTR[public_key], value)

        # Sync the lookup-table FKs whenever the matching denormalized
        # string is updated (or set for the first time on legacy rows).
        # Empty strings clear the FK; non-empty strings get-or-create.
        if "company" in dict(fields):
            row.company_id = (
                get_or_create_company_id(session, row.company) if row.company else None
            )
        if "department" in dict(fields):
            row.department_id = (
                get_or_create_department_id(session, row.department) if row.department else None
            )
        if "shift" in dict(fields):
            row.shift_id = (
                get_or_create_shift_id(session, row.shift) if row.shift else None
            )

        canonical_name = patch.get("name") or old_name
        session.flush()

        # Always run the rename pass — even when the name itself isn't
        # changing, this sweeps up drifted spellings that fuzzy-match to
        # this employee. Mirrors the legacy behavior (opening + saving an
        # employee canonicalizes historical variants).
        _rename_employee_name(
            session,
            old_name,
            canonical_name,
            employee_id=employee_id,
            employees_before=employees_before,
        )

        session.flush()
        return _model_to_employee(row)


def _rename_employee_name(
    session,
    old_name: str,
    new_name: str,
    *,
    employee_id: str,
    employees_before: list["Employee"],
) -> dict[str, int]:
    """Rewrite the employee name across every table that stores it. Picks up
    historical variants (different casing, partial-recognition spellings like
    "Akhil" for "Akhil C V") by fuzzy-matching against the pre-rename roster
    via ``match()`` — only variants whose match resolves to THIS employee are
    rewritten, so similar names belonging to other people are left alone.
    Caller owns the surrounding transaction.
    """
    counts: dict[str, int] = {}
    inspector = inspect(session.get_bind())
    tables = ["snapshot_logs", "attendance_logs", "attendance_report_edits"]
    # Legacy attendance_corrections is preserved for one release as a safety
    # net (see app/upgrade.py). Keep names consistent there too if present.
    if inspector.has_table("attendance_corrections"):
        tables.append("attendance_corrections")

    for table in tables:
        existing_names = [
            r[0]
            for r in session.execute(
                text(f"SELECT DISTINCT name FROM {table}")
            ).all()
        ]
        variants: list[str] = []
        for existing in existing_names:
            if not existing or existing == new_name:
                continue
            if existing == old_name:
                variants.append(existing)
                continue
            matched = match(existing, employees=employees_before)
            if matched and matched.id == employee_id:
                variants.append(existing)

        total = 0
        for variant in variants:
            result = session.execute(
                text(f"UPDATE {table} SET name = :new WHERE name = :old"),
                {"new": new_name, "old": variant},
            )
            total += int(result.rowcount or 0)
        counts[table] = total
        log.info(
            "employee rename: %s rewrote %d rows from %r to %r (variants=%s)",
            table, total, old_name, new_name, variants,
        )
    return counts


def delete(employee_id: str) -> bool:
    with session_scope() as session:
        row = session.get(EmployeeModel, employee_id)
        if row is None:
            return False
        session.delete(row)
        return True


def _seed_rows_from_json() -> list[dict]:
    try:
        raw = json.loads(_SEED_PATH.read_text())
    except (OSError, ValueError) as e:
        log.warning("Could not read seed %s: %s", _SEED_PATH, e)
        return []
    return raw if isinstance(raw, list) else []


def seed_if_empty() -> int:
    """Populate employees from the bundled JSON if the table is empty."""
    with session_scope() as session:
        count = session.execute(select(func.count()).select_from(EmployeeModel)).scalar_one()
        if int(count or 0) > 0:
            return 0
        seed = _seed_rows_from_json()
        for row in seed:
            try:
                emp_id = str(row["id"])
                # Guard against partially-populated DBs where a stray row has
                # the same id but the table-level count was 0 due to a race —
                # in practice this never happens during seeding, but it's
                # cheap to be defensive.
                if session.get(EmployeeModel, emp_id) is not None:
                    continue
                company_str = str(row.get("company") or "")
                department_str = str(row.get("department") or "")
                shift_str = str(row.get("shift") or "")
                session.add(
                    EmployeeModel(
                        id=emp_id,
                        name=str(row["name"]),
                        employee_code=str(row.get("employeeId") or row["id"]),
                        company=company_str,
                        company_id=get_or_create_company_id(session, company_str) if company_str else None,
                        department=department_str,
                        department_id=get_or_create_department_id(session, department_str) if department_str else None,
                        shift=shift_str,
                        shift_id=get_or_create_shift_id(session, shift_str) if shift_str else None,
                        role=str(row.get("role") or "Employee"),
                        dob=str(row.get("dob") or ""),
                        image_url=str(row.get("imageUrl") or ""),
                        email=str(row.get("email") or ""),
                        mobile=str(row.get("mobile") or ""),
                        salary_package=str(row.get("salaryPackage") or ""),
                    )
                )
            except KeyError as e:
                log.warning("Skipping malformed seed row (missing %s): %s", e, row)
        return len(seed)


def _normalize(value: str) -> str:
    return _NORMALIZE_RE.sub("", value.strip().lower())


def match(capture_name: str, *, employees: Optional[list[Employee]] = None) -> Optional[Employee]:
    """Ports frontend nameMatch.ts: case-insensitive, ignores punctuation/
    whitespace, allows bidirectional prefix match. "Ambika" matches
    "Ambika Menon"; "Akhil c v" matches "Akhil".
    """
    a = _normalize(capture_name)
    if not a:
        return None
    for emp in employees if employees is not None else all_employees():
        b = _normalize(emp.name)
        if not b:
            continue
        if a == b or a.startswith(b) or b.startswith(a):
            return emp
    return None


def company_for(capture_name: str, *, employees: Optional[list[Employee]] = None) -> Optional[str]:
    emp = match(capture_name, employees=employees)
    return emp.company if emp else None
