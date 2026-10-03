"""
SQL Executor
------------
Executes validated T-SQL against SQL Server using pyodbc.
- Opens a fresh connection per query (pyodbc handles OS-level pooling via ODBC Driver)
- Enforces a hard row cap to prevent runaway result sets
- Enforces a query timeout
- Returns column names + rows as a structured dict
"""
import logging
import pyodbc
from config.settings import get_connection_string, SQL_ROW_LIMIT, SQL_TIMEOUT

logger = logging.getLogger(__name__)


class ExecutionError(Exception):
    pass


def execute(sql: str) -> dict:
    """
    Execute a validated SELECT query.
    Returns {"columns": [...], "rows": [...], "row_count": N}
    Raises ExecutionError on failure.
    """
    try:
        with pyodbc.connect(get_connection_string(), timeout=SQL_TIMEOUT) as conn:
            conn.timeout = SQL_TIMEOUT
            cur = conn.cursor()
            cur.execute(sql)

            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchmany(SQL_ROW_LIMIT)

            result = {
                "columns": columns,
                "rows": [list(row) for row in rows],
                "row_count": len(rows),
                "capped": len(rows) == SQL_ROW_LIMIT,
            }

            logger.info("Query returned %d rows (capped=%s)", result["row_count"], result["capped"])
            return result

    except pyodbc.Error as e:
        logger.error("SQL execution error: %s", e)
        raise ExecutionError(str(e)) from e
