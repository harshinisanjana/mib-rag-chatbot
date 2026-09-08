from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_agent_or_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/api/retrieval", tags=["retrieval"])


@router.post("/search", response_model=RetrievalResponse)
def search_chunks(
    request: RetrievalRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_agent_or_admin),
):
    try:
        query_embedding = EmbeddingService().embed_text(request.query)
        results = RetrievalService.search(
            db=db,
            query_embedding=query_embedding,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            document_id=request.document_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retrieval is temporarily unavailable",
        ) from exc

    return {
        "items": [
            {
                "chunk_id": result.chunk.id,
                "document_id": result.chunk.document_id,
                "chunk_index": result.chunk.chunk_index,
                "content": result.chunk.content,
                "metadata": result.chunk.chunk_metadata,
                "similarity_score": result.similarity_score,
            }
            for result in results
        ]
    }