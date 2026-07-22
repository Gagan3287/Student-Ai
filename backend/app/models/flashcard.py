"""
Flashcard model — stores a single question/answer card generated from a document.

Tracks all state needed for both the SM-2 algorithm and the Phase 6
Half-Life Regression retention model.

SM-2 fields:
    sm2_interval     — days until the next scheduled review
    sm2_repetitions  — number of consecutive successful reviews
    sm2_easiness     — the "E-factor" multiplier (default 2.5, range 1.3–∞)

Retention model input features (updated incrementally on each review):
    review_count, correct_count, incorrect_count,
    avg_response_time_s, days_since_last_review (computed at query time),
    difficulty (derived from easiness)
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

    # Difficulty: 0.0 = easy, 1.0 = hard — inverse of SM-2 easiness factor
    # computed as: difficulty = max(0, 1 - (sm2_easiness - 1.3) / (2.5 - 1.3))
    difficulty = Column(Float, default=0.3)

    # ─── SM-2 spaced-repetition state ─────────────────────────────────────────
    sm2_interval = Column(Integer, default=1)         # days until next review
    sm2_repetitions = Column(Integer, default=0)      # consecutive correct reviews
    sm2_easiness = Column(Float, default=2.5)         # E-factor (≥ 1.3)

    # ─── Retention model feature accumulators ─────────────────────────────────
    # Updated on every review submission — these are the raw features fed to
    # the GradientBoostingRegressor in Phase 6.
    review_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    incorrect_count = Column(Integer, default=0)
    avg_response_time_s = Column(Float, default=0.0)

    # ─── Scheduling ───────────────────────────────────────────────────────────
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    next_review_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # ─── Retention prediction output ──────────────────────────────────────────
    # Updated after each review by calling RetentionPredictor.predict()
    retention_probability = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="flashcards")
    document = relationship("Document", back_populates="flashcards")
