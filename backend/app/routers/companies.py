"""Admin-only company catalog management — Settings → Edit Companies."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..dependencies import require_admin
from ..services import companies as companies_service

router = APIRouter(tags=["companies"])


class CompanyOut(BaseModel):
    id: int
    name: str
    employeeCount: int
    hasUsers: bool
    # Optional HR account fields — None when no HR account is linked to
    # this company yet. The frontend uses ``hrUserId`` as the target for
    # password-reset / username-change actions in the table.
    hrUserId: str | None = None
    hrUsername: str | None = None
    hrUserActive: bool | None = None


class CompanyListResponse(BaseModel):
    items: list[CompanyOut]


class CompanyRename(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)


def _to_out(d: dict) -> CompanyOut:
    return CompanyOut(
        id=d["id"],
        name=d["name"],
        employeeCount=d["employee_count"],
        hasUsers=d["has_users"],
        hrUserId=d.get("hr_user_id"),
        hrUsername=d.get("hr_username"),
        hrUserActive=d.get("hr_user_active"),
    )


@router.get(
    "/api/companies",
    response_model=CompanyListResponse,
    dependencies=[Depends(require_admin)],
)
def list_companies() -> CompanyListResponse:
    return CompanyListResponse(items=[_to_out(d) for d in companies_service.list_with_counts()])


@router.patch(
    "/api/companies/{company_id}",
    response_model=CompanyOut,
    dependencies=[Depends(require_admin)],
)
def rename_company(company_id: int, payload: CompanyRename) -> CompanyOut:
    try:
        return _to_out(companies_service.rename(company_id, payload.name))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except companies_service.CompanyNameError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/api/companies/{company_id}", dependencies=[Depends(require_admin)])
def delete_company(company_id: int) -> dict:
    try:
        users_cleared = companies_service.delete(company_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except companies_service.CompanyHasEmployeesError as e:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot delete: {e.count} employee(s) still belong to this company. "
                "Reassign or delete them first."
            ),
        )
    return {"status": "deleted", "id": company_id, "users_cleared": users_cleared}
