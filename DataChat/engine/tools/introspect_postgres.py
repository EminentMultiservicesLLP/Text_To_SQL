"""
Draft a client pack from a Postgres database.

Reads only catalog and statistics views (pg_class, pg_attribute, pg_constraint, pg_stat_user_tables,
pg_stats). It does not scan business tables. Output goes to packs/<client>/draft/ for a person to review:
    semantic.draft.yaml   draft pack in the engine's format
    report.md             every table ranked, with the reasons, plus the joins that need checking

Usage (from the engine folder):
    .venv\\Scripts\\python tools\\introspect_postgres.py --client clientx --dsn-env CLIENTX_DSN --schemas public
"""
import argparse
import csv
import math
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import psycopg
import yaml
from dotenv import load_dotenv

ENGINE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ENGINE_ROOT))
from datachat.pack import Pack  # noqa: E402

TABLES_SQL = """
SELECT n.nspname, c.relname,
       GREATEST(c.reltuples, 0)::bigint AS est_rows,
       COALESCE(s.n_live_tup, 0) AS live_rows,
       COALESCE(s.n_tup_ins, 0) + COALESCE(s.n_tup_upd, 0) + COALESCE(s.n_tup_del, 0) AS writes,
       COALESCE(s.seq_scan, 0) + COALESCE(s.idx_scan, 0) AS reads,
       obj_description(c.oid, 'pg_class') AS comment
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_stat_user_tables s ON s.relid = c.oid
WHERE c.relkind IN ('r', 'p') AND n.nspname = ANY(%s)
"""
COLUMNS_SQL = """
SELECT n.nspname, c.relname, a.attname, format_type(a.atttypid, a.atttypmod), NOT a.attnotnull,
       col_description(c.oid, a.attnum)
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE a.attnum > 0 AND NOT a.attisdropped AND c.relkind IN ('r', 'p') AND n.nspname = ANY(%s)
ORDER BY n.nspname, c.relname, a.attnum
"""
PK_SQL = """
SELECT n.nspname, c.relname, a.attname
FROM pg_constraint k
JOIN pg_class c ON c.oid = k.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN LATERAL unnest(k.conkey) AS u(attnum) ON true
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = u.attnum
WHERE k.contype = 'p' AND n.nspname = ANY(%s)
"""
FK_SQL = """
SELECT n1.nspname, c1.relname, a1.attname, n2.nspname, c2.relname, a2.attname, k.conname
FROM pg_constraint k
JOIN pg_class c1 ON c1.oid = k.conrelid
JOIN pg_namespace n1 ON n1.oid = c1.relnamespace
JOIN pg_class c2 ON c2.oid = k.confrelid
JOIN pg_namespace n2 ON n2.oid = c2.relnamespace
JOIN LATERAL unnest(k.conkey, k.confkey) AS u(src, dst) ON true
JOIN pg_attribute a1 ON a1.attrelid = c1.oid AND a1.attnum = u.src
JOIN pg_attribute a2 ON a2.attrelid = c2.oid AND a2.attnum = u.dst
WHERE k.contype = 'f' AND n1.nspname = ANY(%s)
"""
STATS_SQL = """
SELECT schemaname, tablename, attname, n_distinct, null_frac, most_common_vals::text
FROM pg_stats WHERE schemaname = ANY(%s)
"""

NOISE_NAME = re.compile(
    r"(^|_)(log|logs|audit|history|hist|bak|backup|tmp|temp|staging|stg|migration|migrations|archive|old|copy|test)"
    r"(_|$|\d)|^(django_|auth_|flyway|__|pg_|hangfire|aspnet|efmigrations)", re.I)
MONEYISH = re.compile(r"(amount|amt|total|price|value|cost|revenue|sales|tax|discount|fee|charge|paid|balance|"
                      r"qty|quantity|units|count|weight|volume)", re.I)
IDISH = re.compile(r"(^id$|_id$|id$|_code$|code$|_no$|_number$|number$|^year$|^month$|_year$|_month$|pincode|zip)", re.I)
HIDDEN_TEXT = re.compile(r"(email|phone|mobile|password|hash|token|secret|address|url|json|uuid|guid|note|remark|"
                         r"description|comment)", re.I)
