from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.services.embedding_service import EmbeddingService
from app.services.groq_service import GroqService
from app.services.retrieval_service import RetrievedChunk, RetrievalService


INSUFFICIENT_CONTEXT_ANSWER = (
    "I couldn't find enough information in the knowledge base to answer that. "
    "Please contact a support agent for help."
)


@dataclass(frozen=True)
class RAGAnswer:
    answer: str
    sources: list[RetrievedChunk]
    grounded: bool


class RAGService:
    def __init__(self, embedding_service=None, groq_service=None):
        self.embedding_service = embedding_service or EmbeddingService()
        self.groq_service = groq_service or GroqService()

    def answer(
        self,
        db: Session,
        question: str,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> RAGAnswer:
        question = question.strip()
        if not question:
            raise ValueError("question cannot be empty")

        query_embedding = self.embedding_service.embed_text(question)
        sources = RetrievalService.search(
            db,
            query_embedding,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )
        if not sources:
            return RAGAnswer(INSUFFICIENT_CONTEXT_ANSWER, [], False)

        context = [
            f"Source {index}: {source.chunk.content}"
            for index, source in enumerate(sources, start=1)
        ]
        answer = self.groq_service.generate_answer(question, context)
        return RAGAnswer(answer, sources, True)