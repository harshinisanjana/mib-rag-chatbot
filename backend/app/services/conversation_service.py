import uuid
import logging
from dataclasses import dataclass, field
from collections import OrderedDict

logger = logging.getLogger(__name__)

MAX_HISTORY_TURNS = 10  # Keep last N user-assistant pairs per session
MAX_SESSIONS = 100      # Evict oldest sessions to limit memory usage


@dataclass
class ConversationTurn:
    role: str       # "user" or "assistant"
    content: str


@dataclass
class Session:
    session_id: str
    history: list[ConversationTurn] = field(default_factory=list)

    def add_user_message(self, content: str) -> None:
        self.history.append(ConversationTurn(role="user", content=content))

    def add_assistant_message(self, content: str) -> None:
        self.history.append(ConversationTurn(role="assistant", content=content))
        # Trim history to keep memory bounded
        # Each "turn" is a user+assistant pair = 2 entries
        max_entries = MAX_HISTORY_TURNS * 2
        if len(self.history) > max_entries:
            self.history = self.history[-max_entries:]

    def get_context_summary(self) -> str:
        """Build a conversation summary for follow-up question resolution."""
        if len(self.history) <= 1:
            return ""
        # Include recent history so the LLM can resolve pronouns
        lines = []
        for turn in self.history[:-1]:  # Exclude the current (latest) user message
            prefix = "User" if turn.role == "user" else "Assistant"
            lines.append(f"{prefix}: {turn.content}")
        return "\n".join(lines)


class ConversationService:
    """In-memory conversation session manager."""

    def __init__(self):
        self._sessions: OrderedDict[str, Session] = OrderedDict()

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        # Evict oldest session if at capacity
        if len(self._sessions) >= MAX_SESSIONS:
            self._sessions.popitem(last=False)
        self._sessions[session_id] = Session(session_id=session_id)
        return session_id

    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def get_or_create_session(self, session_id: str | None) -> Session:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        new_id = session_id or str(uuid.uuid4())
        if len(self._sessions) >= MAX_SESSIONS:
            self._sessions.popitem(last=False)
        session = Session(session_id=new_id)
        self._sessions[new_id] = session
        return session


# Global singleton
conversation_service = ConversationService()
