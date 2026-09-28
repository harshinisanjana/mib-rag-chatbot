import logging
from pathlib import Path

import chromadb

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Manages ChromaDB collection for document embeddings."""

    _client = None
    _collection = None

    @classmethod
    def get_client(cls) -> chromadb.ClientAPI:
        if cls._client is None:
            persist_path = settings.get_chroma_persist_path()
            persist_path.mkdir(parents=True, exist_ok=True)
            cls._client = chromadb.PersistentClient(path=str(persist_path))
            logger.info("ChromaDB client initialized at %s", persist_path)
        return cls._client

    @classmethod
    def get_collection(cls) -> chromadb.Collection:
        if cls._collection is None:
            client = cls.get_client()
            cls._collection = client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                "ChromaDB collection '%s' ready (%d documents)",
                settings.chroma_collection_name,
                cls._collection.count(),
            )
        return cls._collection

    @classmethod
    def add_chunks(
        cls,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        collection = cls.get_collection()
        # ChromaDB has a batch limit; process in batches of 500
        batch_size = 500
        for i in range(0, len(ids), batch_size):
            collection.add(
                ids=ids[i : i + batch_size],
                documents=documents[i : i + batch_size],
                embeddings=embeddings[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )

    @classmethod
    def query(
        cls,
        query_embedding: list[float],
        top_k: int | None = None,
        where: dict | None = None,
    ) -> dict:
        collection = cls.get_collection()
        n_results = top_k or settings.top_k

        # Don't request more results than exist in the collection
        doc_count = collection.count()
        if doc_count == 0:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        n_results = min(n_results, doc_count)

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        return collection.query(**kwargs)

    @classmethod
    def count(cls) -> int:
        return cls.get_collection().count()

    @classmethod
    def clear_collection(cls) -> None:
        """Delete and recreate the collection."""
        client = cls.get_client()
        try:
            client.delete_collection(settings.chroma_collection_name)
        except Exception:
            pass
        cls._collection = None
        cls.get_collection()

    @classmethod
    def reset(cls) -> None:
        """Reset cached client and collection (for testing)."""
        cls._client = None
        cls._collection = None
