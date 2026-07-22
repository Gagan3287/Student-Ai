"""
DocumentChunk model — a ~500-token slice of a document's text.

Each chunk has:
  - its raw text (used to build RAG context windows)
  - an embedding vector (768-dimensional float array, stored via pgvector)

The HNSW index on the embedding column is created manually in the Supabase
SQL editor (or via a migration) because SQLAlchemy's create_all() does not
support custom index types like HNSW natively.

Run this once in Supabase SQL Editor after the table is created:
    CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)   # 0-based position in document
    page_number = Column(Integer, nullable=True)    # best-guess page, from pypdf
    content = Column(Text, nullable=False)          # raw chunk text

    # 768-dimensional embedding from Gemini gemini-embedding-001
    # Used for cosine similarity search during RAG retrieval
    embedding = Column(Vector(768), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationship
    document = relationship("Document", back_populates="chunks")
