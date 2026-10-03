import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Database ──────────────────────────────────────────────────────────────────
DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_NAME = os.getenv("DB_NAME", "")
DB_TRUSTED = os.getenv("DB_TRUSTED_CONNECTION", "yes").lower() == "yes"
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def get_connection_string() -> str:
    base = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};"
    if DB_TRUSTED:
        return base + "Trusted_Connection=yes;"
    return base + f"UID={DB_USER};PWD={DB_PASSWORD};"

# ── Schema ────────────────────────────────────────────────────────────────────
# Comma-separated list of tables the chatbot is allowed to query
ALLOWED_TABLES: list[str] = [
    t.strip()
    for t in os.getenv("ALLOWED_TABLES", "").split(",")
    if t.strip()
]

_fallback_env = os.getenv("SCHEMA_FALLBACK_PATH", "")
SCHEMA_FALLBACK_PATH: Path | None = Path(_fallback_env) if _fallback_env else None

# Short domain description injected into the system prompt
APP_DOMAIN = os.getenv("APP_DOMAIN", "business database")

# ── Ollama ────────────────────────────────────────────────────────────────────
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

# ── Safety ────────────────────────────────────────────────────────────────────
SQL_ROW_LIMIT = int(os.getenv("SQL_ROW_LIMIT", "500"))
SQL_TIMEOUT = int(os.getenv("SQL_TIMEOUT_SECONDS", "30"))

# ── Vector store ──────────────────────────────────────────────────────────────
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_storage")
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.92"))
