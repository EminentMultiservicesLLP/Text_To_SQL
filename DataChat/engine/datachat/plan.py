from datetime import date
from typing import Literal

from pydantic import BaseModel

TimeUnit = Literal["day", "week", "month", "quarter", "year", "custom"]


class TimeRange(BaseModel):
    start: date
    end: date  # exclusive
    label: str
    unit: TimeUnit = "custom"


class Filter(BaseModel):
    dimension: str
    values: list[str]
    negate: bool = False
    label: str | None = None  # e.g. the group name "pune" when values came from a group


class Sort(BaseModel):
    metric: str
    desc: bool = True


class Having(BaseModel):
    """A condition on a measure's total per group, e.g. branches whose billing is more than 2 crore."""
    metric: str
    op: Literal["gt", "ge", "lt", "le", "between"]
    value: float
    value2: float | None = None  # upper bound for between


class Plan(BaseModel):
    area: str
    metrics: list[str]  # measures of `area`, or "count:<dimension>"
    group_by: list[str] = []  # dimension names, or "time:<grain>"
    filters: list[Filter] = []
    having: list[Having] = []  # metric may also be a derived measure
    time: TimeRange | None = None
    sort: Sort | None = None  # metric may also be a derived measure
    limit: int | None = None
    chart_hint: Literal["pie"] | None = None
    more_metrics: list[str] = []  # "area.metric" from other areas, shown side by side
    derived: list[str] = []  # derived measures worked out from the measures above
    compare: TimeRange | None = None  # second period, shown next to `time` with the change
    share: bool = False  # add each group's % of the total
    detail: bool = False  # list rows instead of totals

    def time_grain(self) -> str | None:
        for g in self.group_by:
            if g.startswith("time:"):
                return g.split(":", 1)[1]
        return None

    def dimension_group_by(self) -> list[str]:
        return [g for g in self.group_by if not g.startswith("time:")]

    def all_metrics(self) -> list[tuple[str, str]]:
        """(area, metric) for every measure the query reads."""
        return [(self.area, m) for m in self.metrics] + [tuple(r.split(".", 1)) for r in self.more_metrics]
