"""Pydantic schemas for document endpoints."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    file_name: str | None
    content_type: str | None
    page_count: int | None
    summary: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
