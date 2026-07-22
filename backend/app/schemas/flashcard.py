"""Pydantic schemas for flashcard endpoints."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class FlashcardResponse(BaseModel):
    id: UUID
    document_id: UUID
    question: str
    answer: str
    difficulty: float
    sm2_interval: int
    next_review_at: datetime
    retention_probability: float | None
    review_count: int
    correct_count: int

    model_config = {"from_attributes": True}


class ReviewRequest(BaseModel):
    """
    quality: SM-2 quality score 0–5.
        5 = perfect recall, instant response
        4 = correct with slight hesitation
        3 = correct with significant difficulty
        2 = incorrect, but correct answer easy to recall on seeing it
        1 = incorrect, correct answer hard to recall
        0 = complete blackout
    response_time_s: seconds taken to answer (used by retention model)
    """
    quality: int        # 0–5 (SM-2 scale)
    response_time_s: float = 0.0


class ReviewResponse(BaseModel):
    id: UUID
    next_review_at: datetime
    sm2_interval: int
    retention_probability: float | None

