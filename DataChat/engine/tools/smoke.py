"""
Ask questions end to end against a client's real database and print what happens.
Usage (from the engine folder):
    .venv\\Scripts\\python tools\\smoke.py <client>                  # the pack's example questions
    .venv\\Scripts\\python tools\\smoke.py <client> "question" ...   # your own questions
"""
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datachat.config import load_settings  # noqa: E402
from datachat.service import ChatRequest, ChatService  # noqa: E402


def main() -> None:
    client = sys.argv[1] if len(sys.argv) > 1 else "bellona_rista"
    svc = ChatService(load_settings())
    questions = sys.argv[2:] or [q for a in svc.runtimes[client].pack.areas.values() for q in a.examples]
    t = time.perf_counter()
    counts = svc.refresh_values(client)
    print(f"Loaded values in {time.perf_counter() - t:.1f}s: {counts}\n")
    for q in questions:
        r = svc.chat(ChatRequest(client_id=client, user_id="smoke", conversation_id=uuid.uuid4().hex, message=q))
        print(f"Q: {q}\n   [{r.type}, {r.elapsed_ms} ms] {r.text}")
        if r.type == "error" and r.sql:
            print("   sql:", r.sql.replace("\n", " "))
        for a in r.assumptions:
            print(f"   note: {a}")
        if r.options:
            print("   options:", [o.label for o in r.options])
        if r.rows:
            print("   first rows:", r.rows[:3])
        print()


if __name__ == "__main__":
    main()
