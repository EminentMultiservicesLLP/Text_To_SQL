"""
What the engine learns, stored in its own SQLite file (never in the client's database).

- A user's clarification choices apply to that user straight away.
- When enough different users pick the same meaning, it is suggested to an admin.
- Only admin-approved words apply to everyone in that client. Nothing crosses between clients.
- Plans and questions are logged; results and answers are not, so nothing stale is ever reused.
"""
import json
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS query_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client TEXT NOT NULL, user_id TEXT NOT NULL, conversation_id TEXT,
    question TEXT NOT NULL, normalized TEXT, plan_json TEXT, sql TEXT,
    status TEXT NOT NULL, message TEXT, source TEXT, elapsed_ms INTEGER,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id INTEGER NOT NULL, client TEXT NOT NULL, user_id TEXT NOT NULL,
    rating INTEGER NOT NULL, comment TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS choices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client TEXT NOT NULL, user_id TEXT NOT NULL, term TEXT NOT NULL, target TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS client_terms (
    client TEXT NOT NULL, term TEXT NOT NULL, target TEXT NOT NULL,
    status TEXT NOT NULL, decided_by TEXT, decided_at TEXT NOT NULL,
    PRIMARY KEY (client, term, target)
);
CREATE INDEX IF NOT EXISTS ix_choices ON choices (client, term, target);
CREATE INDEX IF NOT EXISTS ix_query_log ON query_log (client, created_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class LearningStore:
    def __init__(self, path: Path, promote_min_users: int):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.promote_min_users = promote_min_users
        self._lock = threading.Lock()
        with self._conn() as c:
            c.executescript(_SCHEMA)
            if "trace" not in {r["name"] for r in c.execute("PRAGMA table_info(query_log)")}:
                c.execute("ALTER TABLE query_log ADD COLUMN trace TEXT")

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    # ── logging ─────────────────────────────────────────────────────────────
    def log_query(self, client: str, user_id: str, conversation_id: str | None, question: str,
                  normalized: str, plan: dict | None, sql: str | None, status: str, message: str | None,
                  source: str | None, elapsed_ms: int, trace: str | None = None) -> int:
        with self._lock, self._conn() as c:
            cur = c.execute(
                "INSERT INTO query_log (client, user_id, conversation_id, question, normalized, plan_json, sql,"
                " status, message, source, elapsed_ms, created_at, trace) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (client, user_id, conversation_id, question, normalized, json.dumps(plan, default=str) if plan else None,
                 sql, status, message, source, elapsed_ms, _now(), trace or None),
            )
            return int(cur.lastrowid)

    def add_feedback(self, client: str, user_id: str, query_id: int, rating: int, comment: str | None) -> None:
        with self._lock, self._conn() as c:
            c.execute("INSERT INTO feedback (query_id, client, user_id, rating, comment, created_at)"
                      " VALUES (?,?,?,?,?,?)", (query_id, client, user_id, rating, comment, _now()))

    # ── learned words ───────────────────────────────────────────────────────
    def record_choices(self, client: str, user_id: str, overrides: dict[str, str]) -> None:
        with self._lock, self._conn() as c:
            c.executemany("INSERT INTO choices (client, user_id, term, target, created_at) VALUES (?,?,?,?,?)",
                          [(client, user_id, t.lower().strip(), v, _now()) for t, v in overrides.items()])

    def terms_for(self, client: str, user_id: str) -> dict[str, str]:
        """Approved client words, then this user's own latest choices on top."""
        with self._conn() as c:
            terms = {r["term"]: r["target"] for r in c.execute(
                "SELECT term, target FROM client_terms WHERE client=? AND status='approved'", (client,))}
            for r in c.execute("SELECT term, target FROM choices WHERE client=? AND user_id=? ORDER BY id",
                               (client, user_id)):
                terms[r["term"]] = r["target"]
        return terms

    def suggestions(self, client: str) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                """
                SELECT ch.term, ch.target, COUNT(DISTINCT ch.user_id) AS users, MAX(ch.created_at) AS last_seen
                FROM choices ch
                LEFT JOIN client_terms ct ON ct.client = ch.client AND ct.term = ch.term AND ct.target = ch.target
                WHERE ch.client = ? AND ct.term IS NULL
                GROUP BY ch.term, ch.target
                HAVING COUNT(DISTINCT ch.user_id) >= ?
                ORDER BY users DESC, last_seen DESC
                """, (client, self.promote_min_users)).fetchall()
        return [dict(r) for r in rows]

    def client_terms(self, client: str) -> list[dict]:
        with self._conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT term, target, status, decided_by, decided_at FROM client_terms WHERE client=?"
                " ORDER BY decided_at DESC", (client,))]

    def decide(self, client: str, term: str, target: str, approve: bool, decided_by: str) -> None:
        with self._lock, self._conn() as c:
            if approve:
                c.execute("UPDATE client_terms SET status='replaced', decided_at=? "
                          "WHERE client=? AND term=? AND status='approved' AND target<>?",
                          (_now(), client, term.lower(), target))
            c.execute(
                "INSERT INTO client_terms (client, term, target, status, decided_by, decided_at) VALUES (?,?,?,?,?,?)"
                " ON CONFLICT(client, term, target) DO UPDATE SET status=excluded.status,"
                " decided_by=excluded.decided_by, decided_at=excluded.decided_at",
                (client, term.lower(), target, "approved" if approve else "rejected", decided_by, _now()))

    def failed_questions(self, client: str, limit: int = 100) -> list[dict]:
        with self._conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT id, user_id, question, status, message, created_at FROM query_log"
                " WHERE client=? AND status IN ('unsupported','error') ORDER BY id DESC LIMIT ?", (client, limit))]

    def report_rows(self, client: str, since: str) -> dict:
        """Everything the failure report needs since an ISO timestamp: all questions, and the ones rated wrong."""
        with self._conn() as c:
            rows = [dict(r) for r in c.execute(
                "SELECT id, user_id, conversation_id, question, plan_json, sql, status, message, source,"
                " elapsed_ms, created_at, trace FROM query_log WHERE client=? AND created_at>=? ORDER BY id",
                (client, since))]
            rated = {r["query_id"]: dict(r) for r in c.execute(
                "SELECT query_id, rating, comment FROM feedback WHERE client=? AND created_at>=?", (client, since))}
        return {"queries": rows, "feedback": rated}
