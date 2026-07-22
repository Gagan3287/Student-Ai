"""Pydantic schemas for chat / RAG endpoints."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    title: str | None = "New Chat"
    document_id: UUID | None = None  # None = search all user's docs


class SessionResponse(BaseModel):
    id: UUID
    title: str
    document_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceChunk(BaseModel):
    chunk_id: UUID
    page_number: int | None
    excerpt: str  # first 200 characters of the chunk


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    source_chunks: list[SourceChunk] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    content: str


class SessionDetailResponse(BaseModel):
    session: SessionResponse
    messages: list[MessageResponse]

