"""Primary mode: the model reads every question; the built-in word rules are only a backup when it is down."""
from dataclasses import replace

from conftest import TODAY, FakeExecutor

from datachat.llm import ground, parse_statement
from datachat.service import ChatRequest, ChatService


class StubPlanner:
    """Answers with a fixed statement, like a model; None means the model didn't respond."""

    def __init__(self, line: str | None):
        self.line = line
        self.calls = 0

    def interpret(self, question, pack, parser, today, previous, overrides, learned):
        self.calls += 1
        if self.line is None:
            return None
        return ground(parse_statement(self.line), question, pack, parser, today, overrides, learned)


def make(settings, planner, mode="primary"):
    return ChatService(replace(settings, llm_enabled=True, llm_mode=mode),
                       executor_factory=lambda p, t: FakeExecutor(), planner=planner, today=lambda: TODAY)


def ask(svc, text):
    return svc.chat(ChatRequest(client_id="bellona_rista", user_id="u1", conversation_id="c1", message=text))


def default_line(svc):
    area, a = next(iter(svc.runtimes["bellona_rista"].pack.areas.items()))
    return f"area={area} | measure={a.default_metric} | period=last month"


def test_model_reads_even_familiar_words(settings):
    planner = StubPlanner(None)
    svc = make(settings, planner)
    planner.line = default_line(svc)
    r = ask(svc, "sales last month")
    assert r.type == "answer" and r.source == "llm" and planner.calls == 1


def test_rules_only_when_the_model_is_down(settings):
    svc = make(settings, StubPlanner(None))
    r = ask(svc, "sales last month")
    assert r.type == "answer" and r.source == "rules"
    assert any("did not respond" in a for a in r.assumptions)


def test_greeting_and_refusal_come_from_the_model(settings):
    svc = make(settings, StubPlanner("area=none | greeting"))
    assert ask(svc, "namaste ji").type == "greeting"
    svc = make(settings, StubPlanner("area=none | unanswerable=no weather data"))
    r = ask(svc, "weather in pune")
    assert r.type == "unsupported" and "no weather data" in r.text


def test_fallback_mode_keeps_rules_first(settings):
    planner = StubPlanner(None)
    svc = make(settings, planner, mode="fallback")
    r = ask(svc, "sales last month")
    assert r.source == "rules" and planner.calls == 0
