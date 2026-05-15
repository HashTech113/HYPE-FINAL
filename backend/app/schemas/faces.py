"""Response models for /api/faces/*."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class FaceHistoryItem(BaseModel):
    id: str
    name: str
    entry: str
    exit: str
    image_url: Optional[str] = None


class FaceHistoryResponse(BaseModel):
    count: int
    total: int
    limit: int
    offset: int
    items: list[FaceHistoryItem]
