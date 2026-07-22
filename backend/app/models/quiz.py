"""Quiz attempt model — records a student's quiz session for a document."""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score = Column(Integer, nullable=False)   # number of correct answers
    total = Column(Integer, nullable=False)   # total number of questions

    # JSONB: stores full attempt detail for review
    # Format: [{"question": "...", "options": [...], "chosen": 2, "correct": 1, "is_correct": false}, ...]
    answers = Column(JSONB, nullable=True)

    attempted_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="quiz_attempts")
    document = relationship("Document", back_populates="quiz_attempts")
