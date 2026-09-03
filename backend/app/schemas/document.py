from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.models.document import DocumentStatus


class DocumentBase(BaseModel):
    original_filename: str
    file_type: str


class DocumentResponse(DocumentBase):
    id: int
    filename: str
    file_path: str
    status: DocumentStatus
    chunk_count: int
    uploaded_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int


class DocumentStatusUpdate(BaseModel):
    status: DocumentStatus
    chunk_count: Optional[int] = None
