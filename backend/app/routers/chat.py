"""Chat / RAG router — full session and message management."""

import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import (
    CreateSessionRequest,
    SessionResponse,
    SessionDetailResponse,
    SendMessageRequest,
    MessageResponse,
    SourceChunk,
)
from app.services import chat_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_session_response(session: ChatSession) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        title=session.title or "New Chat",
        document_id=session.document_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _to_message_response(msg: ChatMessage) -> MessageResponse:
    source_chunks = None
    if msg.source_chunks:
        source_chunks = [
            SourceChunk(
                chunk_id=c.get("chunk_id"),
                page_number=c.get("page_number"),
                excerpt=c.get("excerpt", ""),
            )
            for c in msg.source_chunks
        ]
    return MessageResponse(
        id=msg.id,
        role=msg.role,
        content=msg.content,
        source_chunks=source_chunks,
        created_at=msg.created_at,
    )


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    body: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new chat session, optionally scoped to a specific document."""
    session = chat_service.create_session(
        db, current_user.id, body.title or "New Chat", body.document_id
    )
    return _to_session_response(session)


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all chat sessions for the authenticated user."""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return [_to_session_response(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a chat session with its full message history."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format.")

    session = chat_service.get_session_with_messages(db, session_uuid, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied.")

    return SessionDetailResponse(
        session=_to_session_response(session),
        messages=[_to_message_response(m) for m in session.messages],
    )


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    session_id: str,
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a message in a chat session.
    Triggers RAG retrieval + Groq answer generation.
    Returns the assistant's reply with source chunk citations.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format.")

    if not body.content or not body.content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    session = chat_service.get_session_with_messages(db, session_uuid, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied.")

    try:
        assistant_msg, _ = await chat_service.send_message(db, session, body.content.strip())
    except Exception as exc:
        logger.error(f"send_message error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to process message. Please try again.")

    return _to_message_response(assistant_msg)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a chat session and all its messages."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format.")

    deleted = chat_service.delete_session(db, session_uuid, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found or access denied.")
