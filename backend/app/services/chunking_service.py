from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    document_id: int | None
    chunk_index: int
    content: str
    metadata: dict


class ChunkingService:
    def __init__(self, chunk_size_tokens: int = 500, chunk_overlap_tokens: int = 50):
        if chunk_size_tokens <= 0:
            raise ValueError("chunk_size_tokens must be greater than zero")
        if chunk_overlap_tokens < 0 or chunk_overlap_tokens >= chunk_size_tokens:
            raise ValueError("chunk_overlap_tokens must be less than chunk_size_tokens")
        self.chunk_size_tokens = chunk_size_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens

    def chunk_text(
        self,
        text: str,
        metadata: dict | None = None,
        document_id: int | None = None,
    ) -> list[TextChunk]:
        words = text.split()
        if not words:
            return []

        chunks = []
        start = 0
        index = 0
        while start < len(words):
            end = min(start + self.chunk_size_tokens, len(words))
            chunks.append(
                TextChunk(
                    document_id,
                    index,
                    " ".join(words[start:end]),
                    metadata.copy() if metadata else {},
                )
            )
            index += 1
            if end == len(words):
                break
            start = end - self.chunk_overlap_tokens
        return chunks