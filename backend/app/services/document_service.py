import os
from typing import Optional, List, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentStatus
from app.utils.file_utils import save_upload_file, delete_file_from_disk
from app.services.document_processing_service import DocumentProcessingService


class DocumentService:
    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")

    @classmethod
    def list_documents(
        cls,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[DocumentStatus] = None
    ) -> Tuple[List[Document], int]:
        """List documents with optional filtering and pagination."""
        query = db.query(Document)
        if status_filter:
            query = query.filter(Document.status == status_filter)
        
        total = query.count()
        documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
        return documents, total

    @classmethod
    def get_document_by_id(cls, db: Session, document_id: int) -> Optional[Document]:
        """Retrieve document by ID."""
        return db.query(Document).filter(Document.id == document_id).first()

    @classmethod
    def upload_document(cls, db: Session, file: UploadFile, user_id: int) -> Document:
        """
        Validate, safely store file on disk, and create a document record in PostgreSQL.
        Status is initialized to 'uploaded'.
        """
        original_filename, server_filename, file_path, file_size = save_upload_file(
            file, cls.UPLOAD_DIR
        )
        
        file_type = "pdf" if original_filename.lower().endswith(".pdf") else "docx"
        
        doc = Document(
            filename=server_filename,
            original_filename=original_filename,
            file_type=file_type,
            file_path=file_path,
            status=DocumentStatus.uploaded,
            chunk_count=0,
            uploaded_by=user_id
        )
        
        try:
            db.add(doc)
            db.commit()
            db.refresh(doc)
            return DocumentProcessingService.process(db, doc)
        except Exception as e:
            db.rollback()
            # Clean up saved file if DB commit fails
            delete_file_from_disk(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to record uploaded document: {str(e)}"
            )

    @classmethod
    def delete_document(cls, db: Session, document_id: int) -> bool:
        """Delete document from database and delete physical file from disk."""
        doc = cls.get_document_by_id(db, document_id)
        if not doc:
            return False
            
        file_path = doc.file_path
        db.delete(doc)
        db.commit()
        
        # Clean up physical file
        delete_file_from_disk(file_path)
        return True

    @classmethod
    def reprocess_document(cls, db: Session, document_id: int) -> Optional[Document]:
        """Reset document status to 'uploaded' for reprocessing."""
        doc = cls.get_document_by_id(db, document_id)
        if not doc:
            return None
            
        if not os.path.exists(doc.file_path):
            doc.status = DocumentStatus.failed
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Physical document file missing on disk for reprocessing."
            )
            
        doc.status = DocumentStatus.uploaded
        doc.chunk_count = 0
        db.commit()
        db.refresh(doc)
        return DocumentProcessingService.process(db, doc)
