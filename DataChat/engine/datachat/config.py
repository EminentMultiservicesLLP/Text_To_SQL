import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ENGINE_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ENGINE_ROOT / ".env")


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _path(name: str, default: str) -> Path:
    p = Path(os.getenv(name, default))
    return p if p.is_absolute() else (ENGINE_ROOT / p).resolve()


@dataclass(frozen=True)
class Settings:
    packs_dir: Path
    data_dir: Path
    api_key: str
    row_limit: int
    query_timeout_s: int
    strict_unknown_words: bool
    promote_min_users: int
    llm_enabled: bool
    ollama_url: str
    llm_model: str
    llm_timeout_s: int
    llm_num_thread: int
    llm_mode: str = "primary"  # primary: the model reads every question; fallback: only what the rules can't


def load_settings() -> Settings:
    return Settings(
        packs_dir=_path("DATACHAT_PACKS_DIR", "./packs"),
        data_dir=_path("DATACHAT_DATA_DIR", "./data"),
        api_key=os.getenv("DATACHAT_API_KEY", ""),
        row_limit=int(os.getenv("DATACHAT_ROW_LIMIT", "500")),
        query_timeout_s=int(os.getenv("DATACHAT_QUERY_TIMEOUT_SECONDS", "30")),
        strict_unknown_words=_bool("DATACHAT_STRICT_UNKNOWN_WORDS", True),
        promote_min_users=int(os.getenv("DATACHAT_PROMOTE_MIN_USERS", "3")),
        llm_enabled=_bool("DATACHAT_LLM_ENABLED", False),
        ollama_url=os.getenv("DATACHAT_OLLAMA_URL", "http://127.0.0.1:11434"),
        llm_model=os.getenv("DATACHAT_LLM_MODEL", "qwen3:4b"),
        llm_timeout_s=int(os.getenv("DATACHAT_LLM_TIMEOUT_SECONDS", "90")),
        llm_num_thread=int(os.getenv("DATACHAT_LLM_NUM_THREAD", "0")),
        llm_mode=os.getenv("DATACHAT_LLM_MODE", "primary").strip().lower(),
    )
