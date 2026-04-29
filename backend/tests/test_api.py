from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_returns_official_a2ui_surface() -> None:
    response = client.post("/api/chat/message", json={"message": "我想贷20万装修，多久能放款？"})
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
    chat = client.post("/api/chat/message", json={"message": "我能贷多少？"}).json()
    response = client.post(
        "/api/actions/pre_assess",
        json={"conversation_id": chat["conversation_id"], "payload": {"amount": 200000}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "pre_assessing"
    assert data["intent"] == "pre_assessment"
    assert data["a2ui_messages"][0]["createSurface"]["catalogId"].endswith("/a2ui/catalog/v1")
