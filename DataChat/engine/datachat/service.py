import logging
import threading
import time
from collections import OrderedDict
from datetime import date, datetime, timedelta
from typing import Callable, Literal

from pydantic import BaseModel, ValidationError

from datachat.answer import build_run_answer
from datachat.followups import follow_ups
from datachat.compiler import CompileError, compile_detail, compile_plan, distinct_values_sql, latest_date_sql
from datachat.config import Settings
from datachat.executor import ExecutionError, Executor, make_executor
from datachat.guard import GuardError
from datachat.runner import execute, prepare
from datachat.learning import LearningStore
from datachat.pack import Pack, load_lexicon, load_packs
from datachat.parser import Parser, ParseResult
from datachat.plan import Plan

logger = logging.getLogger(__name__)

VALUES_MAX_AGE = timedelta(hours=12)
MAX_VALUES = 20000  # per dimension; larger lists (e.g. every client site) should stay load_values: false
MAX_CONVERSATIONS = 2000


# ── API models ───────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    client_id: str
    user_id: str
    conversation_id: str
    message: str
    overrides: dict[str, str] = {}
    plan: dict | None = None  # a follow-up offered under an earlier answer: run it as it is, without the model


class ColumnOut(BaseModel):
    name: str
    label: str
    kind: str
    format: str | None = None


class ChartOut(BaseModel):
    type: str
    x: str
    y: list[str]


class OptionOut(BaseModel):
    label: str
    overrides: dict[str, str]


class FollowUpOut(BaseModel):
    label: str
    plan: dict


class ChatResponse(BaseModel):
    type: Literal["answer", "clarify", "unsupported", "error", "greeting"]
    text: str
    assumptions: list[str] = []
    sql: str | None = None
    columns: list[ColumnOut] = []
    rows: list[list] = []
    row_count: int = 0
    capped: bool = False
    chart: ChartOut | None = None
    options: list[OptionOut] = []
    follow_ups: list[FollowUpOut] = []
    query_id: int | None = None
    source: str | None = None
    elapsed_ms: int = 0
    plan: dict | None = None  # how the question was read, after fitting it to the data


class FeedbackRequest(BaseModel):
    client_id: str
    user_id: str
    query_id: int
    rating: Literal[1, -1]
    comment: str | None = None


# ── runtime ──────────────────────────────────────────────────────────────────

class ClientRuntime:
    def __init__(self, pack: Pack, parser: Parser, executor: Executor | None):
        self.pack = pack
        self.parser = parser
        self.executor = executor
        self.values_loaded_at: datetime | None = None
        self.latest_dates: dict[str, date] = {}  # area -> most recent date in its data
        self.lock = threading.Lock()


