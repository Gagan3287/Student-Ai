"""Concept and ConceptLink models for the knowledge graph (Phase 4)."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Concept(Base):
    """
    A key concept extracted from a document chunk by the LLM.
    Nodes in the knowledge graph.
    """
    __tablename__ = "concepts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_id = Column(
        UUID(as_uuid=True), ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True
    )
    name = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="concepts")
    document = relationship("Document", back_populates="concepts")
    outgoing_links = relationship(
        "ConceptLink", foreign_keys="ConceptLink.source_id",
        back_populates="source", cascade="all, delete-orphan"
    )
    incoming_links = relationship(
        "ConceptLink", foreign_keys="ConceptLink.target_id",
        back_populates="target", cascade="all, delete-orphan"
    )


class ConceptLink(Base):
    """
    A directed relationship between two concepts.
    Edges in the knowledge graph.
    The UNIQUE constraint prevents duplicate edges when the same relationship
    is extracted multiple times across different document chunks.
    """
    __tablename__ = "concept_links"
    __table_args__ = (UniqueConstraint("source_id", "target_id", name="uq_concept_link"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(
        UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False
    )
    target_id = Column(
        UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False
    )
    relation_label = Column(String(255), nullable=True)  # e.g. "related_to", "part_of"

    # Relationships
    source = relationship("Concept", foreign_keys=[source_id], back_populates="outgoing_links")
    target = relationship("Concept", foreign_keys=[target_id], back_populates="incoming_links")
