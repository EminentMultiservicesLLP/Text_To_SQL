"""
Next questions offered under an answer. Each is a ready plan built from the one just answered, so clicking it
runs straight away without the language model, and it can only use measures and groupings the pack has.
"""
from dataclasses import dataclass
from datetime import date

from datachat.pack import Pack
from datachat.plan import Plan, Sort, TimeRange
from datachat.timeparse import _add_months, previous_period

MAX_FOLLOW_UPS = 3


@dataclass
class FollowUp:
    label: str
    plan: Plan


def follow_ups(plan: Plan, pack: Pack, today: date) -> list[FollowUp]:
    if plan.detail or not plan.metrics:
        return []
    area = pack.areas[plan.area]
    m0 = plan.metrics[0]
    metric = pack.metric(plan.area, m0)
    name = metric.label
    dims_in = plan.dimension_group_by()
    grain_in = plan.time_grain()
    filtered = {f.dimension for f in plan.filters}
    others = [d for d in pack.dimensions_for(plan.area) if d not in dims_in and d not in filtered]
    dated = not metric.snapshot and pack.metric_time_column(plan.area, m0) is not None
    plain = not grain_in and not plan.compare and not plan.more_metrics and not plan.derived
    label = lambda d: pack.dimensions[d].label.lower()  # noqa: E731

    def variant(**changes) -> Plan:
        base = {"sort": None, "limit": None, "share": False, "chart_hint": None, "having": []}
        return plan.model_copy(deep=True, update={**base, **changes})

    out: list[FollowUp] = []
    if not dims_in and others:
        out.append(FollowUp(f"{name} by {label(others[0])}",
                            variant(group_by=[others[0]], sort=Sort(metric=m0))))
    if dated and not grain_in:
        r = plan.time
        if r is None or (r.end - r.start).days < 60:
            end = _add_months(date(today.year, today.month, 1), 1)
            r = TimeRange(start=_add_months(end, -12), end=end, label="last 12 months")
        grain = "month" if (r.end - r.start).days <= 731 else "year"
        out.append(FollowUp(f"{name} {grain}-wise" + (f" ({r.label})" if r is not plan.time else ""),
                            variant(group_by=[f"time:{grain}"], time=r, compare=None)))
    if dated and plan.time and plain:
        prev = previous_period(plan.time)
        out.append(FollowUp(f"Compare with {prev.label}", variant(group_by=dims_in, compare=prev,
                                                                 sort=Sort(metric=m0) if dims_in else None)))
    if dims_in and plain and len(plan.metrics) == 1 and not plan.share:
        out.append(FollowUp(f"Share of each {label(dims_in[0])}", variant(group_by=dims_in, share=True,
                                                                          chart_hint="pie", sort=Sort(metric=m0))))
    if dims_in and others:
        out.append(FollowUp(f"{name} by {label(others[0])}",
                            variant(group_by=[others[0]], sort=Sort(metric=m0), compare=plan.compare)))
    if area.detail_columns and plan.filters and not dims_in:
        out.append(FollowUp(f"List the {area.detail_name or 'rows'}", variant(group_by=[], detail=True,
                                                                             compare=None)))
    seen, unique = set(), []
    for f in out:
        if f.label not in seen:
            seen.add(f.label)
            unique.append(f)
    return unique[:MAX_FOLLOW_UPS]
