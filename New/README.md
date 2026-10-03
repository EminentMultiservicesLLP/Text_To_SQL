# AI Data Assistant

Natural language → SQL chatbot for SQL Server. Runs entirely on-premises — no data leaves the client environment.

## Stack
| Layer | Technology |
|---|---|
| LLM & Embeddings | Ollama (llama3 + nomic-embed-text) — local |
| Database | SQL Server via pyodbc (ODBC Driver 17) |
| Vector cache | ChromaDB (embedded, no separate server) |
| UI | Streamlit |

## Prerequisites
1. [Ollama](https://ollama.com) installed and running
2. `ollama pull llama3` and `ollama pull nomic-embed-text`
3. ODBC Driver 17 for SQL Server installed
4. Python 3.11+

## Setup

```bash
cd New
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
# Edit .env with your DB_SERVER and DB_NAME
```

## Run

```bash
streamlit run ui/app.py
```

## Project structure

```
New/
├── config/settings.py        # all config from .env, no hardcoded values
├── schema/registry.py        # live schema from SQL Server + static fallback
├── memory/vector_store.py    # semantic Q→SQL cache (ChromaDB embedded)
├── core/
│   ├── conversation.py       # per-session turn history
│   ├── prompt_builder.py     # assembles LLM prompt
│   ├── sql_generator.py      # Ollama → raw SQL
│   ├── sql_validator.py      # AST validation + table allowlist
│   ├── sql_executor.py       # pyodbc execution with row cap + timeout
│   └── result_formatter.py   # LLM interprets results → natural language
├── prompts/
│   ├── system.txt            # T-SQL system prompt (edit to tune behaviour)
│   └── few_shots.json        # domain Q→SQL examples (add more to improve accuracy)
└── ui/app.py                 # Streamlit chat interface
```

## Adding new tables

1. Add the table name to `ALLOWED_TABLES` in `schema/registry.py`
2. Add 1-2 representative Q→SQL examples to `prompts/few_shots.json`
3. Restart the app — schema is loaded live from SQL Server on startup

## Adding new few-shot examples

Edit `prompts/few_shots.json`. Each entry is:
```json
{
  "question": "plain English question",
  "sql": "SELECT ... FROM ..."
}
```
No code changes required.

## Tuning the system prompt

Edit `prompts/system.txt` to change LLM behaviour, add business rules,
or restrict output format. No code changes required.

## Security notes
- Only SELECT queries are permitted (validator blocks all DDL and write DML)
- Only tables in `ALLOWED_TABLES` can be queried
- All inference runs locally via Ollama
- DB credentials are read from `.env` — never commit `.env` to source control
- Row results are capped at `SQL_ROW_LIMIT` (default 500)
