"""
What went wrong over the last days, from the engine's own log (never the client's data): questions it could
not answer, queries that failed, answers users marked wrong, times the model did not respond, slow answers.
For each it shows how the question was read (the model's statement and the plan), so a fix can be chosen:
a synonym or example in semantic.yaml, a new measure, or a prompt change.
"""
import json
from collections import Counter
from datetime import datetime, timedelta, timezone

from datachat.learning import LearningStore

SLOW_MS = 20000


def _plan_text(plan_json: str | None) -> str:
    if not plan_json:
        return ""
    p = json.loads(plan_json)
    parts = [f"area={p.get('area')}", "measure=" + ",".join(p.get("metrics", []))]
    if p.get("group_by"):
        parts.append("by=" + ",".join(p["group_by"]))
    if p.get("filters"):
        parts.append("filter=" + "; ".join(f"{f['dimension']}{' not' if f.get('negate') else ''} in "
                                           f"{','.join(f['values'][:3])}" for f in p["filters"]))
    if p.get("time"):
        parts.append(f"time={p['time'].get('label')}")
    if p.get("compare"):
        parts.append(f"vs={p['compare'].get('label')}")
    for k in ("share", "detail"):
        if p.get(k):
            parts.append(k)
    return " | ".join(parts)


def build_report(store: LearningStore, client: str, days: int = 7) -> dict:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")
    data = store.report_rows(client, since)
    qs, fb = data["queries"], data["feedback"]

    def item(q: dict, why: str) -> dict:
        f = fb.get(q["id"]) or {}
        return {"id": q["id"], "when": q["created_at"][:16].replace("T", " "), "user": q["user_id"],
                "question": q["question"], "why": why, "reply": (q["message"] or "")[:300],
                "model_read": q.get("trace") or "", "plan": _plan_text(q["plan_json"]),
                "source": q["source"], "seconds": round((q["elapsed_ms"] or 0) / 1000, 1),
                "comment": f.get("comment") or ""}

    groups = {
        "rated_wrong": [item(q, "user marked the answer wrong") for q in qs if (fb.get(q["id"]) or {}).get("rating") == -1],
        "not_answered": [item(q, "could not answer") for q in qs if q["status"] == "unsupported"],
        "failed": [item(q, "query failed") for q in qs if q["status"] == "error"],
        "model_missing": [item(q, "model did not respond; backup rules used") for q in qs
                          if q["source"] == "rules" and q["status"] == "answer"],
        "slow": [item(q, f"took over {SLOW_MS // 1000}s") for q in qs if (q["elapsed_ms"] or 0) > SLOW_MS],
    }
    # a clarifying question nobody answered in that conversation usually means the options didn't fit
    answered_after = {}
    for q in qs:
        if q["status"] == "answer":
            answered_after[q["conversation_id"]] = q["id"]
    groups["clarify_dropped"] = [item(q, "asked to clarify, user gave up") for q in qs
                                 if q["status"] == "clarify" and answered_after.get(q["conversation_id"], 0) < q["id"]]

    times = sorted(q["elapsed_ms"] or 0 for q in qs if q["status"] == "answer")
    repeated = Counter(" ".join(q["question"].lower().split()) for q in qs if q["status"] in ("unsupported", "error"))
    summary = {
        "days": days, "since": since[:10], "questions": len(qs), "users": len({q["user_id"] for q in qs}),
        "answered": sum(q["status"] == "answer" for q in qs),
        "rated_right": sum(1 for f in fb.values() if f["rating"] == 1),
        "rated_wrong": len(groups["rated_wrong"]),
        "median_seconds": round(times[len(times) // 2] / 1000, 1) if times else None,
        "p95_seconds": round(times[min(len(times) - 1, int(len(times) * 0.95))] / 1000, 1) if times else None,
        "by_source": dict(Counter(q["source"] or "-" for q in qs)),
        "repeated_failures": [{"question": k, "times": n} for k, n in repeated.most_common(10) if n > 1],
    }
    return {"client": client, "summary": summary, "groups": groups}


TITLES = {
    "rated_wrong": "Answers users marked wrong",
    "not_answered": "Questions it could not answer",
    "failed": "Queries that failed",
    "clarify_dropped": "Clarifying questions left unanswered",
    "model_missing": "Answered by the backup rules because the model did not respond",
    "slow": "Slow answers",
}
HINTS = {
    "rated_wrong": "Compare 'Read as' with what the user meant. Wrong measure or grouping: add a synonym or an "
                   "llm_example in semantic.yaml. Wrong figure with the right reading: check the measure's SQL.",
    "not_answered": "If the data has it, add the missing word as a synonym or add the measure; if it doesn't, add it "
                    "to not_available so the reply says why.",
    "failed": "Usually a missing GRANT (run tools/check_access.py) or a timeout on a large table.",
    "clarify_dropped": "The offered choices did not fit; add the word users meant as a synonym.",
    "model_missing": "Check that the DataChat-Ollama task is running and see data/logs/ollama.log.",
    "slow": "Usually the model was busy with other questions, or a large table needs an index.",
}


def report_markdown(r: dict) -> str:
    s = r["summary"]
    rate = f"{s['answered'] / s['questions']:.0%}" if s["questions"] else "-"
    out = [f"# DataChat report for {r['client']}: last {s['days']} days (since {s['since']})", "",
           f"- Questions: {s['questions']} from {s['users']} users; answered {s['answered']} ({rate})",
           f"- Rated right: {s['rated_right']}, rated wrong: {s['rated_wrong']}",
           f"- Answer time: median {s['median_seconds']}s, 95% within {s['p95_seconds']}s",
           "- Read by: " + ", ".join(f"{k} {v}" for k, v in s["by_source"].items())]
    if s["repeated_failures"]:
        out += ["", "## Asked more than once and not answered", ""]
        out += [f"- \"{x['question']}\" ({x['times']} times)" for x in s["repeated_failures"]]
    for key, title in TITLES.items():
        items = r["groups"][key]
        if not items:
            continue
        out += ["", f"## {title} ({len(items)})", "", f"_{HINTS[key]}_", ""]
        for i in items[:50]:
            out.append(f"- **\"{i['question']}\"** ({i['when']}, {i['user']}, {i['seconds']}s)")
            if i["model_read"]:
                out.append(f"  - Model read: `{i['model_read']}`")
            if i["plan"]:
                out.append(f"  - Read as: {i['plan']}")
            out.append(f"  - Reply: {i['reply']}")
            if i["comment"]:
                out.append(f"  - User comment: {i['comment']}")
        if len(items) > 50:
            out.append(f"- ... and {len(items) - 50} more")
    if not any(r["groups"].values()):
        out += ["", "Nothing went wrong in this period."]
    return "\n".join(out) + "\n"
