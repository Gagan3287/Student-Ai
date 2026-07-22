"""Pydantic schemas for concept / knowledge graph endpoints."""
from uuid import UUID
from pydantic import BaseModel


class ConceptNode(BaseModel):
    id: UUID
    name: str
    document_id: UUID
    document_title: str | None = None


class ConceptEdge(BaseModel):
    source: UUID   # concept id
    target: UUID   # concept id
    label: str | None


class GraphResponse(BaseModel):
    nodes: list[ConceptNode]
    edges: list[ConceptEdge]

