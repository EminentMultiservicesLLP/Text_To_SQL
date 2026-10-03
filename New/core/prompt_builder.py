"""
Prompt Builder
--------------
Assembles the final prompt sent to the LLM by combining:
  - System instructions (prompts/system.txt)
  - Live schema text
  - Few-shot examples (prompts/few_shots.json)
  - Business context: region→branchCode mappings, term aliases (prompts/business_context.json)
  - Conversation history

Also exposes resolve_question() which rewrites the user's question by
substituting known region/alias terms with their actual DB values before
the question reaches the LLM — making region queries reliable.
"""
import json
import logging
import re
from pathlib import Path
from schema.registry import schema_to_prompt, load_schema
from config.settings import SQL_ROW_LIMIT, APP_DOMAIN

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_system_template: str | None = None
_few_shots: list[dict] | None = None
_biz_context: dict | None = None


def _get_system_template() -> str:
    global _system_template
    if _system_template is None:
        _system_template = (_PROMPTS_DIR / "system.txt").read_text(encoding="utf-8")
    return _system_template


def _get_few_shots() -> list[dict]:
    global _few_shots
    if _few_shots is None:
        with open(_PROMPTS_DIR / "few_shots.json", encoding="utf-8") as f:
            _few_shots = json.load(f)
    return _few_shots


def _get_biz_context() -> dict:
    global _biz_context
    if _biz_context is None:
        path = _PROMPTS_DIR / "business_context.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                _biz_context = json.load(f)
        else:
            _biz_context = {}
    return _biz_context


def resolve_question(question: str) -> tuple[str, list[str]]:
    """
    Rewrite the question by replacing known region/city names with their
    actual branchCode IN (...) values so the LLM generates correct SQL.

    Returns (resolved_question, warnings) where warnings is a list of
    terms that were mentioned but have no mapping defined.
    """
    ctx = _get_biz_context()
    regions: dict = ctx.get("branch_regions", {})
    warnings: list[str] = []

    resolved = question
    for term, codes in regions.items():
        # Case-insensitive whole-word match
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        if pattern.search(resolved):
            codes_str = ", ".join(f"'{c}'" for c in codes)
            resolved = pattern.sub(
                f"branches with branchCode IN ({codes_str})", resolved
            )
            logger.info("Resolved region '%s' → %s", term, codes_str)

    # Warn about unresolved geographic terms the LLM cannot handle
    geo_pattern = re.compile(
        r"\b(region|city|area|zone|location|district|state)\b", re.IGNORECASE
    )
    if geo_pattern.search(resolved) and resolved == question:
        warnings.append(
            "I couldn't find a branch mapping for the location you mentioned. "
            "Results may be inaccurate. Ask your admin to add it to business_context.json."
        )

    return resolved, warnings


def _format_few_shots(shots: list[dict]) -> str:
    lines = []
    for s in shots:
        lines.append(f"Q: {s['question']}")
        lines.append(f"SQL: {s['sql']}")
        lines.append("")
    return "\n".join(lines)


def _format_biz_context(ctx: dict) -> str:
    """Format business context as a reference block for the LLM."""
    if not ctx:
        return ""

    lines = ["## Business term reference"]

    regions = ctx.get("branch_regions", {})
    if regions:
        lines.append("\nRegion → branchCode mappings:")
        for region, codes in regions.items():
            lines.append(f"  {region}: {', '.join(codes)}")

    aliases = ctx.get("term_aliases", {})
    if aliases:
        lines.append("\nBusiness term → column mappings:")
        for term, col in aliases.items():
            lines.append(f"  '{term}' means {col}")

    return "\n".join(lines)


def _format_history(messages: list[dict]) -> str:
    relevant = [m for m in messages if m["role"] != "system"]
    if not relevant:
        return "No prior conversation."
    return "\n".join(f"{m['role'].upper()}: {m['content']}" for m in relevant[-6:])


def build_system_message(history: list[dict]) -> str:
    """Build the full system message with all context injected."""
    schema = load_schema()
    schema_text = schema_to_prompt(schema)
    few_shots_text = _format_few_shots(_get_few_shots())
    biz_context_text = _format_biz_context(_get_biz_context())
    history_text = _format_history(history)

    return (
        _get_system_template()
        .replace("{app_domain}", APP_DOMAIN)
        .replace("{schema}", schema_text)
        .replace("{few_shots}", few_shots_text)
        .replace("{business_context}", biz_context_text)
        .replace("{history}", history_text)
        .replace("{row_limit}", str(SQL_ROW_LIMIT))
    )
