"""Import all models so SQLAlchemy's metadata knows about every table."""
from app.models.user import User
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.models.flashcard import Flashcard
from app.models.quiz import QuizAttempt
from app.models.chat import ChatSession, ChatMessage
from app.models.concept import Concept, ConceptLink

__all__ = [
    "User",
    "Document",
    "DocumentChunk",
    "Flashcard",
    "QuizAttempt",
    "ChatSession",
    "ChatMessage",
    "Concept",
    "ConceptLink",
]
