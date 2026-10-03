"""Comparisons, measures from several areas, derived measures, share, counts and lists, without a database."""
from datetime import date

import pytest
from conftest import PACKS
from test_parser_bis import BIS_VALUES

from datachat.compiler import compile_detail, compile_plan
from datachat.executor import Executor, QueryResult
from datachat.llm import ground, parse_statement
from datachat.pack import load_pack
from datachat.parser import Parser
from datachat.plan import Filter, Having, Plan, Sort, TimeRange
from datachat.runner import _whole_months, evaluate, execute, prepare
from datachat.timeparse import extract_time, previous_period

TODAY = date(2026, 10, 1)


@pytest.fixture()
def bis(lexicon):
    values = {k: list(v) for k, v in BIS_VALUES.items()}
    values["branch"].append("BHOPAL BRANCH")
    values["customer"].append("BLINK COMMERCE PRIVATE LIMITED")
    values["state"] = values.get("state", []) + ["MAHARASHTRA", "GUJARAT"]
    return Parser(load_pack(PACKS / "bis" / "semantic.yaml"), lexicon, values)


def month(y, m):
    return extract_time(f"{['', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'][m]} {y}", TODAY).ranges[0]


class FakeExecutor(Executor):
    """Answers each query from a function of its SQL, so merges can be checked."""

    def __init__(self, answer):
        self.answer = answer
        self.sqls = []

    def run(self, sql, fetch_limit, cap):
        self.sqls.append(sql)
        cols, rows = self.answer(sql)
        return QueryResult(cols, rows, False, 1)


def test_derived_formula_is_plain_arithmetic():
    assert evaluate("receipt_amount / billing_amount * 100", {"receipt_amount": 50, "billing_amount": 200}) == 25
    assert evaluate("receipt_amount / billing_amount * 100", {"receipt_amount": 5, "billing_amount": 0}) is None
    assert evaluate("a - b", {"a": 5}) is None
    assert evaluate("__import__('os')", {}) is None


def test_whole_months():
    last6 = extract_time("last 6 months", TODAY).ranges[0]
    assert (_whole_months(last6).start, _whole_months(last6).end) == (date(2026, 4, 1), date(2026, 10, 1))
    y = _whole_months(extract_time("yesterday", TODAY).ranges[0])
    assert (y.start, y.end) == (date(2026, 9, 1), date(2026, 10, 1))


def test_previous_period():
    assert previous_period(month(2026, 6)).label == "May 2026"
    fy = extract_time("this financial year", TODAY).ranges[0]
    assert previous_period(fy).label == "FY 2025-26"


def test_like_for_like_when_data_stops_early(bis):
    fy = extract_time("this financial year", TODAY).ranges[0]
    plan = Plan(area="billing", metrics=["billing_amount"], time=fy, compare=previous_period(fy))
    notes = prepare(plan, bis.pack, {"billing": date(2026, 7, 1)}, TODAY)
    assert plan.time.end == date(2026, 8, 1) and plan.compare.end == date(2025, 8, 1)
    assert "same stretch" in notes[-1]


def test_snapshot_measure_ignores_dates(bis):
    plan = Plan(area="employees", metrics=["active_employees"], time=month(2025, 6))
    notes = prepare(plan, bis.pack)
    assert plan.time is None and "current figure" in notes[0]


def test_measure_named_contribution_is_not_a_share(bis):
    p = bis.parse("society contribution by branch", TODAY).plan
    assert p.area == "society" and p.metrics == ["society_contribution"] and not p.share
    p = bis.parse("percentage contribution of top 5 customers in collection 2026", TODAY).plan
    assert p.share


def test_society_measures_join_employee_for_active_members(bis):
    plan = Plan(area="society", metrics=["society_members"], group_by=["department"])
    sql = compile_plan(plan, bis.pack, 500).sql
    assert '"smtbtsociety"' in sql and '"smtbmemployee"' in sql and '"active" = 1' in sql


