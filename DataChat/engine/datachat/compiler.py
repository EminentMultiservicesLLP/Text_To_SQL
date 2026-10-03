"""
Turns a validated Plan into one SELECT statement for the client's database.
Only tables, joins, columns and expressions from the pack can appear; values become escaped literals.
"""
from dataclasses import dataclass
from datetime import date

import networkx as nx

from datachat.pack import PLACEHOLDER_RE, TIME_GRAINS, FilterDef, Pack
from datachat.plan import Plan

_QUOTES = {"tsql": ("[", "]"), "postgres": ('"', '"')}

_GRAIN_SQL = {
    "tsql": {
        "hour": "DATEPART(HOUR, {c})",
        "day": "CAST({c} AS DATE)",
        "week": "CAST(DATEADD(DAY, (DATEDIFF(DAY, 0, CAST({c} AS DATE)) / 7) * 7, 0) AS DATE)",  # Monday
        "month": "DATEFROMPARTS(YEAR({c}), MONTH({c}), 1)",
        "year": "YEAR({c})",
        "weekday": "DATENAME(WEEKDAY, {c})",
    },
    "postgres": {
        "hour": "EXTRACT(HOUR FROM {c})",
        "day": "CAST({c} AS DATE)",
        "week": "CAST(DATE_TRUNC('week', {c}) AS DATE)",
        "month": "CAST(DATE_TRUNC('month', {c}) AS DATE)",
        "year": "EXTRACT(YEAR FROM {c})",
        "weekday": "TRIM(TO_CHAR({c}, 'Day'))",
    },
}
_GRAIN_LABELS = {"hour": "Hour", "day": "Date", "week": "Week starting", "month": "Month", "year": "Year",
                 "weekday": "Weekday"}


_HAVING_OPS = {"gt": ">", "ge": ">=", "lt": "<", "le": "<="}


class CompileError(Exception):
    pass


def _num(v: float) -> str:
    v = float(v)  # never text: this goes into the SQL as a bare number
    return str(int(v)) if v.is_integer() else repr(v)


@dataclass
class ColumnMeta:
    name: str
    label: str
    kind: str  # dimension | time | metric
    format: str | None = None


@dataclass
class CompiledQuery:
    sql: str
    columns: list[ColumnMeta]
    fetch_limit: int  # rows to fetch; one more than the cap when the plan has no explicit limit
    cap: int


class _Sql:
    def __init__(self, pack: Pack):
        self.pack = pack
        self.dialect = pack.database.dialect
        self.lq, self.rq = _QUOTES[self.dialect]

    def q(self, ident: str) -> str:
        return f"{self.lq}{ident.replace(self.rq, self.rq * 2)}{self.rq}"

    def table(self, alias: str) -> str:
        return ".".join(self.q(p) for p in self.pack.tables[alias].name.split("."))

    def col(self, ref: str) -> str:
        alias, column = ref.split(".", 1)
        return f"{self.q(alias)}.{self.q(column)}"

    def expr(self, template: str) -> str:
        return PLACEHOLDER_RE.sub(lambda m: self.col(f"{m[1]}.{m[2]}"), template)

    @staticmethod
    def lit(v) -> str:
        if isinstance(v, date):
            return f"'{v.isoformat()}'"
        return "'" + str(v).replace("'", "''") + "'"

    def filter(self, f: FilterDef) -> str:
        c = self.col(f.column)
        values = f.value if isinstance(f.value, list) else [f.value]
        if f.op == "eq":
            return f"{c} = {self.lit(values[0])}"
        if f.op == "neq":
            return f"({c} IS NULL OR {c} <> {self.lit(values[0])})"
        if f.op == "in":
            return f"{c} IN ({', '.join(self.lit(v) for v in values)})"
        if f.op == "not_in":
            return f"({c} IS NULL OR {c} NOT IN ({', '.join(self.lit(v) for v in values)}))"
        if f.op == "is_null":
            return f"{c} IS NULL"
        return f"{c} IS NOT NULL"

    def select_head(self, n: int | None, distinct: bool = False) -> str:
        d = "DISTINCT " if distinct else ""
        if n is not None and self.dialect == "tsql":
            return f"SELECT {d}TOP ({n}) "
        return f"SELECT {d}"

    def tail_limit(self, n: int | None) -> str:
        return f"\nLIMIT {n}" if n is not None and self.dialect == "postgres" else ""


