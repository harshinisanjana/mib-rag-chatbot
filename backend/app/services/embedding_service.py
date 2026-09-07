from collections.abc import Sequence

from app.core.config import settings


class EmbeddingService:
    """Generate normalized embeddings without coupling callers to the provider."""

    def __init__(self, model_name: str | None = None, batch_size: int | None = None):
        self.model_name = model_name or settings.embedding_model
        self.batch_size = batch_size or settings.embedding_batch_size
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is required for embedding generation"
                ) from exc
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if any(not text.strip() for text in texts):
            raise ValueError("Cannot generate an embedding for empty text")

        vectors = self._get_model().encode(
            list(texts),
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        embeddings = [vector.tolist() if hasattr(vector, "tolist") else list(vector) for vector in vectors]
        if any(len(vector) != settings.embedding_dimension for vector in embeddings):
            raise ValueError(
                f"Embedding dimension does not match configured dimension {settings.embedding_dimension}"
            )
        return embeddings

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]