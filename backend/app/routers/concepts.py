"""Concepts / knowledge graph router — returns extracted concepts and relationships."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.concept import Concept, ConceptLink

router = APIRouter()


@router.get("")
def list_concepts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    concepts = db.query(Concept).filter(Concept.user_id == current_user.id).all()
    return {
        "concepts": [
            {
                "id": str(c.id),
                "name": c.name,
                "document_id": str(c.document_id),
                "created_at": c.created_at,
            }
            for c in concepts
        ]
    }


@router.get("/graph")
def get_graph(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    concepts = db.query(Concept).filter(Concept.user_id == current_user.id).all()
    concept_ids = [c.id for c in concepts]

    links = []
    if concept_ids:
        links = (
            db.query(ConceptLink)
            .filter(ConceptLink.source_id.in_(concept_ids))
            .all()
        )

    nodes = [
        {
            "id": str(c.id),
            "name": c.name,
            "document_id": str(c.document_id),
        }
        for c in concepts
    ]

    edges = [
        {
            "source": str(l.source_id),
            "target": str(l.target_id),
            "label": l.relation_label,
        }
        for l in links
    ]

    return {"nodes": nodes, "edges": edges}


@router.get("/{concept_id}")
def get_concept(concept_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        c_uuid = uuid.UUID(concept_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid concept ID format")

    concept = (
        db.query(Concept)
        .filter(Concept.id == c_uuid, Concept.user_id == current_user.id)
        .first()
    )
    if not concept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found")

    return {
        "id": str(concept.id),
        "name": concept.name,
        "document_id": str(concept.document_id),
        "created_at": concept.created_at,
    }

