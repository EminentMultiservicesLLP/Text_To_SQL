"""
Runs a checked SELECT with a read-only session, a timeout, and a row cap.
Connection strings come from environment variables named in each pack, never from the pack file.
"""
import datetime as dt
import os
import time
from dataclasses import dataclass
from decimal import Decimal

from datachat.pack import Pack


class ExecutionError(Exception):
    pass


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[list]
    capped: bool
    elapsed_ms: int


def _clean(v):
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    if isinstance(v, (dt.datetime, dt.date, dt.time)):
        return v.isoformat()
    if isinstance(v, (bytes, bytearray, memoryview)):
        return bytes(v).hex()
    if isinstance(v, str):
        return v.rstrip()  # fixed-width CHAR columns come back space-padded
    return v


class Executor:
    def run(self, sql: str, fetch_limit: int, cap: int) -> QueryResult:
        raise NotImplementedError

    @staticmethod
    def _finish(cols, raw_rows, cap, started) -> QueryResult:
        rows = [[_clean(v) for v in r] for r in raw_rows]
        capped = len(rows) > cap
        return QueryResult(columns=cols, rows=rows[:cap], capped=capped,
                           elapsed_ms=int((time.perf_counter() - started) * 1000))


class PostgresExecutor(Executor):
    def __init__(self, dsn: str, timeout_s: int):
        self.dsn, self.timeout_s = dsn, timeout_s

    def run(self, sql: str, fetch_limit: int, cap: int) -> QueryResult:
        import psycopg

        started = time.perf_counter()
        try:
            with psycopg.connect(self.dsn, connect_timeout=10) as conn:
                conn.read_only = True
                with conn.cursor() as cur:
                    cur.execute(f"SET statement_timeout = {int(self.timeout_s * 1000)}")
                    cur.execute(sql)
                    cols = [d.name for d in cur.description]
                    raw = cur.fetchmany(fetch_limit)
                conn.rollback()
        except psycopg.Error as e:
            raise ExecutionError(str(e).strip()) from e
        return self._finish(cols, raw, cap, started)


class SqlServerExecutor(Executor):
    def __init__(self, dsn: str, timeout_s: int):
        self.dsn, self.timeout_s = dsn, timeout_s

    def run(self, sql: str, fetch_limit: int, cap: int) -> QueryResult:
        import pyodbc

        started = time.perf_counter()
        try:
            with pyodbc.connect(self.dsn, timeout=10, readonly=True, autocommit=True) as conn:
                conn.timeout = self.timeout_s
                cur = conn.cursor()
                cur.execute(sql)
                cols = [d[0] for d in cur.description]
                raw = cur.fetchmany(fetch_limit)
        except pyodbc.Error as e:
            raise ExecutionError(str(e)) from e
        return self._finish(cols, raw, cap, started)


def make_executor(pack: Pack, timeout_s: int) -> Executor | None:
    dsn = os.getenv(pack.database.dsn_env, "")
    if not dsn:
        return None
    if pack.database.dialect == "postgres":
        return PostgresExecutor(dsn, timeout_s)
    return SqlServerExecutor(dsn, timeout_s)
