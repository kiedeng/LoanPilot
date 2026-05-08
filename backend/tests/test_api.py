import json

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_returns_official_a2ui_surface() -> None:
    response = client.post("/api/chat/message", json={"message": "我想贷款20万装修，多久能放款？"})
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"]
    assert data["surface_id"]
    assert data["a2ui_messages"][0]["version"] == "v0.9"
    assert "createSurface" in data["a2ui_messages"][0]
    assert "updateComponents" in data["a2ui_messages"][2]
    components = data["a2ui_messages"][2]["updateComponents"]["components"]
    assert any(component["id"] == "root" and component["component"] == "LoanInsightCard" for component in components)


def test_pre_assess_action() -> None:
    chat = client.post("/api/chat/message", json={"message": "我想测一下额度"}).json()
    response = client.post(
        "/api/actions/pre_assess",
        json={"conversation_id": chat["conversation_id"], "payload": {"amount": 200000}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "pre_assessing"
    assert data["intent"] == "pre_assessment"
    assert data["a2ui_messages"][0]["createSurface"]["catalogId"].endswith("/a2ui/catalog/v1")


def _stream_events(response) -> list[tuple[str, dict]]:
    events = []
    for block in response.text.strip().split("\n\n"):
        lines = block.splitlines()
        event = next(line.replace("event:", "").strip() for line in lines if line.startswith("event:"))
        data = next(line.replace("data:", "").strip() for line in lines if line.startswith("data:"))
        events.append((event, json.loads(data)))
    return events


def test_chat_stream_returns_tokens_card_and_done() -> None:
    response = client.post(
        "/api/chat/stream",
        json={
            "message": "这个月我需要还多少",
            "user_id": 3,
            "client_context": {"page": "chat", "selected_loan_id": "LN-DEMO-001"},
        },
    )
    assert response.status_code == 200
    events = _stream_events(response)
    event_names = [name for name, _ in events]
    assert event_names[0] == "conversation"
    assert "token" in event_names
    assert "card" in event_names
    assert event_names[-1] == "done"
    card = next(payload for name, payload in events if name == "card")
    assert card["a2ui_messages"][0]["version"] == "v0.9"
    assert "createSurface" in card["a2ui_messages"][0]
    assert events[-1][1]["intent"] == "bill_summary"


def test_chat_stream_clarifies_then_reuses_dify_conversation() -> None:
    first = client.post("/api/chat/stream", json={"message": "这个月我需要还多少", "user_id": 3})
    first_events = _stream_events(first)
    conversation_id = first_events[0][1]["conversation_id"]
    assert first_events[-1][1]["state"] == "clarifying"
    assert not any(name == "card" for name, _ in first_events)

    second = client.post(
        "/api/chat/stream",
        json={"conversation_id": conversation_id, "message": "第一笔", "user_id": 3},
    )
    second_events = _stream_events(second)
    assert any(name == "card" for name, _ in second_events)
    assert second_events[-1][1]["intent"] == "bill_summary"


def test_view_repayment_plan_action() -> None:
    chat = client.post("/api/chat/message", json={"message": "这个月我需要还多少"}).json()
    response = client.post(
        "/api/actions/view_repayment_plan",
        json={"conversation_id": chat["conversation_id"], "payload": {"loanId": "LN-DEMO-001"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "repayment_servicing"
    assert data["intent"] == "repayment_query"
    assert data["a2ui_messages"][0]["version"] == "v0.9"
