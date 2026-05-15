"""Authentication primitives — password hashing, JWT issue/verify, user CRUD.

The login flow is:
    POST /api/auth/login {username, password}
        -> verify_password against users.password_hash
        -> create_access_token({sub, role, company})
        -> client stores the token and sends it as Authorization: Bearer <token>

Roles supported: 'admin' (full access) and 'hr' (scoped to their company).
"""

from __future__ import annotations

import logging
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import bcrypt
import jwt
from sqlalchemy import select

from ..config import JWT_ALGORITHM, JWT_SECRET, JWT_TTL_SECONDS, SEED_ADMIN_PASSWORD, SEED_ADMIN_USERNAME
from ..db import session_scope
from ..models import User as UserModel
from .lookups import get_or_create_company_id

log = logging.getLogger(__name__)


# Per-company HR accounts seeded on first boot. The (username, company,
# display_name) tuples mirror what was previously hardcoded in the frontend
# auth.ts, so existing operators can keep their workflow.
_HR_SEEDS: tuple[tuple[str, str, str], ...] = (
    ("wawu",          "WAWU",            "WAWU HR"),
    ("cap",           "CAP",             "CAP HR"),
    ("owlytics",      "Owlytics",        "Owlytics HR"),
    ("grow",          "Grow",            "Grow HR"),
    ("perform100x",   "Perform100x",     "Perform100x HR"),
    ("sib",           "Study in Bengaluru", "Study in Bengaluru HR"),
    ("careercafeco",  "career cafe co",  "Career Cafe Co HR"),
    ("ceo2",          "CEO Square",      "CEO Square HR"),
    ("karumitra",     "Karumitra",       "Karumitra HR"),
    ("legalquotient", "Legal Quotient",  "Legal Quotient HR"),
    ("startuptv",     "Startup TV",      "Startup TV HR"),
)


@dataclass(frozen=True)
class User:
    id: str
    username: str
    role: str
    company: str
    display_name: str
    avatar_url: str
    is_active: bool


# ---- password hashing -------------------------------------------------------

def hash_password(plain: str) -> str:
    """bcrypt with cost=12. Returns a UTF-8 string for DB storage."""
    if not plain:
        raise ValueError("password must be non-empty")
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---- JWT --------------------------------------------------------------------

def create_access_token(*, user_id: str, username: str, role: str, company: str) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "company": company,
        "iat": now,
        "exp": now + JWT_TTL_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError on invalid / expired tokens — callers convert
    to HTTP 401."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


# ---- user CRUD --------------------------------------------------------------

def _model_to_user(row: UserModel) -> User:
    return User(
        id=str(row.id),
        username=str(row.username),
        role=str(row.role),
        company=str(row.company or ""),
        display_name=str(row.display_name or row.username),
        avatar_url=str(row.avatar_url or ""),
        is_active=bool(row.is_active),
    )


def get_by_username(username: str) -> Optional[tuple[User, str]]:
    """Returns (User, password_hash) or None. The hash is returned separately
    so callers can verify without leaking it through the User dataclass."""
    if not username:
        return None
    with session_scope() as session:
        row = session.execute(
            select(UserModel).where(UserModel.username == username.strip())
        ).scalar_one_or_none()
        if row is None:
            return None
        return _model_to_user(row), str(row.password_hash)


def get_by_id(user_id: str) -> Optional[User]:
    if not user_id:
        return None
    with session_scope() as session:
        row = session.get(UserModel, user_id)
        return _model_to_user(row) if row else None


def update_password(user_id: str, new_plain: str) -> bool:
    new_hash = hash_password(new_plain)
    with session_scope() as session:
        row = session.get(UserModel, user_id)
        if row is None:
            return False
        row.password_hash = new_hash
        return True


def update_profile(
    user_id: str,
    *,
    display_name: Optional[str] = None,
    avatar_url: Optional[str] = None,
    username: Optional[str] = None,
) -> Optional[User]:
    with session_scope() as session:
        row = session.get(UserModel, user_id)
        if row is None:
            return None
        if display_name is not None:
            row.display_name = display_name
        if avatar_url is not None:
            row.avatar_url = avatar_url
        if username is not None:
            row.username = username
        session.flush()
        return _model_to_user(row)


