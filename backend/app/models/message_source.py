from sqlalchemy import Column, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.db.database import Base


class MessageSource(Base):
    __tablename__ = "message_sources"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=False, index=True)
    similarity_score = Column(Float, nullable=True)  # Vector similarity score

    # Relationships
    message = relationship("Message", back_populates="sources")
    chunk = relationship("DocumentChunk", back_populates="sources")
    document = relationship("Document")

    def __repr__(self):
        return f"<MessageSource(id={self.id}, message_id={self.message_id}, chunk_id={self.chunk_id})>"
