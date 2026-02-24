"""
Chat Session Manager for the LinkedIn Post Generator Agent.

Manages per-session state including chat history, extracted user context,
plan generation, and approval workflow.
"""
import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any


@dataclass
class ChatSession:
    """
    Holds per-session conversation state.
    
    Attributes:
        session_id: Unique session identifier
        chat_history: List of (role, content) tuples for LangChain memory
        user_context: Extracted persona/audience/intent information
        plan: Generated research & content plan text
        plan_approved: Whether the user approved the plan
        status: Current session status
        created_at: Session creation timestamp
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chat_history: List[Tuple[str, str]] = field(default_factory=list)
    user_context: Dict[str, Any] = field(default_factory=dict)
    plan: Optional[str] = None
    plan_approved: bool = False
    status: str = "chatting"  # chatting | plan_pending | plan_approved | executing | done
    created_at: float = field(default_factory=time.time)

    def add_user_message(self, message: str) -> None:
        """Add a user message to chat history."""
        self.chat_history.append(("human", message))

    def add_ai_message(self, message: str) -> None:
        """Add an AI message to chat history."""
        self.chat_history.append(("ai", message))

    def set_plan(self, plan: str) -> None:
        """Store the generated plan and update status."""
        self.plan = plan
        self.status = "plan_pending"

    def approve_plan(self) -> None:
        """Mark the plan as approved."""
        self.plan_approved = True
        self.status = "plan_approved"

    def get_field(self) -> str:
        """Get the extracted professional field from context."""
        return self.user_context.get("field", "General Professional")

    def get_additional_context(self) -> str:
        """Build additional context string from collected user info."""
        parts = []
        if self.user_context.get("persona"):
            parts.append(f"Author Persona: {self.user_context['persona']}")
        if self.user_context.get("audience"):
            parts.append(f"Target Audience: {self.user_context['audience']}")
        if self.user_context.get("tone"):
            parts.append(f"Tone: {self.user_context['tone']}")
        if self.user_context.get("goal"):
            parts.append(f"Goal: {self.user_context['goal']}")
        if self.user_context.get("topic"):
            parts.append(f"Topic: {self.user_context['topic']}")
        if self.user_context.get("extra"):
            parts.append(f"Additional Details: {self.user_context['extra']}")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session state for API responses."""
        return {
            "session_id": self.session_id,
            "status": self.status,
            "plan": self.plan,
            "plan_approved": self.plan_approved,
            "message_count": len(self.chat_history),
        }


class SessionManager:
    """
    In-memory store for active chat sessions.
    
    Note: Sessions are lost on server restart. For production,
    use a persistent store (Redis, database, etc.).
    """

    def __init__(self):
        self._sessions: Dict[str, ChatSession] = {}

    def create_session(self) -> ChatSession:
        """Create and store a new chat session."""
        session = ChatSession()
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Retrieve a session by ID."""
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if it existed."""
        return self._sessions.pop(session_id, None) is not None

    def cleanup_old_sessions(self, max_age_seconds: int = 3600) -> int:
        """Remove sessions older than max_age_seconds. Returns count removed."""
        now = time.time()
        to_remove = [
            sid for sid, s in self._sessions.items()
            if (now - s.created_at) > max_age_seconds
        ]
        for sid in to_remove:
            del self._sessions[sid]
        return len(to_remove)


# Global session manager instance
session_manager = SessionManager()
