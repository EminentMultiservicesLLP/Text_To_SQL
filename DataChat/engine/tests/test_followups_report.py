"""Follow-up suggestions under answers, and the failure report built from the engine's log."""
from conftest import TODAY, FakeExecutor

from datachat.report import build_report, report_markdown
from datachat.service import ChatRequest, ChatService, FeedbackRequest

CLIENT = "bellona_rista"


def make(settings):
    return ChatService(settings, executor_factory=lambda p, t: FakeExecutor(), today=lambda: TODAY)


def ask(svc, text, conv="c1", plan=None):
    return svc.chat(ChatRequest(client_id=CLIENT, user_id="u1", conversation_id=conv, message=text, plan=plan))


def test_total_offers_split_trend_and_comparison(settings):
    r = ask(make(settings), "sales last month")
    labels = [f.label for f in r.follow_ups]
    assert len(labels) == 3
    assert " by " in labels[0] and "month-wise" in labels[1] and labels[2] == "Compare with July 2026"


def test_follow_up_runs_without_the_model_and_is_remembered(settings):
    svc = make(settings)
    first = ask(svc, "sales last month")
    fu = first.follow_ups[0]
    r = ask(svc, fu.label, plan=fu.plan)
    assert r.type == "answer" and r.source == "follow-up"
    assert r.plan["group_by"] == fu.plan["group_by"] and r.plan["time"] == first.plan["time"]
    assert ask(svc, "what about swiggy").type in ("answer", "clarify")


def test_breakdown_offers_share_and_no_duplicate_labels(settings):
    r = ask(make(settings), "sales by branch last month")
    labels = [f.label for f in r.follow_ups]
    assert any(lbl.startswith("Share of each") for lbl in labels)
    assert len(labels) == len(set(labels))


def test_follow_up_with_unknown_area_is_refused(settings):
    svc = make(settings)
    plan = ask(svc, "sales last month").follow_ups[0].plan
    r = ask(svc, "x", plan={**plan, "area": "salaries"})
    assert r.type == "error" and "no longer valid" in r.text
    r = ask(svc, "x", plan={**plan, "metrics": ["not_a_measure"]})
    assert r.type == "error"


def test_report_lists_failures_with_how_they_were_read(settings):
    svc = make(settings)
    ok = ask(svc, "sales last month", conv="a")
    ask(svc, "what is the weather in pune", conv="b")
    svc.feedback(FeedbackRequest(client_id=CLIENT, user_id="u1", query_id=ok.query_id, rating=-1,
                                 comment="should be net sales"))
    r = build_report(svc.store, CLIENT, 7)
    s = r["summary"]
    assert s["questions"] == 2 and s["answered"] == 1 and s["rated_wrong"] == 1
    wrong = r["groups"]["rated_wrong"][0]
    assert wrong["question"] == "sales last month" and "area=sales" in wrong["plan"]
    assert wrong["comment"] == "should be net sales"
    missed = r["groups"]["not_answered"] + r["groups"]["clarify_dropped"]
    assert [i["question"] for i in missed] == ["what is the weather in pune"]
    md = report_markdown(r)
    assert "Answers users marked wrong (1)" in md and "should be net sales" in md


def test_report_endpoint_needs_the_key(settings):
    from fastapi.testclient import TestClient

    from datachat.api import create_app
    c = TestClient(create_app(make(settings)))
    assert c.get(f"/v1/admin/{CLIENT}/report").status_code == 401
    r = c.get(f"/v1/admin/{CLIENT}/report?format=md", headers={"X-Api-Key": "test-key"})
    assert r.status_code == 200 and r.text.startswith("# DataChat report")
