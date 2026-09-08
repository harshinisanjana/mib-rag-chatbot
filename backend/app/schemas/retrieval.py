from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=50)
    similarity_threshold: float | None = Field(default=None, ge=0, le=1)
    document_id: int | None = Field(default=None, ge=1)


class RetrievedChunkResponse(BaseModel):
    chunk_id: int
    document_id: int
    chunk_index: int
    content: str
    metadata: dict | None
    similarity_score: float


class RetrievalResponse(BaseModel):
    items: list[RetrievedChunkResponse]