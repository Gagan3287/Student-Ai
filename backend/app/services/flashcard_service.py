"""
Flashcard service — AI generation, SM-2 scheduling, and retention model integration.

Phases covered:
  - Flashcard generation (Groq): prompt-based Q&A extraction from document chunks
  - SM-2 scheduling: applies sm2_update() on each review submission
  - Retention predictor: updates retention_probability after each review
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from app.adapters.groq_adapter import groq_adapter
from app.database import SessionLocal
from app.ml.sm2 import SM2State, sm2_update, next_review_datetime, difficulty_from_easiness
from app.ml.retention_inference import RetentionPredictor, RetentionFeatures
from app.models.flashcard import Flashcard
from app.models.chunk import DocumentChunk

logger = logging.getLogger(__name__)


# ─── Flashcard Generation ─────────────────────────────────────────────────────

FLASHCARD_SYSTEM_PROMPT = """You are an expert academic flashcard creator for engineering students.
Generate high-quality, exam-focused question-answer pairs from the provided study material.
Return ONLY a valid JSON array. No extra text before or after.
Each object must have keys: "question" (string) and "answer" (string).
- Questions should test understanding, not just recall.
- Answers should be concise but complete (2–4 sentences max).
- Aim for conceptual depth: definitions, mechanisms, comparisons, examples."""


async def generate_flashcards_for_document(
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    count: int = 10,
) -> list[Flashcard]:
    """
    Generate flashcards from a document's chunks using Groq.
    Returns a list of saved Flashcard ORM objects.
    Raises ValueError if document has no chunks or AI generation fails.
    """
    db = SessionLocal()
    try:
        # Fetch top chunks by chunk_index for coverage
        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
            .limit(6)
            .all()
        )

        if not chunks:
            raise ValueError("Document has no processed chunks. Ensure the document has status 'ready'.")

        # Build prompt from first 6 chunks (covers most documents)
        combined_text = "\n\n---\n\n".join(c.content for c in chunks)
        prompt = (
            f"Generate exactly {count} flashcard question-answer pairs from the following study material.\n\n"
            f"Material:\n{combined_text[:8000]}\n\n"
            f"Return a JSON array of {count} objects, each with \"question\" and \"answer\" keys."
        )

        raw = await groq_adapter.generate(
            prompt, system_prompt=FLASHCARD_SYSTEM_PROMPT, temperature=0.4, max_tokens=3000
        )

        # Parse JSON — Groq sometimes wraps in ```json ... ``` fences
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("```").strip()

        qa_pairs = json.loads(raw)
        if not isinstance(qa_pairs, list):
            raise ValueError("Groq returned non-list JSON for flashcards")

        # Persist flashcards
        new_cards = []
        for pair in qa_pairs[:count]:
            q = str(pair.get("question", "")).strip()
            a = str(pair.get("answer", "")).strip()
            if not q or not a:
                continue
            card = Flashcard(
                id=uuid.uuid4(),
                document_id=document_id,
                user_id=user_id,
                question=q,
                answer=a,
                difficulty=0.3,
                sm2_interval=1,
                sm2_repetitions=0,
                sm2_easiness=2.5,
                review_count=0,
                correct_count=0,
                incorrect_count=0,
                avg_response_time_s=0.0,
                next_review_at=datetime.now(timezone.utc),
            )
            db.add(card)
            new_cards.append(card)

        db.commit()
        for card in new_cards:
            db.refresh(card)
        return new_cards

    except json.JSONDecodeError as exc:
        raise ValueError(f"Groq returned invalid JSON for flashcards: {exc}") from exc
    finally:
        db.close()


# ─── Review Submission ────────────────────────────────────────────────────────

def apply_review(card: Flashcard, quality: int, response_time_s: float) -> Flashcard:
    """
    Apply an SM-2 review to a flashcard and update retention prediction.
    Mutates `card` in-place. The caller is responsible for committing the session.
    """
    if not 0 <= quality <= 5:
        raise ValueError(f"SM-2 quality must be 0–5, got {quality}")

    # ── SM-2 update ────────────────────────────────────────────────────────────
    state = SM2State(
        interval=card.sm2_interval,
        repetitions=card.sm2_repetitions,
        easiness=card.sm2_easiness,
    )
    new_state = sm2_update(state, quality)

    card.sm2_interval = new_state.interval
    card.sm2_repetitions = new_state.repetitions
    card.sm2_easiness = new_state.easiness
    card.difficulty = difficulty_from_easiness(new_state.easiness)

    # ── Review statistics ──────────────────────────────────────────────────────
    card.review_count += 1
    if quality >= 3:
        card.correct_count += 1
    else:
        card.incorrect_count += 1

    # Update rolling average response time
    n = card.review_count
    card.avg_response_time_s = (
        (card.avg_response_time_s * (n - 1) + response_time_s) / n
    )

    card.last_reviewed_at = datetime.now(timezone.utc)
    card.next_review_at = next_review_datetime(new_state.interval)

    # ── Retention prediction ───────────────────────────────────────────────────
    days_since = (
        (datetime.now(timezone.utc) - card.last_reviewed_at).total_seconds() / 86400
    )
    features = RetentionFeatures(
        review_count=card.review_count,
        correct_count=card.correct_count,
        incorrect_count=card.incorrect_count,
        avg_response_time_s=card.avg_response_time_s,
        days_since_last_review=max(0.0, days_since),
        question_difficulty=card.difficulty,
    )
    card.retention_probability = RetentionPredictor.predict(features)

    return card
