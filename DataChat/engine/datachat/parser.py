"""
Rule-based question reader (no LLM).

Turns a question into a Plan using only the words defined in the client pack, the shared
lexicon, and words users have taught it. Anything it cannot place is reported back as an
unknown word or a clarifying question; it never guesses a table, column, or value.
"""
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from rapidfuzz import fuzz, process

from datachat import timeparse
from datachat.pack import Pack
from datachat.plan import Filter, Having, Plan, Sort, TimeRange

STOPWORDS = {
    # English filler
    "a", "an", "the", "of", "for", "in", "on", "at", "to", "from", "with", "and", "or", "is", "are", "was",
    "were", "be", "been", "it", "its", "this", "that", "these", "those", "me", "my", "our", "we", "us", "you",
    "i", "what", "whats", "which", "who", "how", "much", "many", "show", "give", "tell", "list", "get", "find",
    "display", "see", "view", "please", "pls", "plz", "can", "could", "would", "will", "do", "does", "did",
    "done", "have", "has", "had", "all", "total", "overall", "value", "values", "number", "data", "report",
    "details", "detail", "summary", "by", "per", "each", "every", "across", "wise", "breakdown", "break",
    "down", "split", "vs", "versus", "compare", "compared", "comparison", "against", "between", "than",
    "made", "make", "generated", "earned", "got", "sold", "selling", "happened", "there", "any", "some",
    "about", "only", "also", "same", "again", "now", "then", "instead", "just", "so", "far", "till", "until",
    "upto", "up", "as", "well", "not", "except", "excluding", "exclude", "without", "other", "others",
    "where", "when", "whose", "done", "doing", "performance", "perform", "performed", "did", "count",
    "amount", "under", "over", "during", "into", "out", "time", "period", "range", "wise", "graph", "chart",
    "table", "plot", "trend", "please", "thanks", "thank", "ok", "okay", "hi", "hello", "hey",
    "may", "might", "know", "want", "wanted", "need", "needed", "like", "let", "lets", "kindly", "check",
    "fetch", "provide", "provided", "shown", "much", "whole", "entire", "full", "complete", "happen", "look",
    "looking", "tell", "told", "info", "information", "figure", "figures", "currently", "more", "less",
    "rs", "rupee", "rupees", "inr", "amt", "raised", "issued", "created", "booked", "recorded", "too",
    "similarly", "currently", "present", "right", "today's", "everything", "anything", "whom", "whose",
    # Hindi / Marathi filler (romanized)
    "kya", "hai", "hain", "tha", "thi", "the", "ki", "ka", "ke", "ko", "mein", "me", "se", "par", "pe",
    "aur", "ya", "bhi", "hi", "hua", "hui", "hue", "hota", "hoti", "kuch", "sab", "sabhi", "kaun", "konsa",
    "kaunsa", "kon", "kaise", "kitna", "la", "cha", "chi", "che", "chya", "ahe", "aahe", "hote", "hoti",
    "kay", "kaay", "ani", "va", "madhe", "madhye", "sathi", "kiti", "wala", "wale", "wali", "na", "ne",
    "jinka", "jinki", "jinke", "jinhone", "jiska", "jiski", "jiske", "jo", "jis", "asnare", "asnarya", "asleli",
    "asle", "astil", "jyanchi", "jyancha", "jyanche", "jyanni", "jya", "konte", "konta", "konti", "sang", "sanga",
    "konatya", "konatye", "konata", "kontya", "kuthlya", "kuthla", "kaunse", "kaunsi", "pan", "suddha",
}
_NEGATIONS = {"not", "except", "excluding", "exclude", "without", "other", "minus"}
_GROUP_CUES = {"by", "per", "each", "every", "across", "which", "wise", "breakdown", "split", "distribution"}
_TOP_N = re.compile(
    r"\b(?:(top|best|highest|first|bottom|worst|lowest)\s+(\d{1,4})|(\d{1,4})\s+(top|best|highest|bottom|worst|lowest))\b"
)
_SUPER_DESC = re.compile(r"\b(?:highest|most|best|maximum|max|top|biggest|largest|peak)\b")
_SUPER_ASC = re.compile(r"\b(?:lowest|least|worst|minimum|min|smallest|bottom)\b")
_UNITS = {"crore": 1e7, "crores": 1e7, "cr": 1e7, "crs": 1e7, "karod": 1e7, "karor": 1e7, "koti": 1e7,
          "lakh": 1e5, "lakhs": 1e5, "lac": 1e5, "lacs": 1e5, "lk": 1e5, "l": 1e5,
          "thousand": 1e3, "hazar": 1e3, "hazaar": 1e3, "k": 1e3,
          "million": 1e6, "millions": 1e6, "mn": 1e6, "billion": 1e9, "billions": 1e9, "bn": 1e9}
_UNIT_RE = "|".join(sorted(_UNITS, key=len, reverse=True))
_CMP_BEFORE = {
    "gt": r"more than|greater than|higher than|bigger than|above|over|exceeding|exceeds|exceed|beyond",
    "ge": r"at least|atleast|minimum of|min of|not less than",
    "lt": r"less than|lower than|smaller than|below|under",
    "le": r"at most|atmost|maximum of|max of|not more than|up to|upto",
}
_THRESHOLD_BEFORE = re.compile(
    r"\b(?:" + "|".join(f"(?P<{op}>{words})" for op, words in _CMP_BEFORE.items()) + r")\s+(?:rs\s+|inr\s+)?"
    rf"(?P<n>\d+(?:\.\d+)?)\s*(?P<u>{_UNIT_RE})?\b(?:\s+(?:rupees?|rs))?")
