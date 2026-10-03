"""
Draft one new subject area for an existing client pack from one Postgres table, with the data checks a
person needs before approving it.

Reads the catalog plus aggregate figures (counts, min/max, sums, join match rates, the most common values
of flag-like columns) over a read-only connection. No data rows are printed or sent anywhere, and nothing
is sent to a language model. Output goes to packs/<client>/draft/ for review; the live semantic.yaml is
never changed:
    area-<table>.yaml   tables, joins and area to paste into semantic.yaml after review
    area-<table>.md     data profile: dates out of range, missing links, duplicates, what to decide

Usage (from the engine folder):
    .venv\\Scripts\\python tools\\draft_area.py --client bis --table public.smtbtsociety --alias soc
tools/add_table.py does the same and then fills in the wording, tests and merge in one step.
"""
import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import psycopg
import yaml
from dotenv import load_dotenv

ENGINE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ENGINE_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from datachat.pack import Pack, load_pack  # noqa: E402
from introspect_postgres import (COLUMNS_SQL, FK_SQL, PK_SQL, Column, Table, classify,  # noqa: E402
                                 words)

MIN_MATCH = 0.95  # a join is proposed only when this share of non-empty values finds its row
EARLIEST = date(1990, 1, 1)
FLAG_MAX_VALUES = 6  # a column with this many distinct values or fewer is shown with its value counts


def q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def norm(name: str) -> str:
    return name.lower().replace("_", "")


@dataclass
class Draft:
    client: str
    schema: str
    name: str
    alias: str
    rows: int
    table: Table
    pack: Pack
    pack_path: Path
    links: list[dict] = field(default_factory=list)
    joins: list[dict] = field(default_factory=list)
    profile: list[tuple[Column, dict]] = field(default_factory=list)
    distinct: dict[str, int] = field(default_factory=dict)
    flags: dict[str, list[tuple]] = field(default_factory=dict)  # "alias.column" -> [(value, rows)]
    dims: list[str] = field(default_factory=list)

    @property
    def times(self) -> list[tuple[Column, dict]]:
        return [(c, p) for c, p in self.profile if c.role == "time"]

    @property
    def numbers(self) -> list[tuple[Column, dict]]:
        return [(c, p) for c, p in self.profile if c.role == "metric"]

    def best_time(self) -> str | None:
        t = self.times
        return min(t, key=lambda cp: cp[1]["empty"] + cp[1]["too_old"] + cp[1]["future"])[0].name if t else None