def test_several_names_are_shown_side_by_side(bis):
    plan = Plan(area="billing", metrics=["billing_amount"],
                filters=[Filter(dimension="branch", values=["LUCKNOW BRANCH", "BHOPAL BRANCH"])])
    prepare(plan, bis.pack)
    assert plan.group_by == ["branch"]


def test_compare_merges_two_periods(bis):
    plan = Plan(area="billing", metrics=["billing_amount"], group_by=["branch"], time=month(2026, 6),
                compare=month(2026, 5), sort=Sort(metric="billing_amount"))

    def answer(sql):
        if "'2026-07-01'" in sql:
            return ["branch", "billing_amount"], [["A", 100], ["B", 50]]
        return ["branch", "billing_amount"], [["A", 80], ["C", 10]]
    rr = execute(plan, bis.pack, FakeExecutor(answer), 500)
    names = [c.name for c in rr.columns]
    assert names == ["branch", "billing_amount", "billing_amount__prev", "billing_amount__change",
                     "billing_amount__change_pct"]
    rows = {r[0]: r for r in rr.rows}
    assert rows["A"][1:4] == [100, 80, 20] and rows["A"][4] == pytest.approx(25.0)
    assert rows["C"][1] is None and rows["C"][2] == 10


def test_measures_from_two_areas_and_derived(bis):
    plan = Plan(area="receipts", metrics=["receipt_amount"], more_metrics=["billing.billing_amount"],
                derived=["collection_efficiency"], group_by=["branch"],
                having=[Having(metric="collection_efficiency", op="lt", value=80)],
                sort=Sort(metric="collection_efficiency", desc=False))

    def answer(sql):
        if "dashboard_fact_receipts_monthly" in sql:
            return ["branch", "receipt_amount"], [["A", 70], ["B", 95], ["C", 30]]
        return ["branch", "billing_amount"], [["A", 100], ["B", 100], ["C", 100]]
    ex = FakeExecutor(answer)
    rr = execute(plan, bis.pack, ex, 500)
    assert len(ex.sqls) == 2 and all("HAVING" not in s for s in ex.sqls)
    assert [r[0] for r in rr.rows] == ["C", "A"]
    assert rr.rows[0][-1] == pytest.approx(30.0)


def test_share_uses_the_grand_total(bis):
    plan = Plan(area="billing", metrics=["billing_amount"], group_by=["state"], share=True, limit=2,
                sort=Sort(metric="billing_amount"))

    def answer(sql):
        if "GROUP BY" in sql:
            return ["state", "billing_amount"], [["X", 60], ["Y", 30]]
        return ["billing_amount"], [[200]]
    rr = execute(plan, bis.pack, FakeExecutor(answer), 500)
    assert rr.total == 200 and rr.rows[0][-1] == pytest.approx(30.0)


def test_count_of_a_field_compiles_to_distinct(bis):
    sql = compile_plan(Plan(area="billing", metrics=["count:customer"]), bis.pack, 500).sql
    assert 'COUNT(DISTINCT "cust"."custname")' in sql


def test_list_compiles_listed_columns_only(bis):
    plan = Plan(area="invoices", metrics=["invoice_value"], detail=True, time=month(2026, 7))
    sql = compile_detail(plan, bis.pack, 100).sql
    assert '"inv"."invoiceno"' in sql and "mobileno" not in sql and "NULLS LAST" in sql and "iscancel" in sql


