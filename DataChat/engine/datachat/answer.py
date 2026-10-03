"""
Builds the plain-English answer and chart choice from the result cells only.
No model writes this text, so every number in it comes from the query result.
"""
from dataclasses import dataclass
from datetime import date

from datachat.compiler import CompiledQuery
from datachat.executor import QueryResult
from datachat.pack import Formatting, Pack
from datachat.plan import Plan


@dataclass
class Chart:
    type: str  # bar | line | pie
    x: str
    y: list[str]


def _period_label(grain: str, value, label: str) -> str:
    """'June 2026' / 'week of 2026-06-01' instead of a raw ISO date."""
    try:
        d = date.fromisoformat(str(value)[:10])
    except ValueError:
        return f"{label.lower()} {value}"
    if grain == "month":
        return d.strftime("%B %Y")
    if grain == "year":
        return str(d.year)
    if grain == "week":
        return f"the week of {d.isoformat()}"
    if grain == "day":
        return d.strftime("%d %b %Y").lstrip("0")
    return f"{label.lower()} {value}"


def indian_group(n: int) -> str:
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if n < 0 else "") + s


def _group(n: int, fmt: Formatting) -> str:
    return indian_group(n) if fmt.indian_grouping else f"{n:,}"


def format_value(v, kind: str | None, fmt: Formatting) -> str:
    if v is None:
        return "no data"
    if not isinstance(v, (int, float)):
        return str(v)
    if kind == "currency":
        rounded = round(v)
        return f"{fmt.currency_symbol}{_group(int(rounded), fmt)}" if abs(v) >= 100 else f"{fmt.currency_symbol}{v:,.2f}"
    if kind == "integer":
        return _group(int(round(v)), fmt)
    if kind == "percent":
        return f"{v:.1f}%"
    if isinstance(v, float) and not v.is_integer():
        return f"{v:,.2f}"
    return _group(int(v), fmt)


def describe_plan(plan: Plan, pack: Pack) -> str:
    parts = []
    if plan.time and plan.compare:
        parts.append(f"{plan.time.label} vs {plan.compare.label}")
    elif plan.time:
        parts.append(plan.time.label)
    for f in plan.filters:
        label = pack.dimensions[f.dimension].label
        values = f.label or ", ".join(f.values[:5]) + (" …" if len(f.values) > 5 else "")
        parts.append(f"{label} {'not ' if f.negate else ''}{values}")
    for h in plan.having:
        m = measure_def(pack, plan, h.metric)
        amount = format_value(h.value, m.format, pack.formatting)
        if h.op == "between":
            parts.append(f"{m.label} between {amount} and {format_value(h.value2, m.format, pack.formatting)}")
        else:
            parts.append(f"{m.label} {_HAVING_WORDS[h.op]} {amount}")
    return "; ".join(parts)


def measure_def(pack: Pack, plan: Plan, name: str):
    """Label and format of a measure named in a plan: the area's, another area's, count:<dim>, or derived."""
    if name in pack.derived_metrics:
        return pack.derived_metrics[name]
    if pack.has_metric(plan.area, name):
        return pack.metric(plan.area, name)
    owner = pack.area_of_metric(name)
    if owner:
        return pack.metric(owner, name)
    raise KeyError(name)


_HAVING_WORDS = {"gt": "more than", "ge": "at least", "lt": "less than", "le": "at most"}


def _plural(label: str, n: int) -> str:
    word = label.lower()
    if n == 1:
        return word
    return word + ("es" if word.endswith(("ch", "sh", "s", "x")) else "s")


def _is_additive(pack: Pack, plan: Plan, metric: str) -> bool:
    if not pack.has_metric(plan.area, metric):
        return False
    m = pack.metric(plan.area, metric)
    expr = m.expr.strip().upper()
    return not m.snapshot and (expr.startswith("SUM(") or expr.startswith("COUNT(")) and "DISTINCT" not in expr


