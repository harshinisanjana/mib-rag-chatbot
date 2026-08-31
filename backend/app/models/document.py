from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    processed = "processed"
    failed = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, unique=True)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx
    file_path = Column(String(500), nullable=False)
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.uploaded)
    chunk_count = Column(Integer, default=0)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    uploader = relationship("User")

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
