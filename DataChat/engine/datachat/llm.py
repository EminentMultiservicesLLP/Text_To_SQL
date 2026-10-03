"""
Question reader backed by a local language model (Ollama on the same server; nothing leaves the machine).

The model does the language work: English, Hindi/Marathi in English letters, loose phrasing, follow-ups.
It answers with one short line, a "query statement", naming only what the question says, e.g.

    area=receipts | measure=receipt_amount | by=branch | period=last 3 months | cond=> 2 crore | sort=desc

It never writes SQL and never sees data rows. The engine grounds every part of the statement against the
pack and the database's real values: unknown names or several possible matches become a question to the
user, never a guess.

CPU-only server: writing output is the slow part (a few tokens a second), so the statement is kept to a
single line with only the parts the question uses. The instructions are identical for every question and
Ollama reuses their processed state, so only the question itself is read each time. The model is loaded
once at startup and kept in RAM (keep_alive = -1), so the slow HDD read happens only once.
"""
import logging
import re
import threading
from collections import OrderedDict
from datetime import date

import httpx
from rapidfuzz import fuzz, process

from datachat import timeparse
from datachat.config import Settings
from datachat.pack import TIME_GRAINS, Pack
from datachat.parser import _UNITS, Clarify, ClarifyOption, Parser, ParseResult, Target, norm_key, parse_target
from datachat.plan import Filter, Having, Plan, Sort

logger = logging.getLogger(__name__)

OPS = ["none", "gt", "ge", "lt", "le", "between"]
_OP_SIGNS = {">": "gt", ">=": "ge", "<": "lt", "<=": "le"}
STATEMENT_START = "measure="
MAX_CACHE = 500
MAX_OPTIONS = 8
NUM_CTX = 4096  # must be the same on every call, or Ollama reloads the model and loses its cached instructions