def _change_words(cur, old, fmt_kind: str | None, fmt: Formatting) -> str:
    if cur is None and old is None:
        return "no data in either period"
    diff = (cur or 0) - (old or 0)
    if not old:
        return f"up by {format_value(diff, fmt_kind, fmt)} (nothing in the earlier period)" if diff else "no change"
    pct = diff / abs(old) * 100
    if abs(pct) < 0.05:
        return "no change"
    word = "up" if diff > 0 else "down"
    return f"{word} {abs(pct):.1f}% ({'+' if diff > 0 else '−'}{format_value(abs(diff), fmt_kind, fmt)})"


def build_answer(plan: Plan, pack: Pack, cq: CompiledQuery, result: QueryResult) -> tuple[str, Chart | None]:
    """Answer for a single query (kept for callers that compile one plan themselves)."""
    from datachat.runner import RunResult
    return build_run_answer(plan, pack, RunResult([cq.sql], cq.columns, result.rows, result.capped, cq.cap))


def build_run_answer(plan: Plan, pack: Pack, rr) -> tuple[str, Chart | None]:
    from datachat.runner import CHANGE, PREV, SHARE, short_label
    fmt = pack.formatting
    meta = {c.name: c for c in rr.columns}
    idx = {c.name: i for i, c in enumerate(rr.columns)}
    desc = describe_plan(plan, pack)
    scope = f" ({desc})" if desc else ""
    rows = rr.rows

    def val(row, name):
        return format_value(row[idx[name]], meta[name].format, fmt)

    if plan.detail:
        area = pack.areas[plan.area]
        noun = area.detail_name or "row"
        if not rows:
            return f"No {noun}s found{scope}.", None
        more = f" Only the first {rr.cap} are shown; narrow the question to see the rest." if rr.capped else ""
        newest = ", newest first" if area.time_column else ""
        return f"{len(rows)} {_plural(noun, len(rows))}{scope}{newest}.{more}", None

    value_cols = [c.name for c in rr.columns if c.kind == "metric"]
    main_cols = [n for n in value_cols if not n.endswith((PREV, CHANGE, "__change_pct", SHARE))]
    if not rows or (len(rows) == 1 and all(rows[0][idx[m]] is None for m in value_cols)):
        return f"No matching data{scope}.", None

    grain = plan.time_grain()
    dims = plan.dimension_group_by()
    m0 = main_cols[0]
    m0_label = meta[m0].label.split(" (")[0] if plan.compare else meta[m0].label

    if not plan.group_by:
        r = rows[0]
        if plan.compare:
            bits = []
            for m in main_cols:
                if m + PREV in idx:
                    label = meta[m].label.split(" (")[0]
                    bits.append(f"{label}: {val(r, m)} in {short_label(plan.time)} vs {val(r, m + PREV)} in "
                                f"{short_label(plan.compare)}, "
                                f"{_change_words(r[idx[m]], r[idx[m + PREV]], meta[m].format, fmt)}")
                else:
                    bits.append(f"{meta[m].label}: {val(r, m)}")
            return "; ".join(bits) + scope_without_time(plan, pack) + ".", None
        return "; ".join(f"{meta[m].label}: {val(r, m)}" for m in main_cols) + scope + ".", None

    lines = []
    sort_col = plan.sort.metric if plan.sort and plan.sort.metric in idx else None
    def name(r) -> str:
        return ", ".join("Not recorded" if r[idx[d]] in (None, "") else str(r[idx[d]]) for d in dims)

    if dims and not grain:
        top = rows[0]
        who = name(top)
        if plan.compare and not plan.having:
            lines.append(f"{m0_label} by {', '.join(meta[d].label.lower() for d in dims)}{scope}.")
            changes = [(r, r[idx[m0 + CHANGE]]) for r in rows if r[idx[m0 + CHANGE]] is not None]
            if changes:
                up = max(changes, key=lambda x: x[1])
                down = min(changes, key=lambda x: x[1])
                if up[1] > 0:
                    lines.append(f"Biggest rise: {name(up[0])} (+{format_value(up[1], meta[m0].format, fmt)}).")
                if down[1] < 0:
                    lines.append(f"Biggest fall: {name(down[0])} "
                                 f"(−{format_value(abs(down[1]), meta[m0].format, fmt)}).")
        elif plan.having:
            names = [name(r) for r in rows[:5]]
            more = f" and {len(rows) - 5} more" if len(rows) > 5 else ""
            lines.append(f"{len(rows)}{'+' if rr.capped else ''} {_plural(meta[dims[0]].label, len(rows))} "
                         f"{'matches' if len(rows) == 1 else 'match'}{scope}: {', '.join(names)}{more}.")
        elif plan.share and m0 + SHARE in idx:
            lead = top if not plan.sort or plan.sort.desc else max(rows, key=lambda r: r[idx[m0]] or 0)
            lead_who = name(lead)
            total = format_value(rr.total, meta[m0].format, fmt) if rr.total is not None else "the total"
            lines.append(f"{lead_who} has the largest share of {m0_label.lower()}: {val(lead, m0 + SHARE)} "
                         f"({val(lead, m0)} of {total}){scope}.")
        elif sort_col:
            word = "highest" if plan.sort.desc else "lowest"
            label = meta[sort_col].label
            shown = [meta[m].label for m in main_cols if m not in plan.derived and m != sort_col]
            if plan.more_metrics and shown:
                lines.append(f"{label} and {', '.join(s[0].lower() + s[1:] for s in shown)} by "
                             f"{', '.join(meta[d].label.lower() for d in dims)}{scope}.")
                scope_here = ""
            else:
                scope_here = scope
            lines.append(f"{who} has the {word} {label[0].lower() + label[1:]}: {val(top, sort_col)}{scope_here}.")
        else:
            labels = [meta[m].label for m in main_cols if m not in plan.derived]
            headline = labels[0] + "".join(f" and {lab[0].lower() + lab[1:]}" for lab in labels[1:])
            lines.append(f"{headline} by {', '.join(meta[d].label.lower() for d in dims)}{scope}.")
    elif grain and not dims:
        values = [(r[idx[grain]], r[idx[m0]]) for r in rows if r[idx[m0]] is not None]
        if values:
            peak = max(values, key=lambda x: x[1])
            low = min(values, key=lambda x: x[1])
            lines.append(f"{m0_label}{scope}: highest in {_period_label(grain, peak[0], meta[grain].label)} "
                         f"({format_value(peak[1], meta[m0].format, fmt)})")
            if len(values) > 1:
                lines[-1] += (f", lowest in {_period_label(grain, low[0], meta[grain].label)} "
                              f"({format_value(low[1], meta[m0].format, fmt)})")
            lines[-1] += "."
            if _is_additive(pack, plan, m0):
                total = sum(v for _, v in values)
                lines.append(f"Total across all periods: {format_value(total, meta[m0].format, fmt)}; "
                             f"average per {meta[grain].label.lower().replace('week starting', 'week')}: "
                             f"{format_value(total / len(values), meta[m0].format, fmt)}.")
    else:
        lines.append(f"{m0_label} by {', '.join(c.label.lower() for c in rr.columns if c.kind != 'metric')}"
                     f"{scope}.")

    lines.append(f"{len(rows)} row{'s' if len(rows) != 1 else ''} shown.")
    if rr.capped:
        lines.append(f"Only the first {rr.cap} rows are shown; narrow the question to see the rest.")

    chart = None
    same_kind = [m for m in main_cols if meta[m].format == meta[m0].format and m not in plan.derived]
    bars = [m0, m0 + PREV] if plan.compare else same_kind
    if grain and not dims and len(rows) >= 2:
        chart = Chart("line", grain, same_kind)
    elif len(dims) == 1 and not grain and 2 <= len(rows) <= 30:
        if (plan.chart_hint == "pie" or plan.share) and len(bars) == 1 and len(rows) <= 10:
            chart = Chart("pie", dims[0], bars)
        else:
            chart = Chart("bar", dims[0], bars)
    return " ".join(lines), chart


def scope_without_time(plan: Plan, pack: Pack) -> str:
    desc = describe_plan(plan.model_copy(update={"time": None, "compare": None}), pack)
    return f" ({desc})" if desc else ""
