from types import SimpleNamespace

import pytest

from app.db.database import SessionLocal
from app.models.conversation import ConversationStatus
from app.models.escalation import EscalationStatus
from app.models.message import SenderType
from app.services.chat_service import ChatService
from app.services.rag_service import RAGAnswer


class FakeRAGService:
    def answer(self, db, question):
        return RAGAnswer(
            answer=f"Grounded response for: {question}",
            sources=[],
            grounded=True,
        )


@pytest.fixture
def database_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def test_chat_persists_customer_and_ai_messages(database_session):
    conversation = ChatService.create_conversation(database_session)
    service = ChatService(FakeRAGService())

    result = service.send_message(
        database_session,
        str(conversation.session_id),
        "What services do you provide?",
    )

    database_session.expire_all()
    messages = conversation.messages
    assert result.grounded is True
    assert [message.sender_type for message in messages] == [SenderType.customer, SenderType.ai]
    assert messages[0].content == "What services do you provide?"
    assert messages[1].content.startswith("Grounded response")

    database_session.delete(conversation)
    database_session.commit()


def test_escalation_is_idempotent_and_blocks_follow_up_messages(database_session):
    conversation = ChatService.create_conversation(database_session)
    session_id = str(conversation.session_id)

    first = ChatService.escalate(database_session, session_id, "Customer requested an agent")
    second = ChatService.escalate(database_session, session_id, "A different reason")

    assert first.id == second.id
    assert first.status == EscalationStatus.open
    assert conversation.status == ConversationStatus.escalated

    with pytest.raises(ValueError, match="escalated to a human agent"):
        ChatService(FakeRAGService()).send_message(database_session, session_id, "Follow up")

    database_session.delete(conversation)
    database_session.commit()