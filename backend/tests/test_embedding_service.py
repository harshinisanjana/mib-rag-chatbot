import pytest

from app.services.embedding_service import EmbeddingService


class FakeModel:
    def __init__(self, dimension=384):
        self.dimension = dimension
        self.calls = []

    def encode(self, texts, **kwargs):
        self.calls.append((texts, kwargs))
        return [[float(index)] * self.dimension for index, _ in enumerate(texts)]


def test_embed_texts_uses_provider_and_configured_batch_size():
    service = EmbeddingService(batch_size=7)
    model = FakeModel()
    service._model = model

    embeddings = service.embed_texts(["first", "second"])

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert model.calls[0][1]["batch_size"] == 7
    assert model.calls[0][1]["normalize_embeddings"] is True


def test_empty_input_returns_no_embeddings():
    service = EmbeddingService()

    assert service.embed_texts([]) == []


def test_empty_text_is_rejected():
    service = EmbeddingService()

    with pytest.raises(ValueError, match="empty text"):
        service.embed_texts([" "])


def test_provider_dimension_must_match_configuration():
    service = EmbeddingService()
    service._model = FakeModel(dimension=3)

    with pytest.raises(ValueError, match="dimension"):
        service.embed_text("content")