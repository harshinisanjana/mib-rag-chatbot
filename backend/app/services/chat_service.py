import uuid
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationStatus
from app.models.document import Document
from app.models.escalation import Escalation, EscalationStatus
from app.models.message import Message, SenderType
from app.models.message_source import MessageSource
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


@dataclass
class ChatMessageResult:
    answer: str
    grounded: bool
    sources: list[dict]
    conversation_id: int
    session_id: str


class ChatService:
    def __init__(self, rag_service: RAGService | None = None):
        self._rag = rag_service or RAGService()

    # ------------------------------------------------------------------
    # Conversation management
    # ------------------------------------------------------------------

    @staticmethod
    def create_conversation(db: Session) -> Conversation:
        """Create a new conversation session and persist it."""
        conv = Conversation(
            session_id=uuid.uuid4(),
            status=ConversationStatus.ai_active,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def get_conversation_by_session(db: Session, session_id: str) -> Conversation | None:
        """Fetch a conversation by its UUID session_id."""
        try:
            sid = uuid.UUID(session_id)
        except ValueError:
            return None
        return db.query(Conversation).filter(Conversation.session_id == sid).first()

    # ------------------------------------------------------------------
    # Sending a customer message and generating an AI response
    # ------------------------------------------------------------------

    def send_message(
        self,
        db: Session,
        session_id: str,
        customer_text: str,
    ) -> ChatMessageResult:
        conv = self.get_conversation_by_session(db, session_id)
        if conv is None:
            raise ValueError(f"Conversation '{session_id}' not found")
        if conv.status == ConversationStatus.escalated:
            raise ValueError("This conversation has been escalated to a human agent")

        customer_text = customer_text.strip()
        if not customer_text:
            raise ValueError("Message cannot be empty")

        # Run RAG pipeline BEFORE opening any write transactions.
        # This avoids holding a flushed-but-uncommitted row while
        # the embedding model and Groq API do their work.
        try:
            rag_result = self._rag.answer(db, customer_text)
        except Exception as exc:
            logger.exception("RAG pipeline failed for session %s", session_id)
            raise RuntimeError("RAG pipeline failed") from exc

        # Resolve document names for source chips
        doc_ids = {s.chunk.document_id for s in rag_result.sources}
        doc_map: dict[int, str] = {}
        if doc_ids:
            docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
            doc_map = {d.id: d.original_filename for d in docs}

        # Persist customer message, AI response, and sources atomically
        try:
            customer_msg = Message(
                conversation_id=conv.id,
                sender_type=SenderType.customer,
                content=customer_text,
            )
            db.add(customer_msg)
            db.flush()

            ai_msg = Message(
                conversation_id=conv.id,
                sender_type=SenderType.ai,
                content=rag_result.answer,
            )
            db.add(ai_msg)
            db.flush()

            for source in rag_result.sources:
                db.add(MessageSource(
                    message_id=ai_msg.id,
                    document_id=source.chunk.document_id,
                    chunk_id=source.chunk.id,
                    similarity_score=source.similarity_score,
                ))

            db.commit()
        except Exception as exc:
            db.rollback()
            # Log but do NOT re-raise: the customer still gets their answer
            logger.exception(
                "Failed to persist conversation messages for session %s: %s", session_id, exc
            )

        sources_out = [
            {
                "chunk_id": s.chunk.id,
                "document_id": s.chunk.document_id,
                "document_name": doc_map.get(s.chunk.document_id, f"Document {s.chunk.document_id}"),
                "chunk_index": s.chunk.chunk_index,
                "metadata": s.chunk.chunk_metadata,
                "similarity_score": s.similarity_score,
            }
            for s in rag_result.sources
        ]

        return ChatMessageResult(
            answer=rag_result.answer,
            grounded=rag_result.grounded,
            sources=sources_out,
            conversation_id=conv.id,
            session_id=str(conv.session_id),
        )

    # ------------------------------------------------------------------
    # Escalation
    # ------------------------------------------------------------------

    @staticmethod
    def escalate(db: Session, session_id: str, reason: str | None = None) -> Escalation:
        """Escalate a conversation to human support."""
        conv = ChatService.get_conversation_by_session(db, session_id)
        if conv is None:
            raise ValueError(f"Conversation '{session_id}' not found")

        # Idempotent: if already escalated, return existing record
        existing = db.query(Escalation).filter(Escalation.conversation_id == conv.id).first()
        if existing:
            return existing

        conv.status = ConversationStatus.escalated
        escalation = Escalation(
            conversation_id=conv.id,
            reason=reason or "Customer requested human support",
            status=EscalationStatus.open,
        )
        db.add(escalation)
        db.commit()
        db.refresh(escalation)
        return escalation
