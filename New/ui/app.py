"""
AI SQL Chat — Streamlit UI
--------------------------
Entry point. Run with:  streamlit run ui/app.py
"""
import sys
import uuid
import logging
import pandas as pd
import streamlit as st

# Make sure imports resolve from the New/ root
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from core.conversation import get_session
from core.sql_generator import generate_sql, get_embedding
from core.sql_validator import validate, ValidationError
from core.sql_executor import execute, ExecutionError
from core.result_formatter import format_result, FormatResult
from core.chart_advisor import ChartConfig
from core.prompt_builder import resolve_question
from memory.vector_store import find_similar, store, CacheResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Data Assistant", page_icon="🤖", layout="wide")
st.title("🤖 AI Data Assistant")
st.caption("Ask questions about your sales data in plain English.")

# ── Session state ─────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of {role, content, sql, result}

session_id = st.session_state.session_id
conversation = get_session(session_id)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Session")
    st.caption(f"ID: `{session_id[:8]}...`")
    if st.button("🗑️ Clear conversation"):
        st.session_state.chat_history = []
        conversation.clear()
        st.rerun()

    st.divider()
    st.header("Example questions")
    examples = [
        "What were total sales today?",
        "Top 10 best-selling items this month",
        "Revenue breakdown by payment method",
        "Which branch had highest sales this month?",
        "Hourly sales trend for today",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.pending_question = ex

# ── Chart renderer (reused for history + live response) ──────────────────────
def render_chart(chart: ChartConfig, result: dict) -> None:
    """Render the appropriate Streamlit chart from a ChartConfig."""
    if chart.chart_type == "none" or not result or result["row_count"] == 0:
        return

    df = pd.DataFrame(result["rows"], columns=result["columns"])

    # Coerce value columns to numeric, drop rows that fail
    for col in chart.value_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=chart.value_cols)

    if df.empty or chart.label_col not in df.columns:
        return

    df = df.set_index(chart.label_col)[chart.value_cols]

    title = chart.title or ""
    if chart.chart_type == "bar":
        st.bar_chart(df, use_container_width=True)
    elif chart.chart_type == "line":
        st.line_chart(df, use_container_width=True)
    elif chart.chart_type == "pie":
        # Streamlit has no native pie chart — use a bar chart as fallback
        # with a note. Replace with plotly if available.
        try:
            import plotly.express as px
            fig = px.pie(
                df.reset_index(),
                names=chart.label_col,
                values=chart.value_cols[0],
                title=title,
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.bar_chart(df, use_container_width=True)


# ── Render chat history ───────────────────────────────────────────────────────
for turn in st.session_state.chat_history:
    with st.chat_message(turn["role"]):
        if turn.get("cache_badge"):
            st.caption(turn["cache_badge"])
        st.markdown(turn["content"])
        if turn.get("chart") and turn.get("result"):
            render_chart(turn["chart"], turn["result"])
        if turn.get("sql"):
            with st.expander("🔍 Generated SQL"):
                st.code(turn["sql"], language="sql")
        if turn.get("result") and turn["result"]["row_count"] > 0:
            with st.expander(f"📊 Raw data ({turn['result']['row_count']} rows)"):
                df = pd.DataFrame(turn["result"]["rows"], columns=turn["result"]["columns"])
                st.dataframe(df, use_container_width=True)

# ── Handle input ──────────────────────────────────────────────────────────────
question = st.chat_input("Ask a question about your data...")

# Allow sidebar example buttons to inject a question
if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    # Show user message immediately
    st.session_state.chat_history.append({"role": "user", "content": question})
    conversation.add("user", question)

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            sql = None
            result = None
            answer = None
            chart = None
            cache_badge = None

            try:
                # 1. Resolve region/alias terms in the question
                resolved_question, warnings = resolve_question(question)
                if warnings:
                    for w in warnings:
                        st.warning(w)

                # 2. Embed the resolved question
                embedding = get_embedding(resolved_question)

                # 2. Two-tier cache lookup
                cache = find_similar(embedding)

                if cache.tier == "full":
                    # ── Tier 1: identical question ─────────────────────────
                    sql = cache.sql
                    sql = validate(sql)
                    result = execute(sql)
                    answer = cache.answer
                    chart = cache.chart
                    cache_badge = f"⚡ Full cache hit ({cache.similarity:.0%} match) — no LLM calls"

                elif cache.tier == "sql":
                    # ── Tier 2: similar question ───────────────────────────
                    sql = cache.sql
                    sql = validate(sql)
                    result = execute(sql)
                    fmt = format_result(question, sql, result)
                    answer, chart = fmt.answer, fmt.chart
                    cache_badge = f"🔄 SQL cache hit ({cache.similarity:.0%} match) — SQL reused"

                else:
                    # ── Miss: full pipeline ────────────────────────────────
                    sql = generate_sql(resolved_question, conversation)
                    sql = validate(sql)
                    result = execute(sql)
                    fmt = format_result(question, sql, result)
                    answer, chart = fmt.answer, fmt.chart
                    store(question, sql, answer, embedding, chart)
                    cache_badge = None

                conversation.add("assistant", answer)

            except ValidationError as e:
                answer = f"⚠️ I couldn't generate a safe query for that question: {e}"
                logging.warning("Validation error: %s", e)

            except ExecutionError as e:
                answer = f"⚠️ The query failed to execute: {e}"
                logging.error("Execution error: %s", e)

            except Exception as e:
                answer = f"⚠️ Something went wrong: {e}"
                logging.exception("Unexpected error")

        # Render answer
        if cache_badge:
            st.caption(cache_badge)
        st.markdown(answer)
        if chart:
            render_chart(chart, result)
        if sql:
            with st.expander("🔍 Generated SQL"):
                st.code(sql, language="sql")
        if result and result["row_count"] > 0:
            with st.expander(f"📊 Raw data ({result['row_count']} rows)"):
                df = pd.DataFrame(result["rows"], columns=result["columns"])
                st.dataframe(df, use_container_width=True)

    # Persist to chat history
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer or "",
        "sql": sql,
        "result": result,
        "chart": chart,
        "cache_badge": cache_badge,
    })