def build(client: str, table: str, alias: str | None = None) -> Draft:
    pack_path = ENGINE_ROOT / "packs" / client / "semantic.yaml"
    pack = load_pack(pack_path)
    load_dotenv(ENGINE_ROOT / ".env")
    dsn = os.getenv(pack.database.dsn_env)
    if not dsn:
        sys.exit(f"Environment variable {pack.database.dsn_env} is not set")
    schema, _, name = table.partition(".")
    if not name:
        schema, name = "public", schema
    alias = alias or re.sub(r"\W", "_", name.lower())
    if alias in pack.tables:
        sys.exit(f"Alias '{alias}' is already used in the pack; pass --alias")
    if any(t.name == f"{schema}.{name}" for t in pack.tables.values()):
        sys.exit(f"{schema}.{name} is already in the pack")
    fqn = f"{q(schema)}.{q(name)}"
    pack_table_of = {t.name: a for a, t in pack.tables.items()}

    with psycopg.connect(dsn, connect_timeout=10) as conn:
        conn.read_only = True
        cur = conn.cursor()
        cur.execute("SET statement_timeout = 120000")
        cols = [Column(c, typ, nul, com) for s, t, c, typ, nul, com in cur.execute(COLUMNS_SQL, ([schema],))
                if t == name]
        if not cols:
            sys.exit(f"Table {schema}.{name} not found")
        tbl = Table(schema, name, 0, 0, 0, 0, None, cols)
        pks: dict[str, list[str]] = {}
        for s, t, c in cur.execute(PK_SQL, (list({schema} | {k.split('.')[0] for k in pack_table_of}),)):
            pks.setdefault(f"{s}.{t}", []).append(c)
        tbl.pk = pks.get(f"{schema}.{name}", [])
        declared = {(c1, f"{s2}.{t2}"): c2 for s1, t1, c1, s2, t2, c2, _ in cur.execute(FK_SQL, ([schema],))
                    if t1 == name}
        tbl.est_rows = rows = cur.execute(f"SELECT COUNT(*) FROM {fqn}").fetchone()[0]
        classify(tbl)
        d = Draft(client, schema, name, alias, rows, tbl, pack, pack_path)

        # ── links to tables already in the pack ───────────────────────────────
        for c in tbl.columns:
            for full, palias in pack_table_of.items():
                ppk = pks.get(full, [])
                hit = declared.get((c.name, full)) or (ppk[0] if len(ppk) == 1 and norm(ppk[0]) == norm(c.name)
                                                       and c.name not in tbl.pk else None)
                if not hit:
                    continue
                ps, pt = full.split(".", 1)
                filled, found = cur.execute(
                    f"SELECT COUNT(t.{q(c.name)}), COUNT(p.{q(hit)}) FROM {fqn} t "
                    f"LEFT JOIN {q(ps)}.{q(pt)} p ON p.{q(hit)} = t.{q(c.name)}").fetchone()
                d.links.append({"column": c.name, "to": palias, "to_table": full, "to_column": hit,
                                "filled": filled, "found": found, "declared": (c.name, full) in declared})

        # ── column profile (aggregates only) ──────────────────────────────────
        for c in tbl.columns:
            col = q(c.name)
            if c.role == "time":
                r = cur.execute(f"SELECT MIN({col}), MAX({col}), COUNT(*) - COUNT({col}), "
                                f"COUNT(*) FILTER (WHERE {col} < %s), COUNT(*) FILTER (WHERE {col} > now() + "
                                f"interval '1 year') FROM {fqn}", (EARLIEST,)).fetchone()
                d.profile.append((c, {"min": r[0], "max": r[1], "empty": r[2], "too_old": r[3], "future": r[4]}))
            elif c.role == "metric":
                r = cur.execute(f"SELECT MIN({col}), MAX({col}), SUM({col}), COUNT(*) FILTER (WHERE {col} = 0), "
                                f"COUNT(*) - COUNT({col}) FROM {fqn}").fetchone()
                d.profile.append((c, {"min": r[0], "max": r[1], "sum": r[2], "zero": r[3], "empty": r[4]}))
        keyish = [lk["column"] for lk in d.links] + [c.name for c in tbl.columns if c.name in tbl.pk]
        d.distinct = {k: cur.execute(f"SELECT COUNT(DISTINCT {q(k)}) FROM {fqn}").fetchone()[0]
                      for k in dict.fromkeys(keyish)}

        # ── flag-like columns (status, active, cancelled...) here and in linked tables ──
        good = [lk for lk in d.links if lk["filled"] and lk["found"] / lk["filled"] >= MIN_MATCH]
        for lk in good:
            if not any(j["to"] == lk["to"] for j in d.joins):  # one path per table; the rest are in the report
                d.joins.append({"from": alias, "to": lk["to"], "columns": [[lk["column"], lk["to_column"]]]})
        scan = [(alias, schema, name, fqn, tbl.columns, None)]
        for j in d.joins:
            full = pack.tables[j["to"]].name
            ps, pt = full.split(".", 1)
            pcols = [Column(c, typ, nul, com) for s, t, c, typ, nul, com in cur.execute(COLUMNS_SQL, ([ps],))
                     if t == pt]
            scan.append((j["to"], ps, pt, f"{q(ps)}.{q(pt)}", pcols, j))
        for a, _s, _t, tq, tcols, j in scan:
            for c in tcols:
                typ = c.type.lower()
                if c.name in tbl.pk or not (typ in ("smallint", "boolean", "integer", "character varying", "text",
                                                    "character") or typ.startswith(("character", "varchar"))):
                    continue
                if j is None:
                    src = f"SELECT {q(c.name)} AS v FROM {fqn}"
                else:
                    (fc, pc), = j["columns"]
                    src = f"SELECT p.{q(c.name)} AS v FROM {fqn} t JOIN {tq} p ON p.{q(pc)} = t.{q(fc)}"
                vals = cur.execute(f"SELECT v, COUNT(*) FROM ({src}) x GROUP BY v ORDER BY 2 DESC "
                                   f"LIMIT {FLAG_MAX_VALUES + 1}").fetchall()
                if 2 <= len(vals) <= FLAG_MAX_VALUES:
                    d.flags[f"{a}.{c.name}"] = [(str(v) if v is not None else None, n) for v, n in vals]
        conn.rollback()

    merged = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
    merged["tables"][alias] = {"name": f"{schema}.{name}"}
    merged["joins"] += d.joins
    merged.setdefault("areas", {})[alias] = {"label": "x", "fact": alias, "default_metric": "n",
                                             "metrics": {"n": {"expr": "COUNT(*)", "label": "n"}}}
    reach = Pack.model_validate(merged).reachable_aliases(alias)
    d.dims = [dn for dn, dd in pack.dimensions.items() if dd.alias in reach]
    return d


