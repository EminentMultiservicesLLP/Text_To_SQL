"""Questions real BIS users asked, against the BIS pack with a few sample names (no database needed)."""
from datetime import date

import pytest
from conftest import PACKS, TODAY

from datachat import timeparse
from datachat.pack import load_pack
from datachat.parser import Parser

BIS_VALUES = {
    "branch": ["LUCKNOW BRANCH", "PUNE BRANCH", "PUNE", "SCS MUMBAI", "MUMBAI REGIONAL OFFICE", "THANE BRANCH"],
    "city": ["Mumbai", "Lucknow", "Mayurbhanj"],
    "customer": ["AMITY UNIVERSITY LUCKNOW", "PAI KANE TRANSFORMERS LLP", "DEEPKALA COLLECTION"],
    "designation": ["COLLECTION BOY", "SECURITY GUARD"],
}


@pytest.fixture()
def bis(lexicon):
    return Parser(load_pack(PACKS / "bis" / "semantic.yaml"), lexicon, BIS_VALUES)


def test_polite_question_with_month_of_last_year(bis):
    res = bis.parse("may i know the collection of lucknow branch for last year Dec month", TODAY)
    p = res.plan
    assert p is not None, res.clarify
    assert (p.area, p.metrics, p.group_by) == ("receipts", ["receipt_amount"], [])
    assert (p.time.start, p.time.end) == (date(2025, 12, 1), date(2026, 1, 1))
    assert [(f.dimension, f.values) for f in p.filters] == [("branch", ["LUCKNOW BRANCH"])]


def test_verb_form_of_measure_word(bis):
    res = bis.parse("recovery collected by thane branch for June 2026", TODAY)
    assert res.plan is not None, res.clarify
    assert res.plan.metrics == ["receipt_amount"]
    assert [(f.dimension, f.values) for f in res.plan.filters] == [("branch", ["THANE BRANCH"])]


def test_name_before_field_word_offers_matching_values(bis):
    res = bis.parse("recovery collected by Mumbai branch for June 2026", TODAY)
    labels = [o.label for o in res.clarify.options]
    assert labels == ["MUMBAI REGIONAL OFFICE (Branch)", "SCS MUMBAI (Branch)", "Mumbai (City)"]
    chosen = res.clarify.options[1].overrides
    p = bis.parse("recovery collected by Mumbai branch for June 2026", TODAY, overrides=chosen).plan
    assert [(f.dimension, f.values) for f in p.filters] == [("branch", ["SCS MUMBAI"])]
    assert p.group_by == []


def test_unknown_word_options_come_from_the_chosen_data_only(bis):
    res = bis.parse("collection zzcollectio last month", TODAY)
    labels = [o.label for o in res.clarify.options]
    assert "COLLECTION BOY (Designation)" not in labels  # employees data cannot answer a receipts question
    assert labels[-1] == "Ignore this word"


def test_short_unknown_word_is_asked_without_lookalike_names(bis):
    res = bis.parse("billing xyz last month", TODAY)
    assert res.clarify.kind == "unknown_word"
    assert [o.label for o in res.clarify.options] == ["Ignore this word"]


def test_follow_up_keeps_the_data_of_the_previous_question(bis):
    first = bis.parse("collection of lucknow branch last month", TODAY).plan
    p = bis.parse("what about pune branch", TODAY, previous=first).plan
    assert p.area == "receipts" and [(f.dimension, f.values) for f in p.filters] == [("branch", ["PUNE BRANCH"])]


@pytest.mark.parametrize("q,op,value,value2", [
    ("can you tell my which all branches earns more than 2cr in last month", "gt", 2e7, None),
    ("can you tell me which all branch billing is more than 2 crore in last 3 month", "gt", 2e7, None),
    ("branches with billing above 2.5 crore in july 2026", "gt", 2.5e7, None),
    ("branch billing > 5 cr this financial year", "gt", 5e7, None),
    ("branch billing at least 50 lakh last quarter", "ge", 5e6, None),
    ("branch billing less than 10 lakh last quarter", "lt", 1e6, None),
    ("branches with billing between 1 and 2 crore in july 2026", "between", 1e7, 2e7),
    ("july 2026 madhe 50 lakh peksha jast billing asnare branch", "gt", 5e6, None),
    ("pichhle mahine 2 crore se zyada billing wali branch", "gt", 2e7, None),
    ("branch billing ₹2,00,00,000 or more in july 2026", "ge", 2e7, None),
])
def test_threshold_on_totals(bis, q, op, value, value2):
    res = bis.parse(q, TODAY)
    assert res.plan is not None, (res.clarify, res.unknown)
    p = res.plan
    assert p.group_by == ["branch"] and p.metrics == ["billing_amount"]
    assert [(h.metric, h.op, h.value, h.value2) for h in p.having] == [("billing_amount", op, value, value2)]


def test_threshold_on_a_count_uses_that_measure(bis):
    p = bis.parse("customers with more than 100 invoices in july 2026", TODAY).plan
    assert (p.group_by, p.metrics) == (["customer"], ["invoice_count"])
    assert [(h.metric, h.op, h.value) for h in p.having] == [("invoice_count", "gt", 100)]


def test_threshold_compiles_to_having_on_the_expression(bis):
    from datachat.compiler import compile_plan
    p = bis.parse("which branches earn more than 2 crore this financial year", TODAY).plan
    sql = compile_plan(p, bis.pack, 500).sql
    assert 'HAVING SUM("bill"."billing_amount") > 20000000' in sql
    assert sql.index("GROUP BY") < sql.index("HAVING") < sql.index("ORDER BY")


@pytest.mark.parametrize("text,start,end", [
    ("last year dec", date(2025, 12, 1), date(2026, 1, 1)),
    ("2025 march", date(2025, 3, 1), date(2025, 4, 1)),
    ("december last year", date(2025, 12, 1), date(2026, 1, 1)),
    ("this year dec", date(2026, 12, 1), date(2027, 1, 1)),
    ("jan of this financial year", date(2027, 1, 1), date(2027, 2, 1)),
])
def test_month_inside_year_is_the_month(text, start, end):
    tx = timeparse.extract_time(text, TODAY)
    assert [(r.start, r.end) for r in tx.ranges] == [(start, end)]


def test_month_word_after_a_month_is_not_a_grouping():
    tx = timeparse.extract_time("sales for dec month", TODAY)
    assert "month" not in tx.text.split()
    assert timeparse.extract_time("sales 2025 month wise", TODAY).grain == "month"