def list_all() -> list[User]:
    with session_scope() as session:
        rows = session.execute(
            select(UserModel).order_by(UserModel.role.desc(), UserModel.username)
        ).scalars().all()
        return [_model_to_user(r) for r in rows]


def create_user(
    *,
    username: str,
    password: str,
    role: str,
    company: str,
    display_name: str,
) -> User:
    """Mint a new user. Raises ValueError on duplicate username or bad role."""
    username = (username or "").strip()
    role = (role or "").strip().lower()
    if not username:
        raise ValueError("username is required")
    if role not in ("admin", "hr"):
        raise ValueError("role must be 'admin' or 'hr'")
    if role == "hr" and not (company or "").strip():
        raise ValueError("HR users must have a company assigned")
    with session_scope() as session:
        clash = session.execute(
            select(UserModel.id).where(UserModel.username == username)
        ).scalar_one_or_none()
        if clash is not None:
            raise ValueError(f"username already exists: {username!r}")
        company_id = get_or_create_company_id(session, company) if company else None
        row = UserModel(
            id=f"usr-{uuid.uuid4().hex[:10]}",
            username=username,
            password_hash=hash_password(password),
            role=role,
            company=company or "",
            company_id=company_id,
            display_name=display_name or username,
            avatar_url="",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        session.add(row)
        session.flush()
        return _model_to_user(row)


def update_user_meta(
    user_id: str,
    *,
    username: Optional[str] = None,
    role: Optional[str] = None,
    company: Optional[str] = None,
    display_name: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Optional[User]:
    """Admin-only metadata update. Re-syncs company_id when company changes.

    Username changes are allowed but go through a uniqueness check first —
    the ``users.username`` column has a unique index, so a collision would
    bounce as a low-level integrity error otherwise. Raises ``ValueError``
    on collision so the router can surface a 409.
    """
    with session_scope() as session:
        row = session.get(UserModel, user_id)
        if row is None:
            return None
        if username is not None:
            new_username = username.strip()
            if len(new_username) < 2:
                raise ValueError("username must be at least 2 characters")
            if new_username != row.username:
                clash = session.execute(
                    select(UserModel.id).where(
                        UserModel.username == new_username,
                        UserModel.id != user_id,
                    )
                ).scalar_one_or_none()
                if clash is not None:
                    raise ValueError(f"username {new_username!r} already taken")
                row.username = new_username
        if role is not None:
            r = role.strip().lower()
            if r not in ("admin", "hr"):
                raise ValueError("role must be 'admin' or 'hr'")
            row.role = r
        if company is not None:
            row.company = company
            row.company_id = (
                get_or_create_company_id(session, company) if company else None
            )
        if display_name is not None:
            row.display_name = display_name
        if is_active is not None:
            row.is_active = bool(is_active)
        session.flush()
        return _model_to_user(row)


def reset_password(user_id: str, new_plain: str) -> bool:
    """Admin-only password reset for another user (no current-password check)."""
    return update_password(user_id, new_plain)


def seed_users_if_empty() -> None:
    """Insert default admin + HR accounts on first boot. Idempotent: a row
    already in the table is left alone, so operators can rotate passwords
    without them being overwritten on restart."""
    now = datetime.now(timezone.utc)
    with session_scope() as session:
        existing = {
            row[0] for row in session.execute(select(UserModel.username)).all()
        }

        def _insert(username: str, password: str, role: str, company: str, display_name: str) -> None:
            if username in existing:
                return
            company_id = get_or_create_company_id(session, company) if company else None
            session.add(
                UserModel(
                    id=f"usr-{uuid.uuid4().hex[:10]}",
                    username=username,
                    password_hash=hash_password(password),
                    role=role,
                    company=company,
                    company_id=company_id,
                    display_name=display_name,
                    avatar_url="",
                    is_active=True,
                    created_at=now,
                )
            )
            log.info("seeded user %r (role=%s)", username, role)

        _insert(SEED_ADMIN_USERNAME, SEED_ADMIN_PASSWORD, "admin", "", "Admin")
        for username, company, display_name in _HR_SEEDS:
            # Use the same `<username>@123` convention the frontend used so
            # nothing breaks for existing operators on first deploy.
            _insert(username, f"{username}@123", "hr", company, display_name)


# ---- API key for camera ingest ---------------------------------------------

def constant_time_eq(a: str, b: str) -> bool:
    return secrets.compare_digest(a or "", b or "")
