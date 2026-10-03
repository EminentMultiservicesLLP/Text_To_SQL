"""
Add one database table to a client pack in one step, with one review.

    .venv\\Scripts\\python tools\\add_table.py --client bis --table public.smtbtsociety [--alias soc] [--yes]

1. Profiles the table (tools/draft_area.py): links to the pack, bad dates, duplicates, flag-like columns.
2. Asks the local language model (Ollama on this machine) for the business wording only: labels, synonyms,
   what one row means, rows to exclude, sensitive columns, test questions. It sees column names, types and
   aggregate figures, never data rows. It never writes SQL: every expression is built here from columns
   that exist, and anything it names that doesn't exist is dropped and reported.
3. Runs every proposed measure against the database and the generated questions through the engine.
4. Writes one review (packs/<client>/draft/review-<table>.md), prints it, and asks to approve.
5. On approval, adds the blocks to semantic.yaml and the questions to scenarios/<client>.yaml
   (comments in both files are kept). Nothing changes without approval.
"""
import argparse
import json
import re
import shutil
import sys
import tempfile
from dataclasses import replace
from datetime import date
from pathlib import Path

import httpx
import yaml

ENGINE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ENGINE_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from datachat.config import load_settings  # noqa: E402
from datachat.executor import make_executor  # noqa: E402
from datachat.pack import Pack  # noqa: E402
from datachat.plan import Plan, Sort  # noqa: E402
from datachat.runner import execute  # noqa: E402
from datachat.service import ChatRequest, ChatService  # noqa: E402
from draft_area import CHECKLIST, Draft, build, plain_proposal, report_lines, words  # noqa: E402

