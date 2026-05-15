from __future__ import annotations

from sqlalchemy import func, select

from app.core.constants import Role
from app.models.admin import Admin
from app.repositories.base_repo import BaseRepository


class AdminRepository(BaseRepository[Admin]):
    model = Admin

    def get_by_username(self, username: str) -> Admin | None:
        stmt = select(Admin).where(Admin.username == username)
        return self.db.execute(stmt).scalar_one_or_none()

    def count(self) -> int:
        return int(self.db.execute(select(func.count(Admin.id))).scalar_one())

    def list_by_role(self, role: Role) -> list[Admin]:
        stmt = select(Admin).where(Admin.role == role).order_by(Admin.username)
        return list(self.db.execute(stmt).scalars().all())
