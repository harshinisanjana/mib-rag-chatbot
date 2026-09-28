from collections.abc import Sequence

from app.core.config import settings


class EmbeddingService:
    """Generate normalized embeddings using sentence-transformers."""

    _instance = None
    _model = None

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        """Singleton to avoid reloading the model on every call."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.embedding_model

    def _get_model(self):
        if EmbeddingService._model is None:
            from sentence_transformers import SentenceTransformer
            EmbeddingService._model = SentenceTransformer(self.model_name)
        return EmbeddingService._model

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        model = self._get_model()
        vectors = model.encode(
            list(texts),
            batch_size=32,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [v.tolist() if hasattr(v, "tolist") else list(v) for v in vectors]

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]