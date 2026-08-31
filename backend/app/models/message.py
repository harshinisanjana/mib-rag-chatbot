from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class SenderType(str, enum.Enum):
    customer = "customer"
    ai = "ai"
    agent = "agent"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    sender_type = Column(Enum(SenderType), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sources = relationship("MessageSource", back_populates="message", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, sender_type={self.sender_type})>"
