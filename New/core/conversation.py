"""
Conversation Manager
--------------------
Maintains per-session message history so the LLM has context across turns.
Each session is a list of {role, content} dicts compatible with Ollama's chat API.
"""
from dataclasses import dataclass, field
from typing import Literal

Role = Literal["system", "user", "assistant"]

MAX_HISTORY_TURNS = 10  # keep last N user+assistant pairs to avoid token overflow


@dataclass
class Conversation:
    session_id: str
    _messages: list[dict] = field(default_factory=list)

    def add(self, role: Role, content: str) -> None:
        self._messages.append({"role": role, "content": content})
        self._trim()

    def get_messages(self) -> list[dict]:
        return list(self._messages)

    def _trim(self) -> None:
        """Keep system message + last MAX_HISTORY_TURNS user/assistant pairs."""
        system = [m for m in self._messages if m["role"] == "system"]
        non_system = [m for m in self._messages if m["role"] != "system"]
        max_non_system = MAX_HISTORY_TURNS * 2
        self._messages = system + non_system[-max_non_system:]

    def clear(self) -> None:
        self._messages = [m for m in self._messages if m["role"] == "system"]


# Simple in-memory session registry (replace with Redis for multi-user production)
_sessions: dict[str, Conversation] = {}


def get_session(session_id: str) -> Conversation:
    if session_id not in _sessions:
        _sessions[session_id] = Conversation(session_id=session_id)
    return _sessions[session_id]
