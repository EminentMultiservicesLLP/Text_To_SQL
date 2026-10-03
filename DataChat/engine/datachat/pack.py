"""
Client semantic pack: everything client-specific (tables, joins, metrics, dimensions,
business words) lives in packs/<client>/semantic.yaml. The engine code never names a client.
"""
import re
from pathlib import Path
from typing import Literal

import networkx as nx
import yaml
from pydantic import BaseModel, Field, model_validator

PLACEHOLDER_RE = re.compile(r"\{(\w+)\.(\w+)\}")
TIME_GRAINS = ("hour", "day", "week", "month", "year", "weekday")


class TableDef(BaseModel):
    name: str  # schema-qualified, e.g. dbo.Rista_SaleInvoices or public.orders


class JoinDef(BaseModel):
    """`from_` rows point at exactly one `to` row (many-to-one). one_to_one joins work both ways."""

    from_: str = Field(alias="from")
    to: str
    columns: list[tuple[str, str]]  # [(from_column, to_column)]
    one_to_one: bool = False


class FilterDef(BaseModel):
    column: str  # alias.Column
    op: Literal["eq", "neq", "in", "not_in", "is_null", "not_null"]
    value: str | list[str] | None = None


class MetricDef(BaseModel):
    expr: str  # SQL aggregate with {alias.Column} placeholders
    label: str
    synonyms: list[str] = []
    format: Literal["currency", "number", "integer", "percent"] = "number"
    time_column: str | None = None  # dates for this measure, when not the area's (e.g. date of leaving)
    snapshot: bool = False  # a current count (headcount): a date range does not apply to it

    @property
    def aliases(self) -> set[str]:
        return {a for a, _ in PLACEHOLDER_RE.findall(self.expr)}


class DerivedDef(BaseModel):
    """A measure worked out from other measures' totals, e.g. collection % = receipts / billing * 100."""
    label: str
    formula: str  # measure names, numbers, + - * / and brackets
    format: Literal["currency", "number", "integer", "percent"] = "number"
    synonyms: list[str] = []
    note: str | None = None  # shown with every answer that uses it

    @property
    def inputs(self) -> list[str]:
        return list(dict.fromkeys(re.findall(r"[A-Za-z_]\w*", self.formula)))


class DetailColumn(BaseModel):
    column: str  # alias.Column
    label: str
    format: Literal["currency", "number", "integer", "percent", "date", "text"] = "text"

    @property
    def alias(self) -> str:
        return self.column.split(".", 1)[0]


class DimensionDef(BaseModel):
    column: str  # alias.Column
    label: str
    synonyms: list[str] = []
    values: list[str] | None = None  # static list; otherwise loaded from the database
    load_values: bool = False
    groups: dict[str, list[str]] = {}  # business groupings, e.g. region -> branch codes
    # words that may be left out when a user names a value, e.g. [branch] lets "pune" find "PUNE BRANCH"
    value_strip_words: list[str] = []

    @property
    def alias(self) -> str:
        return self.column.split(".", 1)[0]


class AreaDef(BaseModel):
    label: str
    fact: str
    time_column: str | None = None
    # Compare dates on CAST(column AS DATE). Needed for SQL Server datetimeoffset columns, where comparing
    # against a plain date literal would use UTC instead of the stored local offset.
    time_filter_on_date: bool = False
    synonyms: list[str] = []
    default_metric: str
    default_time: str | None = None  # e.g. "this month"; None means all dates
    default_filters: list[FilterDef] = []
    # "month": the fact holds one row per month, so date ranges are widened to whole months
    time_resolution: Literal["day", "month"] = "day"
    metrics: dict[str, MetricDef]
    detail_columns: list[DetailColumn] = []  # columns for "list the invoices ..." questions
    detail_name: str | None = None  # what one row is called, e.g. "invoice"
    examples: list[str] = []

    @model_validator(mode="after")
    def _default_metric_exists(self):
        if self.default_metric not in self.metrics:
            raise ValueError(f"default_metric '{self.default_metric}' is not a metric of this area")
        return self


class DatabaseDef(BaseModel):
    dialect: Literal["postgres", "tsql"]
    dsn_env: str


class Formatting(BaseModel):
    currency_symbol: str = "₹"
    indian_grouping: bool = True