@pytest.mark.parametrize("question,check", [
    ("billing june 2026 vs may 2026", lambda p: p.compare.label == "May 2026" and p.time.label == "June 2026"),
    ("billing growth this financial year", lambda p: p.compare.label == "FY 2025-26"),
    ("billing vs collection by branch for june 2026",
     lambda p: p.compare is None and p.more_metrics == ["receipts.receipt_amount"]),
    ("collection efficiency by state this financial year",
     lambda p: p.derived == ["collection_efficiency"] and p.group_by == ["state"]),
    ("how many customers were billed in june 2026", lambda p: p.metrics == ["count:customer"]),
    ("share of each state in billing this financial year", lambda p: p.share and p.group_by == ["state"]),
    ("list invoices of blink commerce for july 2026", lambda p: p.detail and p.area == "invoices"),
    ("billing of lucknow and bhopal branch in june 2026",
     lambda p: {v for f in p.filters for v in f.values} == {"LUCKNOW BRANCH", "BHOPAL BRANCH"}),
    ("billing april to june 2026", lambda p: p.time.label == "Apr 2026 to Jun 2026"),
])
def test_rules_read_business_questions(bis, question, check):
    res = bis.parse(question, TODAY)
    assert res.plan is not None, (res.clarify, res.unsupported)
    assert check(res.plan), res.plan


def test_same_for_another_measure_keeps_context(bis):
    first = bis.parse("billing by state this financial year", TODAY).plan
    res = bis.parse("same for collection", TODAY, previous=first)
    assert res.plan.area == "receipts" and res.plan.group_by == ["state"] and res.plan.time == first.time


@pytest.mark.parametrize("line,check", [
    ("area=billing | measure=billing_amount | period=June 2026 | compare=May 2026",
     lambda p: p.compare.label == "May 2026"),
    ("area=billing | measure=billing_amount,receipt_amount | by=branch | period=June 2026",
     lambda p: p.more_metrics == ["receipts.receipt_amount"]),
    ("area=receipts | measure=collection_efficiency | by=state | cond=< 80",
     lambda p: p.derived == ["collection_efficiency"] and p.having[0].metric == "collection_efficiency"),
    ("area=billing | measure=count:customer | period=June 2026", lambda p: p.metrics == ["count:customer"]),
    ("area=invoices | measure=invoice_value | period=July 2026 | show=list", lambda p: p.detail),
    ("area=billing | measure=billing_amount | by=state | share=yes", lambda p: p.share),
])
def test_model_statements_are_grounded(bis, line, check):
    res = ground(parse_statement(line), "q", bis.pack, bis, TODAY, {}, {})
    assert res.plan is not None, (res.clarify, res.unsupported)
    assert check(res.plan), res.plan


@pytest.mark.parametrize("line,question,check", [
    ("area=billing | measure=billing_amount | by=state | filter=state:not Maharashtra",
     "state wise billing excluding maharashtra", lambda p: p.filters[0].negate),
    ("area=billing | measure=billing_amount | filter=branch:lucknow,branch:bhopal | period=June 2026",
     "billing of lucknow and bhopal branch in june 2026",
     lambda p: set(p.filters[0].values) == {"LUCKNOW BRANCH", "BHOPAL BRANCH"}),
    ("area=billing | measure=billing_amount | by=month | period=this financial year",
     "month wise billing this financial year", lambda p: p.time_grain() == "month" and not p.dimension_group_by()),
    ("area=billing | measure=billing_amount | filter=financial_year:2025-26 | period=FY 2025-26",
     "billing for fy 2025-26", lambda p: p.time.label.startswith("FY 2025-26") and not p.filters),
    ("area=invoices | measure=invoice_value | period=01/06/2026 to 15/06/2026",
     "invoice value from 1/6/2026 to 15/6/2026", lambda p: p.time.label == "01 Jun 2026 to 15 Jun 2026"),
    ("area=billing | measure=billing_amount | period=this financial year | compare=previous",
     "billing growth this fy", lambda p: p.compare.label == "FY 2025-26"),
    ("area=billing | measure=billing_amount | by=branch | period=June 2026 | compare=branch:bhopal",
     "compare billing of bhopal branch in june 2026",
     lambda p: p.compare is None and p.filters[0].values == ["BHOPAL BRANCH"]),
    ("area=invoices | measure=invoice_value | filter=customer:\"BLINK COMMERCE\" | period=July 2026 | show=list",
     "list invoices of blink commerce for july 2026",
     lambda p: p.detail and p.filters[0].values == ["BLINK COMMERCE PRIVATE LIMITED"]),
])
def test_small_model_slips_are_repaired(bis, line, question, check):
    res = ground(parse_statement(line), question, bis.pack, bis, TODAY, {}, {})
    assert res.plan is not None, (res.clarify, res.unsupported)
    assert check(res.plan), res.plan


