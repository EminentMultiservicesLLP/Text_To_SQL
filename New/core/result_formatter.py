"""
Result Formatter
----------------
Takes raw SQL results and the original question, returns a FormatResult
containing the natural language answer and a chart recommendation.
"""
import logging
from dataclasses import dataclass
import ollama
from config.settings import LLM_MODEL
from core.chart_advisor import recommend_chart, ChartConfig

logger = logging.getLogger(__name__)

_MAX_ROWS_IN_PROMPT = 50


@dataclass
class FormatResult:
    answer: str
    chart: ChartConfig


def format_result(question: str, sql: str, result: dict) -> FormatResult:
    """Return natural language answer + chart recommendation for the result."""
    chart = recommend_chart(question, result)

    if result["row_count"] == 0:
        return FormatResult(
            answer="The query returned no results. This could mean there is no data matching your criteria for the selected period.",
            chart=chart,
        )

    rows_for_prompt = result["rows"][:_MAX_ROWS_IN_PROMPT]
    table_text = _rows_to_text(result["columns"], rows_for_prompt)
    cap_note = f"\n(Note: results are capped at {result['row_count']} rows)" if result["capped"] else ""

    prompt = f"""You are a business analyst. A user asked the following question about restaurant sales data:

Question: {question}

The following SQL query was executed:
{sql}

Results:{cap_note}
{table_text}

Provide a clear, concise business summary of these results in 2-4 sentences.
Highlight key numbers, trends, or insights. Use plain language — no SQL jargon.
Do not repeat the raw data row by row."""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return FormatResult(
        answer=response["message"]["content"].strip(),
        chart=chart,
    )


def _rows_to_text(columns: list[str], rows: list[list]) -> str:
    header = " | ".join(columns)
    separator = "-" * len(header)
    lines = [header, separator]
    for row in rows:
        lines.append(" | ".join(str(v) if v is not None else "NULL" for v in row))
    return "\n".join(lines)
