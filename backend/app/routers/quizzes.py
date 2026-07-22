"""Quizzes router — AI MCQ generation and attempt scoring."""

import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.quiz import QuizAttempt
from app.schemas.quiz import (
    QuizResponse, MCQQuestion, MCQOption,
    QuizAttemptRequest, QuizAttemptResponse, AnswerResult,
)
from app.services.quiz_service import generate_quiz_questions, score_attempt

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory cache: document_id -> questions list (avoids regenerating per session)
# In production this would be Redis; for this scale a module dict is fine.
_quiz_cache: dict[str, list[dict]] = {}


@router.get("/{document_id}", response_model=QuizResponse)
async def get_quiz(
    document_id: str,
    count: int = Query(5, ge=3, le=15, description="Number of questions to generate"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate (or retrieve cached) MCQ questions for a document.
    Correct answers are NOT exposed — they are only revealed after attempt submission.
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format.")

    doc = db.query(Document).filter(
        Document.id == doc_uuid, Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or access denied.")
    if doc.status != "ready":
        raise HTTPException(
            status_code=422,
            detail=f"Document is not ready for quiz generation (status: {doc.status})."
        )

    cache_key = f"{document_id}:{count}"
    if cache_key not in _quiz_cache:
        try:
            questions = await generate_quiz_questions(doc_uuid, count)
            _quiz_cache[cache_key] = questions
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        except Exception as exc:
            logger.error(f"Quiz generation error for document {document_id}: {exc}")
            raise HTTPException(status_code=500, detail="Quiz generation failed. Please try again.")

    questions = _quiz_cache[cache_key]

    # Strip correct_index before sending to client
    mcq_questions = [
        MCQQuestion(
            index=q["index"],
            question=q["question"],
            options=[MCQOption(index=i, text=opt) for i, opt in enumerate(q["options"])],
        )
        for q in questions
    ]
    return QuizResponse(document_id=doc_uuid, questions=mcq_questions)


@router.post("/{document_id}/attempt", response_model=QuizAttemptResponse, status_code=status.HTTP_201_CREATED)
async def submit_quiz(
    document_id: str,
    body: QuizAttemptRequest,
    count: int = Query(5, ge=3, le=15),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit answers for a quiz attempt.
    Returns score, percentage, and per-question feedback with correct answers.
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format.")

    doc = db.query(Document).filter(
        Document.id == doc_uuid, Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or access denied.")

    cache_key = f"{document_id}:{count}"
    if cache_key not in _quiz_cache:
        # Regenerate if cache was cleared (e.g. server restart)
        try:
            questions = await generate_quiz_questions(doc_uuid, count)
            _quiz_cache[cache_key] = questions
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Could not retrieve quiz questions: {exc}")

    questions = _quiz_cache[cache_key]
    answers_raw = [{"question_index": a.question_index, "chosen_option": a.chosen_option} for a in body.answers]
    scored = score_attempt(questions, answers_raw)

    # Persist to DB
    attempt = QuizAttempt(
        id=uuid.uuid4(),
        document_id=doc_uuid,
        user_id=current_user.id,
        score=scored["score"],
        total=scored["total"],
        answers=scored["results"],
        attempted_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return QuizAttemptResponse(
        id=attempt.id,
        score=scored["score"],
        total=scored["total"],
        percentage=scored["percentage"],
        results=[
            AnswerResult(
                question_index=r["question_index"],
                question=r["question"],
                chosen_option=r["chosen_option"],
                correct_option=r["correct_option"],
                is_correct=r["is_correct"],
            )
            for r in scored["results"]
        ],
        attempted_at=attempt.attempted_at,
    )


@router.get("/history/all")
def quiz_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the user's quiz attempt history with scores."""
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.attempted_at.desc())
        .limit(50)
        .all()
    )
    return {
        "attempts": [
            {
                "id": str(a.id),
                "document_id": str(a.document_id),
                "score": a.score,
                "total": a.total,
                "percentage": round(a.score / a.total * 100, 1) if a.total else 0,
                "attempted_at": a.attempted_at.isoformat() if a.attempted_at else None,
            }
            for a in attempts
        ]
    }