# Hinglish / Marathi put the comparison after the number: "2 crore se zyada", "50 lakh peksha jast"
_THRESHOLD_AFTER = re.compile(
    rf"\b(?P<n>\d+(?:\.\d+)?)\s*(?P<u>{_UNIT_RE})?\s+(?:(?:rupees?|rs)\s+)?(?:se|peksha|pekshya|pexa|or)\s+"
    r"(?P<dir>zyada|jyada|jada|jaada|adhik|jast|jasta|upar|more|kam|kami|niche|less)\b")
_THRESHOLD_BETWEEN = re.compile(
    rf"\bbetween\s+(?:rs\s+)?(?P<n>\d+(?:\.\d+)?)\s*(?P<u>{_UNIT_RE})?\s+(?:and|to|-)\s+(?:rs\s+)?"
    rf"(?P<n2>\d+(?:\.\d+)?)\s*(?P<u2>{_UNIT_RE})?\b(?:\s+(?:rupees?|rs))?")


@dataclass
class Threshold:
    op: str  # gt | ge | lt | le | between
    value: float
    value2: float | None = None


def _extract_threshold(work: str) -> tuple[Threshold | None, str]:
    """Pull 'more than 2 crore' out of the text; the rest is parsed as usual."""
    def amount(n: str, u: str | None) -> float:
        return float(n) * (_UNITS[u] if u else 1)

    m = _THRESHOLD_BETWEEN.search(work)
    if m:
        u2 = m["u2"]
        low, high = amount(m["n"], m["u"] or u2), amount(m["n2"], u2)
        t = Threshold("between", min(low, high), max(low, high))
    elif m := _THRESHOLD_BEFORE.search(work):
        op = next(k for k in _CMP_BEFORE if m[k])
        t = Threshold(op, amount(m["n"], m["u"]))
    elif m := _THRESHOLD_AFTER.search(work):
        op = "lt" if m["dir"] in ("kam", "kami", "niche", "less") else "gt"
        if m["dir"] in ("more", "less"):  # "2 crore or more" / "or less" include the number
            op = "ge" if op == "gt" else "le"
        t = Threshold(op, amount(m["n"], m["u"]))
    else:
        return None, work
    return t, work[: m.start()] + timeparse.MARKER + work[m.end():]
_PIE = re.compile(r"\b(?:share|proportion|percentage|percent|contribution|mix)\b")
_UNIT_WORDS = {"hour": "hour", "day": "day", "date": "day", "week": "week", "month": "month", "year": "year",
               "weekday": "weekday"}
_GREETINGS = {"hi", "hello", "hey", "namaste", "namaskar", "thanks", "thank you", "ok", "okay", "help",
              "what can you do", "what can i ask", "what can i ask you", "how to use", "how does this work"}
GROWTH_WORDS = r"growth|grew|grown|increase|increased|decrease|decreased|change|changed|difference|badhot|vadh"
_GROWTH = re.compile(rf"\b(?:{GROWTH_WORDS})\b")
_COMPARE = re.compile(rf"\b(?:vs|versus|compared?(?: (?:to|with))?|comparison(?: with)?|against|{GROWTH_WORDS})\b")
_SAME_AGAIN = re.compile(r"\b(?:same|also|similarly|too|bhi|pan|suddha|what about|how about)\b")
_LIST = re.compile(r"^\s*(?:list(?: out)?(?: all| of)?|show (?:me )?all|show (?:me )?the list of|details of|detail of)\b")
_COUNT = re.compile(r"\b(?:how many|number of|no of|count of|kitne|kitni|kiti)\b")
COUNT_MARK = "countof"
MAX_NGRAM = 5
_KIND_PRIORITY = ["metric", "group", "value", "dimension"]


def norm_key(s: str) -> str:
    return " ".join(re.findall(r"\w+", s.lower()))


def _singular(phrase: str) -> str | None:
    words = phrase.split()
    w = words[-1]
    if len(w) > 4 and w.endswith("ies"):
        w = w[:-3] + "y"
    elif len(w) > 4 and w.endswith(("ches", "shes", "xes", "ses")):
        w = w[:-2]
    elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    else:
        return None
    return " ".join(words[:-1] + [w])


_STEM_SUFFIXES = ("ations", "ation", "ments", "ment", "ions", "ion", "ings", "ing", "ies", "ed", "es", "s", "y")


def _stem(word: str) -> str:
    """Crude stem so 'collected', 'collection', 'collections' meet at 'collect'. Used for measure/field words only."""
    for suf in _STEM_SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 4:
            return word[: -len(suf)]
    return word


# ── targets ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Target:
    kind: str  # metric | dimension | value | group | area | ignore
    name: str = ""
    area: str | None = None
    value: str | None = None

    def to_str(self) -> str:
        if self.kind in ("value", "group"):
            return f"{self.kind}:{self.name}={self.value}"
        if self.kind == "ignore":
            return "ignore"
        return f"{self.kind}:{self.name}"


def parse_target(s: str, pack: Pack) -> set[Target]:
    """Parse "metric:revenue", "dimension:branch", "value:branch=PUNE001", "group:branch=pune", "ignore"."""
    s = s.strip()
    if s == "ignore":
        return {Target("ignore")}
    kind, _, rest = s.partition(":")
    if kind == "metric":
        return {Target("metric", rest, area=a) for a, ad in pack.areas.items() if rest in ad.metrics}
    if kind == "dimension" and rest in pack.dimensions:
        return {Target("dimension", rest)}
    if kind == "area" and rest in pack.areas:
        return {Target("area", rest)}
    if kind in ("value", "group"):
        dim, _, value = rest.partition("=")
        if dim in pack.dimensions and value:
            if kind == "group" and value not in pack.dimensions[dim].groups:
                return set()
            return {Target(kind, dim, value=value)}
    return set()


