import logging

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import ChatRequest, ChatResponse, SourceInfo, HealthResponse, IngestResponse
from app.rag.pipeline import RAGPipeline
from app.services.llm_service import LLMService
from app.services.vector_store_service import VectorStoreService
from app.ingestion.ingest import ingest_documents

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Send a message and receive a grounded RAG response."""
    try:
        pipeline = RAGPipeline.get_instance()
        result = pipeline.query(
            question=request.message,
            session_id=request.session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("RAG pipeline error")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI service is temporarily unavailable. Please ensure Ollama is running.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error in chat endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again.",
        ) from exc

    return ChatResponse(
        answer=result.answer,
        grounded=result.grounded,
        sources=[SourceInfo(**s) for s in result.sources],
        session_id=result.session_id,
    )


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health check including Ollama and ChromaDB status."""
    ollama_ok = LLMService.check_health()
    doc_count = VectorStoreService.count()

    return HealthResponse(
        status="healthy" if ollama_ok else "degraded",
        service="MIB RAG Chatbot",
        version="1.0.0",
        ollama_status="connected" if ollama_ok else "disconnected",
        documents_indexed=doc_count,
    )


@router.post("/ingest", response_model=IngestResponse)
def run_ingestion():
    """Process all documents in the data/documents directory and index them."""
    try:
        result = ingest_documents(clear_existing=True)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Ingestion failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document ingestion failed: {exc}",
        ) from exc

    return IngestResponse(**result)
