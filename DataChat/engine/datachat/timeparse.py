"""
Reads dates, periods and time grains out of an (already normalized, lowercase English) question.
Every period becomes exact [start, end) dates, so the SQL never computes dates itself.
Indian conventions: dd/mm/yyyy dates, financial year April-March.
"""
import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from datachat.plan import TimeRange

MARKER = " ~ "

_MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3, "april": 4, "apr": 4,
    "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7, "august": 8, "aug": 8,
    "september": 9, "sept": 9, "sep": 9, "october": 10, "oct": 10, "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}
_MONTH_NAMES = "|".join(sorted(_MONTHS, key=len, reverse=True))
_MONTH_NAMES_NO_MAY = "|".join(sorted((m for m in _MONTHS if m != "may"), key=len, reverse=True))

_DATE = (
    r"(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|\d{4}-\d{1,2}-\d{1,2}"
    rf"|\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTH_NAMES})\s*,?\s*\d{{4}}"
    rf"|(?:{_MONTH_NAMES})\s+\d{{1,2}}(?:st|nd|rd|th)?\s*,?\s*\d{{4}})"
)
_YEAR_SPEC = r"(\d{4}|last year|this year|previous year|current year)"

_GRAINS = [
    ("weekday", r"\b(?:by weekday|weekday wise|by day of (?:the )?week|day of (?:the )?week|by day name)\b"),
    ("hour", r"\b(?:hourly|(?:by|per|each|every) hour|hour ?wise|hour-wise)\b"),
    ("day", r"\b(?:daily|day by day|(?:by|per|each|every) (?:day|date)|(?:day|date) ?wise|(?:day|date)-wise)\b"),
    ("week", r"\b(?:weekly|week on week|wow|(?:by|per|each|every) week|week ?wise|week-wise)\b"),
    ("month", r"\b(?:monthly|month on month|mom|(?:by|per|each|every) month|month ?wise|month-wise)\b"),
    ("year", r"\b(?:yearly|annually|year on year|yoy|(?:by|per|each|every) year|year ?wise|year-wise)\b"),
]
_TREND = re.compile(r"\b(?:trend|trends|over time|timeline)\b")


@dataclass
class TimeExtraction:
    ranges: list[TimeRange] = field(default_factory=list)
    grain: str | None = None
    trend: bool = False
    text: str = ""


# ── date helpers ─────────────────────────────────────────────────────────────

def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    last_day = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28,
                31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
    return date(y, m, min(d.day, last_day))


def _month_range(y: int, m: int) -> TimeRange:
    start = date(y, m, 1)
    return TimeRange(start=start, end=_add_months(start, 1), label=start.strftime("%B %Y"), unit="month")


def _year_range(y: int) -> TimeRange:
    return TimeRange(start=date(y, 1, 1), end=date(y + 1, 1, 1), label=str(y), unit="year")


def _quarter_range(y: int, q: int) -> TimeRange:
    start = date(y, 3 * (q - 1) + 1, 1)
    end = _add_months(start, 3)
    return TimeRange(start=start, end=end, label=f"Q{q} {y} ({start:%b}–{_add_months(start, 2):%b})", unit="quarter")


def _fy_range(start_year: int) -> TimeRange:
    return TimeRange(start=date(start_year, 4, 1), end=date(start_year + 1, 4, 1),
                     label=f"FY {start_year}-{str(start_year + 1)[2:]}", unit="year")


def _day_range(d: date, label: str | None = None) -> TimeRange:
    return TimeRange(start=d, end=d + timedelta(days=1), label=label or d.strftime("%d %b %Y"), unit="day")


def _resolve_year(spec: str | None, today: date) -> int | None:
    if not spec:
        return None
    if spec.isdigit():
        return int(spec)
    return today.year - 1 if spec.startswith(("last", "previous")) else today.year


def _parse_date(s: str) -> date:
    s = s.strip().replace(",", " ")
    s = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", s)
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return date(int(m[1]), int(m[2]), int(m[3]))
    m = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", s)
    if m:
        y = int(m[3])
        return date(y + 2000 if y < 100 else y, int(m[2]), int(m[1]))  # day first
    parts = s.split()
    if parts[0].isdigit():
        day, mon, year = parts[0], parts[1], parts[-1]
    else:
        mon, day, year = parts[0], parts[1], parts[-1]
    return date(int(year), _MONTHS[mon], int(day))


# ── range patterns (order matters: most specific first) ──────────────────────

