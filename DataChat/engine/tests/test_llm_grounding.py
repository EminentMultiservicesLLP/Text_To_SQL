"""The model's one-line statement is checked against the pack and real values before any SQL is built."""
from datetime import date

import pytest
from conftest import PACKS, TODAY
from test_parser_bis import BIS_VALUES

from datachat.compiler import compile_plan
from datachat.llm import ground
from datachat.pack import load_pack
from datachat.parser import Parser


@pytest.fixture()
def bis(lexicon):
    return Parser(load_pack(PACKS / "bis" / "semantic.yaml"), lexicon, BIS_VALUES)


def statement(**kw):
    base = {"answerable": True, "reason": "", "area": "billing", "metrics": ["billing_amount"], "group_by": [],
            "time_grain": "none", "period": "none", "filters": [],
            "condition": {"op": "none", "number": 0, "number2": 0, "unit": "none"}, "sort": "none", "limit": 0}
    return {**base, **kw}


def run(bis, raw, question="q", overrides=None, learned=None):
    return ground(raw, question, bis.pack, bis, TODAY, overrides or {}, learned or {})


def test_threshold_and_period(bis):
    raw = statement(group_by=["branch"], period="last 3 months", sort="desc",
                    condition={"op": "gt", "number": 2, "number2": 0, "unit": "crore"})
    p = run(bis, raw).plan
    assert (p.group_by, p.time.start, p.time.end) == (["branch"], date(2026, 7, 1), date(2026, 10, 1))
    assert [(h.op, h.value) for h in p.having] == [("gt", 2e7)]
    assert "HAVING" in compile_plan(p, bis.pack, 500).sql


def test_name_is_grounded_to_the_real_value(bis):
    raw = statement(area="receipts", metrics=["receipt_amount"], period="December last year",
                    filters=[{"dimension": "branch", "text": "lucknow", "exclude": False}])
    res = run(bis, raw, "collection of lucknow branch last year december")
    assert [(f.dimension, f.values) for f in res.plan.filters] == [("branch", ["LUCKNOW BRANCH"])]
    assert (res.plan.time.start, res.plan.time.end) == (date(2025, 12, 1), date(2026, 1, 1))
    assert res.assumptions[0].startswith("Understood as: Amount received")


def test_several_matching_names_are_asked_then_the_choice_is_used(bis):
    raw = statement(filters=[{"dimension": "branch", "text": "mumbai", "exclude": False}])
    res = run(bis, raw, "billing of mumbai")
    assert res.plan is None
    labels = [o.label for o in res.clarify.options]
    assert labels[:2] == ["MUMBAI REGIONAL OFFICE (Branch)", "SCS MUMBAI (Branch)"] and labels[-1] == "Ignore this name"
    p = run(bis, raw, "billing of mumbai", overrides=res.clarify.options[1].overrides).plan
    assert [(f.dimension, f.values) for f in p.filters] == [("branch", ["SCS MUMBAI"])]


def test_unknown_name_is_never_guessed(bis):
    res = run(bis, statement(filters=[{"dimension": "customer", "text": "qwertyuiop", "exclude": False}]),
              "billing of qwertyuiop")
    assert res.plan is None and "couldn't find 'qwertyuiop'" in res.clarify.question


def test_name_in_another_field_is_found(bis):
    raw = statement(filters=[{"dimension": "branch", "text": "amity university", "exclude": False}])
    res = run(bis, raw, "billing of amity university")
    assert [(f.dimension, f.values) for f in res.plan.filters] == [("customer", ["AMITY UNIVERSITY LUCKNOW"])]


def test_area_is_corrected_to_where_the_measure_lives(bis):
    p = run(bis, statement(area="billing", metrics=["receipt_amount"])).plan
    assert p.area == "receipts"


def test_grouping_the_area_cannot_do_is_refused(bis):
    res = run(bis, statement(group_by=["designation"]))
    assert res.plan is None and "can't be split by Designation" in res.unsupported


def test_not_answerable(bis):
    res = run(bis, statement(answerable=False, reason="there is no attendance data"))
    assert "no attendance data" in res.unsupported


def test_unreadable_period_is_asked(bis):
    res = run(bis, statement(period="sometime around diwali"))
    assert res.plan is None and "couldn't work out the dates" in res.clarify.question


@pytest.mark.parametrize("line,expect", [
    ("area=billing | measure=billing_amount | by=branch | period=last 3 months | cond=> 2 crore | sort=desc",
     {"group_by": ["branch"], "period": "last 3 months", "sort": "desc",
      "condition": {"op": "gt", "number": 2e7, "unit": "none"}}),
    ("area=receipts | measure=receipt_amount | period=June 2026 | filter=branch:mumbai; not state:gujarat",
     {"filters": [{"dimension": "branch", "text": "mumbai", "exclude": False},
                  {"dimension": "state", "text": "gujarat", "exclude": True}]}),
    ("area=billing | measure=billing_amount | by=branch | cond=between 1 and 2 cr",
     {"condition": {"op": "between", "number": 1e7, "number2": 2e7, "unit": "none"}}),
    ("area=billing | measure=billing_amount | cond=>= 50 lakh | limit=5",
     {"condition": {"op": "ge", "number": 5e6, "unit": "none"}, "limit": 5}),
])
def test_statement_line_is_read(line, expect):
    from datachat.llm import parse_statement
    raw = parse_statement(line)
    for k, v in expect.items():
        assert raw[k] == v, k


def test_unanswerable_line():
    from datachat.llm import parse_statement
    for line in ("unanswerable=no attendance data", "area=none | unanswerable=no attendance data"):
        raw = parse_statement(line)
        assert raw["answerable"] is False and raw["reason"] == "no attendance data"


def test_named_measures(bis):
    from datetime import date
    parser = bis
    today = date(2026, 9, 30)
    assert parser.named_measures("may i know the collection of lucknow branch for last year Dec month", today) \
        == [("receipts", "receipt_amount")]
    assert parser.named_measures("which all branches earns more than 2cr in last month", today) \
        == [("billing", "billing_amount")]
    assert parser.named_measures("weather in pune today", today) == []


def test_time_word_is_not_a_name(bis):
    res = run(bis, statement(area="employees", metrics=["active_employees"], period="today",
                             filters=[{"dimension": "branch", "text": "today", "exclude": False}]),
              "active employees today")
    assert res.plan is not None and res.plan.filters == []


def test_statement_line_round_trip():
    from datachat.llm import parse_statement, statement_line
    line = "area=billing | measure=billing_amount | by=branch | period=last month | cond=> 2 crore | sort=desc | limit=5"
    assert statement_line(parse_statement(line)) == \
        "measure=billing_amount | area=billing | by=branch | period=last month | cond=> 20000000 | sort=desc | limit=5"


def test_top_n(bis):
    p = run(bis, statement(group_by=["customer"], sort="desc", limit=5, period="this financial year")).plan
    assert (p.sort.desc, p.limit, p.time.start) == (True, 5, date(2026, 4, 1))