def plain_proposal(d: Draft) -> dict:
    metrics = {f"{d.alias}_count": {"expr": "COUNT(*)", "label": f"Number of {words(d.name)} rows",
                                    "format": "integer", "synonyms": ["TODO"]}}
    for c, _p in d.numbers:
        metrics[f"{d.alias}_{norm(c.name)}"] = {"expr": f"SUM({{{d.alias}.{c.name}}})", "label": words(c.name).title(),
                                                "format": "number", "synonyms": ["TODO"]}
    area = {"label": f"TODO {words(d.name).title()}", "fact": d.alias, "synonyms": ["TODO"],
            "default_metric": f"{d.alias}_count", "metrics": metrics, "examples": ["TODO"]}
    if d.best_time():
        area["time_column"] = f"{d.alias}.{d.best_time()}"
    return {"tables": {d.alias: {"name": f"{d.schema}.{d.name}"}}, "joins": d.joins, "areas": {d.alias: area}}


def report_lines(d: Draft) -> list[str]:
    lines = [f"Rows: {d.rows:,}. Alias: `{d.alias}`.", "", "### Links to tables already in the pack", "",
             "| Column | Points at | Filled | Found | Match | Used |", "|---|---|---:|---:|---:|---|"]
    for lk in d.links:
        rate = lk["found"] / lk["filled"] if lk["filled"] else 0
        used = any(j["columns"][0][0] == lk["column"] and j["to"] == lk["to"] for j in d.joins)
        lines.append(f"| `{lk['column']}` | `{lk['to']}.{lk['to_column']}` | {lk['filled']:,} | {lk['found']:,} | "
                     f"{rate:.1%} | {'yes' if used else 'no'}{' (declared FK)' if lk['declared'] else ''} |")
    if not d.links:
        lines.append("| - | no links found | | | | |")
    lines += ["", f"Groupings reachable: {', '.join(d.dims) or 'none'}.", "",
              "### Keys", "", "| Column | Distinct values | Rows per value |", "|---|---:|---:|"]
    lines += [f"| `{k}` | {v:,} | {d.rows / v:.2f} |" for k, v in d.distinct.items() if v]
    lines += ["", "### Date columns", "", "| Column | Earliest | Latest | Empty | Before 1990 | Over 1 year ahead |",
              "|---|---|---|---:|---:|---:|"]
    lines += [f"| `{c.name}` | {p['min']} | {p['max']} | {p['empty']:,} | {p['too_old']:,} | {p['future']:,} |"
              for c, p in d.times] or ["| - | none | | | | |"]
    lines += ["", "### Number columns", "", "| Column | Min | Max | Total | Zero | Empty |", "|---|---:|---:|---:|---:|---:|"]
    lines += [f"| `{c.name}` | {p['min']} | {p['max']} | {p['sum']} | {p['zero']:,} | {p['empty']:,} |"
              for c, p in d.numbers] or ["| - | none | | | | |"]
    lines += ["", "### Flag-like columns (value: rows)", ""]
    lines += [f"- `{k}`: " + ", ".join(f"{v!r}: {n:,}" for v, n in vals) for k, vals in d.flags.items()] or ["- none"]
    return lines


CHECKLIST = [
    "What one row means (an event with a date, or a current state such as a membership). "
    "For a current state, mark its measures `snapshot: true`.",
    "Labels and synonyms in the business's own words.",
    "Rows that should never count (cancelled, deleted, test) as `default_filters`.",
    "Dates before 1990 or far in the future: exclude them, or tell users the figure includes them.",
    "Links below 95% match: rows without a match drop out of any grouping on that link.",
    "Whether any column is sensitive (salary, personal data) and must stay out.",
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--client", required=True, help="existing pack name, e.g. bis")
    ap.add_argument("--table", required=True, help="schema.table to add, e.g. public.smtbtsociety")
    ap.add_argument("--alias", default=None, help="short name for the table in the pack (default: table name)")
    args = ap.parse_args()

    d = build(args.client, args.table, args.alias)
    out = ENGINE_ROOT / "packs" / args.client / "draft"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / f"area-{d.name}.yaml", "w", encoding="utf-8") as f:
        f.write(f"# DRAFT area for {d.schema}.{d.name}. Fill in every TODO, check the report, then paste each block\n"
                f"# into the matching section of packs/{args.client}/semantic.yaml.\n")
        yaml.safe_dump(plain_proposal(d), f, sort_keys=False, allow_unicode=True, width=120)
    lines = [f"# Draft area: `{d.schema}.{d.name}`", ""] + report_lines(d)
    lines += ["", "## To decide before going live", ""] + [f"- {c}" for c in CHECKLIST]
    lines += [f"- Grant read access: `GRANT SELECT ON {d.schema}.{d.name} TO <read-only login>;`",
              "- Add scenarios to scenarios/<client>.yaml and run tools/scenario_test.py."]
    (out / f"area-{d.name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out / f'area-{d.name}.yaml'} and {out / f'area-{d.name}.md'}")


if __name__ == "__main__":
    main()
