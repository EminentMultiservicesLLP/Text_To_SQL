"""
Runs a plan. Most questions are one query; some need a few (two periods, measures from different areas
or with different dates, share of the total). Their results are lined up by group into one table.
Every number still comes from SQL; derived measures are plain arithmetic on those totals.
"""
import ast
import operator
import re
from dataclasses import dataclass, field
from datetime import date

from datachat.compiler import ColumnMeta, CompileError, CompiledQuery, compile_detail, compile_plan
from datachat.executor import Executor, QueryResult
from datachat.guard import check_sql
from datachat.pack import Pack
from datachat.plan import Having, Plan, TimeRange
from datachat.timeparse import union

PREV = "__prev"
CHANGE = "__change"
CHANGE_PCT = "__change_pct"
SHARE = "__share"


@dataclass
class RunResult:
    sqls: list[str]
    columns: list[ColumnMeta]
    rows: list[list]
    capped: bool
    cap: int
    notes: list[str] = field(default_factory=list)
    total: float | None = None  # grand total of the first measure, when share was asked


def short_label(r: TimeRange) -> str:
    return re.sub(r"\s*\(.*?\)", "", r.label).strip()


# ── adjusting the plan to the data ───────────────────────────────────────────

def _first_of_next_month(d: date) -> date:
    return date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def _whole_months(r: TimeRange) -> TimeRange:
    """Short ranges become the month(s) they fall in; longer ones snap to the nearest month boundaries,
    so 'last 6 months' (2 Apr - 1 Oct) is April to September, not seven months."""
    if (r.end - r.start).days < 28:
        start = r.start.replace(day=1)
        last_day = date.fromordinal(r.end.toordinal() - 1)
        end = _first_of_next_month(last_day)
    else:
        start = r.start.replace(day=1) if r.start.day <= 15 else _first_of_next_month(r.start)
        end = r.end.replace(day=1) if r.end.day <= 15 else _first_of_next_month(r.end)
        if end <= start:
            end = _first_of_next_month(start)
    if (start, end) == (r.start, r.end):
        return r
    last = date(end.year - (end.month == 1), (end.month - 2) % 12 + 1, 1)
    label = start.strftime("%B %Y") if start == last else f"{start:%b %Y} to {last:%b %Y}"
    return TimeRange(start=start, end=end, label=label, unit="month" if start == last else "custom")


def _months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + b.month - a.month


