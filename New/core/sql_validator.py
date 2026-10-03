"""
SQL Validator
-------------
Validates generated SQL before execution using two layers:
  1. Keyword blocklist — rejects any DDL or write operations
  2. Table allowlist  — rejects queries referencing unauthorized tables

Uses sqlparse for proper token-level parsing rather than naive string matching,
which prevents bypass via comments, mixed case, or whitespace tricks.
"""
import logging
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DDL, DML
from schema.registry import get_allowed_tables

logger = logging.getLogger(__name__)

# Any statement containing these token types is rejected outright
_BLOCKED_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "EXEC", "EXECUTE", "XP_", "SP_", "OPENROWSET",
    "BULK", "GRANT", "REVOKE", "DENY",
}


class ValidationError(Exception):
    pass


def validate(sql: str) -> str:
    """
    Validate SQL and return the cleaned statement, or raise ValidationError.
    """
    if not sql or not sql.strip():
        raise ValidationError("Empty SQL statement")

    cleaned = sql.strip().rstrip(";")
    parsed = sqlparse.parse(cleaned)

    if not parsed:
        raise ValidationError("Could not parse SQL statement")

    statement: Statement = parsed[0]

    _check_blocked_keywords(statement, cleaned)
    _check_allowed_tables(cleaned)

    logger.info("SQL validation passed")
    return cleaned


def _check_blocked_keywords(statement: Statement, raw: str) -> None:
    """Reject any statement containing DDL, write DML, or dangerous keywords."""
    # Check via sqlparse token types
    for token in statement.flatten():
        if token.ttype in (DDL,):
            raise ValidationError(f"DDL statement not allowed: {token.value}")
        if token.ttype in (DML,) and token.normalized.upper() != "SELECT":
            raise ValidationError(f"Write operation not allowed: {token.value}")

    # Secondary check: raw uppercase scan for things sqlparse may miss
    upper = raw.upper()
    for kw in _BLOCKED_KEYWORDS:
        # Word-boundary check to avoid false positives (e.g. "EXECUTE" in a column name)
        import re
        if re.search(rf"\b{re.escape(kw)}\b", upper):
            raise ValidationError(f"Blocked keyword detected: {kw}")


def _check_allowed_tables(sql: str) -> None:
    """Ensure only allowlisted tables are referenced."""
    allowed = {t.lower() for t in get_allowed_tables()}
    # Extract identifiers that look like table names (after FROM / JOIN)
    import re
    referenced = re.findall(
        r"(?:FROM|JOIN)\s+\[?(\w+)\]?",
        sql,
        re.IGNORECASE,
    )
    for table in referenced:
        if table.lower() not in allowed:
            raise ValidationError(f"Table not in allowlist: {table}")