def describe_target(t: Target, pack: Pack) -> str:
    if t.kind == "metric":
        return f"{pack.areas[t.area].metrics[t.name].label} (measure)"
    if t.kind == "dimension":
        return f"{pack.dimensions[t.name].label} (grouping)"
    if t.kind == "value":
        return f"{t.value} ({pack.dimensions[t.name].label})"
    if t.kind == "group":
        return f"{t.value} ({pack.dimensions[t.name].label} group)"
    if t.kind == "area":
        return pack.areas[t.name].label
    return "Ignore this word"


# ── term index ───────────────────────────────────────────────────────────────

class TermIndex:
    """Every phrase the pack knows, mapped to what it means. Built once per pack and value refresh."""

    def __init__(self, pack: Pack, values: dict[str, list[str]]):
        self.pack = pack
        entries: dict[str, set[Target]] = defaultdict(set)

        def add(phrase: str, target: Target):
            k = norm_key(phrase)
            if k:
                entries[k].add(target)

        for aname, area in pack.areas.items():
            for s in area.synonyms:
                add(s, Target("area", aname))
            for mname, m in area.metrics.items():
                for s in [mname.replace("_", " "), m.label, *m.synonyms]:
                    add(s, Target("metric", mname, area=aname))
        self.dim_values: dict[str, list[tuple[str, frozenset[str]]]] = {}
        self.value_starts: dict[str, list[tuple[tuple[str, ...], Target]]] = defaultdict(list)
        for dname, d in pack.dimensions.items():
            for s in [dname.replace("_", " "), d.label, *d.synonyms]:
                add(s, Target("dimension", dname))
            self.dim_values[dname] = [(v, frozenset(norm_key(v).split()))
                                      for v in dict.fromkeys((d.values or []) + values.get(dname, []))]
            for v, _ in self.dim_values[dname]:
                words = tuple(norm_key(v).split())
                if words:
                    self.value_starts[words[0]].append((words, Target("value", dname, value=v)))
            strip = {norm_key(w) for w in d.value_strip_words}
            for v in (d.values or []) + values.get(dname, []):
                add(v, Target("value", dname, value=v))
                if strip:
                    add(" ".join(w for w in norm_key(v).split() if w not in strip), Target("value", dname, value=v))
            for g in d.groups:
                add(g, Target("group", dname, value=g))

        self.entries = dict(entries)
        self.fuzzy_keys = [k for k in self.entries if len(k.replace(" ", "")) >= 5]
        self.word_keys: dict[str, list[str]] = defaultdict(list)
        for k in self.entries:
            for w in set(k.split()):
                self.word_keys[w].append(k)
        self.single_words = set(self.word_keys)
        # measures, fields and subject areas by word stem; names (values) are never stem-matched
        self.stems: dict[str, set[Target]] = defaultdict(set)
        for k, targets in self.entries.items():
            if " " not in k and len(k) >= 5:
                kept = {t for t in targets if t.kind in ("metric", "dimension", "area")}
                if kept:
                    self.stems[_stem(k)] |= kept

    def names_starting(self, words: list[str]) -> set[Target]:
        """Values whose name begins with these words ('blink commerce' -> BLINK COMMERCE PRIVATE LIMITED).
        One word counts only when it is distinctive: at least 5 letters and the start of exactly one name."""
        hits = {t for vw, t in self.value_starts.get(words[0], []) if vw[:len(words)] == tuple(words)}
        if len(words) == 1 and (len(words[0]) < 5 or len(hits) != 1):
            return set()
        return hits


class _Lookup:
    """TermIndex plus per-request words (the user's learned words and clarification choices)."""

    def __init__(self, index: TermIndex, extra: dict[str, set[Target]]):
        self.index = index
        self.extra = extra
        self.fuzzy_keys = index.fuzzy_keys + [k for k in extra if len(k.replace(" ", "")) >= 5]

    def get(self, phrase: str) -> set[Target] | None:
        for p in (phrase, _singular(phrase)):
            if p is None:
                continue
            if p in self.extra:
                return self.extra[p]
            if p in self.index.entries:
                return self.index.entries[p]
        if " " not in phrase and len(phrase) >= 5 and phrase not in STOPWORDS:
            return self.index.stems.get(_stem(phrase))
        return None


@dataclass
class Match:
    phrase: str
    start: int
    end: int
    targets: set[Target]


# ── results ──────────────────────────────────────────────────────────────────

@dataclass
class ClarifyOption:
    label: str
    overrides: dict[str, str]


@dataclass
class Clarify:
    question: str
    term: str
    options: list[ClarifyOption]
    kind: str = "ambiguous"  # ambiguous | unknown_word


@dataclass
class ParseResult:
    plan: Plan | None = None
    clarify: Clarify | None = None
    unsupported: str | None = None
    greeting: bool = False
    assumptions: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    normalized: str = ""
    trace: str = ""  # the model's statement, kept in the log to see why a question went wrong


