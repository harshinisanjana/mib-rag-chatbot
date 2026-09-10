from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.rag import RAGRequest, RAGResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/answer", response_model=RAGResponse)
def answer_question(
    request: RAGRequest,
    db: Session = Depends(get_db),
):
    try:
        result = RAGService().answer(
            db=db,
            question=request.question,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer generation is temporarily unavailable",
        ) from exc

    return {
        "answer": result.answer,
        "grounded": result.grounded,
        "sources": [
            {
                "chunk_id": source.chunk.id,
                "document_id": source.chunk.document_id,
                "chunk_index": source.chunk.chunk_index,
                "metadata": source.chunk.chunk_metadata,
                "similarity_score": source.similarity_score,
            }
            for source in result.sources
        ],
    }