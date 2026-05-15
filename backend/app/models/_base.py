"""SQLAlchemy declarative base shared by every model.

Lives in its own module so model files and ``app.db`` can both import it
without creating a circular dependency.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
