"""
Write the failure report for a client from the engine's log. Run on the server, e.g. every Monday:
    .venv\\Scripts\\python tools\\failure_report.py bis [--days 7] [--scenarios]
Writes reports/<client>-<date>.md. --scenarios also writes reports/<client>-<date>-scenarios.yaml with the
failed questions as scenario stubs: fill in `expect`, then copy them into scenarios/<client>.yaml so the
fix is tested from then on.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from datachat.config import load_settings  # noqa: E402
from datachat.learning import LearningStore  # noqa: E402
from datachat.report import build_report, report_markdown  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("client")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--scenarios", action="store_true", help="also write the failed questions as scenario stubs")
    args = ap.parse_args()
    settings = load_settings()
    store = LearningStore(settings.data_dir / "learning.db", settings.promote_min_users)
    r = build_report(store, args.client, args.days)
    out = Path(__file__).resolve().parent.parent / "reports"
    out.mkdir(exist_ok=True)
    path = out / f"{args.client}-{date.today():%Y-%m-%d}.md"
    path.write_text(report_markdown(r), encoding="utf-8")
    s = r["summary"]
    print(f"{s['questions']} questions, {s['answered']} answered, {s['rated_wrong']} rated wrong, "
          f"{len(r['groups']['not_answered'])} not answered, {len(r['groups']['failed'])} failed. Report: {path}")
    if args.scenarios:
        seen, lines = set(), [f"# Failed questions from {s['since']}: fill in expect, then copy into "
                              f"scenarios/{args.client}.yaml", "scenarios:"]
        for key in ("rated_wrong", "not_answered", "clarify_dropped"):
            for i in r["groups"][key]:
                q = " ".join(i["question"].lower().split())
                if q in seen:
                    continue
                seen.add(q)
                lines.append(f"  - {{ id: F{len(seen):03d}, group: Feedback, ask: {json.dumps(i['question'])}, "
                             f"expect: {{ type: answer }} }}  # {i['why']}; read as: {i['plan'] or i['reply'][:80]}")
        spath = out / f"{args.client}-{date.today():%Y-%m-%d}-scenarios.yaml"
        spath.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{len(seen)} scenario stubs: {spath}")


if __name__ == "__main__":
    main()
