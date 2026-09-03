from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.models.document import DocumentStatus
from app.models.user import User
from app.services.document_service import DocumentService
from app.api.deps import get_current_admin, get_current_agent_or_admin

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[DocumentStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_agent_or_admin)
):
    """List documents with pagination and optional status filter (Admin and Support Agent)."""
    items, total = DocumentService.list_documents(
        db=db, skip=skip, limit=limit, status_filter=status
    )
    return {"items": items, "total": total}


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Upload a new PDF or DOCX document (Admin-only)."""
    return DocumentService.upload_document(db=db, file=file, user_id=current_admin.id)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_agent_or_admin)
):
    """Get single document details (Admin and Support Agent)."""
    doc = DocumentService.get_document_by_id(db, document_id=document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Delete a document and its stored file (Admin-only)."""
    deleted = DocumentService.delete_document(db, document_id=document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    return None


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
def reprocess_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Trigger reprocessing for an existing document (Admin-only)."""
    doc = DocumentService.reprocess_document(db, document_id=document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    return doc
