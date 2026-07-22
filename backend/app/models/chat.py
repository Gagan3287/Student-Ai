"""Chat session and message models for the RAG doubt-solving chatbot."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class ChatSession(Base):
    """
    A named conversation thread.
    document_id = None means the RAG search spans all of the user's documents.
    document_id = <some UUID> means RAG search is scoped to that document only.
    """
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String(500), default="New Chat")
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    document = relationship("Document", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan",
                            order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """
    A single message in a chat session.
    role: "user" | "assistant"
    source_chunks: list of RAG chunks that backed the assistant's answer.
        Format: [{"chunk_id": "...", "page_number": 3, "excerpt": "...first 200 chars..."}]
    """
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role = Column(String(20), nullable=False)   # "user" | "assistant"
    content = Column(Text, nullable=False)
    source_chunks = Column(JSONB, nullable=True)  # populated only for assistant messages

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationship
    session = relationship("ChatSession", back_populates="messages")
