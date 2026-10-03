"""
Last check before any SQL reaches the database: exactly one SELECT, no write or DDL nodes,
and only the tables listed in the client pack. The read-only database login is the real boundary;
this catches mistakes early and covers SQL that did not come from the compiler (for example cached SQL).
"""
import sqlglot
from sqlglot import exp


class GuardError(Exception):
    pass


_FORBIDDEN = tuple(
    getattr(exp, name)
    for name in ("Insert", "Update", "Delete", "Drop", "Create", "Alter", "AlterTable", "Command", "Merge",
                 "TruncateTable", "Into", "Grant", "Use", "Set", "Transaction", "Commit", "Rollback")
    if hasattr(exp, name)
)


def check_sql(sql: str, dialect: str, allowed_tables: set[str]) -> None:
    try:
        statements = [s for s in sqlglot.parse(sql, read=dialect) if s is not None]
    except sqlglot.errors.SqlglotError as e:
        raise GuardError(f"SQL could not be parsed: {e}") from e
    if len(statements) != 1:
        raise GuardError("Exactly one statement is allowed")
    stmt = statements[0]
    if not isinstance(stmt, exp.Select):
        raise GuardError(f"Only SELECT is allowed, got {type(stmt).__name__}")
    bad = next(stmt.find_all(*_FORBIDDEN), None) if _FORBIDDEN else None
    if bad is not None:
        raise GuardError(f"Statement contains a forbidden operation: {type(bad).__name__}")
    for t in stmt.find_all(exp.Table):
        name = ".".join(p for p in (t.catalog, t.db, t.name) if p).lower()
        if name not in allowed_tables:
            raise GuardError(f"Table not allowed: {name}")
