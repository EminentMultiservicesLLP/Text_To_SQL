"""
SQL Generator
-------------
Sends the assembled prompt + conversation history to the local Ollama LLM
and extracts a clean SQL string from the response.
All inference happens locally — no data leaves the environment.
"""
import re
import logging
import ollama
from config.settings import LLM_MODEL, EMBED_MODEL
from core.prompt_builder import build_system_message
from core.conversation import Conversation

logger = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"```(?:sql)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def get_embedding(text: str) -> list[float]:
    """Generate a text embedding using the local Ollama embed model."""
    response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return response["embedding"]


def generate_sql(question: str, conversation: Conversation) -> str:
    """
    Generate a T-SQL query for the given question using conversation context.
    Returns the raw SQL string (no markdown, no explanation).
    """
    history = conversation.get_messages()
    system_msg = build_system_message(history)

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": question},
    ]

    logger.info("Calling LLM (%s) for SQL generation", LLM_MODEL)
    response = ollama.chat(model=LLM_MODEL, messages=messages)
    raw = response["message"]["content"].strip()

    return _clean_sql_response(raw)


def _clean_sql_response(raw: str) -> str:
    """Strip markdown fences and extract just the SQL statement."""
    match = _FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()
    # If no fences, return as-is but strip any leading/trailing prose
    lines = [l for l in raw.splitlines() if l.strip()]
    # Drop lines that look like prose (don't start with SQL keywords)
    sql_keywords = {"SELECT", "WITH", "--"}
    for i, line in enumerate(lines):
        if any(line.upper().startswith(kw) for kw in sql_keywords):
            return "\n".join(lines[i:]).strip()
    return raw.strip()
