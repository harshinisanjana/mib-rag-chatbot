from sqlalchemy import Column, Integer, String, DateTime, Enum, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum
import uuid


class ConversationStatus(str, enum.Enum):
    ai_active = "ai_active"
    escalated = "escalated"
    human_active = "human_active"
    resolved = "resolved"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    status = Column(Enum(ConversationStatus), nullable=False, default=ConversationStatus.ai_active)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    escalation = relationship("Escalation", back_populates="conversation", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation(id={self.id}, session_id={self.session_id}, status={self.status})>"