class Pack(BaseModel):
    client: str
    display_name: str
    database: DatabaseDef
    formatting: Formatting = Formatting()
    tables: dict[str, TableDef]
    joins: list[JoinDef] = []
    dimensions: dict[str, DimensionDef] = {}
    areas: dict[str, AreaDef]
    derived_metrics: dict[str, DerivedDef] = {}
    lexicon: dict[str, str] = {}  # client-specific word replacements, applied like the shared lexicon
    not_available: dict[str, str] = {}  # word or phrase -> why this data can't answer it
    llm_examples: dict[str, str] = {}  # question -> statement line, extra worked examples for the language model

    def unavailable(self, normalized_question: str) -> str | None:
        """The reason when the question asks for something this client's data doesn't hold."""
        text = f" {normalized_question} "
        for term, reason in self.not_available.items():
            if re.search(rf"\b{re.escape(term.lower())}", text):
                return reason
        return None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def _references_exist(self):
        def check_alias(alias: str, where: str):
            if alias not in self.tables:
                raise ValueError(f"{where}: unknown table alias '{alias}'")

        for j in self.joins:
            check_alias(j.from_, "join")
            check_alias(j.to, "join")
        for name, d in self.dimensions.items():
            check_alias(d.alias, f"dimension {name}")
        for aname, a in self.areas.items():
            check_alias(a.fact, f"area {aname}")
            if a.time_column:
                check_alias(a.time_column.split(".")[0], f"area {aname} time_column")
            for mname, m in a.metrics.items():
                for alias in m.aliases:
                    check_alias(alias, f"metric {aname}.{mname}")
                if m.time_column:
                    check_alias(m.time_column.split(".")[0], f"metric {aname}.{mname} time_column")
            for c in a.detail_columns:
                check_alias(c.alias, f"area {aname} detail column")
        owners: dict[str, list[str]] = {}
        for aname, a in self.areas.items():
            for mname in a.metrics:
                owners.setdefault(mname, []).append(aname)
        for dname, d in self.derived_metrics.items():
            if dname in owners:
                raise ValueError(f"derived measure '{dname}' has the same name as a measure")
            if re.search(r"[^\w\s.+\-*/()]", d.formula):
                raise ValueError(f"derived measure '{dname}': only names, numbers, + - * / ( ) are allowed")
            for name in d.inputs:
                if len(owners.get(name, [])) != 1:
                    raise ValueError(f"derived measure '{dname}': '{name}' must be a measure of exactly one area")
        return self

    # ── measures ────────────────────────────────────────────────────────────
    def area_of_metric(self, metric: str) -> str | None:
        """The one area that owns a measure name, or None (unknown, or found in several areas)."""
        owners = [a for a, ad in self.areas.items() if metric in ad.metrics]
        return owners[0] if len(owners) == 1 else None

    def metric(self, area: str, name: str) -> MetricDef:
        """A pack measure, or 'count:<dimension>' = how many different values of that dimension."""
        if name.startswith("count:"):
            dim = self.dimensions.get(name[6:])
            if dim is None or dim.alias not in self.reachable_aliases(area):
                raise KeyError(name)
            plural = dim.synonyms[1] if len(dim.synonyms) > 1 else dim.label.lower() + "s"
            return MetricDef(expr=f"COUNT(DISTINCT {{{dim.column}}})", label=f"Number of {plural}",
                             format="integer")
        return self.areas[area].metrics[name]

    def has_metric(self, area: str, name: str) -> bool:
        try:
            self.metric(area, name)
            return True
        except KeyError:
            return False

    def metric_time_column(self, area: str, name: str) -> str | None:
        m = self.metric(area, name)
        return m.time_column or self.areas[area].time_column

    # ── join graph ──────────────────────────────────────────────────────────
    def join_graph(self) -> nx.DiGraph:
        g = nx.DiGraph()
        g.add_nodes_from(self.tables)
        for j in self.joins:
            g.add_edge(j.from_, j.to, columns=j.columns)
            if j.one_to_one:
                g.add_edge(j.to, j.from_, columns=[(b, a) for a, b in j.columns])
        return g

    def reachable_aliases(self, area: str) -> set[str]:
        g = self.join_graph()
        fact = self.areas[area].fact
        return {fact} | nx.descendants(g, fact)

    def dimensions_for(self, area: str) -> list[str]:
        reach = self.reachable_aliases(area)
        return [name for name, d in self.dimensions.items() if d.alias in reach]

    def allowed_table_names(self) -> set[str]:
        return {t.name.lower() for t in self.tables.values()}


def load_pack(path: Path) -> Pack:
    with open(path, encoding="utf-8-sig") as f:
        return Pack.model_validate(yaml.safe_load(f))


def load_packs(packs_dir: Path) -> dict[str, Pack]:
    packs = {}
    for file in sorted(packs_dir.glob("*/semantic.yaml")):
        pack = load_pack(file)
        packs[pack.client] = pack
    return packs


def load_lexicon(packs_dir: Path) -> dict[str, str]:
    """Shared word/phrase replacements (romanized Hindi, Marathi, spelling variants)."""
    lex: dict[str, str] = {}
    for file in sorted((packs_dir / "_lexicon").glob("*.yaml")):
        with open(file, encoding="utf-8-sig") as f:
            data = yaml.safe_load(f) or {}
        for key, value in (data.get("replacements") or {}).items():
            lex[str(key).lower().strip()] = str(value).lower().strip()
    return lex