def _value_clarify(phrase: str, targets: set[Target], pack: Pack) -> Clarify | None:
    """A word naming values in several fields, or several values of one field (PUNE / PUNE BRANCH), is asked."""
    dims = {t.name for t in targets}
    if len(dims) <= 1 and sum(t.kind == "value" for t in targets) <= 1:
        return None
    where = "more than one field" if len(dims) > 1 else f"more than one {pack.dimensions[next(iter(dims))].label.lower()}"
    return Clarify(
        question=f"'{phrase}' matches {where}. Which one do you mean?",
        term=phrase,
        options=[ClarifyOption(describe_target(t, pack), {phrase: t.to_str()})
                 for t in sorted(targets, key=lambda t: (t.name, str(t.value)))],
    )


# ── parser ───────────────────────────────────────────────────────────────────

class Parser:
    def __init__(self, pack: Pack, shared_lexicon: dict[str, str], values: dict[str, list[str]] | None = None):
        self.pack = pack
        lex = {**shared_lexicon, **{k.lower(): v.lower() for k, v in pack.lexicon.items()}}
        self.phrase_lex = sorted(((k, v) for k, v in lex.items() if " " in k or "-" in k),
                                 key=lambda kv: len(kv[0]), reverse=True)
        self.word_lex = {k: v for k, v in lex.items() if " " not in k and "-" not in k}
        self.fuzzy_lex_keys = [k for k in self.word_lex if len(k) >= 5]
        self.set_values(values or {})

    def set_values(self, values: dict[str, list[str]]) -> None:
        self.index = TermIndex(self.pack, values)

    # ── normalization ───────────────────────────────────────────────────────
    def normalize(self, text: str) -> str:
        t = text.lower().replace("’", "").replace("'", "").replace("₹", " rs ")
        for sym, words in ((">=", " at least "), ("<=", " at most "), (">", " more than "), ("<", " less than ")):
            t = t.replace(sym, words)
        t = re.sub(r"(\d),(?=\d)", r"\1", t)  # 2,00,00,000 -> 200000000
        t = re.sub(r"[^\w\s/\-:.]", " ", t)
        t = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", t)  # keep the dot only inside numbers like 2.5
        t = f" {t} "
        for key, value in self.phrase_lex:
            t = re.sub(rf"(?<![\w-]){re.escape(key)}(?![\w-])", f" {value} ", t)
        out = []
        for w in t.split():
            if w in self.word_lex:
                out.append(self.word_lex[w])
            elif (len(w) >= 5 and w.isalpha() and w not in STOPWORDS and w not in self.index.single_words
                  and self.fuzzy_lex_keys):
                hit = process.extractOne(w, self.fuzzy_lex_keys, scorer=fuzz.ratio, score_cutoff=88)
                out.append(self.word_lex[hit[0]] if hit and hit[0][0] == w[0] else w)
            else:
                out.append(w)
        return " ".join(out)

    # ── main entry ──────────────────────────────────────────────────────────
    def parse(self, question: str, today: date, overrides: dict[str, str] | None = None,
              learned: dict[str, str] | None = None, previous: Plan | None = None,
              strict_unknown: bool = True) -> ParseResult:
        pack = self.pack
        res = ParseResult()
        text = self.normalize(question)
        res.normalized = text
        if text in _GREETINGS:
            res.greeting = True
            return res

        extra: dict[str, set[Target]] = {}
        for term, target in {**(learned or {}), **(overrides or {})}.items():
            targets = parse_target(target, pack)
            if targets:
                extra[norm_key(term)] = targets
        lookup = _Lookup(self.index, extra)

        tx = timeparse.extract_time(text, today)
        threshold, work = _extract_threshold(f" {tx.text} ")

        sort_desc: bool | None = None
        top_n: int | None = None
        m = _TOP_N.search(work)
        if m:
            word = m[1] or m[4]
            top_n = int(m[2] or m[3])
            sort_desc = word not in ("bottom", "worst", "lowest")
            work = work[: m.start()] + timeparse.MARKER + work[m.end():]
        superlative = False
        if _SUPER_ASC.search(work):
            superlative = sort_desc is None
            sort_desc = False
        elif _SUPER_DESC.search(work) and sort_desc is None:
            sort_desc, superlative = True, True
        work = _SUPER_DESC.sub(timeparse.MARKER, _SUPER_ASC.sub(timeparse.MARKER, work))
        chart_hint = None
        # a measure whose name holds a share word ('society contribution') is the measure, not a share cue
        kept = {}
        for i, phrase in enumerate(sorted({norm_key(s) for a in pack.areas.values() for md in a.metrics.values()
                                           for s in [md.label, *md.synonyms] if _PIE.search(norm_key(s))},
                                          key=len, reverse=True)):
            if re.search(rf"\b{re.escape(phrase)}\b", work):
                kept[f"\x00{i}\x00"] = phrase
                work = re.sub(rf"\b{re.escape(phrase)}\b", f"\x00{i}\x00", work)
        if _PIE.search(work):
            chart_hint = "pie"
            work = _PIE.sub(timeparse.MARKER, work)
        for token, phrase in kept.items():
            work = work.replace(token, phrase)
        derived_names = []
        for dname, dd in pack.derived_metrics.items():
            for syn in sorted(dd.synonyms, key=len, reverse=True):
                pat = rf"\b{re.escape(norm_key(syn))}\b"
                if norm_key(syn) and re.search(pat, work):
                    derived_names.append(dname)
                    work = re.sub(pat, timeparse.MARKER, work)
                    break
        compare_cue = bool(_COMPARE.search(work))
        growth_cue = bool(_GROWTH.search(work))
        work = _COMPARE.sub(timeparse.MARKER, work)
        list_cue = bool(_LIST.search(work))
        work = _LIST.sub(timeparse.MARKER, work)
        work = _COUNT.sub(f" {COUNT_MARK} ", work)

        tokens = re.findall(r"~|\w+", work)
        matches = self._attach_names(tokens, self._match(tokens, lookup))

        # ── classify matches ────────────────────────────────────────────────
        consumed = set()
        metric_terms: list[tuple[str, set[Target]]] = []
        dim_mentions: list[tuple[str, bool]] = []
        value_terms: list[tuple[str, set[Target], bool]] = []
        area_hits: set[str] = set()
        count_dims: list[str] = []
        breakdown_cue = any(t in ("breakdown", "split", "distribution") for t in tokens)

        for mt in matches:
            consumed.update(range(mt.start, mt.end))
            area_hits |= {t.name for t in mt.targets if t.kind == "area"}
            kinds = {t.kind for t in mt.targets}
            if "ignore" in kinds:
                continue
            kind = next((k for k in _KIND_PRIORITY if k in kinds), None)
            if kind is None:
                continue
            chosen = {t for t in mt.targets if t.kind == kind}
            prev_tok = tokens[mt.start - 1] if mt.start > 0 else ""
            next_tok = tokens[mt.end] if mt.end < len(tokens) else ""
            if kind == "metric":
                metric_terms.append((mt.phrase, chosen))
            elif kind == "dimension":
                if prev_tok == COUNT_MARK:
                    count_dims.extend(t.name for t in chosen)
                    continue
                cue = prev_tok in _GROUP_CUES or next_tok == "wise" or breakdown_cue or superlative or top_n
                for t in chosen:
                    dim_mentions.append((t.name, bool(cue)))
            else:
                value_terms.append((mt.phrase, chosen, prev_tok in _NEGATIONS))

        grain = tx.grain
        unknown = []
        for i, tok in enumerate(tokens):
            if i in consumed or tok == "~" or tok in STOPWORDS or tok == COUNT_MARK:
                continue
            if tok in _UNIT_WORDS and grain is None:
                grain = _UNIT_WORDS[tok]
                continue
            if tok in _UNIT_WORDS:
                continue
            unknown.append(tok)
        res.unknown = unknown

        for dname in derived_names:
            for name in pack.derived_metrics[dname].inputs:
                owner = pack.area_of_metric(name)
                if owner and not any(t.name == name for _, ts in metric_terms for t in ts):
                    metric_terms.append((dname, {Target("metric", name, area=owner)}))
        anything = (metric_terms or dim_mentions or value_terms or tx.ranges or grain or tx.trend or area_hits
                    or threshold or count_dims or (previous is not None and (top_n or sort_desc is not None)))
        if not anything:
            if unknown:
                res.unsupported = self._not_understood(unknown)
            else:
                res.unsupported = "Please ask about your data, for example: " + "; ".join(self.examples()[:3])
            return res

        if list_cue:
            # "list invoices ...": the area whose rows are named, whatever measure the word also means
            words = set(tokens)
            listed = next((a for a, ad in pack.areas.items() if ad.detail_name
                           and {ad.detail_name, ad.detail_name + "s"} & words), None)
            if listed:
                area_hits = {listed}
                metric_terms = [m for m in metric_terms if any(t.area == listed for t in m[1])]
        followup = previous is not None and not metric_terms and not area_hits and not count_dims
        dim_needs = ([{d} for d, _ in dim_mentions] + [{t.name for t in ts} for _, ts, _ in value_terms]
                     + [{d} for d in count_dims])
        need_time = bool(tx.ranges or grain or tx.trend)
        area = (previous.area if followup else
                self._choose_area(metric_terms, dim_needs, area_hits, need_time,
                                  previous.area if previous is not None else None))
        if area is None and not followup and len(metric_terms) > 1:
            # measures from different areas: the first one's area leads, the others are shown beside it
            area = self._choose_area(metric_terms[:1], dim_needs, area_hits, need_time)
        if area is None and not followup and metric_terms:
            # a one-word name the measure's data can't use is more likely an everyday word ('aaya' = came,
            # also a designation): drop it with a note rather than refuse the question
            owners = {t.area for t in metric_terms[0][1] if t.area}
            dims_of = {a: set(pack.dimensions_for(a)) for a in owners}
            stray = [v for v in value_terms if " " not in v[0]
                     and all(not ({t.name for t in v[1]} & dims_of[a]) for a in owners)]
            if stray:
                kept = [v for v in value_terms if v not in stray]
                needs = ([{d} for d, _ in dim_mentions] + [{t.name for t in ts} for _, ts, _ in kept]
                         + [{d} for d in count_dims])
                area = self._choose_area(metric_terms[:1], needs, area_hits, need_time)
                if area is not None:
                    value_terms = kept
                    for phrase, ts, _ in stray:
                        dim = pack.dimensions[next(iter(ts)).name].label
                        res.assumptions.append(f"Ignored '{phrase}' (a {dim} name), since "
                                               f"{pack.areas[area].label} isn't split by {dim}.")

        # ── unknown words: offer only what the chosen data can answer ───────
        if unknown and strict_unknown:
            word = unknown[0]
            options = self._unknown_word_options(word, lookup, area)
            question = (f"I don't know the word '{word}'. What does it mean here?" if options else
                        f"I don't know the word '{word}'. If it doesn't matter for this question, choose Ignore; "
                        "otherwise please rephrase it.")
            res.clarify = Clarify(question=question, term=word,
                                  options=options + [ClarifyOption("Ignore this word", {word: "ignore"})],
                                  kind="unknown_word")
            return res
        if unknown:
            res.assumptions.append(f"Ignored words I don't know: {', '.join(unknown)}.")

        # ── follow-up: no measure named, reuse the previous question ────────
        if followup:
            res = self._merge_followup(res, previous, dim_mentions, value_terms, tx, grain,
                                       sort_desc, top_n, superlative, chart_hint)
            if res.plan is not None and threshold:
                res.plan.having = [self._having(threshold, res.plan, res)]
            return res

        # ── choose the subject area ─────────────────────────────────────────
        if area is None:
            res.unsupported = self._conflict_message(metric_terms, dim_needs)
            return res
        area_def = pack.areas[area]
        area_dims = set(pack.dimensions_for(area))

        # ── measures ────────────────────────────────────────────────────────
        metrics: list[str] = []
        more: list[str] = []
        for phrase, targets in metric_terms:
            names = sorted({t.name for t in targets if t.area == area})
            if not names:
                order = list(pack.areas)
                t = min(targets, key=lambda t: (order.index(t.area) if t.area in order else 99, t.name))
                if f"{t.area}.{t.name}" not in more:
                    more.append(f"{t.area}.{t.name}")
                continue
            if len(names) > 1:
                res.clarify = Clarify(
                    question=f"By '{phrase}', which measure do you mean?",
                    term=phrase,
                    options=[ClarifyOption(area_def.metrics[n].label, {phrase: f"metric:{n}"}) for n in names],
                )
                return res
            if names[0] not in metrics:
                metrics.append(names[0])
        metrics = [f"count:{d}" for d in dict.fromkeys(count_dims) if d in area_dims] + metrics
        if not metrics:
            metrics = [area_def.default_metric]
            res.assumptions.append(f"No measure named, so showing {area_def.metrics[metrics[0]].label}.")

        # ── filters ─────────────────────────────────────────────────────────
        filters: dict[tuple[str, bool], Filter] = {}
        anchored = {next(iter({t.name for t in ts})) for _, ts, _ in value_terms
                    if len({t.name for t in ts if t.name in area_dims}) == 1}
        for phrase, targets, negate in value_terms:
            in_area = {t for t in targets if t.name in area_dims}
            narrowed = {t for t in in_area if t.name in anchored}
            if narrowed and len({t.name for t in in_area}) > 1:
                in_area = narrowed  # "lucknow and bhopal branch": lucknow is a branch too
            if clarify := _value_clarify(phrase, in_area, pack):
                res.clarify = clarify
                return res
            for t in in_area:
                values = pack.dimensions[t.name].groups[t.value] if t.kind == "group" else [t.value]
                f = filters.setdefault((t.name, negate), Filter(dimension=t.name, values=[], negate=negate))
                f.values.extend(v for v in values if v not in f.values)
                if t.kind == "group":
                    f.label = t.value

        # ── grouping ────────────────────────────────────────────────────────
        filtered_dims = {d for d, _ in filters}
        group_by: list[str] = []
        for d, cue in dim_mentions:
            if (d not in filtered_dims or cue) and d not in group_by:
                group_by.append(d)

        time_range = self._resolve_time(res, tx, area, today)
        compare = None
        if len(tx.ranges) == 2 and compare_cue and grain is None and not tx.trend:
            time_range, compare = tx.ranges
        elif len(tx.ranges) == 1 and growth_cue and grain is None and not tx.trend:
            compare = timeparse.previous_period(time_range)
            res.assumptions.append(f"Compared with the period before: {compare.label}.")
        if len(tx.ranges) > 1 and grain is None and compare is None:
            grain = timeparse.grain_for_unit(tx.ranges[0].unit)
        if tx.trend and grain is None:
            grain = timeparse.auto_grain(time_range) if time_range else "day"
        if grain:
            group_by.append(f"time:{grain}")

        plan = Plan(area=area, metrics=metrics, group_by=group_by, filters=list(filters.values()),
                    time=time_range, chart_hint=chart_hint, compare=compare, share=chart_hint == "pie",
                    more_metrics=more, derived=list(dict.fromkeys(derived_names)))
        if list_cue:
            if area_def.detail_columns:
                plan.detail, plan.group_by, plan.share = True, [], False
                res.assumptions = [a for a in res.assumptions if not a.startswith("No measure named")]
                res.plan = plan
                return res
            res.assumptions.append(f"{area_def.label} can't be listed row by row, so showing totals.")
        if threshold:
            plan.having = [self._having(threshold, plan, res)]
        self._apply_sort(plan, sort_desc, top_n, superlative)
        if plan.derived and plan.sort:
            plan.sort.metric = plan.derived[0]
        if (previous is not None and _SAME_AGAIN.search(text) and not dim_mentions and not value_terms
                and not tx.ranges and not grain and not count_dims):
            self._carry_context(plan, previous, res)
        res.plan = plan
        return res

    def _carry_context(self, plan: Plan, previous: Plan, res: ParseResult) -> None:
        """'same for collection': the new measure with the previous question's split, names and dates."""
        dims = set(self.pack.dimensions_for(plan.area))
        plan.group_by = [g for g in previous.group_by if g.startswith("time:") or g in dims]
        plan.filters = [f.model_copy() for f in previous.filters if f.dimension in dims]
        plan.time, plan.compare = previous.time, previous.compare
        if previous.sort and plan.group_by:
            plan.sort = Sort(metric=plan.derived[0] if plan.derived else plan.metrics[0], desc=previous.sort.desc)
            plan.limit = previous.limit
        res.assumptions = [a for a in res.assumptions if not a.startswith("No date given")]
        res.assumptions.append("Continuing from your previous question.")

    def _having(self, t: Threshold, plan: Plan, res: ParseResult) -> Having:
        if plan.derived:
            return Having(metric=plan.derived[0], op=t.op, value=t.value, value2=t.value2)
        metric = plan.metrics[0]
        if len(plan.metrics) > 1:
            res.assumptions.append(
                f"The condition applies to {self.pack.metric(plan.area, metric).label}.")
        if not plan.group_by:
            res.assumptions.append("Nothing to compare per group, so the condition is checked on the overall total.")
        return Having(metric=metric, op=t.op, value=t.value, value2=t.value2)

    # ── helpers ─────────────────────────────────────────────────────────────
    def named_measures(self, question: str, today: date) -> list[tuple[str, str]]:
        """(area, metric) for each measure the question names with one of the pack's own words."""
        work = timeparse.extract_time(self.normalize(question), today).text
        tokens = re.findall(r"~|\w+", work)
        found: dict[tuple[str, str], bool] = {}  # -> named only by a word that also names the whole area
        for mt in self._match(tokens, _Lookup(self.index, {})):
            generic = any(t.kind == "area" for t in mt.targets)
            for t in mt.targets:
                if t.kind == "metric" and t.area:
                    found[(t.area, t.name)] = found.get((t.area, t.name), True) and generic
        specific_areas = {a for (a, _), g in found.items() if not g}
        return [(a, m) for (a, m), g in found.items() if not (g and a in specific_areas)]

    def _match(self, tokens: list[str], lookup: _Lookup) -> list[Match]:
        matches: list[Match] = []
        i = 0
        while i < len(tokens):
            if tokens[i] == "~":
                i += 1
                continue
            hit = None
            for n in range(min(MAX_NGRAM, len(tokens) - i), 0, -1):
                span = tokens[i:i + n]
                if "~" in span or (n == 1 and span[0] in STOPWORDS):
                    continue
                phrase = " ".join(span)
                targets = lookup.get(phrase)
                if targets:
                    hit = Match(phrase, i, i + n, targets)
                    break
            if hit is None:
                for n in range(min(3, len(tokens) - i), 0, -1):
                    span = tokens[i:i + n]
                    if "~" in span or all(w in STOPWORDS for w in span) or span[0] in STOPWORDS:
                        continue
                    phrase = " ".join(span)
                    if len(phrase.replace(" ", "")) < 5 or any(ch.isdigit() for ch in phrase):
                        continue
                    best = process.extractOne(phrase, lookup.fuzzy_keys, scorer=fuzz.ratio, score_cutoff=90)
                    if best:
                        hit = Match(phrase, i, i + n, lookup.get(best[0]) or set())
                        break
            if hit is None:
                for n in range(min(4, len(tokens) - i), 0, -1):
                    span = tokens[i:i + n]
                    if "~" in span or any(w in STOPWORDS or w.isdigit() for w in span):
                        continue
                    found = self.index.names_starting(span)
                    if found:
                        hit = Match(" ".join(span), i, i + n, found)
                        break
            if hit:
                matches.append(hit)
                i = hit.end
            else:
                i += 1
        return matches

    def _attach_names(self, tokens: list[str], matches: list[Match]) -> list[Match]:
        """'mumbai branch': a name right before a field word is looked up among that field's values.

        Values containing every word of the name become candidates (SCS MUMBAI, MUMBAI REGIONAL OFFICE),
        alongside what the name already matched elsewhere (Mumbai the city); several candidates are asked.
        """
        covered = {i for mt in matches for i in range(mt.start, mt.end)}
        out: list[Match] = []
        for mt in matches:
            dims = {t.name for t in mt.targets if t.kind == "dimension"}
            if not dims or any(t.kind == "metric" for t in mt.targets):
                out.append(mt)
                continue
            prev = out[-1] if out and out[-1].end == mt.start else None
            if prev is not None and prev.targets and all(t.kind in ("value", "group") for t in prev.targets):
                start = prev.start
            else:
                prev, start = None, mt.start
                while start > 0 and start - 1 not in covered and tokens[start - 1] not in STOPWORDS \
                        and tokens[start - 1] != "~":
                    start -= 1
            words = set(tokens[start:mt.start])
            found = {Target("value", d, value=v) for d in dims
                     for v, vwords in self.index.dim_values.get(d, []) if words and words <= vwords}
            if not found:
                out.append(mt)
                continue
            if prev is not None:
                out.pop()
                found |= {t for t in prev.targets if t.name not in dims}
            out.append(Match(" ".join(tokens[start:mt.end]), start, mt.end, found))
        return out

    def _choose_area(self, metric_terms, dim_needs, area_hits, need_time: bool,
                     previous_area: str | None = None) -> str | None:
        feasible = []
        for aname, a in self.pack.areas.items():
            dims = set(self.pack.dimensions_for(aname))
            if any(not (need & dims) for need in dim_needs):
                continue
            if any(not any(t.area == aname for t in ts) for _, ts in metric_terms):
                continue
            if need_time and not a.time_column:
                continue
            feasible.append(aname)
        if not feasible:
            return None
        order = list(self.pack.areas)
        # named in the question first, then the data the conversation was already using, then pack order
        feasible.sort(key=lambda a: (a not in area_hits, a != previous_area, order.index(a)))
        return feasible[0]

    def _resolve_time(self, res: ParseResult, tx: timeparse.TimeExtraction, area: str,
                      today: date) -> TimeRange | None:
        area_def = self.pack.areas[area]
        if len(tx.ranges) == 1:
            return tx.ranges[0]
        if len(tx.ranges) > 1:
            return timeparse.union(tx.ranges)
        if tx.trend:
            default = timeparse.extract_time("last 30 days", today).ranges[0]
            res.assumptions.append("No date range given for the trend, so showing the last 30 days.")
            return default
        if area_def.default_time:
            found = timeparse.extract_time(area_def.default_time, today).ranges
            if found:
                res.assumptions.append(f"No date given, so showing {found[0].label}.")
                return found[0]
        if area_def.time_column:
            res.assumptions.append("No date given, so this covers all dates.")
        return None

    @staticmethod
    def _apply_sort(plan: Plan, sort_desc: bool | None, top_n: int | None, superlative: bool) -> None:
        metric = plan.metrics[0]
        if sort_desc is not None and plan.group_by:
            plan.sort = Sort(metric=metric, desc=sort_desc)
            plan.limit = top_n or (5 if superlative else None)
        elif plan.dimension_group_by() and not plan.time_grain():
            plan.sort = Sort(metric=metric, desc=True)
        elif top_n:
            plan.limit = top_n

    def _merge_followup(self, res, previous: Plan, dim_mentions, value_terms, tx, grain,
                        sort_desc, top_n, superlative, chart_hint) -> ParseResult:
        pack = self.pack
        dim_needs = [{d} for d, _ in dim_mentions] + [{t.name for t in ts} for _, ts, _ in value_terms]
        area = previous.area
        area_dims = set(pack.dimensions_for(area))
        if any(not (need & area_dims) for need in dim_needs):
            res.unsupported = ("I can't apply that to the previous question. "
                               "Please ask the full question, including what to measure.")
            return res
        plan = previous.model_copy(deep=True)
        plan.chart_hint = chart_hint or plan.chart_hint

        new_filters: dict[tuple[str, bool], Filter] = {}
        for phrase, targets, negate in value_terms:
            in_area = {t for t in targets if t.name in area_dims}
            if clarify := _value_clarify(phrase, in_area, pack):
                res.clarify = clarify
                return res
            for t in in_area:
                values = pack.dimensions[t.name].groups[t.value] if t.kind == "group" else [t.value]
                f = new_filters.setdefault((t.name, negate), Filter(dimension=t.name, values=[], negate=negate))
                f.values.extend(v for v in values if v not in f.values)
                if t.kind == "group":
                    f.label = t.value
        if new_filters:
            replaced = {d for d, _ in new_filters}
            plan.filters = [f for f in plan.filters if f.dimension not in replaced] + list(new_filters.values())

        new_group = [d for d, cue in dim_mentions if d not in {f.dimension for f in new_filters.values()} or cue]
        if tx.ranges:
            plan.time = tx.ranges[0] if len(tx.ranges) == 1 else timeparse.union(tx.ranges)
        if new_group or grain:
            plan.group_by = list(dict.fromkeys(new_group)) + ([f"time:{grain}"] if grain else [])
            plan.sort, plan.limit = None, None
        if sort_desc is not None or new_group or grain:
            self._apply_sort(plan, sort_desc, top_n, superlative)
        res.assumptions.append("Continuing from your previous question.")
        res.plan = plan
        return res

    def _unknown_word_options(self, word: str, lookup: _Lookup, area: str | None) -> list[ClarifyOption]:
        """Close whole-word matches that the chosen subject area can use; empty when nothing is close."""
        if len(word) < 4 or word.isdigit():
            return []
        area_dims = set(self.pack.dimensions_for(area)) if area else set(self.pack.dimensions)

        def usable(t: Target) -> bool:
            if t.kind == "metric":
                return area is None or t.area == area
            return t.kind in ("dimension", "value", "group") and t.name in area_dims

        vocab = list(lookup.index.word_keys) + [w for k in lookup.extra for w in k.split()]
        keys: list[str] = []
        for w, _score, _ in process.extract(word, vocab, scorer=fuzz.ratio, limit=12, score_cutoff=85):
            if len(w) < 4:
                continue
            keys += lookup.index.word_keys.get(w, []) + [k for k in lookup.extra if w in k.split()]
        options: list[ClarifyOption] = []
        seen = set()
        for key in dict.fromkeys(keys):
            for t in sorted(lookup.get(key) or set(), key=lambda t: (t.kind, t.name, t.value or "")):
                if not usable(t):
                    continue
                s = "metric:" + t.name if t.kind == "metric" else t.to_str()
                if s not in seen:
                    seen.add(s)
                    options.append(ClarifyOption(describe_target(t, self.pack), {word: s}))
        return options[:4]

    def _conflict_message(self, metric_terms, dim_needs) -> str:
        measures = ", ".join(f"'{p}'" for p, _ in metric_terms) or "that measure"
        fields = sorted({self.pack.dimensions[d].label for need in dim_needs for d in need})
        if fields:
            return (f"I can't combine {measures} with {', '.join(fields)}; they come from different parts of "
                    "the data. Try asking about them separately.")
        return f"I can't answer {measures} for that. Try one of: " + "; ".join(self.examples()[:3])

    def _not_understood(self, unknown: list[str]) -> str:
        return (f"I didn't understand: {', '.join(unknown[:5])}. "
                "Try something like: " + "; ".join(self.examples()[:3]))

    def examples(self) -> list[str]:
        return [e for a in self.pack.areas.values() for e in a.examples]
