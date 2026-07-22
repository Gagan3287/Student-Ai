"""
Quiz service — MCQ generation and attempt scoring.

Uses Groq to generate multiple-choice questions from document chunks,
persists attempts to quiz_attempts table with per-question answer breakdown.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from app.adapters.groq_adapter import groq_adapter
from app.models.chunk import DocumentChunk
from app.models.quiz import QuizAttempt

logger = logging.getLogger(__name__)


QUIZ_SYSTEM_PROMPT = """You are an expert quiz generator for engineering students.
Generate multiple-choice questions from the provided study material.
Return ONLY valid JSON — no extra text or markdown fences.
Each question object must have:
  "question": string
  "options": array of exactly 4 strings (A, B, C, D answer text)
  "correct_index": integer 0-3 (index of the correct option in "options")
  "explanation": string (brief explanation of the correct answer)
Questions should test conceptual understanding, not just memorisation."""


async def generate_quiz_questions(
    document_id: uuid.UUID,
    count: int = 5,
) -> list[dict]:
    """
    Generate MCQ questions from document chunks.
    Returns list of dicts with keys: question, options, correct_index, explanation.
    """
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
            .limit(5)
            .all()
        )
        if not chunks:
            raise ValueError("No processed chunks found for this document.")

        combined_text = "\n\n---\n\n".join(c.content for c in chunks)
        prompt = (
            f"Generate exactly {count} multiple-choice questions from the study material below.\n\n"
            f"Material:\n{combined_text[:7000]}\n\n"
            f"Return a JSON array of {count} question objects."
        )

        raw = await groq_adapter.generate(
            prompt, system_prompt=QUIZ_SYSTEM_PROMPT, temperature=0.3, max_tokens=3000
        )

        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("```").strip()

        questions = json.loads(raw)
        if not isinstance(questions, list):
            raise ValueError("Groq returned non-list JSON for quiz")

        # Validate and normalise
        validated = []
        for i, q in enumerate(questions[:count]):
            if not q.get("question") or not q.get("options"):
                continue
            validated.append({
                "index": i,
                "question": str(q["question"]).strip(),
                "options": [str(o).strip() for o in q["options"][:4]],
                "correct_index": int(q.get("correct_index", 0)),
                "explanation": str(q.get("explanation", "")).strip(),
            })
        return validated

    except json.JSONDecodeError as exc:
        raise ValueError(f"Groq returned invalid JSON for quiz: {exc}") from exc
    finally:
        db.close()


def score_attempt(questions: list[dict], answers: list[dict]) -> dict:
    """
    Score a quiz attempt.

    Args:
        questions: list of question dicts (with correct_index)
        answers: list of {question_index, chosen_option} dicts

    Returns:
        dict with score, total, percentage, results list
    """
    answer_map = {a["question_index"]: a["chosen_option"] for a in answers}
    results = []
    score = 0

    for q in questions:
        idx = q["index"]
        chosen = answer_map.get(idx, -1)
        correct = q["correct_index"]
        is_correct = chosen == correct
        if is_correct:
            score += 1
        results.append({
            "question_index": idx,
            "question": q["question"],
            "chosen_option": chosen,
            "correct_option": correct,
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
        })

    total = len(questions)
    return {
        "score": score,
        "total": total,
        "percentage": round(score / total * 100, 1) if total else 0.0,
        "results": results,
    }