def test_a_name_the_user_never_wrote_is_dropped(bis):
    res = ground(parse_statement("measure=billing_amount | area=billing | period=last month | filter=branch:agra"),
                 "pichle mahine ki billing kitni thi", bis.pack, bis, TODAY, {}, {})
    assert res.plan.filters == [] and any("agra" in a for a in res.assumptions)
    res = ground(parse_statement("measure=billing_amount | area=billing | filter=branch:lucknow"),
                 "billing of lucknwo branch", bis.pack, bis, TODAY, {}, {})
    assert res.plan.filters[0].values == ["LUCKNOW BRANCH"]


def test_a_follow_up_keeps_names_from_the_previous_statement(bis):
    res = ground(parse_statement("measure=billing_amount | area=billing | period=May 2026 | filter=branch:lucknow"),
                 "what about may 2026", bis.pack, bis, TODAY, {}, {},
                 context="measure=billing_amount | area=billing | filter=branch:LUCKNOW BRANCH")
    assert res.plan.filters[0].values == ["LUCKNOW BRANCH"]


def test_typo_found_in_the_chosen_field(bis):
    res = ground(parse_statement("measure=billing_amount | area=billing | filter=branch:lucknwo"),
                 "billing of lucknwo branch", bis.pack, bis, TODAY, {}, {})
    assert [(f.dimension, f.values) for f in res.plan.filters] == [("branch", ["LUCKNOW BRANCH"])]


def test_field_word_as_a_name_becomes_a_split(bis):
    res = ground(parse_statement("measure=receipt_amount | area=receipts | filter=customer:clients"),
                 "how much money came in from clients", bis.pack, bis, TODAY, {}, {})
    assert res.plan.filters == [] and res.plan.group_by == ["customer"]


@pytest.mark.parametrize("line,check", [
    ("measure=branch | area=receipts | period=this financial year", lambda p: p.metrics == ["count:branch"]),
    ("measure=sharing | area=billing | by=state | period=this financial year",
     lambda p: p.share and p.metrics == ["billing_amount"]),
    ("measure=billing_amount | area=billing | period=June 2026, June 2025",
     lambda p: p.time.label == "June 2026" and p.compare.label == "June 2025"),
])
def test_more_model_slips(bis, line, check):
    res = ground(parse_statement(line), "q", bis.pack, bis, TODAY, {}, {})
    assert res.plan is not None, (res.clarify, res.unsupported)
    assert check(res.plan), res.plan


def test_measure_name_inside_model_wording(bis):
    res = ground(parse_statement("measure=total billing_amount | area=billing"), "total billing", bis.pack, bis,
                 TODAY, {}, {})
    assert res.plan.metrics == ["billing_amount"]


def test_data_the_client_does_not_hold_is_named(bis):
    assert "exit dates" in bis.pack.unavailable("employee attrition last month")
    assert bis.pack.unavailable("billing by branch this year") is None


def test_invented_measure_is_refused(bis):
    res = ground(parse_statement("area=employees | measure=attendance | period=today"), "attendance today",
                 bis.pack, bis, TODAY, {}, {})
    assert res.plan is None and "attendance" in res.unsupported


def test_list_of_area_without_rows_is_refused(bis):
    res = ground(parse_statement("area=billing | measure=billing_amount | show=list"), "list billing",
                 bis.pack, bis, TODAY, {}, {})
    assert res.plan is None and "not a list" in res.unsupported
