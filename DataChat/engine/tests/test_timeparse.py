from datetime import date

import pytest

from conftest import TODAY
from datachat.timeparse import extract_time


def rng(text):
    tx = extract_time(text, TODAY)
    assert len(tx.ranges) == 1, f"{text!r} -> {tx.ranges}"
    return tx.ranges[0].start, tx.ranges[0].end


@pytest.mark.parametrize("text,start,end", [
    ("sales today", date(2026, 9, 30), date(2026, 10, 1)),
    ("yesterday", date(2026, 9, 29), date(2026, 9, 30)),
    ("day before yesterday", date(2026, 9, 28), date(2026, 9, 29)),
    ("last month", date(2026, 8, 1), date(2026, 9, 1)),
    ("this month", date(2026, 9, 1), date(2026, 10, 1)),
    ("this week", date(2026, 9, 28), date(2026, 10, 5)),
    ("last week", date(2026, 9, 21), date(2026, 9, 28)),
    ("last year", date(2025, 1, 1), date(2026, 1, 1)),
    ("october last year", date(2025, 10, 1), date(2025, 11, 1)),
    ("october", date(2025, 10, 1), date(2025, 11, 1)),
    ("august", date(2026, 8, 1), date(2026, 9, 1)),
    ("oct 2024", date(2024, 10, 1), date(2024, 11, 1)),
    ("q1 last year", date(2025, 1, 1), date(2025, 4, 1)),
    ("last quarter", date(2026, 4, 1), date(2026, 7, 1)),
    ("last 7 days", date(2026, 9, 24), date(2026, 10, 1)),
    ("between 01/09/2026 and 15/09/2026", date(2026, 9, 1), date(2026, 9, 16)),
    ("on 2026-09-05", date(2026, 9, 5), date(2026, 9, 6)),
    ("5 sep 2026", date(2026, 9, 5), date(2026, 9, 6)),
    ("this financial year", date(2026, 4, 1), date(2027, 4, 1)),
    ("last fy", date(2025, 4, 1), date(2026, 4, 1)),
    ("fy 2025-26", date(2025, 4, 1), date(2026, 4, 1)),
    ("fy26", date(2025, 4, 1), date(2026, 4, 1)),
    ("in 2024", date(2024, 1, 1), date(2025, 1, 1)),
    ("mtd", date(2026, 9, 1), date(2026, 10, 1)),
])
def test_ranges(text, start, end):
    assert rng(text) == (start, end)


@pytest.mark.parametrize("text,grain", [
    ("hourly sales", "hour"), ("sales per day", "day"), ("day wise sales", "day"),
    ("monthly revenue", "month"), ("sales by weekday", "weekday"), ("year on year", "year"),
])
def test_grains(text, grain):
    assert extract_time(text, TODAY).grain == grain


def test_may_as_a_verb_is_not_a_month():
    assert extract_time("may i see sales", TODAY).ranges == []


def test_two_ranges_are_both_found():
    tx = extract_time("this year vs last year", TODAY)
    assert [r.start.year for r in tx.ranges] == [2026, 2025]


def test_impossible_date_is_left_in_text():
    tx = extract_time("sales on 31/02/2026", TODAY)
    assert tx.ranges == [] and "31/02/2026" in tx.text
