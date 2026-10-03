"""
Schema Registry
---------------
Loads table schemas directly from SQL Server's information_schema.
Falls back to SCHEMA_FALLBACK_PATH (set in .env) if the DB is unreachable.
All table and fallback configuration comes from .env — no hardcoded values.
"""
import json
import logging
import pyodbc
from config.settings import get_connection_string, ALLOWED_TABLES, SCHEMA_FALLBACK_PATH

logger = logging.getLogger(__name__)


def load_live_schema() -> dict:
    """Pull schema directly from SQL Server information_schema."""
    if not ALLOWED_TABLES:
        raise ValueError("ALLOWED_TABLES is empty — set it in .env")

    schema = {"tables": []}
    placeholders = ",".join("?" * len(ALLOWED_TABLES))

    with pyodbc.connect(get_connection_string(), timeout=10) as conn:
        cur = conn.cursor()

        cur.execute(f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'dbo'
              AND table_name IN ({placeholders})
              AND table_type = 'BASE TABLE'
        """, ALLOWED_TABLES)

        tables = [row[0] for row in cur.fetchall()]

        for table in tables:
            table_obj = {"name": table, "columns": [], "primary_key": None, "foreign_keys": []}

            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = ?
                ORDER BY ordinal_position
            """, table)
            table_obj["columns"] = [
                {"name": r[0], "type": r[1], "nullable": r[2] == "YES"}
                for r in cur.fetchall()
            ]

            cur.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = ? AND tc.constraint_type = 'PRIMARY KEY'
            """, table)
            pk = cur.fetchone()
            if pk:
                table_obj["primary_key"] = pk[0]

            cur.execute("""
                SELECT kcu.column_name, ccu.table_name, ccu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = ?
            """, table)
            table_obj["foreign_keys"] = [
                {"column": r[0], "references": f"{r[1]}.{r[2]}"}
                for r in cur.fetchall()
            ]

            schema["tables"].append(table_obj)

    return schema


def load_schema() -> dict:
    """Load live schema; fall back to static JSON on failure."""
    try:
        schema = load_live_schema()
        logger.info("Schema loaded from SQL Server (%d tables)", len(schema["tables"]))
        return schema
    except Exception as e:
        logger.warning("Live schema load failed (%s), using static fallback", e)
        if not SCHEMA_FALLBACK_PATH or not SCHEMA_FALLBACK_PATH.exists():
            raise RuntimeError(
                "Live schema failed and no valid SCHEMA_FALLBACK_PATH is set in .env"
            ) from e
        with open(SCHEMA_FALLBACK_PATH, encoding="utf-8") as f:
            return json.load(f)


def schema_to_prompt(schema: dict) -> str:
    """Convert schema dict to a compact, LLM-readable text block."""
    lines = []
    for table in schema["tables"]:
        lines.append(f"\nTABLE {table['name']}")
        for col in table["columns"]:
            pk_marker = " [PK]" if col["name"] == table.get("primary_key") else ""
            null_marker = "" if col["nullable"] else " NOT NULL"
            lines.append(f"  {col['name']} ({col['type']}{null_marker}){pk_marker}")
        for fk in table.get("foreign_keys", []):
            lines.append(f"  FK: {fk['column']} → {fk['references']}")
    return "\n".join(lines)


def get_allowed_tables() -> list[str]:
    return ALLOWED_TABLES
