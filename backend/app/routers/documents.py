"""Documents router — Phase 2 implementation."""

import logging
import uuid
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.adapters.storage_adapter import storage_adapter
from app.services.document_service import process_document_background, update_document_status

logger = logging.getLogger(__name__)
router = APIRouter()


async def download_file_bytes(storage_path: str) -> bytes:
    """Download file bytes from Supabase storage using a signed URL."""
    signed_url = await storage_adapter.get_signed_url(storage_path)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(signed_url)
        resp.raise_for_status()
        return resp.content


async def reprocess_document_task(document_id: uuid.UUID, storage_path: str, content_type: str):
    """Wrapper background task to download file bytes first and then run document processing."""
    try:
        file_bytes = await download_file_bytes(storage_path)
        await process_document_background(document_id, file_bytes, content_type)
    except Exception as exc:
        logger.error(f"Failed to download and reprocess document {document_id}: {exc}")
        # Run DB update in thread as it is blocking
        import asyncio
        await asyncio.to_thread(
            update_document_status,
            document_id,
            "error",
            None,
            f"Reprocessing failed during download: {str(exc)}"
        )


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF or TXT file to Supabase Storage, create a pending Document record,
    and trigger text parsing and embedding generation in a background worker task.
    """
    # Validate content type/extension
    content_type = file.content_type
    file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    
    if content_type not in ("application/pdf", "text/plain") and file_extension not in ("pdf", "txt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only PDF and TXT files are accepted."
        )

    # Standardize content type mapping
    if file_extension == "pdf" and content_type != "application/pdf":
        content_type = "application/pdf"
    elif file_extension == "txt" and content_type != "text/plain":
        content_type = "text/plain"

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )

    # Generate a unique storage path within user's folder
    storage_path = f"{current_user.id}/{uuid.uuid4()}_{file.filename}"
    
    try:
        await storage_adapter.upload_file(storage_path, file_bytes, content_type)
    except Exception as exc:
        logger.error(f"Failed to upload file to Supabase Storage: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store file: {str(exc)}"
        )

    # Create the DB entry in pending state
    db_doc = Document(
        id=uuid.uuid4(),
        user_id=current_user.id,
        title=file.filename,
        file_name=file.filename,
        storage_path=storage_path,
        content_type=content_type,
        status="pending",
    )
    
    try:
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
    except Exception as exc:
        db.rollback()
        # Clean up storage if DB write fails
        background_tasks.add_task(storage_adapter.delete_file, storage_path)
        logger.error(f"Database error registering uploaded document: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register upload details in database."
        )

    # Enqueue background text extraction, chunking, embedding generation, and summary
    background_tasks.add_task(
        process_document_background,
        db_doc.id,
        file_bytes,
        content_type
    )

    return db_doc


@router.get("", response_model=DocumentListResponse)
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all documents uploaded by the authenticated user."""
    docs = db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.created_at.desc()).all()
    return DocumentListResponse(documents=docs, total=len(docs))


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details of a specific document."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format."
        )

    doc = db.query(Document).filter(Document.id == doc_uuid, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    background_tasks: BackgroundTasks,
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a document, all its chunks, and its backing file in storage."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format."
        )

    doc = db.query(Document).filter(Document.id == doc_uuid, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )

    # Queue storage file delete
    background_tasks.add_task(storage_adapter.delete_file, doc.storage_path)

    # Delete DB record (related document chunks are deleted cascade automatically via model configuration)
    try:
        db.delete(doc)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to delete document from database: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document metadata from database."
        )


@router.post("/{document_id}/process", status_code=status.HTTP_202_ACCEPTED)
def process_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually re-trigger document parsing, chunking, and embedding generation
    for a document (e.g. if it previously failed and has 'error' status).
    """
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format."
        )

    doc = db.query(Document).filter(Document.id == doc_uuid, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )

    # Set status back to pending
    try:
        doc.status = "pending"
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to reset status to pending: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset document processing state."
        )

    # Trigger background download & re-processing task
    background_tasks.add_task(reprocess_document_task, doc.id, doc.storage_path, doc.content_type)

    return {"message": "Reprocessing started in background.", "document_id": document_id}