def _join_clauses(s: _Sql, fact: str, needed: set[str]) -> list[str]:
    g = s.pack.join_graph()
    edges: list[tuple[str, str]] = []
    for alias in sorted(needed - {fact}):
        try:
            path = nx.shortest_path(g, fact, alias)
        except nx.NetworkXNoPath:
            raise CompileError(f"No approved join from {fact} to {alias}")
        for a, b in zip(path, path[1:]):
            if (a, b) not in edges:
                edges.append((a, b))
    clauses = []
    for a, b in edges:
        on = " AND ".join(f"{s.col(f'{a}.{ca}')} = {s.col(f'{b}.{cb}')}" for ca, cb in g.edges[a, b]["columns"])
        clauses.append(f"LEFT JOIN {s.table(b)} AS {s.q(b)} ON {on}")
    return clauses


def plan_time_column(plan: Plan, pack: Pack) -> str | None:
    """The date column the plan's measures share; measures with different dates need separate queries."""
    cols = set()
    for m in plan.metrics:
        try:
            cols.add(pack.metric_time_column(plan.area, m))
        except KeyError:
            raise CompileError(f"Unknown measure {m} in {plan.area}")
    if len(cols) > 1:
        raise CompileError("These measures use different dates; ask about them separately")
    return next(iter(cols), pack.areas[plan.area].time_column)


def _where(s: _Sql, plan: Plan, pack: Pack, tcol_ref: str | None, needed: set[str]) -> list[str]:
    area = pack.areas[plan.area]
    reach = pack.reachable_aliases(plan.area)
    where = []
    for f in area.default_filters:
        needed.add(f.column.split(".")[0])
        where.append(s.filter(f))
    if plan.time:
        if not tcol_ref:
            raise CompileError(f"{plan.area} has no date column")
        needed.add(tcol_ref.split(".")[0])
        tcol = s.col(tcol_ref)
        if area.time_filter_on_date:
            tcol = f"CAST({tcol} AS DATE)"
        where.append(f"{tcol} >= {s.lit(plan.time.start)}")
        where.append(f"{tcol} < {s.lit(plan.time.end)}")
    for f in plan.filters:
        dim = pack.dimensions.get(f.dimension)
        if dim is None or dim.alias not in reach or not f.values:
            raise CompileError(f"Cannot filter on {f.dimension} in {plan.area}")
        needed.add(dim.alias)
        where.append(s.filter(FilterDef(column=dim.column, op="not_in" if f.negate else "in", value=f.values)))
    return where


def compile_detail(plan: Plan, pack: Pack, row_limit: int) -> CompiledQuery:
    """Rows of the area's fact table ("list the invoices ..."), newest first, only the pack's listed columns."""
    if plan.area not in pack.areas:
        raise CompileError(f"Unknown area {plan.area}")
    area = pack.areas[plan.area]
    if not area.detail_columns:
        raise CompileError(f"{area.label} has no list view")
    s = _Sql(pack)
    reach = pack.reachable_aliases(plan.area)
    needed = {area.fact}
    select, columns = [], []
    for i, c in enumerate(area.detail_columns):
        needed.add(c.alias)
        name = f"c{i}"
        select.append(f"{s.col(c.column)} AS {s.q(name)}")
        kind = "time" if c.format == "date" else "metric" if c.format in ("currency", "number", "integer") else "dimension"
        columns.append(ColumnMeta(name, c.label, kind, None if c.format in ("text", "date") else c.format))
    where = _where(s, plan, pack, area.time_column, needed)
    unreachable = needed - reach
    if unreachable:
        raise CompileError(f"Tables not reachable from {plan.area}: {', '.join(sorted(unreachable))}")
    cap = row_limit
    fetch = min(plan.limit, cap) if plan.limit else cap + 1
    sql = s.select_head(fetch) + ",\n       ".join(select)
    sql += f"\nFROM {s.table(area.fact)} AS {s.q(area.fact)}"
    for j in _join_clauses(s, area.fact, needed):
        sql += f"\n{j}"
    if where:
        sql += "\nWHERE " + "\n  AND ".join(where)
    if area.time_column:
        sql += f"\nORDER BY {s.col(area.time_column)} DESC" + (" NULLS LAST" if s.dialect == "postgres" else "")
    sql += s.tail_limit(fetch)
    return CompiledQuery(sql=sql, columns=columns, fetch_limit=fetch, cap=cap)


