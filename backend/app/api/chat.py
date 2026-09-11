from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.rag import RAGSourceResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ConversationResponse(BaseModel):
    session_id: str
    conversation_id: int
    status: str


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    answer: str
    grounded: bool
    sources: list[RAGSourceResponse]
    session_id: str
    conversation_id: int


class EscalateRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class EscalateResponse(BaseModel):
    escalated: bool
    session_id: str
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(db: Session = Depends(get_db)):
    """Create a new conversation session. Returns a session_id to use for subsequent messages."""
    conv = ChatService.create_conversation(db)
    return {
        "session_id": str(conv.session_id),
        "conversation_id": conv.id,
        "status": conv.status.value,
    }


@router.post("/conversations/{session_id}/messages", response_model=ChatMessageResponse)
def send_message(
    session_id: str,
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
):
    """Send a customer message and receive an AI-generated, grounded response."""
    try:
        result = ChatService().send_message(
            db=db,
            session_id=session_id,
            customer_text=request.message,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The support service is temporarily unavailable. Please try again.",
        ) from exc

    return {
        "answer": result.answer,
        "grounded": result.grounded,
        "sources": result.sources,
        "session_id": result.session_id,
        "conversation_id": result.conversation_id,
    }


@router.post("/conversations/{session_id}/escalate", response_model=EscalateResponse)
def escalate_conversation(
    session_id: str,
    request: EscalateRequest,
    db: Session = Depends(get_db),
):
    """Escalate a conversation to the human support team."""
    try:
        ChatService.escalate(db=db, session_id=session_id, reason=request.reason)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not escalate the conversation right now.",
        ) from exc

    return {
        "escalated": True,
        "session_id": session_id,
        "message": (
            "Your conversation has been routed to our support team. "
            "Please contact us directly at support@mibtechsolutions.com so a representative can assist you."
        ),
    }