NUMERIC_TYPES = ("numeric", "money", "double precision", "real", "decimal")
INTEGER_TYPES = ("integer", "bigint", "smallint")
TIME_TYPES = ("timestamp", "date")
TEXT_TYPES = ("text", "character varying", "character", "varchar", "citext")


@dataclass
class Column:
    name: str
    type: str
    nullable: bool
    comment: str | None
    n_distinct: float | None = None
    null_frac: float | None = None
    common_values: list[str] = field(default_factory=list)
    role: str = "hidden"  # metric | time | dimension | hidden


@dataclass
class Table:
    schema: str
    name: str
    est_rows: int
    live_rows: int
    writes: int
    reads: int
    comment: str | None
    columns: list[Column] = field(default_factory=list)
    pk: list[str] = field(default_factory=list)
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.schema}.{self.name}"

    @property
    def rows(self) -> int:
        return max(self.est_rows, self.live_rows)


@dataclass
class Edge:
    child: str
    child_col: str
    parent: str
    parent_col: str
    declared: bool


def words(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name).replace("_", " ").lower().strip()


def alias_for(t: Table, used: set[str]) -> str:
    base = re.sub(r"\W", "_", t.name.lower() if t.schema == "public" else f"{t.schema}_{t.name}".lower())
    alias, i = base, 2
    while alias in used:
        alias, i = f"{base}_{i}", i + 1
    used.add(alias)
    return alias


def parse_pg_array(text: str | None) -> list[str]:
    if not text or len(text) < 2:
        return []
    return next(csv.reader([text[1:-1]], quotechar='"', escapechar="\\", skipinitialspace=True), [])


def distinct_estimate(col: Column, rows: int) -> float | None:
    if col.n_distinct is None:
        return None
    return col.n_distinct if col.n_distinct >= 0 else -col.n_distinct * rows


def classify(t: Table) -> None:
    for c in t.columns:
        typ = c.type.lower()
        est = distinct_estimate(c, t.rows)
        if typ.startswith(TIME_TYPES):
            c.role = "time"
        elif c.name in t.pk or IDISH.search(c.name):
            c.role = "hidden"
        elif typ.startswith(NUMERIC_TYPES) or (typ.startswith(INTEGER_TYPES) and MONEYISH.search(c.name)):
            c.role = "metric"
        elif typ == "boolean":
            c.role = "dimension"
        elif typ.startswith(TEXT_TYPES) and not HIDDEN_TEXT.search(c.name) and est is not None and 2 <= est <= 200:
            c.role = "dimension"


