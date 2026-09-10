from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.rag_service import INSUFFICIENT_CONTEXT_ANSWER, RAGService

client = TestClient(app)


class FakeEmbeddingService:
    def embed_text(self, text):
        return [0.1] * 384


class FakeGroqService:
    def __init__(self, answer="Grounded answer"):
        self.answer = answer
        self.calls = []

    def generate_answer(self, question, context):
        self.calls.append((question, context))
        return self.answer


def retrieved_chunk(content="The reset link expires after 24 hours."):
    return SimpleNamespace(
        chunk=SimpleNamespace(
            id=1,
            document_id=2,
            chunk_index=0,
            content=content,
            chunk_metadata={"page": 1},
        ),
        similarity_score=0.91,
    )


def test_rag_generates_answer_from_retrieved_context(monkeypatch):
    groq = FakeGroqService()
    service = RAGService(FakeEmbeddingService(), groq)
    monkeypatch.setattr(
        "app.services.rag_service.RetrievalService.search",
        lambda *args, **kwargs: [retrieved_chunk()],
    )

    result = service.answer(None, "How long does the reset link last?")

    assert result.answer == "Grounded answer"
    assert result.grounded is True
    assert len(result.sources) == 1
    assert "expires after 24 hours" in groq.calls[0][1][0]


def test_rag_refuses_to_generate_without_relevant_context(monkeypatch):
    groq = FakeGroqService()
    service = RAGService(FakeEmbeddingService(), groq)
    monkeypatch.setattr(
        "app.services.rag_service.RetrievalService.search",
        lambda *args, **kwargs: [],
    )

    result = service.answer(None, "What is the refund policy?")

    assert result.answer == INSUFFICIENT_CONTEXT_ANSWER
    assert result.grounded is False
    assert result.sources == []
    assert groq.calls == []


def test_rag_rejects_blank_questions():
    with pytest.raises(ValueError, match="question cannot be empty"):
        RAGService(FakeEmbeddingService(), FakeGroqService()).answer(None, "  ")


def test_rag_endpoint_is_public(monkeypatch):
    monkeypatch.setattr(
        "app.api.rag.RAGService.answer",
        lambda self, **kwargs: SimpleNamespace(answer="Public answer", grounded=False, sources=[]),
    )

    response = client.post("/api/rag/answer", json={"question": "What is the refund policy?"})

    assert response.status_code == 200
    assert response.json()["grounded"] is False