class ChatService:
    def __init__(self, settings: Settings,
                 executor_factory: Callable[[Pack, int], Executor | None] = make_executor,
                 planner=None, today: Callable[[], date] = date.today):
        self.settings = settings
        self.executor_factory = executor_factory
        self.today = today
        self.store = LearningStore(settings.data_dir / "learning.db", settings.promote_min_users)
        self.planner = planner
        if self.planner is None and settings.llm_enabled:
            from datachat.llm import LlmInterpreter
            self.planner = LlmInterpreter(settings)
        self._conversations: OrderedDict[tuple[str, str], Plan] = OrderedDict()
        self._conv_lock = threading.Lock()
        self.runtimes: dict[str, ClientRuntime] = {}
        self.reload()

    # ── setup ───────────────────────────────────────────────────────────────
    def reload(self) -> None:
        lexicon = load_lexicon(self.settings.packs_dir)
        runtimes = {}
        for client, pack in load_packs(self.settings.packs_dir).items():
            runtimes[client] = ClientRuntime(pack, Parser(pack, lexicon),
                                             self.executor_factory(pack, self.settings.query_timeout_s))
        self.runtimes = runtimes
        logger.info("Loaded client packs: %s", ", ".join(runtimes) or "none")

    def refresh_values(self, client: str) -> dict[str, int]:
        """Load distinct values for dimensions marked load_values (branch codes, categories, ...)."""
        rt = self.runtimes[client]
        loaded: dict[str, list[str]] = {}
        if rt.executor is not None:
            for name, dim in rt.pack.dimensions.items():
                if not dim.load_values:
                    continue
                try:
                    r = rt.executor.run(distinct_values_sql(rt.pack, name, MAX_VALUES), MAX_VALUES, MAX_VALUES)
                    loaded[name] = sorted({str(row[0]).strip() for row in r.rows
                                           if row[0] is not None and str(row[0]).strip()})
                except ExecutionError as e:
                    logger.warning("Could not load values for %s.%s: %s", client, name, e)
            for aname in rt.pack.areas:
                sql = latest_date_sql(rt.pack, aname)
                if sql is None:
                    continue
                try:
                    latest = rt.executor.run(sql, 1, 1).rows
                    if latest and latest[0][0]:
                        rt.latest_dates[aname] = date.fromisoformat(str(latest[0][0])[:10])
                except (ExecutionError, ValueError) as e:
                    logger.warning("Could not read latest date for %s.%s: %s", client, aname, e)
        rt.parser.set_values(loaded)
        rt.values_loaded_at = datetime.now()
        return {k: len(v) for k, v in loaded.items()}

    def _ensure_values(self, rt: ClientRuntime) -> None:
        if rt.values_loaded_at is None:
            with rt.lock:
                if rt.values_loaded_at is None:
                    self.refresh_values(rt.pack.client)
        elif datetime.now() - rt.values_loaded_at > VALUES_MAX_AGE and rt.lock.acquire(blocking=False):
            def work():
                try:
                    self.refresh_values(rt.pack.client)
                finally:
                    rt.lock.release()
            threading.Thread(target=work, daemon=True).start()

    def warm_up(self) -> None:
        if self.planner is not None:
            self.planner.warm_up()
        for rt in self.runtimes.values():
            try:
                self._ensure_values(rt)
            except Exception:
                logger.exception("Value preload failed for %s", rt.pack.client)
        if self.planner is not None and hasattr(self.planner, "prime"):
            for rt in self.runtimes.values():
                if rt.executor is None:
                    continue
                try:
                    self.planner.prime(rt.pack, rt.parser, self.today())
                except Exception:
                    logger.exception("LLM prime failed for %s", rt.pack.client)

    # ── conversation memory ─────────────────────────────────────────────────
    def _previous(self, client: str, conversation_id: str) -> Plan | None:
        with self._conv_lock:
            return self._conversations.get((client, conversation_id))

    def _remember(self, client: str, conversation_id: str, plan: Plan) -> None:
        with self._conv_lock:
            self._conversations[(client, conversation_id)] = plan
            self._conversations.move_to_end((client, conversation_id))
            while len(self._conversations) > MAX_CONVERSATIONS:
                self._conversations.popitem(last=False)

    # ── chat ────────────────────────────────────────────────────────────────
    def chat(self, req: ChatRequest) -> ChatResponse:
        started = time.perf_counter()
        rt = self.runtimes.get(req.client_id)
        if rt is None:
            return ChatResponse(type="error", text=f"Unknown client '{req.client_id}'.")
        pack = rt.pack
        self._ensure_values(rt)

        if req.overrides:
            self.store.record_choices(pack.client, req.user_id, req.overrides)
        learned = self.store.terms_for(pack.client, req.user_id)
        previous = self._previous(pack.client, req.conversation_id)
        today = self.today()

        def rules() -> ParseResult:
            r = rt.parser.parse(req.message, today, overrides=req.overrides, learned=learned, previous=previous,
                                strict_unknown=self.settings.strict_unknown_words)
            reason = pack.unavailable(r.normalized or rt.parser.normalize(req.message))
            if reason:
                r = ParseResult(normalized=r.normalized, unsupported=f"I can't answer that from this data: "
                                f"{reason}. Try something like: " + "; ".join(rt.parser.examples()[:3]))
            return r

        res, source = None, "llm"
        if req.plan is not None:
            try:
                given = Plan.model_validate(req.plan)
                if given.area not in pack.areas or not all(pack.has_metric(given.area, m) for m in given.metrics):
                    raise ValueError(given.area)
            except (ValidationError, ValueError):
                return ChatResponse(type="error", text="That suggestion is no longer valid; please type the question.")
            res, source = ParseResult(plan=given, normalized=req.message), "follow-up"
        elif self.planner is not None and self.settings.llm_mode == "primary":
            # the model reads every question; the built-in word rules are only an emergency backup
            res = self.planner.interpret(req.message, pack, rt.parser, today, previous, req.overrides, learned)
            if res is None:
                res, source = rules(), "rules"
                res.assumptions.append("The language model did not respond, so this was read with the built-in "
                                       "backup rules.")
        else:
            res, source = rules(), "rules"
            rules_stuck = (res.plan is None and (
                res.unsupported or (res.clarify is not None and res.clarify.kind == "unknown_word"))) \
                or bool(res.plan is not None and res.unknown)
            if self.planner is not None and not res.greeting and rules_stuck:
                llm_res = self.planner.interpret(req.message, pack, rt.parser, today, previous,
                                                 req.overrides, learned)
                if llm_res is not None:
                    res, source = llm_res, "llm"
        plan = res.plan

        def finish(resp: ChatResponse, status: str, sql: str | None = None) -> ChatResponse:
            resp.elapsed_ms = int((time.perf_counter() - started) * 1000)
            resp.source = source
            resp.plan = plan.model_dump(mode="json") if plan else None
            resp.query_id = self.store.log_query(
                pack.client, req.user_id, req.conversation_id, req.message, res.normalized,
                plan.model_dump(mode="json") if plan else None, sql, status, resp.text, source, resp.elapsed_ms,
                res.trace)
            return resp

        if res.greeting:
            examples = rt.parser.examples()[:4]
            topics = "; ".join(f"{a.label} ({', '.join(m.label.lower() for m in a.metrics.values())})"
                               for a in pack.areas.values())
            return finish(ChatResponse(
                type="greeting",
                text=(f"I can answer questions about: {topics}. You can ask for totals, splits by "
                      f"{', '.join(d.label.lower() for d in list(pack.dimensions.values())[:4])} and more, top or "
                      "bottom lists, monthly trends, comparisons with an earlier period, amounts above or below "
                      "a limit, and share of the total. For example: " + "; ".join(examples))), "greeting")
        if plan is None and res.clarify is not None:
            c = res.clarify
            return finish(ChatResponse(type="clarify", text=c.question,
                                       options=[OptionOut(label=o.label, overrides=o.overrides) for o in c.options]),
                          "clarify")
        if plan is None:
            return finish(ChatResponse(type="unsupported", text=res.unsupported or "I couldn't read that question."),
                          "unsupported")

        asked = plan.model_copy(deep=True)
        try:
            notes = prepare(plan, pack, rt.latest_dates, today)
            res.assumptions += notes
            for d in plan.derived:
                if pack.derived_metrics[d].note:
                    res.assumptions.append(pack.derived_metrics[d].note)
            if rt.executor is None:
                cq = (compile_detail(plan, pack, self.settings.row_limit) if plan.detail else
                      compile_plan(plan.model_copy(update={"more_metrics": []}), pack, self.settings.row_limit))
                return finish(ChatResponse(type="error", sql=cq.sql, assumptions=res.assumptions,
                                           text=f"No database connection is configured for this client "
                                                f"(set {pack.database.dsn_env})."), "error", cq.sql)
            rr = execute(plan, pack, rt.executor, self.settings.row_limit)
        except (CompileError, GuardError) as e:
            logger.warning("Plan rejected for %s: %s", pack.client, e)
            return finish(ChatResponse(type="unsupported", text=f"I can't answer that from this data: {e}.",
                                       assumptions=res.assumptions), "error")
        except ExecutionError as e:
            logger.error("Query failed for %s: %s", pack.client, e)
            return finish(ChatResponse(type="error", text=f"The query failed: {e}"), "error")

        sql = "\n\n".join(rr.sqls)
        text, chart = build_run_answer(plan, pack, rr)
        value_idx = [i for i, c in enumerate(rr.columns) if c.kind == "metric"]
        no_data = not rr.rows or all(row[i] in (None, 0) for row in rr.rows for i in value_idx)
        if no_data and plan.time:
            stale = [(a, d) for a in {a for a, _ in plan.all_metrics()} | {plan.area}
                     if (d := rt.latest_dates.get(a)) and plan.time.end > d + timedelta(days=1)]
            for a, d in stale:
                text += (f" Note: {pack.areas[a].label} data currently goes up to {d:%d %b %Y}, "
                         "so later dates have nothing to show yet.")
        self._remember(pack.client, req.conversation_id, asked)
        return finish(ChatResponse(
            type="answer", text=text, assumptions=res.assumptions, sql=sql,
            columns=[ColumnOut(name=c.name, label=c.label, kind=c.kind, format=c.format) for c in rr.columns],
            rows=rr.rows, row_count=len(rr.rows), capped=rr.capped,
            chart=ChartOut(type=chart.type, x=chart.x, y=chart.y) if chart else None,
            follow_ups=[FollowUpOut(label=f.label, plan=f.plan.model_dump(mode="json"))
                        for f in follow_ups(asked, pack, today)],
        ), "answer", sql)

    def feedback(self, req: FeedbackRequest) -> None:
        self.store.add_feedback(req.client_id, req.user_id, req.query_id, req.rating, req.comment)

    def client_info(self, client: str) -> dict | None:
        rt = self.runtimes.get(client)
        if rt is None:
            return None
        return {"client_id": client, "display_name": rt.pack.display_name, "examples": rt.parser.examples(),
                "currency_symbol": rt.pack.formatting.currency_symbol,
                "indian_grouping": rt.pack.formatting.indian_grouping}
