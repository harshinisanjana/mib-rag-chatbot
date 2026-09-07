import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def fake_embedding_service(monkeypatch):
	from app.services import document_processing_service

	class FakeEmbeddingService:
		def embed_texts(self, texts):
			return [[float(index + 1)] * 384 for index, _ in enumerate(texts)]

	monkeypatch.setattr(document_processing_service, "EmbeddingService", FakeEmbeddingService)
