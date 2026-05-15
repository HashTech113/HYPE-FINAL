"""FastAPI dependencies for authn / authz.

Usage:
    @router.get("/api/admin/...", dependencies=[Depends(require_admin)])
    @router.get("/api/.../...",   dependencies=[Depends(require_admin_or_hr)])
    @router.post("/api/ingest",   dependencies=[Depends(require_api_key)])

When a route needs the user object, declare it positionally:
    def handler(user: User = Depends(get_current_user)): ...
"""

from __future__ import annotations

import logging
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status

from .config import INGEST_API_KEY
from .services import auth as auth_service
from .services.auth import User

log = logging.getLogger(__name__)


def _extract_bearer(auth_header: Optional[str]) -> str:
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return parts[1].strip()


def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    token = _extract_bearer(authorization)
    try:
        payload = auth_service.decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    user = auth_service.get_by_id(user_id) if user_id else None
    # Re-fetching from DB on every request lets us deactivate a user (or change
    # their role) without waiting for the JWT to expire.
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


def require_admin_or_hr(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("admin", "hr"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return user


def hr_scope(user: User) -> tuple[bool, str]:
    """Decide whether the caller's view should be filtered to a single company.

    Returns ``(filter_active, target_company)`` where ``target_company`` is
    pre-normalized for case-insensitive comparison:

    * Admins → ``(False, "")`` — full access; caller skips filtering.
    * HR with a company → ``(True, "owlytics")`` — caller filters to it.
    * HR with no company → ``(True, "")`` — empty target naturally filters
      everything out, so the user sees nothing instead of everything. Logged
      so a super-admin can repair the misconfigured account.
    """
    if user.role != "hr":
        return False, ""
    own = (user.company or "").strip().lower()
    if not own:
        log.warning(
            "HR user %r has no company assigned; serving empty result",
            user.username,
        )
        return True, ""
    return True, own


def require_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """Camera ingest authn. The server must have INGEST_API_KEY configured;
    if it isn't, ingest is closed (fail-closed by design — we never want a
    misconfigured deploy to silently accept unauthenticated face captures)."""
    if not INGEST_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingest is not configured on this server",
        )
    if not x_api_key or not auth_service.constant_time_eq(x_api_key, INGEST_API_KEY):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