FORMATS = ("currency", "integer", "number")
SCHEMA = {
    "type": "object",
    "properties": {
        "area_name": {"type": "string"},
        "label": {"type": "string"},
        "synonyms": {"type": "array", "items": {"type": "string"}},
        "row_meaning": {"type": "string", "enum": ["event", "current_state"]},
        "time_column": {"type": "string"},
        "active_flag": {"type": "object", "properties": {"column": {"type": "string"}, "value": {"type": "string"}},
                        "required": ["column", "value"]},
        "exclude": {"type": "array", "items": {"type": "object", "properties": {
            "column": {"type": "string"}, "value": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["column", "value", "reason"]}},
        "measures": {"type": "array", "items": {"type": "object", "properties": {
            "name": {"type": "string"}, "kind": {"type": "string", "enum": ["count", "sum", "average"]},
            "column": {"type": "string"}, "label": {"type": "string"},
            "synonyms": {"type": "array", "items": {"type": "string"}},
            "format": {"type": "string", "enum": list(FORMATS)}},
            "required": ["name", "kind", "column", "label", "synonyms", "format"]}},
        "sensitive_columns": {"type": "array", "items": {"type": "string"}},
        "test_questions": {"type": "array", "items": {"type": "object", "properties": {
            "question": {"type": "string"}, "measure": {"type": "string"}, "by": {"type": "string"}},
            "required": ["question", "measure", "by"]}},
        "open_questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["area_name", "label", "synonyms", "row_meaning", "time_column", "exclude", "measures",
                 "sensitive_columns", "test_questions", "open_questions"],
}


def snake(text: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", text.lower())).strip("_")


# ── 2. wording from the local model ───────────────────────────────────────────
def facts_for_model(d: Draft) -> str:
    cols = ", ".join(f"{c.name} ({c.type})" for c in d.table.columns)
    lines = [f"Table {d.schema}.{d.name}: {d.rows:,} rows. Columns: {cols}.",
             f"Linked to existing pack tables: " + (", ".join(f"{j['columns'][0][0]} -> {j['to']} "
                                                            f"({d.pack.tables[j['to']].name})" for j in d.joins) or "none"),
             f"Groupings users can already ask by: {', '.join(d.dims) or 'none'}.",
             "Rows per key: " + ", ".join(f"{k}: {d.rows / v:.2f}" for k, v in d.distinct.items() if v) + "."]
    lines += [f"Date column {c.name}: {p['min']} to {p['max']}, empty {p['empty']}, before 1990 {p['too_old']}, "
              f"future {p['future']}." for c, p in d.times]
    lines += [f"Number column {c.name}: min {p['min']}, max {p['max']}, total {p['sum']}." for c, p in d.numbers]
    lines += [f"Flag-like column {k} (value: rows): " + ", ".join(f"{v}: {n}" for v, n in vals)
              for k, vals in d.flags.items()]
    areas = "; ".join(f"{n} ({a.label}: {', '.join(a.metrics)})" for n, a in d.pack.areas.items())
    lines.append(f"Areas already in the pack: {areas}.")
    return "\n".join(lines)


INSTRUCTIONS = """You help add a database table to a business question-answering system for an Indian company.
Users ask in English, or Hindi/Marathi written in English letters. From the facts below, describe the table in
business words. Use only column names that appear in the facts; columns of linked tables are written alias.column.
- row_meaning: "event" if each row happened on a date (an invoice, a joining, a payment); "current_state" if each
  row describes how things are now (a membership, a balance, a master record).
- time_column: the date column users mean by "last month"/"this year", or "none".
- active_flag: for current_state, the flag that marks rows that count today (e.g. emp.active = 1), if any.
- exclude: rows that must never count (cancelled, deleted, test), only when a flag clearly says so.
- measures: 2-5 things users would total or count. kind count needs no column; sum/average need a number column
  of this table. Money is format currency. Labels short, in business words. 4-8 synonyms each, including
  Hindi/Marathi words people use.
- sensitive_columns: personal or salary data that must not be queryable.
- test_questions: 6 everyday questions, each with the measure name and a grouping from the list above (or "").
- open_questions: anything a person must confirm (meaning of a flag, odd dates, unclear columns)."""


def ask_model(d: Draft, settings) -> tuple[dict | None, str]:
    body = {"model": settings.llm_model, "stream": False, "think": False, "keep_alive": -1, "format": SCHEMA,
            "options": {"temperature": 0, "num_ctx": 4096, **({"num_thread": settings.llm_num_thread}
                                                              if settings.llm_num_thread else {})},
            "messages": [{"role": "system", "content": INSTRUCTIONS},
                         {"role": "user", "content": facts_for_model(d)}]}
    try:
        r = httpx.post(f"{settings.ollama_url}/api/chat", json=body, timeout=max(settings.llm_timeout_s, 600))
        r.raise_for_status()
        return json.loads(r.json()["message"]["content"]), ""
    except (httpx.HTTPError, KeyError, ValueError) as e:
        return None, f"The local model could not be used ({e}); the draft has TODO wording to fill in by hand."


# ── turning the model's answer into a checked pack block ─────────────────────
def build_area(d: Draft, m: dict) -> tuple[str, dict, list[str], list[dict]]:
    """(area name, area block, problems found, test questions) - every column checked, every SQL built here."""
    problems: list[str] = []
    a = d.alias
    known = {f"{a}.{c.name}": c for c in d.table.columns}
    flag_cols = set(d.flags)
    linked = {j["to"] for j in d.joins}

    def col_ref(name: str) -> str | None:
        name = (name or "").strip()
        if not name or name.lower() == "none":
            return None
        ref = name if "." in name else f"{a}.{name}"
        alias, _, _ = ref.partition(".")
        if ref in known or ref in flag_cols or (alias in linked and ref in flag_cols):
            return ref
        problems.append(f"The model named a column that isn't there: `{name}` (ignored).")
        return None

    sensitive = {s.split(".")[-1].lower() for s in m.get("sensitive_columns", [])}
    numbers = {c.name for c, _ in d.numbers}
    area_name = snake(m.get("area_name") or d.name)
    if area_name in d.pack.areas:
        area_name = f"{area_name}_{a}"

    snapshot = m.get("row_meaning") == "current_state"
    active = None
    af = m.get("active_flag") or {}
    ref = col_ref(af.get("column", "")) if af else None
    if ref and af.get("value", "") != "":
        vals = [v for v, _ in d.flags.get(ref, [])]
        if vals and af["value"] not in vals:
            problems.append(f"Active flag value `{af['value']}` never occurs in `{ref}` (ignored).")
        else:
            active = (ref, af["value"])
    lit = lambda v: v if re.fullmatch(r"-?\d+(\.\d+)?", v) else "'" + v.replace("'", "''") + "'"  # noqa: E731
    cond = f"{{{active[0]}}} = {lit(active[1])}" if active else None

    metrics: dict[str, dict] = {}
    for x in m.get("measures", []):
        name = snake(x.get("name", ""))
        if not name or name in metrics:
            continue
        kind, column = x.get("kind"), (x.get("column") or "").split(".")[-1]
        if kind in ("sum", "average"):
            if column not in numbers:
                problems.append(f"Measure `{name}`: `{column}` is not a number column of this table (dropped).")
                continue
            if column.lower() in sensitive:
                problems.append(f"Measure `{name}` uses sensitive column `{column}` (dropped).")
                continue
        val = f"{{{a}.{column}}}"
        s = (f"SUM(CASE WHEN {cond} THEN {val} ELSE 0 END)" if cond else f"SUM({val})") if kind != "count" else None
        n = f"SUM(CASE WHEN {cond} THEN 1 ELSE 0 END)" if cond else "COUNT(*)"
        expr = {"count": n, "sum": s, "average": f"{s} / NULLIF({n}, 0)" if s else None}.get(kind)
        if not expr:
            continue
        md = {"expr": expr, "label": (x.get("label") or words(name)).strip(),
              "format": x.get("format") if x.get("format") in FORMATS else "number"}
        if snapshot and (cond or kind != "count"):
            md["snapshot"] = True
        md["synonyms"] = list(dict.fromkeys(s.strip().lower() for s in x.get("synonyms", []) if s.strip()))[:10]
        metrics[name] = md
    if not metrics:
        problems.append("No usable measure came back; a plain row count was added.")
        metrics[f"{area_name}_count"] = {"expr": "COUNT(*)", "label": f"Number of {words(d.name)} rows",
                                         "format": "integer", "synonyms": [words(d.name)]}

    area: dict = {"label": (m.get("label") or words(d.name).title()).strip(), "fact": a}
    tref = col_ref(m.get("time_column", ""))
    if tref and tref.split(".", 1)[1] in {c.name for c, _ in d.times}:
        area["time_column"] = tref
    elif d.best_time() and not snapshot:
        area["time_column"] = f"{a}.{d.best_time()}"
        problems.append(f"No usable date column came back; `{d.best_time()}` was used.")
    area["synonyms"] = list(dict.fromkeys(s.strip().lower() for s in m.get("synonyms", []) if s.strip()))[:8]
    area["default_metric"] = next(iter(metrics))
    excludes = []
    for x in m.get("exclude", []):
        ref = col_ref(x.get("column", ""))
        if not ref:
            continue
        vals = [v for v, _ in d.flags.get(ref, [])]
        if x.get("value") not in vals:
            problems.append(f"Exclusion `{ref} = {x.get('value')}` matches no rows (ignored).")
            continue
        excludes.append({"column": ref, "op": "neq", "value": x["value"]})
    if excludes:
        area["default_filters"] = excludes
    area["metrics"] = metrics
    tests = []
    for t in m.get("test_questions", []):
        mname = snake(t.get("measure", ""))
        if t.get("question") and mname in metrics:
            by = t.get("by") if t.get("by") in d.dims else ""
            tests.append({"question": t["question"].strip(), "measure": mname, "by": by})
    area["examples"] = [t["question"] for t in tests[:3]]
    return area_name, area, problems, tests


# ── 3. testing on a copy of the pack ─────────────────────────────────────────
def candidate_pack(d: Draft, area_name: str, area: dict) -> dict:
    merged = yaml.safe_load(d.pack_path.read_text(encoding="utf-8"))
    merged["tables"][d.alias] = {"name": f"{d.schema}.{d.name}"}
    merged["joins"] += d.joins
    merged["areas"][area_name] = area
    Pack.model_validate(merged)
    return merged


def run_checks(d: Draft, merged: dict, area_name: str, tests: list[dict], settings) -> tuple[list[str], list[dict]]:
    pack = Pack.model_validate(merged)
    out, results = [], []
    ex = make_executor(pack, settings.query_timeout_s)
    by = d.dims[0] if d.dims else None
    for mname, md in pack.areas[area_name].metrics.items():
        for group in ([[]] + ([[by]] if by else [])):
            plan = Plan(area=area_name, metrics=[mname], group_by=group, sort=Sort(metric=mname) if group else None)
            try:
                rr = execute(plan, pack, ex, 5)
                first = rr.rows[0] if rr.rows else None
                shown = f"{first[-1]:,}" if first and isinstance(first[-1], (int, float)) else (
                    str(first[-1]) if first else "no rows")
                out.append(f"- {md.label}{' by ' + by if group else ''}: {shown}"
                                f"{' (highest: ' + str(first[0]) + ')' if group and first else ''}")
            except Exception as e:  # noqa: BLE001 - a failing measure is reported, never merged silently
                out.append(f"- {md.label}{' by ' + by if group else ''}: FAILED - {e}")
    tmp = Path(tempfile.mkdtemp(prefix="datachat-addtable-"))
    try:
        shutil.copytree(ENGINE_ROOT / "packs" / "_lexicon", tmp / "_lexicon")
        (tmp / d.client).mkdir()
        (tmp / d.client / "semantic.yaml").write_text(yaml.safe_dump(merged, sort_keys=False, allow_unicode=True),
                                                      encoding="utf-8")
        svc = ChatService(replace(settings, packs_dir=tmp, data_dir=tmp / "data", llm_enabled=False))
        svc.warm_up()
        for i, t in enumerate(tests):
            r = svc.chat(ChatRequest(client_id=d.client, user_id="add-table", conversation_id=f"t{i}",
                                     message=t["question"]))
            ok = r.type == "answer" and r.plan is not None and r.plan.get("area") == area_name
            results.append({**t, "ok": ok, "type": r.type, "text": r.text})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out, results


# ── 5. merging without losing comments ───────────────────────────────────────
def insert_in_section(text: str, section: str, block: str) -> str:
    lines = text.split("\n")
    start = next((i for i, ln in enumerate(lines) if re.match(rf"^{section}:\s*$", ln)), None)
    if start is None:
        return text.rstrip("\n") + f"\n\n{section}:\n{block}\n"
    j = start + 1
    while j < len(lines) and (lines[j].startswith((" ", "\t")) or not lines[j].strip()):
        j += 1
    while j > start + 1 and not lines[j - 1].strip():
        j -= 1
    return "\n".join(lines[:j] + block.split("\n") + lines[j:])


def merge(d: Draft, area_name: str, area: dict, problems: list[str], tests: list[dict]) -> list[str]:
    text = d.pack_path.read_text(encoding="utf-8")
    text = insert_in_section(text, "tables", f"  {d.alias}: {{ name: {d.schema}.{d.name} }}")
    text = insert_in_section(text, "joins", "\n".join(
        f"  - {{ from: {j['from']}, to: {j['to']}, columns: [[{j['columns'][0][0]}, {j['columns'][0][1]}]] }}"
        for j in d.joins)) if d.joins else text
    body = yaml.safe_dump({area_name: area}, sort_keys=False, allow_unicode=True, width=110)
    note = [f"  # Added {date.today():%d %b %Y} with tools/add_table.py from {d.schema}.{d.name} ({d.rows:,} rows)."]
    note += [f"  # CHECK: {p}" for p in problems]
    text = insert_in_section(text, "areas", "\n" + "\n".join(note) + "\n" +
                             "\n".join("  " + ln if ln else ln for ln in body.rstrip("\n").split("\n")))
    Pack.model_validate(yaml.safe_load(text))
    d.pack_path.write_text(text, encoding="utf-8")

    scen = ENGINE_ROOT / "scenarios" / f"{d.client}.yaml"
    added = []
    if scen.exists() and tests:
        existing = set(re.findall(r"id:\s*([A-Za-z0-9_]+)", scen.read_text(encoding="utf-8")))
        prefix = re.sub(r"[^A-Z]", "", area_name.upper())[:2] or "X"
        n, rows = 1, [f"\n  # -- {area['label']} (added by tools/add_table.py) --"]
        for t in tests:
            while f"{prefix}{n:02d}" in existing:
                n += 1
            sid = f"{prefix}{n:02d}"
            existing.add(sid)
            expect = {"type": "answer", "area": area_name, "metrics": [t["measure"]]}
            if t["by"]:
                expect["group_by"] = [t["by"]]
            model = "" if t.get("ok") else "needs_model: true, "
            rows.append(f"  - {{ id: {sid}, group: {json.dumps(area['label'])}, {model}"
                        f"ask: {json.dumps(t['question'])}, expect: {json.dumps(expect)} }}")
            added.append(sid)
        scen.write_text(scen.read_text(encoding="utf-8").rstrip("\n") + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return added


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--client", required=True)
    ap.add_argument("--table", required=True, help="schema.table, e.g. public.smtbtsociety")
    ap.add_argument("--alias", default=None, help="short name for the table (default: table name)")
    ap.add_argument("--yes", action="store_true", help="approve without asking (only after reading the review)")
    ap.add_argument("--review-only", action="store_true", help="write the review and stop; change nothing")
    args = ap.parse_args()
    settings = load_settings()

    print(f"1/4 Profiling {args.table} ...", flush=True)
    d = build(args.client, args.table, args.alias)
    print("2/4 Asking the local model for business wording (can take a few minutes on CPU) ...", flush=True)
    m, warn = ask_model(d, settings)
    if m is None:
        prop = plain_proposal(d)
        area_name, area = d.alias, prop["areas"][d.alias]
        problems, tests, open_q = [warn], [], []
    else:
        area_name, area, problems, tests = build_area(d, m)
        open_q = m.get("open_questions", [])
    merged = candidate_pack(d, area_name, area)
    print("3/4 Testing measures and questions against the database ...", flush=True)
    figures, results = run_checks(d, merged, area_name, tests, settings)
    failed = any("FAILED" in f for f in figures)

    review = [f"# Review: add `{d.schema}.{d.name}` to {args.client} as area `{area_name}`", "",
              "## What will be added", "", "```yaml",
              yaml.safe_dump({"areas": {area_name: area}}, sort_keys=False, allow_unicode=True, width=110).rstrip(),
              "```", "", f"Joins: " + (", ".join(f"{j['columns'][0][0]} → {j['to']}" for j in d.joins) or "none"),
              "", "## Figures from the database", ""] + figures
    review += ["", "## Test questions (built-in rules; the model is tested on the server)", ""]
    review += [f"- {'PASS' if r['ok'] else 'CHECK'}: \"{r['question']}\" → {r['text']}" for r in results] or ["- none"]
    review += ["", "## Please confirm", ""] + [f"- {p}" for p in problems + open_q] + [f"- {c}" for c in CHECKLIST]
    review += ["", "## Data profile", ""] + report_lines(d)
    out = ENGINE_ROOT / "packs" / args.client / "draft"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"review-{d.name}.md"
    path.write_text("\n".join(review) + "\n", encoding="utf-8")

    print("4/4 Review\n")
    print("\n".join(review[: review.index("## Data profile")]))
    print(f"\nFull review with the data profile: {path}")
    if failed:
        sys.exit("A measure failed against the database, so nothing was added. See the review.")
    if m is None:
        sys.exit("Nothing was added because the wording is still TODO. Start Ollama and rerun.")
    if args.review_only:
        return
    if not args.yes and input("\nAdd this to the pack? Type yes to approve: ").strip().lower() != "yes":
        sys.exit("Not added. Edit nothing by hand; rerun this command after deciding the open points.")
    added = merge(d, area_name, area, problems, results)
    print(f"\nAdded area '{area_name}' to {d.pack_path}" + (f" and scenarios {', '.join(added)}" if added else ""))
    print(f"Next: on the server, grant access with  GRANT SELECT ON {d.schema}.{d.name} TO <read-only login>;")


if __name__ == "__main__":
    main()
