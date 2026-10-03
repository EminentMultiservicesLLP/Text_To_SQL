"""
Chart Advisor
-------------
Decides whether to render a chart and which type, based on:
  - Keywords in the user's question (compare, trend, breakdown, top, etc.)
  - Shape of the result (number of rows, column data types)

No LLM call — pure heuristic logic. Fast and deterministic.

Returns a ChartConfig the UI uses to render the appropriate Streamlit chart.
"""
import re
from dataclasses import dataclass
from typing import Literal

ChartType = Literal["bar", "line", "pie", "none"]


@dataclass
class ChartConfig:
    chart_type: ChartType
    label_col: str        # x-axis / category column
    value_cols: list[str] # y-axis / numeric columns
    title: str = ""


# ── Keyword signals ───────────────────────────────────────────────────────────

_COMPARISON_WORDS = re.compile(
    r"\b(compar|vs\.?|versus|between|breakdown|by branch|by channel|by method"
    r"|by category|by payment|by mode|top \d+|rank|highest|lowest|best|worst"
    r"|each|per branch|per channel|distribution)\b",
    re.IGNORECASE,
)

_TREND_WORDS = re.compile(
    r"\b(trend|over time|by (hour|day|week|month|year)|hourly|daily|weekly"
    r"|monthly|yearly|timeline|growth|change|progress)\b",
    re.IGNORECASE,
)

_PIE_WORDS = re.compile(
    r"\b(breakdown|share|proportion|percentage|split|distribution|mix)\b",
    re.IGNORECASE,
)

# ── Type helpers ──────────────────────────────────────────────────────────────

def _is_numeric(values: list) -> bool:
    """Check if a column's values are mostly numeric."""
    non_null = [v for v in values if v is not None]
    if not non_null:
        return False
    numeric = sum(1 for v in non_null if isinstance(v, (int, float)))
    return numeric / len(non_null) >= 0.8


def _classify_columns(columns: list[str], rows: list[list]) -> tuple[list[str], list[str]]:
    """Split columns into label (categorical) and value (numeric) groups."""
    if not rows:
        return [], []

    label_cols, value_cols = [], []
    for i, col in enumerate(columns):
        col_values = [row[i] for row in rows]
        if _is_numeric(col_values):
            value_cols.append(col)
        else:
            label_cols.append(col)

    return label_cols, value_cols


# ── Public API ────────────────────────────────────────────────────────────────

def recommend_chart(question: str, result: dict) -> ChartConfig:
    """
    Analyse the question and result shape, return a ChartConfig.
    Returns chart_type='none' if a chart is not appropriate.
    """
    columns = result.get("columns", [])
    rows = result.get("rows", [])
    row_count = result.get("row_count", 0)

    # Need at least 2 rows and 2 columns to draw anything meaningful
    if row_count < 2 or len(columns) < 2:
        return ChartConfig(chart_type="none", label_col="", value_cols=[])

    label_cols, value_cols = _classify_columns(columns, rows)

    if not label_cols or not value_cols:
        return ChartConfig(chart_type="none", label_col="", value_cols=[])

    label_col = label_cols[0]

    # Decide chart type from question intent
    if _TREND_WORDS.search(question):
        return ChartConfig(
            chart_type="line",
            label_col=label_col,
            value_cols=value_cols,
            title="Trend Over Time",
        )

    if _PIE_WORDS.search(question) and len(value_cols) == 1 and row_count <= 10:
        return ChartConfig(
            chart_type="pie",
            label_col=label_col,
            value_cols=value_cols,
            title="Distribution",
        )

    if _COMPARISON_WORDS.search(question):
        return ChartConfig(
            chart_type="bar",
            label_col=label_col,
            value_cols=value_cols,
            title="Comparison",
        )

    # Default: if result looks like a ranking/grouping, show a bar chart
    if row_count <= 20 and len(value_cols) >= 1:
        return ChartConfig(
            chart_type="bar",
            label_col=label_col,
            value_cols=value_cols,
            title="",
        )

    return ChartConfig(chart_type="none", label_col="", value_cols=[])
