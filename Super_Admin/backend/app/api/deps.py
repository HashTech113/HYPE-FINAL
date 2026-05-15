from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.constants import Role
from app.core.exceptions import AuthenticationError

_bearer_scheme = HTTPBearer(auto_error=False)

from app.db.session import get_sessionmaker
from app.models.admin import Admin
from app.services.auth_service import AuthService
from app.services.cooldown_service import CooldownService, get_cooldown_service
from app.services.embedding_cache import EmbeddingCache
from app.services.face_service import FaceService
from app.workers.camera_manager import CameraManager


def get_db() -> Generator[Session, None, None]:
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_face_service(request: Request) -> FaceService:
    svc: FaceService | None = getattr(request.app.state, "face_service", None)
    if svc is None:
        svc = FaceService()
        svc.load()
        request.app.state.face_service = svc
    return svc


def get_embedding_cache(request: Request) -> EmbeddingCache:
    cache: EmbeddingCache | None = getattr(request.app.state, "embedding_cache", None)
    if cache is None:
        cache = EmbeddingCache()
        cache.load_from_db()
        request.app.state.embedding_cache = cache
    return cache


def get_cooldown(_: Request = None) -> CooldownService:  # type: ignore[assignment]
    return get_cooldown_service()


def get_camera_manager(request: Request) -> CameraManager:
    mgr: CameraManager | None = getattr(request.app.state, "camera_manager", None)
    if mgr is None:
        raise RuntimeError("Camera manager not initialized")
    return mgr


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Admin:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Missing bearer token")
    return AuthService(db).resolve_admin(credentials.credentials)


def require_roles(*roles: Role):
    def _dep(admin: Admin = Depends(get_current_admin)) -> Admin:
        AuthService.require_role(admin, *roles)
        return admin

    return _dep


def get_company_scope(admin: Admin = Depends(get_current_admin)) -> str | None:
    """Returns the company an admin is restricted to, or None for
    cross-company roles. HR users see only their own company.
    SUPER_ADMIN / ADMIN / VIEWER see everything (None).

    Endpoints that need to filter by company should `Depends(...)` on
    this and pass the result to the repo layer. Saves every endpoint
    from re-implementing the role-check.
    """
    if admin.role == Role.HR:
        if not admin.company:
            # Misconfigured HR account — fail closed rather than leak data
            from app.core.exceptions import AuthorizationError

            raise AuthorizationError("HR account has no company assigned; ask an admin to fix it")
        return admin.company
    return None
