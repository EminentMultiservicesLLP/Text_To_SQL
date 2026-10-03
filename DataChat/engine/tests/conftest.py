import re
import sys
from datetime import date
from pathlib import Path

import pytest

ENGINE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ENGINE_ROOT))

from datachat.config import Settings  # noqa: E402
from datachat.executor import Executor, QueryResult  # noqa: E402
from datachat.pack import load_lexicon, load_pack  # noqa: E402
from datachat.parser import Parser  # noqa: E402

TODAY = date(2026, 9, 30)  # a Wednesday
PACKS = ENGINE_ROOT / "packs"

VALUES = {
    "branch": ["PUNE001", "PUNE002", "PUNE003", "MUM001", "DEL001"],
    "channel": ["Swiggy", "Zomato", "POS"],
    "source": ["Swiggy", "Zomato"],
    "delivery_mode": ["Delivery", "DineIn", "TakeAway"],
    "category": ["Beverages", "Starters", "Main Course"],
    "payment_mode": ["Cash", "Card", "UPI"],
    "item": ["Paneer Tikka", "Masala Dosa", "Cold Coffee"],
}
_DISTINCT_COLUMNS = {
    "branchCode": "branch", "Channel": "channel", "Source": "source", "DeliveryMode": "delivery_mode",
    "CategoryName": "category", "Mode": "payment_mode", "LongName": "item",
}


@pytest.fixture(scope="session")
def pack():
    return load_pack(PACKS / "bellona_rista" / "semantic.yaml")


@pytest.fixture(scope="session")
def lexicon():
    return load_lexicon(PACKS)


@pytest.fixture()
def parser(pack, lexicon):
    return Parser(pack, lexicon, VALUES)


class FakeExecutor(Executor):
    """Answers distinct-value queries from VALUES and returns three made-up rows for anything else."""

    def __init__(self):
        self.queries: list[str] = []

    def run(self, sql: str, fetch_limit: int, cap: int) -> QueryResult:
        self.queries.append(sql)
        if "DISTINCT" in sql:
            col = re.search(r"\.\[(\w+)\]", sql)[1]
            return QueryResult([col], [[v] for v in VALUES.get(_DISTINCT_COLUMNS.get(col, ""), [])], False, 1)
        select = sql.split("\nFROM", 1)[0]
        items = re.findall(r"(\S.*?) AS \[(\w+)\]", select)
        cols = [name for _, name in items]
        rows = []
        for i in range(3):
            row = []
            for expr, _ in items:
                is_measure = re.match(r"\s*(SELECT\s+(TOP\s*\(\d+\)\s*)?)?(SUM|COUNT|AVG)\(", expr)
                row.append(1000.0 * (3 - i) if is_measure else f"V{i + 1}")
            rows.append(row)
        return QueryResult(cols, rows[:cap], False, 1)


@pytest.fixture()
def settings(tmp_path):
    return Settings(packs_dir=PACKS, data_dir=tmp_path, api_key="test-key", row_limit=500, query_timeout_s=30,
                    strict_unknown_words=True, promote_min_users=3, llm_enabled=False,
                    ollama_url="http://127.0.0.1:11434", llm_model="qwen3:4b", llm_timeout_s=30, llm_num_thread=0)
