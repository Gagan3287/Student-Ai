"""Dashboard router — real stats from database."""

import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.flashcard import Flashcard
from app.models.quiz import QuizAttempt

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats")
def get_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return real dashboard stats computed from the database."""
    now = datetime.now(timezone.utc)

    # Total documents
    total_documents = db.query(func.count(Document.id)).filter(
        Document.user_id == current_user.id
    ).scalar() or 0

    # Due flashcards
    due_cards_count = db.query(func.count(Flashcard.id)).filter(
        Flashcard.user_id == current_user.id,
        Flashcard.next_review_at <= now,
    ).scalar() or 0

    # Total flashcards
    total_flashcards = db.query(func.count(Flashcard.id)).filter(
        Flashcard.user_id == current_user.id
    ).scalar() or 0

    # Average quiz score (last 10 attempts)
    recent_attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.attempted_at.desc())
        .limit(10)
        .all()
    )
    if recent_attempts:
        avg_score = sum(
            a.score / a.total * 100 for a in recent_attempts if a.total > 0
        ) / len(recent_attempts)
        average_quiz_score = round(avg_score, 1)
    else:
        average_quiz_score = None

    # Revision streak: count consecutive days the user reviewed at least one flashcard
    # Simplified: count distinct days with a review in the last 30 days
    thirty_days_ago = now - timedelta(days=30)
    reviewed_cards = (
        db.query(Flashcard.last_reviewed_at)
        .filter(
            Flashcard.user_id == current_user.id,
            Flashcard.last_reviewed_at >= thirty_days_ago,
            Flashcard.last_reviewed_at != None,
        )
        .all()
    )
    # Build streak from review dates
    review_days = set()
    for (dt,) in reviewed_cards:
        if dt:
            review_days.add(dt.date())

    streak = 0
    check_date = now.date()
    while check_date in review_days:
        streak += 1
        check_date = check_date - timedelta(days=1)

    # Total quiz attempts
    total_quiz_attempts = db.query(func.count(QuizAttempt.id)).filter(
        QuizAttempt.user_id == current_user.id
    ).scalar() or 0

    return {
        "revision_streak": streak,
        "due_cards_count": due_cards_count,
        "total_documents": total_documents,
        "total_flashcards": total_flashcards,
        "total_quiz_attempts": total_quiz_attempts,
        "average_quiz_score": average_quiz_score,
    }


@router.get("/quiz-history")
def get_quiz_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Quiz score time series for the progress chart."""
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.attempted_at.asc())
        .limit(30)
        .all()
    )
    return {
        "history": [
            {
                "attempted_at": a.attempted_at.isoformat() if a.attempted_at else None,
                "score": a.score,
                "total": a.total,
                "percentage": round(a.score / a.total * 100, 1) if a.total else 0,
                "document_id": str(a.document_id),
            }
            for a in attempts
        ]
    }