def _add_months(d: date, n: int) -> date:
    m = d.month - 1 + n
    return date(d.year + m // 12, m % 12 + 1, 1)


def _span_label(r: TimeRange, start: date, end: date) -> str:
    last = date.fromordinal(end.toordinal() - 1)
    if start.day == 1 and end.day == 1:
        span = f"{start:%b}–{last:%b %Y}" if start.year == last.year else f"{start:%b %Y}–{last:%b %Y}"
    else:
        span = f"{start:%d %b}–{last:%d %b %Y}"
    return f"{short_label(r)} ({span})"


def _like_for_like(plan: Plan, pack: Pack, latest: dict[str, date], today: date | None) -> str | None:
    """A period still running (or past the last data loaded) is compared with the same stretch of the other
    period, so 'this year vs last year' in July compares April-July with April-July."""
    areas = {a for a, _ in plan.all_metrics()} | {plan.area}
    cutoffs = [date.fromordinal(today.toordinal() + 1)] if today else []
    for a in areas:
        if a in latest:
            d = latest[a]
            cutoffs.append(_first_of_next_month(d) if pack.areas[a].time_resolution == "month"
                           else date.fromordinal(d.toordinal() + 1))
    if not cutoffs:
        return None
    cutoff = min(cutoffs)
    t, c = plan.time, plan.compare
    if not (t.start < cutoff < t.end):
        return None
    if t.start.day == 1 and cutoff.day == 1 and c.start.day == 1:
        c_end = _add_months(c.start, _months_between(t.start, cutoff))
    else:
        c_end = date.fromordinal(c.start.toordinal() + (cutoff - t.start).days)
    if c_end >= c.end:
        return None
    plan.time = TimeRange(start=t.start, end=cutoff, label=_span_label(t, t.start, cutoff))
    plan.compare = TimeRange(start=c.start, end=c_end, label=_span_label(c, c.start, c_end))
    return (f"The data so far only covers {plan.time.label.split('(')[1].rstrip(')')}, so both periods are "
            f"compared over the same stretch: {plan.time.label} vs {plan.compare.label}.")


def prepare(plan: Plan, pack: Pack, latest: dict[str, date] | None = None, today: date | None = None) -> list[str]:
    """Fits the plan to what the data can answer, and says what changed."""
    notes: list[str] = []
    areas = {a for a, _ in plan.all_metrics()} | {plan.area}

    if plan.time and not plan.detail and not plan.more_metrics and plan.metrics and all(
            pack.metric(plan.area, m).snapshot for m in plan.metrics):
        labels = ", ".join(pack.metric(plan.area, m).label for m in plan.metrics)
        notes.append(f"{labels} is a current figure (as on today), so the dates in the question don't apply.")
        plan.time, plan.compare = None, None
        plan.group_by = [g for g in plan.group_by if not g.startswith("time:")]

    if any(pack.areas[a].time_resolution == "month" for a in areas):
        for attr in ("time", "compare"):
            r = getattr(plan, attr)
            if r is not None:
                w = _whole_months(r)
                if w is not r:
                    setattr(plan, attr, w)
                    notes.append(f"This data is recorded by month, so '{short_label(r)}' is read as {w.label}.")

    if plan.compare and plan.time_grain():
        plan.time = union([plan.time, plan.compare]) if plan.time else plan.compare
        plan.compare = None

    if plan.compare and plan.time is None:
        plan.compare = None
    if plan.compare:
        note = _like_for_like(plan, pack, latest or {}, today)
        if note:
            notes.append(note)

    if not plan.detail:
        for f in plan.filters:
            if len(f.values) > 1 and not f.negate and not f.label and f.dimension not in plan.group_by:
                plan.group_by.insert(0, f.dimension)
    if plan.share and not plan.dimension_group_by():
        plan.share = False
    return notes


# ── running ──────────────────────────────────────────────────────────────────

def _split(plan: Plan, pack: Pack) -> list[Plan]:
    """One plan per (area, date column); the first holds the question's main measure."""
    groups: dict[tuple[str, str | None], list[str]] = {}
    for a, m in plan.all_metrics():
        if a not in pack.areas or not pack.has_metric(a, m):
            raise CompileError(f"Unknown measure {a}.{m}")
        groups.setdefault((a, pack.metric_time_column(a, m)), []).append(m)
    parts = []
    for i, ((a, _), ms) in enumerate(groups.items()):
        dims = set(pack.dimensions_for(a))
        for d in plan.dimension_group_by():
            if d not in dims:
                raise CompileError(f"{pack.areas[a].label} can't be split by {pack.dimensions[d].label}")
        for f in plan.filters:
            if f.dimension not in dims:
                raise CompileError(f"{pack.areas[a].label} can't be filtered by {pack.dimensions[f.dimension].label}")
        sub = plan.model_copy(deep=True, update={"area": a, "metrics": ms, "more_metrics": [], "derived": [],
                                                 "compare": None, "share": False})
        sub.having = [h for h in plan.having if h.metric in ms] if i == 0 else []
        if i > 0 or (plan.sort and plan.sort.metric not in ms):
            sub.sort, sub.limit = None, None
        if i == 0 and len(sub.having) < len(plan.having):
            sub.limit = None
        parts.append(sub)
    return parts


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def evaluate(formula: str, values: dict[str, float | None]) -> float | None:
    """Arithmetic on measure totals; None when an input is missing or a division is by zero."""
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.Name):
            v = values.get(n.id)
            if v is None:
                raise ValueError(n.id)
            return float(v)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -ev(n.operand)
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        raise ValueError("unsupported")
    try:
        return ev(ast.parse(formula, mode="eval"))
    except (ValueError, ZeroDivisionError, SyntaxError):
        return None


def _passes(v, h: Having) -> bool:
    if v is None:
        return False
    if h.op == "between":
        return h.value <= v <= (h.value2 if h.value2 is not None else h.value)
    return {"gt": v > h.value, "ge": v >= h.value, "lt": v < h.value, "le": v <= h.value}[h.op]