def _range_patterns(today: date, bare_months: list[TimeRange] | None = None):
    week_start = today - timedelta(days=today.weekday())
    fy_start = today.year if today.month >= 4 else today.year - 1
    q_now = (today.month - 1) // 3 + 1

    def between(m):
        a, b = _parse_date(m[1]), _parse_date(m[2])
        return TimeRange(start=a, end=b + timedelta(days=1), label=f"{a:%d %b %Y} to {b:%d %b %Y}")

    def since(m):
        a = _parse_date(m[1])
        return TimeRange(start=a, end=today + timedelta(days=1), label=f"since {a:%d %b %Y}")

    def latest_year(mon: int) -> int:
        return today.year if mon <= today.month else today.year - 1

    def month_span(m):
        m1, m2 = _MONTHS[m[1]], _MONTHS[m[3]]
        y1, y2 = _resolve_year(m[2], today), _resolve_year(m[4], today)
        if y2 is None:
            y2 = (y1 + (m2 < m1)) if y1 is not None else latest_year(m2)
        if y1 is None:
            y1 = y2 if m1 <= m2 else y2 - 1
        start = date(y1, m1, 1)
        end = _add_months(date(y2, m2, 1), 1)
        if end <= start:
            raise ValueError("backwards range")
        return TimeRange(start=start, end=end, label=f"{start:%b %Y} to {date(y2, m2, 1):%b %Y}")

    def since_month(m):
        mon = _MONTHS[m[1]]
        y = _resolve_year(m[2], today) or latest_year(mon)
        start = date(y, mon, 1)
        return TimeRange(start=start, end=today + timedelta(days=1), label=f"since {start:%B %Y} (to today)")

    def last_n(m):
        n, unit = int(m[1]), m[2]
        end = today + timedelta(days=1)
        if unit == "day":
            start = today - timedelta(days=n - 1)
        elif unit == "week":
            start = today - timedelta(days=7 * n - 1)
        elif unit == "month":
            start = _add_months(today, -n) + timedelta(days=1)
        else:
            start = _add_months(today, -12 * n) + timedelta(days=1)
        return TimeRange(start=start, end=end, label=f"last {n} {unit}{'s' if n > 1 else ''} (including today)")

    def fy_relative(m):
        return _fy_range(fy_start - 1 if m[1] in ("last", "previous") else fy_start)

    def fy_explicit(m):
        a = int(m[1])
        a = a + 2000 if a < 100 else a
        if m[2]:
            return _fy_range(a)  # "fy 2025-26" names the start year
        return _fy_range(a - 1)  # "fy26" / "fy 2026" names the year it ends

    def quarter_explicit(m):
        y = _resolve_year(m[2], today) or today.year
        return _quarter_range(y, int(m[1]))

    def quarter_relative(m):
        q, y = q_now, today.year
        if m[1] in ("last", "previous"):
            q -= 1
            if q == 0:
                q, y = 4, y - 1
        return _quarter_range(y, q)

    def month_name(m):
        mon = _MONTHS[m[1]]
        y = _resolve_year(m[2], today)
        if y is None:
            r = _month_range(today.year if mon <= today.month else today.year - 1, mon)
            if bare_months is not None:
                bare_months.append(r)
            return r
        return _month_range(y, mon)

    def relative(m):
        which, unit = m[1], m[2]
        last = which in ("last", "previous", "past")
        if unit == "week":
            start = week_start - timedelta(days=7) if last else week_start
            return TimeRange(start=start, end=start + timedelta(days=7),
                             label=("last week" if last else "this week") + f" (from {start:%d %b})", unit="week")
        if unit == "month":
            first = today.replace(day=1)
            if last:
                first = _add_months(first, -1)
            return _month_range(first.year, first.month)
        return _year_range(today.year - 1 if last else today.year)

    def to_date(m):
        kind = m[1]
        if kind == "m":
            start = today.replace(day=1)
        elif kind == "y":
            start = date(today.year, 1, 1)
        else:
            start = week_start
        return TimeRange(start=start, end=today + timedelta(days=1), label=f"{kind}td (to today)")

    return [
        (rf"\b(?:between|from)\s+({_DATE})\s+(?:and|to|till|until)\s+({_DATE})", between),
        (rf"\bsince\s+({_DATE})", since),
        (rf"\bbetween\s+({_MONTH_NAMES})(?:\s+{_YEAR_SPEC})?\s+and\s+({_MONTH_NAMES})(?:\s+{_YEAR_SPEC})?\b",
         month_span),
        (rf"\b(?:from\s+)?({_MONTH_NAMES})(?:\s+{_YEAR_SPEC})?\s*(?:to|till|until|through|-)\s*"
         rf"({_MONTH_NAMES})(?:\s+{_YEAR_SPEC})?\b", month_span),
        (rf"\b(?:since|from)\s+({_MONTH_NAMES})(?:\s+{_YEAR_SPEC})?(?:\s+(?:till|until|to)\s+(?:now|date|today))?\b",
         since_month),
        (rf"\b(?:on\s+)?({_DATE})", lambda m: _day_range(_parse_date(m[1]))),
        (r"\bday before yesterday\b", lambda m: _day_range(today - timedelta(days=2), "day before yesterday")),
        (r"\b(?:last|past|previous)\s+(\d{1,3})\s+(day|week|month|year)s?\b", last_n),
        (r"\b(this|current|last|previous)\s+(?:financial year|fiscal year|fy)\b", fy_relative),
        (r"\bfy\s*'?(\d{2,4})(?:\s*-\s*(\d{2,4}))?\b", fy_explicit),
        (rf"\bq([1-4])(?:\s+(?:of\s+)?{_YEAR_SPEC})?\b", quarter_explicit),
        (r"\b(this|current|last|previous)\s+quarter\b", quarter_relative),
        (rf"\b({_MONTH_NAMES})\s+(?:of\s+)?{_YEAR_SPEC}\b", month_name),
        (rf"\b(?:in|for|during|of)\s+(may)\b()", month_name),
        (rf"\b({_MONTH_NAMES_NO_MAY})\b()", month_name),
        (r"\b(this|current|last|previous|past)\s+(week|month|year)\b", relative),
        (r"\b(w|m|y)td\b", to_date),
        (r"\btoday'?s?\b", lambda m: _day_range(today, "today")),
        (r"\byesterday'?s?\b", lambda m: _day_range(today - timedelta(days=1), "yesterday")),
        (r"(?<![\w/\-])(20\d{2})(?![\w/\-])", lambda m: _year_range(int(m[1]))),
    ]


