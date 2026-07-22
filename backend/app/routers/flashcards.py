"""Flashcards router — full SM-2 + AI generation implementation."""

import uuid
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.flashcard import Flashcard
from app.models.document import Document
from app.schemas.flashcard import FlashcardResponse, ReviewRequest, ReviewResponse
from app.services.flashcard_service import generate_flashcards_for_document, apply_review

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=list[FlashcardResponse])
def list_flashcards(
    document_id: str | None = Query(None, description="Filter by document ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all flashcards for the authenticated user, optionally filtered by document."""
    query = db.query(Flashcard).filter(Flashcard.user_id == current_user.id)
    if document_id:
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid document ID format.")
        query = query.filter(Flashcard.document_id == doc_uuid)
    return query.order_by(Flashcard.created_at.desc()).all()


@router.get("/due", response_model=list[FlashcardResponse])
def get_due_flashcards(
    document_id: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all flashcards due for review (next_review_at <= now)."""
    now = datetime.now(timezone.utc)
    query = db.query(Flashcard).filter(
        Flashcard.user_id == current_user.id,
        Flashcard.next_review_at <= now,
    )
    if document_id:
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid document ID format.")
        query = query.filter(Flashcard.document_id == doc_uuid)
    return query.order_by(Flashcard.next_review_at).all()


@router.post("/generate/{document_id}", response_model=list[FlashcardResponse], status_code=status.HTTP_201_CREATED)
async def generate_flashcards(
    document_id: str,
    count: int = Query(10, ge=3, le=20, description="Number of flashcards to generate (3–20)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate AI flashcards for a document using Groq LLM.
    The document must have status='ready' (fully processed).
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
            detail=f"Document is not ready for flashcard generation (status: {doc.status}). Wait for processing to complete."
        )

    try:
        cards = await generate_flashcards_for_document(doc_uuid, current_user.id, count)
        return cards
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error(f"Flashcard generation error for document {document_id}: {exc}")
        raise HTTPException(status_code=500, detail="Flashcard generation failed. Please try again.")


@router.post("/{flashcard_id}/review", response_model=ReviewResponse)
def review_flashcard(
    flashcard_id: str,
    body: ReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit a review result for a flashcard.
    Updates SM-2 scheduling and retention probability.
    quality: 0–5 (SM-2 scale, 0=blackout, 5=perfect recall)
    """
    try:
        card_uuid = uuid.UUID(flashcard_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid flashcard ID format.")

    card = db.query(Flashcard).filter(
        Flashcard.id == card_uuid, Flashcard.user_id == current_user.id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found or access denied.")

    try:
        apply_review(card, body.quality, body.response_time_s)
        db.commit()
        db.refresh(card)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return ReviewResponse(
        id=card.id,
        next_review_at=card.next_review_at,
        sm2_interval=card.sm2_interval,
        retention_probability=card.retention_probability,
    )


@router.delete("/{flashcard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flashcard(
    flashcard_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a flashcard."""
    try:
        card_uuid = uuid.UUID(flashcard_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid flashcard ID format.")

    card = db.query(Flashcard).filter(
        Flashcard.id == card_uuid, Flashcard.user_id == current_user.id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found or access denied.")

    db.delete(card)
    db.commit()
