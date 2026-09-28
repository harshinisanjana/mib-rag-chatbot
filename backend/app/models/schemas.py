from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, description="Session ID for conversation continuity")


class SourceInfo(BaseModel):
    document_name: str
    page: int | None = None
    chunk_index: int
    similarity_score: float
    content_preview: str = Field(description="First ~200 chars of the chunk")


class ChatResponse(BaseModel):
    answer: str
    grounded: bool
    sources: list[SourceInfo]
    session_id: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    ollama_status: str
    documents_indexed: int


class IngestResponse(BaseModel):
    documents_processed: int
    total_chunks: int
    details: list[dict]