class LlmInterpreter:
    def __init__(self, settings: Settings):
        self.url = settings.ollama_url.rstrip("/")
        self.model = settings.llm_model
        self.timeout = settings.llm_timeout_s
        self.num_thread = settings.llm_num_thread
        self._cache: OrderedDict[tuple, dict] = OrderedDict()
        self._lock = threading.Lock()
        self._prompts: dict[str, list[dict]] = {}

    # ── model calls ─────────────────────────────────────────────────────────
    def _options(self) -> dict:
        return {"num_ctx": NUM_CTX, **({"num_thread": self.num_thread} if self.num_thread else {})}

    def warm_up(self) -> None:
        try:
            httpx.post(f"{self.url}/api/generate", json={"model": self.model, "prompt": "", "keep_alive": -1,
                                                         "options": self._options()}, timeout=900)
            logger.info("LLM %s loaded", self.model)
        except httpx.HTTPError as e:
            logger.warning("LLM warm-up failed: %s", e)

    def prime(self, pack: Pack, parser: Parser, today: date) -> None:
        """Process the fixed instructions once so the first real question only pays for itself."""
        area = next(iter(pack.areas.values()))
        self._ask(pack, parser, today, "total " + area.metrics[area.default_metric].label.lower(), None)

    def _ask(self, pack: Pack, parser: Parser, today: date, question: str, previous: Plan | None,
             start: str = STATEMENT_START) -> dict | None:
        prev_line = statement_line(_statement_of(previous)) if previous else ""
        key = (pack.client, today.isoformat(), question.strip().lower(), prev_line, start)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
        user = (f"Previous statement in this conversation: {prev_line}\n"
                "If the question only changes part of it (like 'what about pune'), give the full updated "
                "statement.\n" if prev_line else "") + f"Question: {question}"
        messages = self._messages(pack, parser, today) + [{"role": "user", "content": user}]
        body = {
            "model": self.model,
            "prompt": _chatml(messages) + start,
            "raw": True,
            "stream": False,
            "keep_alive": -1,
            "options": {**self._options(), "temperature": 0, "num_predict": 60,
                        "stop": ["\n", "<|im_end|>", "<|endoftext|>"]},
        }
        try:
            r = httpx.post(f"{self.url}/api/generate", json=body, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            line = start + data["response"].rstrip()
            logger.info("LLM read %s new prompt tokens in %.1fs, wrote %s tokens in %.1fs: %s",
                        data.get("prompt_eval_count"), data.get("prompt_eval_duration", 0) / 1e9,
                        data.get("eval_count"), data.get("eval_duration", 0) / 1e9, line)
        except (httpx.HTTPError, KeyError, ValueError) as e:
            logger.warning("LLM call failed: %s", e)
            return None
        raw = parse_statement(line)
        raw["line"] = line
        if raw["answerable"] and not raw.get("greeting") and not (raw.get("area") and (raw["metrics"] or raw.get("detail"))):
            logger.warning("LLM statement not understood: %s", line)
            return None
        with self._lock:
            self._cache[key] = raw
            while len(self._cache) > MAX_CACHE:
                self._cache.popitem(last=False)
        return raw

    def _messages(self, pack: Pack, parser: Parser, today: date) -> list[dict]:
        cache_key = f"{pack.client}|{today.isoformat()}|{id(parser.index)}"
        if cache_key not in self._prompts:
            self._prompts = {cache_key: _build_messages(pack, parser, today)}
        return self._prompts[cache_key]

    # ── main entry ──────────────────────────────────────────────────────────
    def interpret(self, question: str, pack: Pack, parser: Parser, today: date, previous: Plan | None,
                  overrides: dict[str, str], learned: dict[str, str]) -> ParseResult | None:
        """A ParseResult (plan, clarify or unsupported), or None when the model is not reachable."""
        raw = self._ask(pack, parser, today, question, previous)
        if raw is not None and not raw["answerable"]:
            # small models refuse ordinary questions over a detail; one second look, still free to refuse
            raw = self._ask(pack, parser, today, question + "\n(Look again: if any measure above fits this "
                            "question, write its statement. Refuse only if no measure fits at all.)", previous) or raw
        if raw is not None and not raw["answerable"] and previous is not None:
            # a follow-up the model refused on its own ('and bhopal?'): ask again from the previous statement
            raw = self._ask(pack, parser, today, question, previous,
                            f"measure={','.join(previous.metrics)} | area={previous.area}") or raw
        if raw is None:
            return None
        context = statement_line(_statement_of(previous)) if previous else ""
        res = ground(raw, question, pack, parser, today, overrides, learned, context)
        res.trace = raw.get("line", "")
        return res


# ── the one-line statement ───────────────────────────────────────────────────

def parse_statement(line: str) -> dict:
    """'area=x | measure=a,b | by=c | grain=month | period=... | filter=dim:text; not dim:text | cond=> 2 crore
    | sort=desc | limit=5' -> the dict ground() checks. Anything malformed is left out, then checked as missing."""
    raw: dict = {"answerable": True, "metrics": [], "group_by": [], "filters": [], "period": "none",
                 "time_grain": "none", "condition": {"op": "none", "number": 0, "unit": "none"},
                 "sort": "none", "limit": 0}
    line = line.strip().strip("`").strip()
    if re.search(r"\bgreeting\b", line, re.IGNORECASE):
        raw["greeting"] = True
        return raw
    m = re.search(r"unanswerable\s*=?\s*(.*)", line, re.IGNORECASE)
    if m:
        raw["answerable"] = False
        raw["reason"] = re.split(r"(?<=[.;(])", m[1].strip(), maxsplit=1)[0].rstrip(".;( ")
        return raw
    for part in line.split("|"):
        if "=" not in part:
            continue
        k, v = (s.strip() for s in part.split("=", 1))
        k = k.lower()
        if k == "area":
            raw["area"] = v
        elif k in ("measure", "measures", "metric", "metrics"):
            raw["metrics"] = [m.strip() for m in v.split(",") if m.strip()]
        elif k in ("by", "group_by"):
            raw["group_by"] = [d.strip() for d in v.split(",") if d.strip()]
        elif k == "grain":
            raw["time_grain"] = v.lower()
        elif k == "period":
            raw["period"] = v
        elif k in ("filter", "filters"):
            for f in v.split(";"):
                f = f.strip()
                exclude = f.lower().startswith("not ")
                if exclude:
                    f = f[4:].strip()
                if ":" not in f:
                    continue
                dim, text = (s.strip() for s in f.split(":", 1))
                # small models write 'branch:lucknow,branch:bhopal' or 'state:not maharashtra'
                for piece in text.split(","):
                    piece = piece.strip().strip("\"'`").strip()
                    pdim = dim
                    m = re.match(r"(\w+)\s*:\s*(.+)", piece)
                    if m:
                        pdim, piece = m[1], m[2].strip()
                    neg = exclude
                    if re.match(r"(not|except|excluding|without)\s+", piece, re.IGNORECASE):
                        neg, piece = True, piece.split(None, 1)[1]
                    if piece:
                        raw["filters"].append({"dimension": pdim, "text": piece, "exclude": neg})
        elif k in ("cond", "condition"):
            raw["condition"] = _parse_condition(v)
        elif k == "sort" and v.lower() in ("desc", "asc"):
            raw["sort"] = v.lower()
        elif k in ("limit", "top") and v.strip().isdigit():
            raw["limit"] = int(v)
        elif k in ("compare", "vs") and v.lower() not in ("", "none", "no"):
            raw["compare"] = v
        elif k == "show" and v.lower() in ("list", "rows", "details"):
            raw["detail"] = True
        elif k == "share" and v.lower() in ("yes", "true", "1"):
            raw["share"] = True
    return raw


def _parse_condition(v: str) -> dict:
    num = r"(\d+(?:\.\d+)?)\s*([a-z]+)?"
    m = re.match(rf"\s*between\s+{num}\s+(?:and|to|-)\s+{num}", v.lower())
    if m:
        u2 = _UNITS.get(m[4] or "", 1)
        low, high = float(m[1]) * _UNITS.get(m[2] or "", u2), float(m[3]) * u2
        return {"op": "between", "number": min(low, high), "number2": max(low, high), "unit": "none"}
    m = re.match(rf"\s*(>=|<=|>|<)\s*{num}", v.lower())
    if m:
        return {"op": _OP_SIGNS[m[1]], "number": float(m[2]) * _UNITS.get(m[3] or "", 1), "unit": "none"}
    return {"op": "none", "number": 0, "unit": "none"}


def statement_line(raw: dict) -> str:
    """The inverse of parse_statement, used for worked examples and follow-ups."""
    parts = [f"measure={','.join(raw['metrics'])}", f"area={raw['area']}"]
    if raw.get("group_by"):
        parts.append(f"by={','.join(raw['group_by'])}")
    if raw.get("time_grain", "none") != "none":
        parts.append(f"grain={raw['time_grain']}")
    if raw.get("period", "none") != "none":
        parts.append(f"period={raw['period']}")
    if raw.get("compare"):
        parts.append(f"compare={raw['compare']}")
    if raw.get("filters"):
        parts.append("filter=" + "; ".join(f"{'not ' if f['exclude'] else ''}{f['dimension']}:{f['text']}"
                                           for f in raw["filters"]))
    cond = raw.get("condition") or {}
    if cond.get("op", "none") != "none":
        unit = "" if cond.get("unit", "none") == "none" else f" {cond['unit']}"
        parts.append(f"cond=between {_n(cond['number'])} and {_n(cond['number2'])}{unit}" if cond["op"] == "between"
                     else f"cond={ {v: k for k, v in _OP_SIGNS.items()}[cond['op']]} {_n(cond['number'])}{unit}")
    if raw.get("sort", "none") != "none":
        parts.append(f"sort={raw['sort']}")
    if raw.get("limit"):
        parts.append(f"limit={raw['limit']}")
    if raw.get("share"):
        parts.append("share=yes")
    if raw.get("detail"):
        parts.append("show=list")
    return " | ".join(parts)


def _chatml(messages: list[dict]) -> str:
    """Qwen's chat layout with the reply already opened and thinking skipped, so the model can only continue
    the statement instead of reasoning in prose first."""
    turns = "".join(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in messages)
    return turns + "<|im_start|>assistant\n<think>\n\n</think>\n\n"


def _n(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else str(v)


def _build_messages(pack: Pack, parser: Parser, today: date) -> list[dict]:
    fy = today.year if today.month >= 4 else today.year - 1
    lines = [
        "Turn a business-data question (English, or Hindi/Marathi in English letters) into ONE line:",
        "measure=<m1,m2> | area=<area> | by=<dims> | grain=<day|week|month|year|hour|weekday> | period=<text> | "
        "compare=<text> | filter=<dim:name; not dim:name> | cond=<op number unit> | sort=<desc|asc> | "
        "limit=<n> | share=yes | show=list",
        "Leave out parts the question doesn't use. First pick the closest measure: words in a measure's brackets "
        "mean that measure; area is the one that has it. Money coming in (paid, payment, received) is the amount received; money charged "
        "(billed, invoiced, sales) is the billed amount. Names, places and periods are checked later, so never "
        "refuse because of them. Only if the question is about something no area has (e.g. stock, weather, or a "
        "topic listed under NOT IN THIS DATA), write: measure=none | unanswerable=<short reason>. "
        "For a greeting, thanks or 'what can you do', write: measure=none | greeting. "
        "Every part of the line is supported: any period, grouping, top/bottom, comparisons, growth, two names "
        "side by side, share, conditions and lists - never refuse because of them. Questions are often short, "
        "jumbled or ungrammatical; words may come in any order - still write the statement.",
        f"Today is {today:%d %B %Y}. Financial year = April to March (this FY: April {fy}-March {fy + 1}).",
        "measure: earnings/income/sales = the money measure. Measures of different areas may be listed together "
        "(billing vs collection). 'how many <dim>s' (how many customers/branches) = count:<dim>, never a count of "
        "invoices or rows. Use a DERIVED measure only when the question asks for that ratio or difference by "
        "name; plain 'collection' is the amount received.",
        "compare: the second period for 'vs', 'compared to', 'than last year' (period=this month | "
        "compare=last month); compare=previous for growth or change without a second period. Two names compared "
        "('lucknow vs bhopal') are two filters, not compare.",
        "share=yes for 'share', 'percentage of total', 'what % each one contributes' (a measure named "
        "contribution is a measure, not share). show=list to list individual rows "
        "(only areas marked LIST): 'list', 'show all', 'details of'.",
        "by: 'by X', 'each X', 'which X', 'har X', 'X wise'. grain: only for trends, monthly, daily.",
        "period in plain English: 'last month', 'December 2025', 'last 3 months', 'this financial year', "
        "'FY 2025-26', 'April 2026 to June 2026', '01/06/2026 to 15/06/2026'.",
        "filter: one dim:name per name mentioned, separated by ';' (filter=branch:lucknow; branch:bhopal), "
        "written as the user wrote it, without the word branch/customer etc.; 'not dim:name' to exclude.",
        "cond: limit on each group's total. more than 2 crore / 2 crore se zyada / 2 cr peksha jast = > 2 crore;"
        " less than = <; at least = >=; between 1 and 2 crore.",
        "sort: desc for highest/top, asc for lowest. limit: 'top 5' = 5, 'which had the highest' = 1.",
        "",
    ]
    for aname, a in pack.areas.items():
        measures = "; ".join(f"{m} ({', '.join(dict.fromkeys([md.label.lower(), *md.synonyms[:16]]))})"
                             for m, md in a.metrics.items())
        lines.append(f"AREA {aname}: measures {measures}. dimensions: {', '.join(pack.dimensions_for(aname))}"
                     + (f". LIST of {a.detail_name or 'row'}s" if a.detail_columns else ""))
    for dname, d in pack.derived_metrics.items():
        lines.append(f"DERIVED {dname} ({', '.join([d.label.lower(), *d.synonyms[:6]])}) = {d.formula}")
    for dname, d in pack.dimensions.items():
        sample = [v for v, _ in parser.index.dim_values.get(dname, [])][:3]
        lines.append(f"DIM {dname}: {', '.join([d.label.lower(), *d.synonyms[:3]])}"
                     + (f"; e.g. {', '.join(sample)}" if sample else ""))
    reasons: dict[str, list[str]] = {}
    for term, why in pack.not_available.items():
        reasons.setdefault(why, []).append(term)
    if reasons:
        lines.append("NOT IN THIS DATA (answer unanswerable with the reason): "
                     + "; ".join(f"{', '.join(terms)} - {why}" for why, terms in reasons.items()))
    system = "\n".join(lines)

    # three worked examples built from this client's own names
    area_name, area = next(iter(pack.areas.items()))
    metric = area.default_metric
    label = area.metrics[metric].label.lower()
    dims = pack.dimensions_for(area_name)
    dim = dims[0] if dims else None
    name = "x"
    if dim:
        strip = {norm_key(s) for s in pack.dimensions[dim].value_strip_words}
        first = next((v for v, _ in parser.index.dim_values.get(dim, [])), "x")
        name = " ".join(w for w in norm_key(first).split() if w not in strip) or norm_key(first)
    base = {"area": area_name, "metrics": [metric]}
    examples = [
        (f"may i know {label} of {name} for last year dec month",
         {**base, "period": "December last year",
          "filters": [{"dimension": dim, "text": name, "exclude": False}] if dim else []}),
        (f"which all {dim or 'items'} have {label} more than 2cr in last 3 months",
         {**base, "group_by": [dim] if dim else [], "period": "last 3 months", "sort": "desc",
          "condition": {"op": "gt", "number": 2, "unit": "crore"}}),
        (f"pichhle mahine top 5 {dim or ''} konte", {**base, "group_by": [dim] if dim else [],
                                                       "period": "last month", "sort": "desc", "limit": 5}),
    ]
    other = next(((n, a) for n, a in pack.areas.items() if n != area_name), None)
    if other:
        oname, oarea = other
        om = oarea.metrics[oarea.default_metric]
        word = next((s for s in om.synonyms if " " not in s), om.label.lower())
        odim = dim if dim in pack.dimensions_for(oname) else None
        examples.append((f"{word} from {name} in june {today.year}" if odim else f"{word} in june {today.year}",
                         {"area": oname, "metrics": [oarea.default_metric], "period": f"June {today.year}",
                          "filters": [{"dimension": odim, "text": name, "exclude": False}] if odim else []}))
    examples.append((f"{label} this month vs last month by {dim or 'item'}",
                     {**base, "group_by": [dim] if dim else [], "period": "this month", "compare": "last month"}))
    count_dim = next((d for d in dims if d != dim), dim)
    if count_dim:
        examples.append((f"how many {count_dim}s had {label} this financial year",
                         {"area": area_name, "metrics": [f"count:{count_dim}"], "period": "this financial year"}))
    # one example per kind of question small models get wrong, built from this client's own words
    names = [" ".join(w for w in norm_key(v).split() if w not in strip) or norm_key(v)
             for v, _ in parser.index.dim_values.get(dim, [])][:2] if dim else []
    dim2 = dims[1] if len(dims) > 1 else dim
    examples.append((f"{label} last month", {**base, "period": "last month"}))
    if dim:
        examples.append((f"{dim}s whose {label} is less than 10 lakh this year",
                         {**base, "group_by": [dim], "period": "this year",
                          "condition": {"op": "lt", "number": 10, "unit": "lakh"}}))
        examples.append((f"share of each {dim} in {label} last year",
                         {**base, "group_by": [dim], "period": "last year", "share": True}))
    if len(names) == 2:
        examples.append((f"{label} of {names[0]} vs {names[1]} this financial year",
                         {**base, "period": "this financial year",
                          "filters": [{"dimension": dim, "text": n, "exclude": False} for n in names]}))
    if dim2:
        examples.append((f"is saal ki {label} har {dim2}", {**base, "group_by": [dim2], "period": "this year"}))
    examples.append((f"{label} growth in march {today.year} compared to march {today.year - 1}",
                     {**base, "period": f"March {today.year}", "compare": f"March {today.year - 1}"}))
    if other and dim in pack.dimensions_for(other[0]):
        examples.append((f"{label} vs {word} by {dim} last month",
                         {**base, "metrics": [metric, other[1].default_metric], "group_by": [dim],
                          "period": "last month"}))
    for dname, d in list(pack.derived_metrics.items())[:2]:
        examples.append((f"{(d.synonyms or [d.label])[0].lower()} this financial year",
                         {"area": pack.area_of_metric(d.inputs[0]), "metrics": [dname],
                          "period": "this financial year"}))
    listed = next(((n, a) for n, a in pack.areas.items() if a.detail_columns), None)
    if listed:
        examples.append((f"list all {listed[1].detail_name or 'row'}s of yesterday",
                         {"area": listed[0], "metrics": [listed[1].default_metric], "period": "yesterday",
                          "detail": True}))
    messages = [{"role": "system", "content": system}]
    for q, ans in examples:
        messages += [{"role": "user", "content": f"Question: {q}"},
                     {"role": "assistant", "content": statement_line(ans)}]
    for q, line in pack.llm_examples.items():
        messages += [{"role": "user", "content": f"Question: {q}"}, {"role": "assistant", "content": line}]
    messages += [{"role": "user", "content": "Question: what is the weather in mumbai today"},
                 {"role": "assistant", "content": "measure=none | unanswerable=no weather data"},
                 {"role": "user", "content": "Question: hello, what can you do?"},
                 {"role": "assistant", "content": "measure=none | greeting"}]
    return messages


def _statement_of(plan: Plan) -> dict:
    """The previous plan as a statement, for follow-up questions."""
    h = plan.having[0] if plan.having else None
    short = lambda r: re.sub(r"\s*\(.*?\)", "", r.label)  # noqa: E731
    return {
        "area": plan.area,
        "metrics": plan.derived or plan.metrics + [r.split(".", 1)[1] for r in plan.more_metrics],
        "group_by": plan.dimension_group_by(),
        "time_grain": plan.time_grain() or "none", "period": short(plan.time) if plan.time else "none",
        "compare": short(plan.compare) if plan.compare else "",
        "filters": [{"dimension": f.dimension, "text": f.label or ", ".join(f.values), "exclude": f.negate}
                    for f in plan.filters],
        "condition": {"op": h.op, "number": h.value, "number2": h.value2 or 0, "unit": "none"} if h else
        {"op": "none"},
        "sort": ("desc" if plan.sort.desc else "asc") if plan.sort else "none", "limit": plan.limit or 0,
        "share": plan.share, "detail": plan.detail,
    }


# ── grounding: every part of the statement is checked against the pack and real values ─────

def ground(raw: dict, question: str, pack: Pack, parser: Parser, today: date,
           overrides: dict[str, str], learned: dict[str, str], context: str = "") -> ParseResult:
    """`context` is the previous statement of the conversation: names a follow-up keeps come from there."""
    res = ParseResult(normalized=" ".join(question.lower().split()))
    if raw.get("greeting"):
        res.greeting = True
        return res
    if not raw.get("answerable", True):
        reason = (raw.get("reason") or "").strip()
        res.unsupported = ("I can't answer that from the available data" + (f": {reason}" if reason else ".")
                           + " Try something like: " + "; ".join(parser.examples()[:3]))
        return res

    # measures: the area's own, other areas' (shown side by side), count:<dimension>, or derived ones
    known = {m for a in pack.areas.values() for m in a.metrics} | set(pack.derived_metrics) \
        | {f"count:{d}" for d in pack.dimensions}
    wanted = []
    raw = dict(raw)
    for m in (m.strip() for m in raw.get("metrics") or [] if m.strip()):
        if m not in known:  # 'total billing_amount': the pack's name inside the model's wording
            m = next((k for k in sorted(known, key=len, reverse=True) if re.search(rf"(?<!\w){re.escape(k)}\b", m)), m)
        if m not in known:  # 'invoice raised', 'bing_amount': a slip in writing one of the pack's names
            close = process.extractOne(re.sub(r"\s+", "_", m.lower()), list(known), scorer=fuzz.ratio, score_cutoff=80)
            m = close[0] if close else m
        if m not in known:  # 'measure=branch': the model means how many of that field
            dim = next((d for d, dd in pack.dimensions.items()
                        if norm_key(m) in {norm_key(s) for s in [d, dd.label, *dd.synonyms]}), None)
            m = f"count:{dim}" if dim else m
        if m not in known and fuzz.ratio(m.lower(), "share") >= 65:  # the share flag written as a measure
            raw["share"] = True
            continue
        if m not in wanted:
            wanted.append(m)
    derived = [m for m in wanted if m in pack.derived_metrics]
    plain = list(dict.fromkeys(i for m in wanted for i in (pack.derived_metrics[m].inputs
                                                            if m in pack.derived_metrics else [m])))
    unknown = [m for m in plain if not m.startswith("count:") and not pack.area_of_metric(m)
               and not any(m in a.metrics for a in pack.areas.values())]
    if unknown:
        res.unsupported = (f"I don't have a measure for '{unknown[0].replace('_', ' ')}'. "
                           "Try something like: " + "; ".join(parser.examples()[:3]))
        return res
    area = raw.get("area")
    owned = [m for m in plain if not m.startswith("count:")]
    if area not in pack.areas or (owned and owned[0] not in pack.areas[area].metrics):
        area = next((a for a, ad in pack.areas.items() if owned and owned[0] in ad.metrics), area)
    if area not in pack.areas:
        res.unsupported = "I couldn't tell which data this is about. Try something like: " + \
                          "; ".join(parser.examples()[:3])
        return res
    area_def = pack.areas[area]
    metrics, more = [], []
    for m in plain:
        if m.startswith("count:"):
            if not pack.has_metric(area, m):
                what = pack.dimensions[m[6:]].label.lower() if m[6:] in pack.dimensions else m[6:]
                res.unsupported = f"{area_def.label} can't count {what}."
                return res
            metrics.append(m)
        elif m in area_def.metrics:
            metrics.append(m)
        else:
            more.append(f"{pack.area_of_metric(m)}.{m}")
    if not metrics:
        metrics = [area_def.default_metric]
        if not more:
            res.assumptions.append(f"No measure named, so showing {area_def.metrics[metrics[0]].label}.")
    lead = wanted[0] if wanted and wanted[0] in pack.derived_metrics else metrics[0]
    area_dims = set(pack.dimensions_for(area))

    group_by = []
    grain = raw.get("time_grain")
    for d in raw.get("group_by") or []:
        as_grain = {"daily": "day", "weekly": "week", "monthly": "month", "yearly": "year"}.get(d.lower(), d.lower())
        if d not in area_dims and as_grain in TIME_GRAINS:
            grain = as_grain
            continue
        if d not in area_dims:
            res.unsupported = (f"{area_def.label} can't be split by {pack.dimensions[d].label}"
                               if d in pack.dimensions else "I couldn't place one of the groupings.")
            return res
        if d not in group_by:
            group_by.append(d)

    # filters: names are matched to real values; one match is used, several are asked, none is asked
    extra: dict[str, set[Target]] = {}
    for term, target in {**learned, **overrides}.items():
        targets = parse_target(target, pack)
        if targets:
            extra[norm_key(term)] = targets
    raw_filters = list(raw.get("filters") or [])
    compare_text = re.sub(r"\(.*?\)", " ", raw.get("compare") or "").strip()
    if compare_text and compare_text.lower() != "previous" \
            and not timeparse.extract_time(parser.normalize(compare_text), today).ranges:
        # 'maharashtra vs gujarat': the second name, not a second period
        m = re.match(r"(\w+)\s*:\s*(.+)", compare_text)
        dim, text = (m[1], m[2]) if m else (group_by[0] if group_by else None, compare_text)
        raw_filters.append({"dimension": dim, "text": text, "exclude": False})
        compare_text = ""
    filters: dict[tuple[str, bool], Filter] = {}
    for f in raw_filters:
        text = (f.get("text") or "").strip()
        dim = f.get("dimension")
        if not text:
            continue
        as_time = timeparse.extract_time(parser.normalize(text), today)
        if as_time.ranges and not re.sub(r"[~\s]", "", as_time.text):
            continue
        if dim not in pack.dimensions and re.fullmatch(r"[\d\s/\-]+", text):
            continue  # a period the model put under a made-up field ('financial_year:2025-26')
        chosen = extra.get(norm_key(text))
        field_word = next((d for d, dd in pack.dimensions.items()
                           if norm_key(text) in {norm_key(s) for s in [dd.label, *dd.synonyms]}), None)
        if chosen is None and field_word:
            # 'customer:clients' names the field itself: a split by it, not a name
            if field_word in area_dims and field_word not in group_by:
                group_by.append(field_word)
            continue
        if chosen is None and not _said(text, f"{question} {context}"):
            res.assumptions.append(f"Ignored the name '{text}': it isn't in your question.")
            continue
        if chosen and any(t.kind == "ignore" for t in chosen):
            res.assumptions.append(f"Ignored '{text}' as you asked.")
            continue
        if chosen is None:
            found = _find_values(text, dim, area_dims, pack, parser)
            if len(found) != 1:
                res.clarify = _value_question(text, dim, found, pack)
                return res
            chosen = found
        for t in chosen:
            if t.name not in area_dims:
                res.unsupported = f"{area_def.label} can't be filtered by {pack.dimensions[t.name].label}."
                return res
            values = pack.dimensions[t.name].groups[t.value] if t.kind == "group" else [t.value]
            key = (t.name, bool(f.get("exclude")))
            flt = filters.setdefault(key, Filter(dimension=t.name, values=[], negate=key[1]))
            flt.values.extend(v for v in values if v not in flt.values)
            if t.kind == "group":
                flt.label = t.value

    # period: the model's plain-English phrase (never the user's own words), turned into exact dates
    time_range = None
    period = re.sub(r"\(.*?\)", " ", raw.get("period") or "").strip()
    ranges = []
    if period and period.lower() != "none":
        ranges = _read_period(period, parser, today)
        if not ranges:
            res.clarify = Clarify(question=f"I couldn't work out the dates for '{period}'. Could you give them "
                                           "like 'June 2026' or '1 June 2026 to 15 June 2026'?", term=period,
                                  options=[], kind="unknown_word")
            return res
    two_periods = None
    if len(ranges) == 2 and not compare_text and grain in (None, "none"):
        two_periods = ranges  # two separate periods without a trend grain: a comparison
    elif ranges:
        time_range = ranges[0] if len(ranges) == 1 else timeparse.union(ranges)
    if two_periods:
        time_range = two_periods[0]
    if time_range and not area_def.time_column:
        res.unsupported = f"{area_def.label} has no dates to filter on."
        return res
    if time_range is None and area_def.time_column:
        res.assumptions.append("No date given, so this covers all dates.")

    compare_range = None
    compare = compare_text
    if compare.lower() == "previous" and time_range is not None and grain in (None, "none"):
        compare_range = timeparse.previous_period(time_range)
        res.assumptions.append(f"Compared with the period before: {compare_range.label}.")
    elif compare and compare.lower() != "previous" and time_range is not None:
        cranges = _read_period(compare, parser, today)
        if len(cranges) != 1:
            res.clarify = Clarify(question=f"Which period should I compare with? I couldn't read '{compare}'.",
                                  term=compare, options=[], kind="unknown_word")
            return res
        compare_range = cranges[0]
        if (compare_range.start, compare_range.end) == (time_range.start, time_range.end):
            compare_range = None
    elif two_periods:
        compare_range = two_periods[1]

    if grain in TIME_GRAINS and area_def.time_column:
        group_by.append(f"time:{grain}")

    plan = Plan(area=area, metrics=metrics, group_by=group_by, filters=list(filters.values()), time=time_range,
                more_metrics=more, derived=derived, compare=compare_range, share=bool(raw.get("share")))

    if raw.get("detail"):
        if not area_def.detail_columns:
            res.unsupported = f"I can show totals for {area_def.label}, but not a list of individual rows."
            return res
        plan.detail, plan.group_by, plan.more_metrics, plan.derived = True, [], [], []
        res.assumptions = [a for a in res.assumptions if not a.startswith("No measure named")]
        plan.compare, plan.share = None, False
        limit = raw.get("limit")
        plan.limit = limit if isinstance(limit, int) and limit > 0 else None
        res.assumptions.insert(0, "Understood as: " + describe_statement(plan, pack) + ".")
        res.plan = plan
        return res

    cond = raw.get("condition") or {}
    if cond.get("op") in OPS[1:] and cond.get("number"):
        mult = _UNITS.get(cond.get("unit") or "", 1)
        n1, n2 = float(cond["number"]) * mult, float(cond.get("number2") or 0) * mult
        if cond["op"] == "between":
            plan.having = [Having(metric=lead, op="between", value=min(n1, n2), value2=max(n1, n2))]
        else:
            plan.having = [Having(metric=lead, op=cond["op"], value=n1)]

    sort, limit = raw.get("sort"), raw.get("limit")
    if sort in ("desc", "asc") and plan.group_by:
        plan.sort = Sort(metric=lead, desc=sort == "desc")
    elif plan.dimension_group_by() and not plan.time_grain():
        plan.sort = Sort(metric=lead, desc=True)
    if isinstance(limit, int) and limit > 0 and plan.group_by:
        plan.limit = limit

    res.assumptions.insert(0, "Understood as: " + describe_statement(plan, pack) + ".")
    res.plan = plan
    return res


def _said(text: str, where: str) -> bool:
    """Whether a name the model wrote was really in the user's words (typos allowed), so it can't add its own."""
    words = norm_key(where).split()
    return all(any(fuzz.ratio(w, u) >= 80 for u in words) for w in norm_key(text).split() if len(w) > 2)


def _read_period(text: str, parser: Parser, today: date) -> list:
    """Exact dates for the model's period phrase ('June 2026', 'FY 2025-26', '01/06/2026 to 15/06/2026')."""
    norm = parser.normalize(text)
    ranges = timeparse.extract_time(norm, today).ranges
    if len(ranges) == 2 and re.search(r"\b(?:to|till|until)\b", norm):
        joined = timeparse.extract_time(f"from {norm}", today).ranges
        if len(joined) == 1:
            return joined
    return ranges


def _find_values(text: str, dim: str | None, area_dims: set[str], pack: Pack, parser: Parser) -> set[Target]:
    """Values the user may mean by `text`, preferring the dimension the model chose."""
    key = norm_key(text)
    index = parser.index

    def in_dims(dims) -> set[Target]:
        hits = {t for t in index.entries.get(key, set()) if t.kind in ("value", "group") and t.name in dims}
        if hits:
            return hits
        words = set(key.split())
        for d in dims:
            words_d = words - {w for s in pack.dimensions[d].synonyms + [pack.dimensions[d].label]
                               for w in norm_key(s).split()}
            if not words_d:
                continue
            hits |= {Target("value", d, value=v) for v, vw in index.dim_values.get(d, []) if words_d <= vw}
        if hits:
            return hits
        for d in dims:
            # typos: compare without the field's own words ('lucknwo' vs 'LUCKNOW BRANCH' -> 'lucknow')
            strip = {norm_key(s) for s in pack.dimensions[d].value_strip_words + pack.dimensions[d].synonyms}
            bare_key = " ".join(w for w in key.split() if w not in strip) or key
            choices = {}
            for v, _ in index.dim_values.get(d, []):
                choices.setdefault(" ".join(w for w in norm_key(v).split() if w not in strip) or norm_key(v), []).append(v)
            for k, _s, _ in process.extract(bare_key, list(choices), scorer=fuzz.ratio, score_cutoff=85, limit=5):
                hits |= {Target("value", d, value=v) for v in choices[k]}
        return hits

    if dim in area_dims:
        found = in_dims([dim])
        if found:
            return found
    return in_dims(sorted(area_dims))


def _value_question(text: str, dim: str | None, found: set[Target], pack: Pack) -> Clarify:
    options = [ClarifyOption(f"{t.value} ({pack.dimensions[t.name].label})", {text: t.to_str()})
               for t in sorted(found, key=lambda t: (t.name, str(t.value)))][:MAX_OPTIONS]
    label = pack.dimensions[dim].label.lower() if dim in pack.dimensions else "name"
    if not found:
        question = f"I couldn't find '{text}' in the {label} list. Please check the spelling, or ignore it."
    elif len(found) > MAX_OPTIONS:
        question = f"'{text}' matches {len(found)} names. Which one do you mean? (or type a more exact name)"
    else:
        question = f"'{text}' matches more than one name. Which one do you mean?"
    return Clarify(question=question, term=text,
                   options=options + [ClarifyOption("Ignore this name", {text: "ignore"})], kind="ambiguous")


def describe_statement(plan: Plan, pack: Pack) -> str:
    from datachat.answer import format_value, measure_def
    area = pack.areas[plan.area]
    if plan.detail:
        parts = [f"list of {area.detail_name or 'row'}s"]
    else:
        names = plan.derived + plan.metrics + [r.split(".", 1)[1] for r in plan.more_metrics]
        parts = [" and ".join(dict.fromkeys(measure_def(pack, plan, m).label for m in names))]
    dims = [pack.dimensions[d].label for d in plan.dimension_group_by()]
    if dims:
        parts.append("by " + ", ".join(dims))
    if plan.time_grain():
        parts.append(f"per {plan.time_grain()}")
    text = " ".join(parts)
    if plan.time:
        text += f", {plan.time.label}"
    if plan.compare:
        text += f" compared with {plan.compare.label}"
    for f in plan.filters:
        text += f", {'excluding' if f.negate else 'only'} {pack.dimensions[f.dimension].label} " \
                f"{f.label or ', '.join(f.values[:3])}{' …' if len(f.values) > 3 else ''}"
    for h in plan.having:
        md = measure_def(pack, plan, h.metric)
        words = {"gt": "more than", "ge": "at least", "lt": "less than", "le": "at most"}
        amount = format_value(h.value, md.format, pack.formatting)
        text += (f", where {md.label.lower()} is between {amount} and "
                 f"{format_value(h.value2, md.format, pack.formatting)}" if h.op == "between" else
                 f", where {md.label.lower()} is {words[h.op]} {amount}")
    if plan.share:
        text += ", with each one's share of the total"
    if plan.sort and plan.limit:
        text += f", {'top' if plan.sort.desc else 'bottom'} {plan.limit}"
    return text
