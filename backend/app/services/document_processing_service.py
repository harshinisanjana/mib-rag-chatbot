import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.services.chunking_service import ChunkingService
from app.services.text_cleaning_service import clean_text
from app.services.text_extraction_service import TextExtractionError, TextExtractionService

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    @staticmethod
    def process(db: Session, document: Document) -> Document:
        document.status = DocumentStatus.processing
        db.commit()

        try:
            extracted_pages = TextExtractionService.extract_pages(document.file_path, document.file_type)
            chunks = []
            chunker = ChunkingService(settings.chunk_size_tokens, settings.chunk_overlap_tokens)
            for page in extracted_pages:
                page_text = clean_text(page.content)
                if page_text:
                    chunks.extend(
                        chunker.chunk_text(
                            page_text,
                            {"page": page.page_number} if page.page_number else {},
                            document_id=document.id,
                        )
                    )

            if not chunks:
                raise TextExtractionError("Document contains no extractable text")

            db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete(
                synchronize_session=False
            )
            db.add_all([
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk.content,
                    chunk_metadata=chunk.metadata,
                )
                for index, chunk in enumerate(chunks)
            ])
            document.chunk_count = len(chunks)
            document.status = DocumentStatus.processed
            db.commit()
        except Exception as exc:
            db.rollback()
            document.status = DocumentStatus.failed
            document.chunk_count = 0
            db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete(
                synchronize_session=False
            )
            db.commit()
            logger.exception("Document processing failed for document %s", document.id)
        db.refresh(document)
        return document