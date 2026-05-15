"""POST /api/auth/login + companion endpoints (me, change-password, profile)."""

# NOTE: ``from __future__ import annotations`` is intentionally NOT used here.
# slowapi wraps the rate-limited endpoint and FastAPI's pydantic resolver
# can't find the request-body class via its forward-ref string when the
# enclosing function has been decorated, so we keep eagerly-resolved
# annotations on this file specifically.

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..config import JWT_TTL_SECONDS
from ..dependencies import get_current_user, require_admin_or_hr
from ..ratelimit import limiter
from ..services import auth as auth_service
from ..services.auth import User

log = logging.getLogger(__name__)

router = APIRouter(tags=["auth"], prefix="/api/auth")


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=256)


class UserOut(BaseModel):
    id: str
    username: str
    role: str
    company: str
    displayName: str
    avatarUrl: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        role=user.role,
        company=user.company,
        displayName=user.display_name or user.username,
        avatarUrl=user.avatar_url,
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest) -> LoginResponse:
    record = auth_service.get_by_username(payload.username)
    # Same generic message for "no such user" and "wrong password" so the
    # response can't be used to enumerate accounts.
    if record is None:
        log.info("login failed (unknown user) username=%r", payload.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    user, password_hash = record
    if not user.is_active:
        log.info("login failed (inactive user) username=%r", payload.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if not auth_service.verify_password(payload.password, password_hash):
        log.info("login failed (bad password) username=%r", payload.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = auth_service.create_access_token(
        user_id=user.id, username=user.username, role=user.role, company=user.company
    )
    log.info("login ok username=%r role=%s", user.username, user.role)
    return LoginResponse(access_token=token, expires_in=JWT_TTL_SECONDS, user=_user_out(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return _user_out(user)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=256)
    new_password: str = Field(..., min_length=6, max_length=256)


@router.post("/change-password")
@limiter.limit("5/minute")
def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
) -> dict:
    record = auth_service.get_by_username(user.username)
    if record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    _, password_hash = record
    if not auth_service.verify_password(payload.current_password, password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    auth_service.update_password(user.id, payload.new_password)
    log.info("password changed for username=%r", user.username)
    return {"status": "ok"}


class UpdateProfileRequest(BaseModel):
    displayName: Optional[str] = Field(None, max_length=128)
    avatarUrl: Optional[str] = Field(None, max_length=2_500_000)  # data: URL fits 2 MB image
    username: Optional[str] = Field(None, min_length=1, max_length=128)


@router.put("/profile", response_model=UserOut)
def update_profile(
    payload: UpdateProfileRequest,
    user: User = Depends(require_admin_or_hr),
) -> UserOut:
    """Self-update of the calling user's profile. Both admin and HR can call
    this — each only updates their OWN row, never anyone else's. The change
    is mirrored into the JWT cache via the get_by_id refresh on the next
    authenticated request."""
    new_username = payload.username.strip() if payload.username else None
    if new_username and new_username != user.username:
        existing = auth_service.get_by_username(new_username)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    updated = auth_service.update_profile(
        user.id,
        display_name=payload.displayName.strip() if payload.displayName else None,
        avatar_url=payload.avatarUrl,
        username=new_username,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _user_out(updated)
