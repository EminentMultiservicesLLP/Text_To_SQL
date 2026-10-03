"""
Ask every scenario question of a client, then run every follow-up offered under each answer, and report any
follow-up that does not come back as an answer. Built-in rules only, so it needs the database but no model.
    .venv\\Scripts\\python tools\\followup_check.py bis
"""
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from datachat.config import load_settings  # noqa: E402
from datachat.service import ChatRequest, ChatService  # noqa: E402


def main() -> int:
    client = sys.argv[1] if len(sys.argv) > 1 else "bis"
    root = Path(__file__).resolve().parent.parent
    scen = yaml.safe_load((root / "scenarios" / f"{client}.yaml").read_text(encoding="utf-8"))["scenarios"]
    svc = ChatService(replace(load_settings(), llm_enabled=False, data_dir=Path(tempfile.mkdtemp())))
    svc.warm_up()
    asked = offered = bad = 0
    for s in scen:
        if s.get("needs_model") or not isinstance(s["ask"], str):
            continue
        r = svc.chat(ChatRequest(client_id=client, user_id="fu", conversation_id=s["id"], message=s["ask"]))
        if r.type != "answer":
            continue
        asked += 1
        for f in r.follow_ups:
            offered += 1
            fr = svc.chat(ChatRequest(client_id=client, user_id="fu", conversation_id=s["id"], message=f.label,
                                      plan=f.plan))
            if fr.type != "answer":
                bad += 1
                print(f"{s['id']} '{s['ask']}' -> '{f.label}': {fr.type}: {fr.text}")
    print(f"{asked} answers, {offered} follow-ups offered, {bad} did not answer")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
