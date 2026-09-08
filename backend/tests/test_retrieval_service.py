import pytest
from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.main import app
from app.services.retrieval_service import RetrievalService

client = TestClient(app)


def test_retrieval_rejects_invalid_query_embedding():
    with pytest.raises(ValueError, match="384 dimensions"):
        RetrievalService.search(None, [0.1])


def test_retrieval_rejects_invalid_search_options():
    with pytest.raises(ValueError, match="top_k"):
        RetrievalService.search(None, [0.1] * 384, top_k=0)

    with pytest.raises(ValueError, match="between 0 and 1"):
        RetrievalService.search(None, [0.1] * 384, similarity_threshold=2)


def test_retrieval_search_returns_top_k_processed_chunks():
    db = SessionLocal()
    try:
        results = RetrievalService.search(
            db,
            [1.0] * 384,
            top_k=2,
            similarity_threshold=0.0,
        )
        assert all(result.chunk.document.status.value == "processed" for result in results)
    finally:
        db.close()

    assert len(results) <= 2
    assert all(0 <= result.similarity_score <= 1 for result in results)


def test_retrieval_endpoint_requires_authentication():
    response = client.post("/api/retrieval/search", json={"query": "password reset"})

    assert response.status_code == 401