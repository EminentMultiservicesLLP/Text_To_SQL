"""
Check that the engine's database login can read every table its packs use, and print the GRANT lines for
any it can't. Run on the server after an update:  .venv\\Scripts\\python tools\\check_access.py
Exit code 1 when something is missing.
"""
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ENGINE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ENGINE_ROOT))
from datachat.pack import load_packs  # noqa: E402


def main() -> int:
    load_dotenv(ENGINE_ROOT / ".env")
    missing_all = 0
    for client, pack in load_packs(ENGINE_ROOT / "packs").items():
        if pack.database.dialect != "postgres":
            continue
        dsn = os.getenv(pack.database.dsn_env)
        if not dsn:
            print(f"[{client}] {pack.database.dsn_env} is not set in .env")
            missing_all += 1
            continue
        with psycopg.connect(dsn, connect_timeout=10) as conn:
            user = conn.execute("SELECT current_user").fetchone()[0]
            missing = []
            for t in sorted({t.name for t in pack.tables.values()}):
                ok = conn.execute("SELECT to_regclass(%s) IS NOT NULL AND has_table_privilege(%s, %s, 'SELECT')",
                                  (t, user, t)).fetchone()[0]
                if not ok:
                    missing.append(t)
        if missing:
            missing_all += len(missing)
            print(f"[{client}] login '{user}' cannot read {len(missing)} table(s). As the database owner run:")
            for t in missing:
                print(f"    GRANT SELECT ON {t} TO {user};")
        else:
            print(f"[{client}] login '{user}' can read all {len(pack.tables)} tables.")
    return 1 if missing_all else 0


if __name__ == "__main__":
    sys.exit(main())