def execute(plan: Plan, pack: Pack, executor: Executor, row_limit: int) -> RunResult:
    sqls: list[str] = []

    def run(cq: CompiledQuery) -> QueryResult:
        check_sql(cq.sql, pack.database.dialect, pack.allowed_table_names())
        sqls.append(cq.sql)
        return executor.run(cq.sql, cq.fetch_limit, cq.cap)

    if plan.detail:
        cq = compile_detail(plan, pack, row_limit)
        r = run(cq)
        return RunResult(sqls, cq.columns, r.rows, r.capped, cq.cap)

    parts = _split(plan, pack)
    results: list[tuple[Plan, CompiledQuery, QueryResult, bool]] = []  # (part, query, result, is_previous)
    for i, part in enumerate(parts):
        cq = compile_plan(part, pack, row_limit)
        results.append((part, cq, run(cq), False))
        if plan.compare:
            prev = part.model_copy(deep=True, update={"time": plan.compare, "sort": None, "limit": None,
                                                      "having": []})
            pcq = compile_plan(prev, pack, row_limit)
            results.append((prev, pcq, run(pcq), True))

    first_cq = results[0][1]
    key_cols = [c for c in first_cq.columns if c.kind != "metric"]
    keys = [c.name for c in key_cols]
    restrict = bool(parts[0].limit or parts[0].having)
    table: dict[tuple, dict[str, object]] = {}
    order: list[tuple] = []
    metric_cols: list[ColumnMeta] = []
    names_used: set[str] = set()
    name_of: dict[tuple[str, str], str] = {}

    for idx_part, (part, cq, res, is_prev) in enumerate(results):
        pos = {n: i for i, n in enumerate(res.columns)}
        for c in cq.columns:
            if c.kind != "metric":
                continue
            base = name_of.get((part.area, c.name))
            if base is None:
                base = c.name if c.name not in names_used else f"{part.area}.{c.name}"
                names_used.add(base)
                name_of[(part.area, c.name)] = base
            label = c.label if base == c.name else f"{c.label} ({pack.areas[part.area].label})"
            if plan.compare:
                label += f" ({short_label(plan.compare if is_prev else plan.time)})"
            metric_cols.append(ColumnMeta(base + (PREV if is_prev else ""), label, "metric", c.format))
        for row in res.rows:
            key = tuple(row[pos[k]] for k in keys)
            if key not in table:
                if idx_part > 0 and restrict:
                    continue
                table[key] = {k: row[pos[k]] for k in keys}
                order.append(key)
            for c in cq.columns:
                if c.kind == "metric":
                    table[key][name_of[(part.area, c.name)] + (PREV if is_prev else "")] = row[pos[c.name]]

    columns = key_cols + metric_cols
    m0 = name_of[(parts[0].area, parts[0].metrics[0])]
    m0_col = next(c for c in metric_cols if c.name == m0)
    if plan.compare:
        columns += [ColumnMeta(m0 + CHANGE, "Change", "metric", m0_col.format),
                    ColumnMeta(m0 + CHANGE_PCT, "Change %", "metric", "percent")]
        for rowd in table.values():
            cur, old = rowd.get(m0), rowd.get(m0 + PREV)
            rowd[m0 + CHANGE] = (cur or 0) - (old or 0) if cur is not None or old is not None else None
            rowd[m0 + CHANGE_PCT] = ((cur or 0) - old) / abs(old) * 100 if old else None
    for d in plan.derived:
        dd = pack.derived_metrics[d]
        columns.append(ColumnMeta(d, dd.label, "metric", dd.format))
        for rowd in table.values():
            rowd[d] = evaluate(dd.formula, {k: v for k, v in rowd.items() if isinstance(v, (int, float))})

    total = None
    if plan.share:
        tot_plan = parts[0].model_copy(deep=True, update={"group_by": [], "sort": None, "limit": None,
                                                          "having": [], "metrics": [parts[0].metrics[0]]})
        tr = run(compile_plan(tot_plan, pack, row_limit))
        total = tr.rows[0][0] if tr.rows else None
        columns.append(ColumnMeta(m0 + SHARE, "Share %", "metric", "percent"))
        for rowd in table.values():
            v = rowd.get(m0)
            rowd[m0 + SHARE] = v / total * 100 if total and v is not None else None

    rows_d = [table[k] for k in order]
    sql_having = {h.metric for h in parts[0].having}
    for h in plan.having:
        if h.metric not in sql_having:
            col = name_of.get((plan.area, h.metric), h.metric)
            rows_d = [r for r in rows_d if _passes(r.get(col), h)]
    if plan.sort and plan.sort.metric not in parts[0].metrics:
        col = name_of.get((plan.area, plan.sort.metric), plan.sort.metric)
        present = [r for r in rows_d if r.get(col) is not None]
        rows_d = sorted(present, key=lambda r: r[col], reverse=plan.sort.desc) + \
            [r for r in rows_d if r.get(col) is None]
    if plan.limit and len(rows_d) > plan.limit:
        rows_d = rows_d[:plan.limit]

    cap = first_cq.cap
    capped = any(r.capped for _, _, r, _ in results) or len(rows_d) > cap
    rows = [[r.get(c.name) for c in columns] for r in rows_d[:cap]]
    return RunResult(sqls, columns, rows, capped, cap, total=total)
