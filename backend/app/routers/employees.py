"""Employee directory CRUD.

Authorization model:
* Admin can read/create/update/delete every employee record.
* HR can read every employee but write only within their own ``company``.
  Cross-company writes (HR creating/editing/deleting an employee whose
  ``company`` doesn't match their own) get a 403 — same shape as the rest
  of the app's HR scoping.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from ..dependencies import hr_scope, require_admin_or_hr
from ..services import employees as employees_service
from ..services.auth import User

router = APIRouter(tags=["employees"])


def _ensure_can_write(user: User, company: str) -> None:
    """Admins are unrestricted. HR can only write rows whose company
    matches their own. Empty/missing company is treated as out-of-scope
    for HR (admin-only), since seed/legacy rows without a company can't
    safely be assigned to a single HR's bucket."""
    if user.role == "admin":
        return
    if user.role != "hr":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role",
        )
    target = (company or "").strip().lower()
    own = (user.company or "").strip().lower()
    if not target or not own or target != own:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR can only modify employees in their own company",
        )


class EmployeeOut(BaseModel):
    id: str
    name: str
    employeeId: str
    company: str
    department: str
    shift: str
    role: str
    dob: str = ""
    imageUrl: str = ""
    email: str = ""
    mobile: str = ""
    salaryPackage: str = ""


class EmployeeListResponse(BaseModel):
    items: list[EmployeeOut]


class EmployeeCreate(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1)
    employeeId: str = Field(..., min_length=1)
    company: str = ""
    department: str = ""
    shift: str = ""
    role: str = "Employee"
    dob: str = ""
    imageUrl: str = ""
    email: str = ""
    mobile: str = ""
    salaryPackage: str = ""


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    employeeId: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    shift: Optional[str] = None
    role: Optional[str] = None
    dob: Optional[str] = None
    imageUrl: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    salaryPackage: Optional[str] = None


def _serialize(emp) -> EmployeeOut:
    return EmployeeOut(
        id=emp.id,
        name=emp.name,
        employeeId=emp.employee_id,
        company=emp.company,
        department=emp.department,
        shift=emp.shift,
        role=emp.role,
        dob=emp.dob,
        imageUrl=emp.image_url,
        email=emp.email,
        mobile=emp.mobile,
        salaryPackage=emp.salary_package,
    )


@router.get(
    "/api/employees",
    response_model=EmployeeListResponse,
)
def list_employees(
    response: Response,
    user: User = Depends(require_admin_or_hr),
) -> EmployeeListResponse:
    items = [_serialize(e) for e in employees_service.all_employees()]
    filter_active, target = hr_scope(user)
    if filter_active:
        items = [it for it in items if (it.company or "").strip().lower() == target]
    # Browser-side cache: when multiple components mount and all call
    # /api/employees within 5 s, only the first goes to the network — the
    # rest are served from the browser's own cache. ``private`` keeps any
    # shared cache (proxy / CDN) from holding the auth-scoped roster.
    response.headers["Cache-Control"] = "private, max-age=5"
    return EmployeeListResponse(items=items)


@router.post(
    "/api/employees",
    response_model=EmployeeOut,
    status_code=201,
)
def create_employee(
    payload: EmployeeCreate,
    user: User = Depends(require_admin_or_hr),
) -> EmployeeOut:
    _ensure_can_write(user, payload.company)
    new_id = payload.id or f"emp-{uuid.uuid4().hex[:10]}"
    if employees_service.get_by_id(new_id):
        raise HTTPException(status_code=409, detail=f"employee id already exists: {new_id}")
    created = employees_service.create(
        id=new_id,
        name=payload.name,
        employee_id=payload.employeeId,
        company=payload.company,
        department=payload.department,
        shift=payload.shift,
        role=payload.role,
        dob=payload.dob,
        image_url=payload.imageUrl,
        email=payload.email,
        mobile=payload.mobile,
        salary_package=payload.salaryPackage,
    )
    return _serialize(created)


@router.put(
    "/api/employees/{employee_id}",
    response_model=EmployeeOut,
)
def update_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    user: User = Depends(require_admin_or_hr),
) -> EmployeeOut:
    existing = employees_service.get_by_id(employee_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"employee not found: {employee_id}")
    # HR may only edit rows in their own company. Check both the existing
    # row and the patched company (if provided) so HR can't move an employee
    # out of their own bucket.
    _ensure_can_write(user, existing.company)
    if payload.company is not None and payload.company != existing.company:
        _ensure_can_write(user, payload.company)

    patch = payload.model_dump(exclude_none=True)
    # Map camelCase input → snake_case DB columns
    if "employeeId" in patch:
        patch["employee_id"] = patch.pop("employeeId")
    if "imageUrl" in patch:
        patch["image_url"] = patch.pop("imageUrl")
    if "salaryPackage" in patch:
        patch["salary_package"] = patch.pop("salaryPackage")
    updated = employees_service.update(employee_id, patch)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"employee not found: {employee_id}")
    return _serialize(updated)


@router.delete("/api/employees/{employee_id}")
def delete_employee(
    employee_id: str,
    user: User = Depends(require_admin_or_hr),
) -> dict:
    existing = employees_service.get_by_id(employee_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"employee not found: {employee_id}")
    _ensure_can_write(user, existing.company)
    ok = employees_service.delete(employee_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"employee not found: {employee_id}")
    return {"status": "deleted", "id": employee_id}
