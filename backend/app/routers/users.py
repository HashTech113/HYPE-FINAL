"""Admin-only user management — Settings → User Accounts.

Lets an admin list, create, disable, and reset passwords for HR / admin
accounts at runtime. Without these endpoints, onboarding a new company's
HR account would require editing _HR_SEEDS in services/auth.py and
restarting the server.
"""

from __future__ import annotations

import secrets
import string
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..dependencies import require_admin
from ..services import auth as auth_service
from ..services.auth import User

router = APIRouter(tags=["users"])


class UserOut(BaseModel):
    id: str
    username: str
    role: str
    company: str
    displayName: str
    isActive: bool


class UserListResponse(BaseModel):
    items: list[UserOut]


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    role: str = Field(..., pattern=r"^(admin|hr)$")
    company: str = Field("", max_length=128)
    displayName: str = Field("", max_length=128)
    # Optional — when omitted, server generates a strong default and returns it
    # once in the response. Useful for "create + email password to user" flows.
    password: Optional[str] = Field(None, min_length=6, max_length=128)


class UserUpdate(BaseModel):
    # Renaming is supported but goes through a uniqueness check in the
    # service layer (``users.username`` has a unique index).
    username: Optional[str] = Field(None, min_length=2, max_length=64)
    role: Optional[str] = Field(None, pattern=r"^(admin|hr)$")
    company: Optional[str] = Field(None, max_length=128)
    displayName: Optional[str] = Field(None, max_length=128)
    isActive: Optional[bool] = None


class PasswordReset(BaseModel):
    password: str = Field(..., min_length=6, max_length=128)


class UserCreateResponse(UserOut):
    # Plaintext password is only ever surfaced here; never stored or logged.
    generatedPassword: Optional[str] = None


def _to_out(u: User) -> UserOut:
    return UserOut(
        id=u.id,
        username=u.username,
        role=u.role,
        company=u.company,
        displayName=u.display_name,
        isActive=u.is_active,
    )


def _generate_strong_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(14))


@router.get(
    "/api/admin/users",
    response_model=UserListResponse,
    dependencies=[Depends(require_admin)],
)
def list_users() -> UserListResponse:
    return UserListResponse(items=[_to_out(u) for u in auth_service.list_all()])


@router.post(
    "/api/admin/users",
    response_model=UserCreateResponse,
    status_code=201,
)
def create_user(
    payload: UserCreate,
    actor: User = Depends(require_admin),
) -> UserCreateResponse:
    plaintext = payload.password or _generate_strong_password()
    try:
        created = auth_service.create_user(
            username=payload.username,
            password=plaintext,
            role=payload.role,
            company=payload.company,
            display_name=payload.displayName,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    out = _to_out(created)
    # Only echo the password back when the server generated it; if the caller
    # supplied their own, they already know it.
    generated = plaintext if payload.password is None else None
    return UserCreateResponse(**out.model_dump(), generatedPassword=generated)


@router.patch(
    "/api/admin/users/{user_id}",
    response_model=UserOut,
)
def update_user(
    user_id: str,
    payload: UserUpdate,
    actor: User = Depends(require_admin),
) -> UserOut:
    # Guard rails so an admin can't accidentally lock themselves out by
    # disabling/demoting their own account.
    if user_id == actor.id:
        if payload.isActive is False:
            raise HTTPException(status_code=400, detail="Cannot disable your own account")
        if payload.role is not None and payload.role != actor.role:
            raise HTTPException(status_code=400, detail="Cannot change your own role")
    try:
        updated = auth_service.update_user_meta(
            user_id,
            username=payload.username,
            role=payload.role,
            company=payload.company,
            display_name=payload.displayName,
            is_active=payload.isActive,
        )
    except ValueError as e:
        # Uniqueness conflicts surface as 409; everything else (bad role,
        # short username) is a 400.
        msg = str(e)
        status = 409 if "already taken" in msg else 400
        raise HTTPException(status_code=status, detail=msg)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"user not found: {user_id}")
    return _to_out(updated)


@router.post(
    "/api/admin/users/{user_id}/reset-password",
    response_model=UserOut,
)
def reset_password(
    user_id: str,
    payload: PasswordReset,
    actor: User = Depends(require_admin),
) -> UserOut:
    if not auth_service.reset_password(user_id, payload.password):
        raise HTTPException(status_code=404, detail=f"user not found: {user_id}")
    user = auth_service.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"user not found: {user_id}")
    return _to_out(user)