def extract_time(text: str, today: date) -> TimeExtraction:
    out = TimeExtraction()
    work = f" {text} "

    for grain, pattern in _GRAINS:
        m = re.search(pattern, work)
        if m:
            out.grain = grain
            work = work[: m.start()] + MARKER + work[m.end():]
            break

    if _TREND.search(work):
        out.trend = True
        work = _TREND.sub(MARKER, work)

    found: list[tuple[int, TimeRange]] = []
    bare_months: list[TimeRange] = []
    for pattern, handler in _range_patterns(today, bare_months):
        regex = re.compile(pattern)
        pos = 0
        while m := regex.search(work, pos):
            try:
                r = handler(m)
            except (ValueError, KeyError):
                pos = m.end()  # an impossible date like 31/02 stays in the text and is reported as unknown
                continue
            found.append((m.start(), r))
            work = work[: m.start()] + MARKER + work[m.end():]
            pos = m.start() + len(MARKER)

    ranges = [r for _, r in sorted(found, key=lambda x: x[0])]
    # a month named without a year belongs to the one year named with it ("2025 march", "this fy jan")
    years = [r for r in ranges if r.unit == "year"]
    if len(years) == 1:
        y = years[0]
        ranges = [_month_range(y.start.year + (1 if r.start.month < y.start.month else 0), r.start.month)
                  if any(r is b for b in bare_months) else r for r in ranges]
    # "last year dec" / "2025 december": a range inside another names the narrower period, not two periods
    out.ranges = [r for r in ranges
                  if not any(o is not r and o.start >= r.start and o.end <= r.end and (o.start, o.end) != (r.start, r.end)
                             for o in ranges)]
    # "dec month", "june month": the unit word belongs to the date, it is not a request to group by month
    for r in out.ranges:
        if r.unit in ("month", "week", "year", "day"):
            work = re.sub(rf"~(\s+~)*\s+{r.unit}\b", "~", work)
    out.text = re.sub(r"\s+", " ", work).strip()
    return out


def auto_grain(r: TimeRange) -> str:
    days = (r.end - r.start).days
    if days <= 2:
        return "hour"
    if days <= 62:
        return "day"
    if days <= 731:
        return "month"
    return "year"


def union(ranges: list[TimeRange]) -> TimeRange:
    start = min(r.start for r in ranges)
    end = max(r.end for r in ranges)
    return TimeRange(start=start, end=end, label=" vs ".join(r.label for r in ranges), unit="custom")


def previous_period(r: TimeRange) -> TimeRange:
    """The period just before r, of the same kind: May for June, last FY for this FY, Q1 for Q2."""
    if r.unit == "month":
        p = _add_months(r.start, -1)
        return _month_range(p.year, p.month)
    if r.unit == "quarter":
        p = _add_months(r.start, -3)
        return _quarter_range(p.year, (p.month - 1) // 3 + 1)
    if r.unit == "year":
        return _fy_range(r.start.year - 1) if r.label.startswith("FY") else _year_range(r.start.year - 1)
    days = (r.end - r.start).days
    start = r.start - timedelta(days=days)
    return TimeRange(start=start, end=r.start, label=f"{start:%d %b %Y} to {r.start - timedelta(days=1):%d %b %Y}")


def grain_for_unit(unit: str) -> str:
    return {"day": "day", "week": "week", "month": "month", "quarter": "month", "year": "year"}.get(unit, "day")