def compile_plan(plan: Plan, pack: Pack, row_limit: int) -> CompiledQuery:
    if plan.area not in pack.areas:
        raise CompileError(f"Unknown area {plan.area}")
    s = _Sql(pack)
    reach = pack.reachable_aliases(plan.area)
    needed = {pack.areas[plan.area].fact}
    select, group, columns = [], [], []
    tcol_ref = plan_time_column(plan, pack)

    for g in plan.group_by:
        if g.startswith("time:"):
            grain = g.split(":", 1)[1]
            if grain not in TIME_GRAINS or not tcol_ref:
                raise CompileError(f"Cannot group by {g}")
            e = _GRAIN_SQL[s.dialect][grain].format(c=s.col(tcol_ref))
            needed.add(tcol_ref.split(".")[0])
            columns.append(ColumnMeta(grain, _GRAIN_LABELS[grain], "time"))
            select.append(f"{e} AS {s.q(grain)}")
        else:
            dim = pack.dimensions.get(g)
            if dim is None or dim.alias not in reach:
                raise CompileError(f"Cannot group by {g} in {plan.area}")
            e = s.col(dim.column)
            needed.add(dim.alias)
            columns.append(ColumnMeta(g, dim.label, "dimension"))
            select.append(f"{e} AS {s.q(g)}")
        group.append(e)

    if not plan.metrics:
        raise CompileError("Plan has no measure")
    exprs = {}
    for m in plan.metrics:
        try:
            md = pack.metric(plan.area, m)
        except KeyError:
            raise CompileError(f"Unknown measure {m} in {plan.area}")
        needed |= md.aliases
        exprs[m] = s.expr(md.expr)
        columns.append(ColumnMeta(m, md.label, "metric", md.format))
        select.append(f"{exprs[m]} AS {s.q(m)}")

    where = _where(s, plan, pack, tcol_ref, needed)

    unreachable = needed - reach
    if unreachable:
        raise CompileError(f"Tables not reachable from {plan.area}: {', '.join(sorted(unreachable))}")

    cap = row_limit
    fetch = min(plan.limit, cap) if plan.limit else cap + 1

    sql = s.select_head(fetch) + ",\n       ".join(select)
    fact = pack.areas[plan.area].fact
    sql += f"\nFROM {s.table(fact)} AS {s.q(fact)}"
    for j in _join_clauses(s, fact, needed):
        sql += f"\n{j}"
    if where:
        sql += "\nWHERE " + "\n  AND ".join(where)
    if group:
        sql += "\nGROUP BY " + ", ".join(group)
    having = []
    for h in plan.having:
        if h.metric not in plan.metrics:
            raise CompileError(f"Condition on {h.metric}, which is not a measure of this question")
        e = exprs[h.metric]
        if h.op == "between":
            if h.value2 is None:
                raise CompileError("Range condition needs two numbers")
            having.append(f"{e} BETWEEN {_num(h.value)} AND {_num(h.value2)}")
        else:
            having.append(f"{e} {_HAVING_OPS[h.op]} {_num(h.value)}")
    if having:
        sql += "\nHAVING " + "\n   AND ".join(having)
    if plan.sort and plan.sort.metric in plan.metrics:
        sql += f"\nORDER BY {s.q(plan.sort.metric)} {'DESC' if plan.sort.desc else 'ASC'}"
    elif plan.time_grain():
        sql += f"\nORDER BY {s.q(plan.time_grain())}"
    sql += s.tail_limit(fetch)
    return CompiledQuery(sql=sql, columns=columns, fetch_limit=fetch, cap=cap)


def latest_date_sql(pack: Pack, area_name: str) -> str | None:
    """Most recent date in an area's fact table, used to explain empty answers ('data runs up to ...')."""
    area = pack.areas[area_name]
    if not area.time_column or area.time_column.split(".")[0] != area.fact:
        return None
    s = _Sql(pack)
    return f"SELECT MAX({s.col(area.time_column)}) AS {s.q('latest')}\nFROM {s.table(area.fact)} AS {s.q(area.fact)}"


def distinct_values_sql(pack: Pack, dimension: str, limit: int = 5000) -> str:
    s = _Sql(pack)
    dim = pack.dimensions[dimension]
    c = s.col(dim.column)
    return (s.select_head(limit, distinct=True) + c
            + f"\nFROM {s.table(dim.alias)} AS {s.q(dim.alias)}\nWHERE {c} IS NOT NULL"
            + s.tail_limit(limit))
