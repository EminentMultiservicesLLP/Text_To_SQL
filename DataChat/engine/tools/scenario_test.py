"""
Runs a client's business scenarios (scenarios/<client>.yaml) end to end against the real database and checks
each reading and answer. Writes a report to scenarios/reports/<client>-<mode>.md.
Usage (from the engine folder):
    .venv\\Scripts\\python tools\\scenario_test.py bis                 # model as configured in .env
    .venv\\Scripts\\python tools\\scenario_test.py bis --rules         # built-in rules only
    .venv\\Scripts\\python tools\\scenario_test.py bis --llm-mode primary   # the model reads every question
    .venv\\Scripts\\python tools\\scenario_test.py bis --only A01,H02  # some scenarios
    .venv\\Scripts\\python tools\\scenario_test.py bis --group "Compare periods"
Exit code is 1 when any scenario fails.
"""
import argparse
import sys
import tempfile
import time
import uuid
from dataclasses import replace
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from datachat.config import load_settings  # noqa: E402
from datachat.service import ChatRequest, ChatResponse, ChatService  # noqa: E402


def _list(v) -> list:
    return v if isinstance(v, list) else [v]


def check(expect: dict, r: ChatResponse) -> list[str]:
    """What is wrong with the response; empty when it meets every expectation."""
    bad = []
    p = r.plan or {}
    if "type" in expect and r.type not in _list(expect["type"]):
        bad.append(f"type is {r.type}, expected {expect['type']}")
        return bad
    if "area" in expect and p.get("area") not in _list(expect["area"]):
        bad.append(f"area is {p.get('area')}, expected {expect['area']}")
    for key in ("metrics", "more", "derived"):
        field = {"more": "more_metrics"}.get(key, key)
        missing = [m for m in expect.get(key, []) if m not in (p.get(field) or [])]
        if missing:
            bad.append(f"{key} {p.get(field)} lacks {missing}")
    if "group_by" in expect:
        dims = [g for g in p.get("group_by") or [] if not g.startswith("time:")]
        if sorted(dims) != sorted(expect["group_by"]):
            bad.append(f"split by {dims}, expected {expect['group_by']}")
    if "grain" in expect:
        grains = [g[5:] for g in p.get("group_by") or [] if g.startswith("time:")]
        if expect["grain"] not in grains:
            bad.append(f"time grain {grains}, expected {expect['grain']}")
    for key, negate in (("filters", False), ("exclude", True)):
        for dim, text in (expect.get(key) or {}).items():
            values = [v for f in p.get("filters") or [] if f["dimension"] == dim and f["negate"] == negate
                      for v in f["values"]]
            if not any(str(text).lower() in v.lower() for v in values):
                bad.append(f"{key} on {dim} is {values}, expected one containing '{text}'")
    for key in ("period", "compare"):
        if key in expect:
            rng = p.get("time" if key == "period" else "compare")
            label = rng["label"] if rng else None
            if not label or str(expect[key]).lower() not in label.lower():
                bad.append(f"{key} is {label!r}, expected '{expect[key]}'")
    if expect.get("no_filters") and p.get("filters"):
        bad.append(f"filters {p['filters']}, expected none (a name the user never wrote)")
    if expect.get("no_period") and p.get("time"):
        bad.append(f"period should be dropped, got {p['time']['label']!r}")
    if "having" in expect:
        ops = [h["op"] for h in p.get("having") or []]
        if expect["having"] not in ops:
            bad.append(f"condition {ops}, expected {expect['having']}")
    if "sort" in expect:
        s = p.get("sort")
        got = None if not s else ("desc" if s["desc"] else "asc")
        if got != expect["sort"]:
            bad.append(f"sort {got}, expected {expect['sort']}")
    if "limit" in expect and p.get("limit") != expect["limit"]:
        bad.append(f"limit {p.get('limit')}, expected {expect['limit']}")
    for key in ("share", "detail"):
        if key in expect and bool(p.get(key)) != expect[key]:
            bad.append(f"{key} is {bool(p.get(key))}, expected {expect[key]}")
    for t in expect.get("text", []):
        if t.lower() not in r.text.lower():
            bad.append(f"answer lacks '{t}'")
    notes = " ".join(r.assumptions).lower()
    for t in expect.get("notes", []):
        if t.lower() not in notes:
            bad.append(f"notes lack '{t}'")
    if "options" in expect and not any(expect["options"].lower() in o.label.lower() for o in r.options):
        bad.append(f"options {[o.label for o in r.options]} lack '{expect['options']}'")
    for t in expect.get("sql_excludes", []):
        if r.sql and t.lower() in r.sql.lower():
            bad.append(f"SQL contains '{t}'")
    if "min_rows" in expect and r.row_count < expect["min_rows"]:
        bad.append(f"{r.row_count} rows, expected at least {expect['min_rows']}")
    return bad