def score(t: Table, degree: int) -> None:
    s = 2 * math.log10(t.rows + 1) + math.log10(t.writes + 1) + 0.5 * math.log10(t.reads + 1) + 3 * degree
    t.reasons.append(f"rows≈{t.rows:,}, writes={t.writes:,}, reads={t.reads:,}, joins={degree}")
    if t.rows == 0:
        s -= 100
        t.reasons.append("empty")
    if NOISE_NAME.search(t.name):
        s -= 8
        t.reasons.append("name looks like log/backup/temp/framework table")
    if any(c.role == "metric" for c in t.columns) and any(c.role == "time" for c in t.columns):
        s += 4
        t.reasons.append("has measures and a date column (possible fact table)")
    t.score = round(s, 1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--client", required=True, help="pack name, e.g. clientx")
    ap.add_argument("--dsn-env", required=True, help="environment variable holding the Postgres connection string")
    ap.add_argument("--schemas", default="public", help="comma-separated schemas to scan")
    ap.add_argument("--max-areas", type=int, default=6)
    ap.add_argument("--display-name", default=None)
    args = ap.parse_args()

    load_dotenv(ENGINE_ROOT / ".env")
    dsn = os.getenv(args.dsn_env)
    if not dsn:
        sys.exit(f"Environment variable {args.dsn_env} is not set")
    schemas = [s.strip() for s in args.schemas.split(",") if s.strip()]

    with psycopg.connect(dsn, connect_timeout=10) as conn:
        conn.read_only = True
        cur = conn.cursor()
        tables = {f"{r[0]}.{r[1]}": Table(*r) for r in cur.execute(TABLES_SQL, (schemas,)).fetchall()}
        for sch, tbl, col, typ, nullable, comment in cur.execute(COLUMNS_SQL, (schemas,)).fetchall():
            if f"{sch}.{tbl}" in tables:
                tables[f"{sch}.{tbl}"].columns.append(Column(col, typ, nullable, comment))
        for sch, tbl, col in cur.execute(PK_SQL, (schemas,)).fetchall():
            if f"{sch}.{tbl}" in tables:
                tables[f"{sch}.{tbl}"].pk.append(col)
        fk_rows = cur.execute(FK_SQL, (schemas,)).fetchall()
        stats = {(r[0], r[1], r[2]): r[3:] for r in cur.execute(STATS_SQL, (schemas,)).fetchall()}
        conn.rollback()

    for t in tables.values():
        for c in t.columns:
            st = stats.get((t.schema, t.name, c.name))
            if st:
                c.n_distinct, c.null_frac, c.common_values = st[0], st[1], parse_pg_array(st[2])[:50]
        classify(t)

    # ── joins: declared foreign keys, then name-based guesses ──────────────
    edges: list[Edge] = [Edge(f"{a}.{b}", c, f"{d}.{e}", f, True)
                         for a, b, c, d, e, f, _ in fk_rows if f"{a}.{b}" in tables and f"{d}.{e}" in tables]
    linked = {(e.child, e.child_col) for e in edges}

    def norm(name: str) -> str:
        return name.lower().replace("_", "")

    # a column named like another table's single-column primary key (customerid, customer_id -> customerid);
    # when several tables share that key name (1:1 splits of one entity), the shortest table name owns it
    pk_owner: dict[str, Table] = {}
    for t in sorted(tables.values(), key=lambda t: (len(t.name), t.name)):
        if len(t.pk) == 1 and norm(t.pk[0]) not in ("id", "rowid", "uid", "guid"):
            pk_owner.setdefault(norm(t.pk[0]), t)
    # a column <entity>_id / <entity>Id pointing at a table named <entity>, allowing a short prefix (tbl_, smtbm)
    by_name = defaultdict(list)
    for t in tables.values():
        by_name[norm(t.name)].append(t)
        stripped = re.sub(r"^(?:tbl_?|tb_|[a-z]{0,3}tb[mt]_?|m_|t_)", "", t.name.lower()).replace("_", "")
        if stripped and stripped != norm(t.name):
            by_name[stripped].append(t)

    for t in tables.values():
        for c in t.columns:
            if t.pk == [c.name] or (t.key, c.name) in linked:
                continue
            owner = pk_owner.get(norm(c.name))
            if owner is not None and owner.key != t.key and owner.pk != t.pk:
                edges.append(Edge(t.key, c.name, owner.key, owner.pk[0], False))
                linked.add((t.key, c.name))
                continue
            m = re.match(r"^(.*?)_?id$", c.name, re.IGNORECASE)
            if not m or not m[1]:
                continue
            base = norm(m[1])
            candidates = {base, base + "s", base + "es", (base[:-1] + "ies") if base.endswith("y") else base}
            parents = [p for cand in candidates for p in by_name.get(cand, [])
                       if p.key != t.key and len(p.pk) == 1]
            if parents:
                parent = min(parents, key=lambda p: (len(p.name), p.name))
                edges.append(Edge(t.key, c.name, parent.key, parent.pk[0], False))
                linked.add((t.key, c.name))

    degree = defaultdict(int)
    for e in edges:
        degree[e.child] += 1
        degree[e.parent] += 1
    for t in tables.values():
        score(t, degree[t.key])
    ranked = sorted(tables.values(), key=lambda t: t.score, reverse=True)

    # ── subject areas: best fact tables and what they join to (2 hops) ──────
    out_edges = defaultdict(list)
    for e in edges:
        out_edges[e.child].append(e)
    facts = [t for t in ranked if t.score > 0 and any(c.role == "metric" for c in t.columns)
             and any(c.role == "time" for c in t.columns)][: args.max_areas]

    used_aliases: set[str] = set()
    alias_of: dict[str, str] = {}

    def alias(key: str) -> str:
        if key not in alias_of:
            alias_of[key] = alias_for(tables[key], used_aliases)
        return alias_of[key]

    pack_tables, pack_joins, dimensions, areas = {}, [], {}, {}
    join_seen = set()
    for fact in facts:
        reach = [fact.key]
        frontier = [fact.key]
        for _ in range(2):
            nxt = []
            for k in frontier:
                for e in out_edges[k]:
                    if e.parent not in reach:
                        reach.append(e.parent)
                        nxt.append(e.parent)
                    jk = (e.child, e.child_col, e.parent)
                    if jk not in join_seen:
                        join_seen.add(jk)
                        pack_joins.append({"from": alias(e.child), "to": alias(e.parent),
                                           "columns": [[e.child_col, e.parent_col]]})
            frontier = nxt
        for k in reach:
            pack_tables[alias(k)] = {"name": k}
            for c in tables[k].columns:
                if c.role == "dimension":
                    dname = alias(k) + "_" + re.sub(r"\W", "_", c.name.lower())
                    dimensions.setdefault(dname, {
                        "column": f"{alias(k)}.{c.name}", "label": words(c.name).title(),
                        "synonyms": [words(c.name)], "load_values": True})
        fa = alias(fact.key)
        metrics = {f"{fa}_count": {"expr": "COUNT(*)", "label": f"Number of {words(fact.name)}",
                                   "format": "integer", "synonyms": [words(fact.name), "count"]}}
        for c in fact.columns:
            if c.role == "metric":
                metrics[fa + "_" + re.sub(r"\W", "_", c.name.lower())] = {
                    "expr": f"SUM({{{fa}.{c.name}}})", "label": f"Total {words(c.name)}",
                    "format": "number", "synonyms": [words(c.name)]}
        time_col = next(c.name for c in fact.columns if c.role == "time")
        areas[fa] = {"label": words(fact.name).title(), "fact": fa, "time_column": f"{fa}.{time_col}",
                     "synonyms": [words(fact.name)], "default_metric": f"{fa}_count", "metrics": metrics,
                     "examples": []}

    draft = {"client": args.client, "display_name": args.display_name or args.client,
             "database": {"dialect": "postgres", "dsn_env": args.dsn_env},
             "tables": pack_tables, "joins": pack_joins, "dimensions": dimensions, "areas": areas}
    Pack.model_validate(draft)  # the draft must load before anyone reviews it

    out_dir = ENGINE_ROOT / "packs" / args.client / "draft"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "semantic.draft.yaml", "w", encoding="utf-8") as f:
        f.write("# DRAFT generated from database statistics. Review every table, join, metric and label,\n"
                "# then save the reviewed version as packs/<client>/semantic.yaml.\n")
        yaml.safe_dump(draft, f, sort_keys=False, allow_unicode=True, width=120)

    lines = [f"# Draft pack report: {args.client}", "",
             f"Scanned schemas: {', '.join(schemas)}. Tables: {len(tables)}. Proposed subject areas: {len(areas)}.",
             "", "## Proposed subject areas", ""]
    for a in areas.values():
        lines.append(f"- **{a['label']}** (`{pack_tables[a['fact']]['name']}`), date column `{a['time_column']}`, "
                     f"{len(a['metrics'])} measures")
    lines += ["", "## Joins guessed from column names (check each one)", ""]
    guessed = [e for e in edges if not e.declared]
    lines += [f"- `{e.child}.{e.child_col}` → `{e.parent}.{e.parent_col}`" for e in guessed] or ["- none"]
    lines += ["", "## All tables, ranked", "", "| Score | Table | Rows (est.) | Measures | Dates | Groupings | Notes |",
              "|---:|---|---:|---:|---:|---:|---|"]
    for t in ranked:
        roles = defaultdict(int)
        for c in t.columns:
            roles[c.role] += 1
        lines.append(f"| {t.score} | `{t.key}` | {t.rows:,} | {roles['metric']} | {roles['time']} | "
                     f"{roles['dimension']} | {'; '.join(t.reasons)} |")
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_dir / 'semantic.draft.yaml'} and {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()
