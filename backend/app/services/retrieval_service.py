from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: DocumentChunk
    similarity_score: float


class RetrievalService:
    @staticmethod
    def search(
        db: Session,
        query_embedding: list[float],
        top_k: int | None = None,
        similarity_threshold: float | None = None,
        document_id: int | None = None,
    ) -> list[RetrievedChunk]:
        limit = top_k if top_k is not None else settings.vector_search_top_k
        threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.similarity_threshold
        )
        if not query_embedding:
            raise ValueError("query_embedding cannot be empty")
        if len(query_embedding) != settings.embedding_dimension:
            raise ValueError(
                f"Query embedding must have {settings.embedding_dimension} dimensions"
            )
        if limit <= 0:
            raise ValueError("top_k must be greater than zero")
        if not 0 <= threshold <= 1:
            raise ValueError("similarity_threshold must be between 0 and 1")

        distance = DocumentChunk.embedding.cosine_distance(query_embedding)
        query = (
            db.query(DocumentChunk, distance.label("distance"))
            .join(Document, Document.id == DocumentChunk.document_id)
            .filter(
                Document.status == DocumentStatus.processed,
                DocumentChunk.embedding.isnot(None),
                distance <= 1 - threshold,
            )
        )
        if document_id is not None:
            query = query.filter(DocumentChunk.document_id == document_id)
        query = query.order_by(distance.asc()).limit(limit)

        return [
            RetrievedChunk(chunk=chunk, similarity_score=max(0.0, 1.0 - float(distance_value)))
            for chunk, distance_value in query.all()
        ]