def run_scenario(svc: ChatService, client: str, sc: dict) -> tuple[ChatResponse, list[str], float]:
    conv = uuid.uuid4().hex
    user = f"scenario-{sc['id']}"
    started = time.perf_counter()
    r = None
    last_q = ""
    for step in _list(sc["ask"]):
        if isinstance(step, dict) and "choose" in step:
            opt = next((o for o in (r.options if r else []) if step["choose"].lower() in o.label.lower()), None)
            if opt is None:
                return r, [f"no option containing '{step['choose']}' in {[o.label for o in r.options]}"], \
                    time.perf_counter() - started
            r = svc.chat(ChatRequest(client_id=client, user_id=user, conversation_id=conv, message=last_q,
                                     overrides=opt.overrides))
            continue
        last_q = step
        r = svc.chat(ChatRequest(client_id=client, user_id=user, conversation_id=conv, message=step))
    return r, check(sc.get("expect") or {}, r), time.perf_counter() - started


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("client")
    ap.add_argument("--rules", action="store_true", help="built-in rules only, no language model")
    ap.add_argument("--only", help="comma-separated scenario ids")
    ap.add_argument("--group", help="only this group")
    ap.add_argument("--today", help="override the catalogue's date (YYYY-MM-DD)")
    ap.add_argument("--llm-mode", choices=["fallback", "primary"],
                    help="override DATACHAT_LLM_MODE (primary = the model reads every question)")
    args = ap.parse_args()

    spec = yaml.safe_load((ROOT / "scenarios" / f"{args.client}.yaml").read_text(encoding="utf-8"))
    today = date.fromisoformat(str(args.today or spec.get("today") or date.today()))
    scenarios = spec["scenarios"]
    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        scenarios = [s for s in scenarios if s["id"] in wanted]
    if args.group:
        scenarios = [s for s in scenarios if s.get("group", "").lower() == args.group.lower()]
    if args.rules:
        scenarios = [s for s in scenarios if not s.get("needs_model")]

    settings = load_settings()
    settings = replace(settings, data_dir=Path(tempfile.mkdtemp(prefix="datachat-scenarios-")),
                       llm_enabled=settings.llm_enabled and not args.rules,
                       llm_mode=args.llm_mode or settings.llm_mode)
    mode = f"llm-{settings.llm_mode}" if settings.llm_enabled else "rules"
    svc = ChatService(settings, today=lambda: today)
    print(f"{len(scenarios)} scenarios for {args.client}, mode={mode}, today={today}. Warming up...", flush=True)
    svc.warm_up()

    results = []
    for sc in scenarios:
        r, bad, secs = run_scenario(svc, args.client, sc)
        results.append((sc, r, bad, secs))
        mark = "PASS" if not bad else "FAIL"
        q = " -> ".join(s if isinstance(s, str) else f"[{s.get('choose')}]" for s in _list(sc["ask"]))
        print(f"{mark} {sc['id']:4} {secs:5.1f}s  {q}", flush=True)
        if bad:
            print(f"      {r.type if r else '-'}: {(r.text if r else '')[:160]}")
            for b in bad:
                print(f"      - {b}")

    passed = sum(1 for *_, bad, _ in results if not bad)
    print(f"\n{passed}/{len(results)} passed ({mode}).")
    write_report(args.client, mode, today, results)
    return 0 if passed == len(results) else 1


def write_report(client: str, mode: str, today: date, results) -> None:
    out = ROOT / "scenarios" / "reports" / f"{client}-{mode}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    passed = sum(1 for *_, bad, _ in results if not bad)
    lines = [f"# Scenario results: {client} ({mode})", "",
             f"{passed}/{len(results)} passed. Date used as today: {today}.", "",
             "| Id | Group | Question | Result | Seconds | Reading / problem |", "|---|---|---|---|---|---|"]
    for sc, r, bad, secs in results:
        q = " → ".join(s if isinstance(s, str) else f"[{s.get('choose')}]" for s in _list(sc["ask"]))
        reading = next((a for a in (r.assumptions if r else []) if a.startswith("Understood as")), "")
        detail = "; ".join(bad) if bad else (reading or (r.text[:120] if r else ""))
        lines.append(f"| {sc['id']} | {sc.get('group', '')} | {q} | {'PASS' if not bad else '**FAIL**'} | "
                     f"{secs:.1f} | {detail.replace('|', '/')} |")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report: {out}")


if __name__ == "__main__":
    sys.exit(main())
