from pydantic import BaseModel, Field


class RAGRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=50)
    similarity_threshold: float | None = Field(default=None, ge=0, le=1)


class RAGSourceResponse(BaseModel):
    chunk_id: int
    document_id: int
    document_name: str
    chunk_index: int
    metadata: dict | None
    similarity_score: float


class RAGResponse(BaseModel):
    answer: str
    grounded: bool
    sources: list[RAGSourceResponse]