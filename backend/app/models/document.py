"""Document model — represents an uploaded PDF or text file."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    file_name = Column(String(500), nullable=True)
    storage_path = Column(Text, nullable=True)   # Supabase Storage object path
    content_type = Column(String(100), nullable=True)  # "application/pdf" | "text/plain"
    page_count = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)        # LLM-generated summary (populated after processing)

    # Processing status lifecycle:
    #   pending → processing → ready
    #                       ↘ error
    status = Column(String(50), default="pending", nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="document", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="document", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="document")
    concepts = relationship("Concept", back_populates="document", cascade="all, delete-orphan")
