from datetime import date

from conftest import TODAY


def plan_of(parser, q, **kw):
    res = parser.parse(q, TODAY, **kw)
    assert res.plan is not None, f"{q!r}: clarify={res.clarify} unsupported={res.unsupported} unknown={res.unknown}"
    return res.plan, res


def test_total_sales_today(parser):
    p, _ = plan_of(parser, "What were total sales today?")
    assert (p.area, p.metrics, p.group_by) == ("sales", ["revenue"], [])
    assert p.time.start == TODAY


def test_highest_branch_this_month(parser):
    p, _ = plan_of(parser, "Which branch had the highest sales this month?")
    assert p.group_by == ["branch"] and p.sort.desc and p.limit == 5
    assert p.time.start == date(2026, 9, 1)


def test_hinglish(parser):
    p, _ = plan_of(parser, "pichhle mahine ki bikri har branch")
    assert (p.metrics, p.group_by) == (["revenue"], ["branch"])
    assert p.time.start == date(2026, 8, 1)


def test_marathi(parser):
    p, _ = plan_of(parser, "magchya mahinyat vikri kiti")
    assert p.metrics == ["revenue"] and p.time.start == date(2026, 8, 1)


def test_spelling_variant_of_lexicon_word(parser):
    p, _ = plan_of(parser, "pichhley mahine ki bikri")
    assert p.time.start == date(2026, 8, 1)


def test_typo_in_measure(parser):
    p, _ = plan_of(parser, "revnue by branch yesterday")
    assert p.metrics == ["revenue"] and p.group_by == ["branch"]


def test_top_items_goes_to_items_area(parser):
    p, _ = plan_of(parser, "Top 10 best selling items this month")
    assert (p.area, p.metrics, p.group_by, p.limit) == ("items", ["quantity"], ["item"], 10)


def test_sales_by_category_uses_item_level_measure(parser):
    p, _ = plan_of(parser, "sales by category last month")
    assert (p.area, p.metrics, p.group_by) == ("items", ["item_sales"], ["category"])


def test_payment_mode_breakdown(parser):
    p, _ = plan_of(parser, "revenue breakdown by payment mode")
    assert (p.area, p.metrics, p.group_by) == ("payments", ["payment_amount"], ["payment_mode"])


def test_ambiguous_measure_asks(parser):
    res = parser.parse("earnings last month", TODAY)
    assert res.plan is None and res.clarify is not None
    assert {o.overrides["earnings"] for o in res.clarify.options} == {"metric:net_sales", "metric:revenue"}


def test_clarification_choice_is_applied(parser):
    p, _ = plan_of(parser, "earnings last month", overrides={"earnings": "metric:net_sales"})
    assert p.metrics == ["net_sales"]


def test_region_group_filter(parser):
    p, _ = plan_of(parser, "sales for pune branches last year")
    assert p.group_by == []
    assert p.filters[0].dimension == "branch" and p.filters[0].values == ["PUNE001", "PUNE002", "PUNE003"]
    assert p.filters[0].label == "pune"


def test_group_and_filter_same_dimension(parser):
    p, _ = plan_of(parser, "sales by branch in pune")
    assert p.group_by == ["branch"] and p.filters[0].label == "pune"


def test_value_in_two_fields_asks(parser):
    res = parser.parse("swiggy orders yesterday", TODAY)
    assert res.clarify is not None
    assert {o.overrides["swiggy"] for o in res.clarify.options} == {"value:channel=Swiggy", "value:source=Swiggy"}


def test_negated_value(parser):
    p, _ = plan_of(parser, "sales except cash yesterday")
    assert p.area == "payments"
    assert p.filters[0].negate and p.filters[0].values == ["Cash"]


def test_hourly_trend(parser):
    p, _ = plan_of(parser, "hourly sales trend for yesterday")
    assert p.group_by == ["time:hour"] and p.time.start == date(2026, 9, 29)


def test_period_comparison(parser):
    p, _ = plan_of(parser, "sales this year vs last year")
    assert p.time.start == date(2026, 1, 1) and p.compare.start == date(2025, 1, 1)
    assert p.group_by == []


def test_two_periods_without_compare_word_become_a_trend(parser):
    p, _ = plan_of(parser, "sales in 2025 and 2026")
    assert p.time.start == date(2025, 1, 1) and p.time.end == date(2027, 1, 1)
    assert p.group_by == ["time:year"] and p.compare is None


def test_unknown_word_asks_and_offers_ignore(parser):
    res = parser.parse("veg sales today", TODAY)
    assert res.clarify is not None and res.clarify.kind == "unknown_word"
    assert res.clarify.options[-1].overrides == {"veg": "ignore"}


def test_unknown_word_can_be_ignored(parser):
    p, _ = plan_of(parser, "veg sales today", overrides={"veg": "ignore"})
    assert p.metrics == ["revenue"]


def test_learned_word_maps_to_value(parser):
    p, _ = plan_of(parser, "chai sales today", learned={"chai": "value:item=Cold Coffee"})
    assert p.filters[0].values == ["Cold Coffee"]


def test_follow_up_keeps_previous_question(parser):
    first, _ = plan_of(parser, "sales by branch last month")
    p, res = plan_of(parser, "and for yesterday", previous=first)
    assert p.metrics == ["revenue"] and p.group_by == ["branch"] and p.time.start == date(2026, 9, 29)
    assert "previous question" in " ".join(res.assumptions)


def test_follow_up_adds_filter(parser):
    first, _ = plan_of(parser, "sales last month")
    p, _ = plan_of(parser, "only pune", previous=first)
    assert p.filters[0].label == "pune" and p.time.start == date(2026, 8, 1)


def test_greeting(parser):
    assert parser.parse("hi", TODAY).greeting


def test_nonsense_is_unsupported(parser):
    res = parser.parse("hello world foo", TODAY)
    assert res.plan is None and res.unsupported


def test_no_measure_uses_default_and_says_so(parser):
    p, res = plan_of(parser, "by branch yesterday")
    assert p.metrics == ["revenue"]
    assert any("No measure named" in a for a in res.assumptions)
