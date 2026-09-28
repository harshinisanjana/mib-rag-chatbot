from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    # Application
    app_name: str = "MIB RAG Chatbot"
    env: str = "development"
    debug: bool = True

    # Ollama LLM
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.2:3b"
    llm_temperature: float = 0.1
    llm_request_timeout: int = 120
    llm_context_window: int = 2048

    # Embedding
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ChromaDB
    chroma_persist_dir: str = "data/chroma"
    chroma_collection_name: str = "mib_documents"

    # Document Processing
    documents_dir: str = "data/documents"
    chunk_size: int = 500
    chunk_overlap: int = 50

    # Retrieval (Tuned for lightweight 2-5 MIB document knowledge base)
    top_k: int = Field(default=3, description="Number of top relevant chunks to retrieve (3-5)")
    similarity_threshold: float = Field(default=0.3, description="Minimum cosine similarity cutoff")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated list of CORS origins",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow",
    )

    def get_cors_origins(self) -> list[str]:
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins

    def get_chroma_persist_path(self) -> Path:
        """Resolve ChromaDB path relative to the backend directory."""
        path = Path(self.chroma_persist_dir)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent.parent / path
        return path

    def get_documents_path(self) -> Path:
        """Resolve documents directory relative to the backend directory."""
        path = Path(self.documents_dir)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent.parent / path
        return path


settings = Settings()
