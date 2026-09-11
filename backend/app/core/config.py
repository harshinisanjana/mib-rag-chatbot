from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # App
    app_name: str = "AI Customer Support Knowledge Base"
    env: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/mib_rag_chatbot"

    # JWT
    secret_key: str = "your_secret_key_here_change_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Groq API
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    groq_temperature: float = 0.0
    groq_max_tokens: int = 800

    # Document Processing
    max_file_size_mb: int = 50
    chunk_size_tokens: int = 500
    chunk_overlap_tokens: int = 50
    vector_search_top_k: int = 5
    similarity_threshold: float = 0.1

    # Embedding
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    embedding_batch_size: int = 32

    # CORS - Accept comma-separated string and parse it
    cors_origins: str = Field(
        default="http://localhost:4200,http://localhost:3000",
        description="Comma-separated list of CORS origins"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow"
    )

    def get_cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins"""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins

settings = Settings()
