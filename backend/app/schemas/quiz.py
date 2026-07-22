"""Pydantic schemas for quiz endpoints."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class MCQOption(BaseModel):
    index: int
    text: str


class MCQQuestion(BaseModel):
    index: int
    question: str
    options: list[MCQOption]
    # correct_index is NOT exposed here — only returned after submission


class QuizResponse(BaseModel):
    document_id: UUID
    questions: list[MCQQuestion]


class AnswerSubmission(BaseModel):
    question_index: int
    chosen_option: int


class QuizAttemptRequest(BaseModel):
    answers: list[AnswerSubmission]


class AnswerResult(BaseModel):
    question_index: int
    question: str
    chosen_option: int
    correct_option: int
    is_correct: bool


class QuizAttemptResponse(BaseModel):
    id: UUID
    score: int
    total: int
    percentage: float
    results: list[AnswerResult]
    attempted_at: datetime

