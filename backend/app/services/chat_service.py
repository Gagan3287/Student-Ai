"""
Chat / RAG service — session management and retrieval-augmented generation.

RAG pipeline per message:
  1. Embed the user query with Gemini (RETRIEVAL_QUERY task type)
  2. Cosine-similarity search against document_chunks via pgvector
  3. Build a context window from the top-k chunks
  4. Pass context + conversation history to Groq for answer generation
  5. Persist both the user message and assistant reply to the DB
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.adapters.gemini_adapter import gemini_adapter
from app.adapters.groq_adapter import groq_adapter
from app.models.chat import ChatSession, ChatMessage
from app.models.chunk import DocumentChunk

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are StudyMate AI — a helpful academic study companion for engineering students.
Answer questions based ONLY on the context passages provided below.
If the answer is not in the context, say: "I couldn't find information about that in your notes."
Be concise, accurate, and use bullet points when listing multiple items.
Always cite which part of the notes you drew from if possible."""


# ─── Session Management ───────────────────────────────────────────────────────

def create_session(db: Session, user_id: uuid.UUID, title: str, document_id: Optional[uuid.UUID]) -> ChatSession:
    session = ChatSession(
        id=uuid.uuid4(),
        user_id=user_id,
        title=title or "New Chat",
        document_id=document_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session_with_messages(db: Session, session_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ChatSession]:
    return (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
        .first()
    )


def delete_session(db: Session, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == user_id
    ).first()
    if not session:
        return False
    db.delete(session)
    db.commit()
    return True


# ─── RAG Retrieval ─────────────────────────────────────────────────────────────

async def retrieve_relevant_chunks(
    db: Session,
    user_id: uuid.UUID,
    query: str,
    document_id: Optional[uuid.UUID],
    top_k: int = 4,
) -> list[DocumentChunk]:
    """
    Embed the query with Gemini, then run pgvector cosine similarity search.
    Scoped to a single document if document_id is set, else all user documents.
    """
    try:
        query_embedding = await gemini_adapter.embed_query(query)
    except Exception as exc:
        logger.error(f"Failed to embed query: {exc}")
        return []

    # Build pgvector query — cosine similarity = 1 - cosine distance
    embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

    if document_id:
        sql = text("""
            SELECT dc.id, dc.content, dc.page_number, dc.document_id
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE d.user_id = :user_id AND dc.document_id = :document_id
                AND dc.embedding IS NOT NULL
            ORDER BY dc.embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """)
        params = {
            "user_id": str(user_id),
            "document_id": str(document_id),
            "embedding": embedding_str,
            "top_k": top_k,
        }
    else:
        sql = text("""
            SELECT dc.id, dc.content, dc.page_number, dc.document_id
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE d.user_id = :user_id AND dc.embedding IS NOT NULL
            ORDER BY dc.embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """)
        params = {
            "user_id": str(user_id),
            "embedding": embedding_str,
            "top_k": top_k,
        }

    try:
        rows = db.execute(sql, params).fetchall()
        chunks = []
        for row in rows:
            # Build a lightweight object for the caller
            chunk = type("ChunkRow", (), {
                "id": row[0],
                "content": row[1],
                "page_number": row[2],
                "document_id": row[3],
            })()
            chunks.append(chunk)
        return chunks
    except Exception as exc:
        logger.error(f"pgvector similarity search failed: {exc}")
        return []


# ─── Message Handling ─────────────────────────────────────────────────────────

async def send_message(
    db: Session,
    session: ChatSession,
    user_content: str,
) -> tuple[ChatMessage, list[dict]]:
    """
    Process a user message through the RAG pipeline and return the assistant reply.

    Returns:
        (assistant_message, source_chunks_list)
    """
    # 1. Persist user message
    user_msg = ChatMessage(
        id=uuid.uuid4(),
        session_id=session.id,
        role="user",
        content=user_content,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user_msg)
    db.commit()

    # 2. Retrieve relevant chunks
    chunks = await retrieve_relevant_chunks(
        db, session.user_id, user_content, session.document_id
    )

    # 3. Build context
    source_chunks_meta = []
    if chunks:
        context_parts = []
        for i, chunk in enumerate(chunks):
            context_parts.append(f"[Source {i+1}, Page {chunk.page_number or '?'}]\n{chunk.content}")
            source_chunks_meta.append({
                "chunk_id": str(chunk.id),
                "page_number": chunk.page_number,
                "excerpt": chunk.content[:200],
            })
        context_text = "\n\n".join(context_parts)
    else:
        context_text = "No relevant notes found."

    # 4. Build conversation history (last 6 messages for context window)
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(6)
        .all()
    )
    history_text = ""
    if len(history) > 1:
        prior = list(reversed(history[1:]))  # exclude the user msg we just saved
        history_text = "\n".join(
            f"{'Student' if m.role == 'user' else 'StudyMate'}: {m.content}"
            for m in prior
        )

    # 5. Build prompt and call Groq
    prompt = (
        f"CONTEXT FROM STUDENT'S NOTES:\n{context_text}\n\n"
        + (f"CONVERSATION HISTORY:\n{history_text}\n\n" if history_text else "")
        + f"STUDENT QUESTION:\n{user_content}\n\n"
        + "ANSWER (based only on the context above):"
    )

    try:
        answer = await groq_adapter.generate(
            prompt, system_prompt=RAG_SYSTEM_PROMPT, temperature=0.2, max_tokens=1024
        )
    except Exception as exc:
        logger.error(f"Groq generation failed for chat: {exc}")
        raise RuntimeError(f"Groq AI generation error: {exc}") from exc

    # 6. Persist assistant message
    assistant_msg = ChatMessage(
        id=uuid.uuid4(),
        session_id=session.id,
        role="assistant",
        content=answer.strip(),
        source_chunks=source_chunks_meta if source_chunks_meta else None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(assistant_msg)

    # Update session timestamp
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg, source_chunks_meta
