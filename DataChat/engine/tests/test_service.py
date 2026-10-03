from fastapi.testclient import TestClient

from conftest import TODAY, FakeExecutor
from datachat.answer import indian_group
from datachat.api import create_app
from datachat.service import ChatRequest, ChatService


def make_service(settings):
    fake = FakeExecutor()
    svc = ChatService(settings, executor_factory=lambda pack, timeout: fake, today=lambda: TODAY)
    return svc, fake


def ask(svc, text, user="u1", conv="c1", overrides=None):
    return svc.chat(ChatRequest(client_id="bellona_rista", user_id=user, conversation_id=conv, message=text,
                                overrides=overrides or {}))


def test_answer_with_chart(settings):
    svc, fake = make_service(settings)
    r = ask(svc, "Which branch had the highest sales last month?")
    assert r.type == "answer", r.text
    assert r.chart.type == "bar" and r.chart.x == "branch" and r.chart.y == ["revenue"]
    assert r.text.startswith("V1 has the highest total sales: ₹3,000")
    assert [c.name for c in r.columns] == ["branch", "revenue"] and r.row_count == 3
    assert r.query_id is not None and "SELECT TOP (5)" in r.sql


def test_values_loaded_from_database(settings):
    svc, fake = make_service(settings)
    r = ask(svc, "sales for PUNE001 yesterday")
    assert r.type == "answer", r.text
    assert "IN ('PUNE001')" in r.sql
    assert any("DISTINCT" in q for q in fake.queries)


def test_clarify_then_learn_for_that_user_only(settings):
    svc, _ = make_service(settings)
    r = ask(svc, "earnings last month")
    assert r.type == "clarify" and len(r.options) == 2
    chosen = next(o for o in r.options if o.overrides["earnings"] == "metric:net_sales")
    r2 = ask(svc, "earnings last month", overrides=chosen.overrides)
    assert r2.type == "answer" and "NetAmount" in r2.sql
    assert ask(svc, "earnings yesterday").type == "answer"
    assert ask(svc, "earnings yesterday", user="someone_else").type == "clarify"


def test_choice_becomes_client_wide_only_after_admin_approval(settings):
    svc, _ = make_service(settings)
    for user in ("a", "b", "c"):
        ask(svc, "earnings last month", user=user, overrides={"earnings": "metric:net_sales"})
    suggestions = svc.store.suggestions("bellona_rista")
    assert suggestions[0]["term"] == "earnings" and suggestions[0]["users"] == 3
    assert ask(svc, "earnings last month", user="new").type == "clarify"
    svc.store.decide("bellona_rista", "earnings", "metric:net_sales", True, "admin")
    assert ask(svc, "earnings last month", user="new").type == "answer"


def test_follow_up_in_same_conversation(settings):
    svc, _ = make_service(settings)
    ask(svc, "sales by branch last month")
    r = ask(svc, "and yesterday")
    assert r.type == "answer" and "[branch]" in r.sql and "'2026-09-29'" in r.sql


def test_trend_line_chart_and_total(settings):
    svc, _ = make_service(settings)
    r = ask(svc, "daily sales last month")
    assert r.chart.type == "line" and "Total across all periods: ₹6,000" in r.text


def test_unknown_client(settings):
    svc, _ = make_service(settings)
    r = svc.chat(ChatRequest(client_id="nope", user_id="u", conversation_id="c", message="sales"))
    assert r.type == "error"


def test_no_database_configured(settings):
    svc = ChatService(settings, executor_factory=lambda pack, timeout: None, today=lambda: TODAY)
    r = ask(svc, "sales today")
    assert r.type == "error" and "BELLONA_RISTA_DSN" in r.text and r.sql


def test_api_requires_key(settings):
    svc, _ = make_service(settings)
    with TestClient(create_app(svc)) as client:
        assert client.get("/health").status_code == 200
        body = {"client_id": "bellona_rista", "user_id": "u", "conversation_id": "c", "message": "sales today"}
        assert client.post("/v1/chat", json=body).status_code == 401
        r = client.post("/v1/chat", json=body, headers={"X-Api-Key": "test-key"})
        assert r.status_code == 200 and r.json()["type"] == "answer"
        fb = {"client_id": "bellona_rista", "user_id": "u", "query_id": r.json()["query_id"], "rating": 1}
        assert client.post("/v1/feedback", json=fb, headers={"X-Api-Key": "test-key"}).status_code == 200


def test_indian_grouping():
    assert indian_group(1234567) == "12,34,567"
    assert indian_group(999) == "999"
    assert indian_group(-100000) == "-1,00,000"
