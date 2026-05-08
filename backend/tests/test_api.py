import json
import re

from app.agent_messages import card_message
from app.db.session import SessionLocal
from app.schemas.chat import ChatStreamRequest
from app.services.ai_gateway import AiGateway


def _gateway_response(message: str, user_id: int = 1, conversation_id: str | None = None):
    db = SessionLocal()
    try:
        return AiGateway(db).chat_message(ChatStreamRequest(message=message, user_id=user_id, conversation_id=conversation_id))
    finally:
        db.close()


def _stream_events(message: str, user_id: int = 1, conversation_id: str | None = None, client_context: dict | None = None) -> list[tuple[str, dict]]:
    db = SessionLocal()
    try:
        request = ChatStreamRequest(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            client_context=client_context or {},
        )
        return list(AiGateway(db).stream_chat(request))
    finally:
        db.close()


def _run_action(action_id: str, conversation_id: str, payload: dict):
    db = SessionLocal()
    try:
        return AiGateway(db).handle_action(1, conversation_id, action_id, payload)
    finally:
        db.close()


def _message_card(message: dict, source_seq: str) -> dict:
    cards = message["meta_data"]["multi_load"]
    return next(card for card in cards if card["source_seq"] == source_seq)


def _visible_content(content: str) -> str:
    without_placeholders = re.sub(r"\[\([^)]+\)\]", "", content)
    return re.sub(r"\n{3,}", "\n\n", without_placeholders).strip()


def _streamable_content(content: str) -> str:
    first_placeholder = re.search(r"\[\([^)]+\)\]", content)
    if not first_placeholder:
        return _visible_content(content)
    return content[: first_placeholder.start()].strip()


def _source_seqs(content: str) -> list[str]:
    return re.findall(r"\[\(([^)]+)\)\]", content)


def test_chat_returns_qwen_like_agent_message() -> None:
    data = _gateway_response("我想贷款20万装修，多久能放款？").model_dump()
    assert data["conversation_id"]
    assert "surface_id" not in data
    assert "a2ui_messages" not in data
    message = data["messages"][0]
    assert message["mime_type"] == "multi_load/iframe"
    source_seq = re.search(r"\[\(([^)]+)\)\]", message["content"]).group(1)
    card = _message_card(message, source_seq)
    assert card["type"] == "loan_recommend"
    assert message["meta_data"]["intent_data"]["intent"] == "product_recommendation"
    assert message["content"].index("我先根据你的用途") < message["content"].index(f"[({source_seq})]")
    assert message["content"].index(f"[({source_seq})]") < message["content"].index("你可以先看额度")


def test_pre_assess_action_returns_agent_message() -> None:
    chat = _gateway_response("我想测一下额度")
    data = _run_action("pre_assess", chat.conversation_id, {"amount": 200000}).model_dump()
    assert data["state"] == "pre_assessing"
    assert data["intent"] == "pre_assessment"
    message = data["messages"][0]
    assert message["mime_type"] == "multi_load/iframe"
    assert _message_card(message, "assessment_result_1")["type"] == "assessment_result"


def test_chat_stream_returns_tokens_message_and_done() -> None:
    events = _stream_events(
        "这个月我需要还多少",
        user_id=3,
        client_context={"page": "chat", "selected_loan_id": "LN-DEMO-001"},
    )
    event_names = [name for name, _ in events]
    assert event_names[0] == "conversation"
    assert "token" in event_names
    assert "message" in event_names
    assert "card" not in event_names
    assert event_names[-1] == "done"
    final_message = next(payload["message"] for name, payload in events if name == "message")
    merged_tokens = "".join(payload["content"] for name, payload in events if name == "token")
    assert merged_tokens == _streamable_content(final_message["content"])
    assert _message_card(final_message, "bill_summary_1")["type"] == "bill_summary"
    assert events[-1][1]["intent"] == "bill_summary"


def test_product_recommendation_payload_has_slots_and_no_external_fields() -> None:
    events = _stream_events("我是开餐饮店的，想贷50万周转")
    message = next(payload["message"] for name, payload in events if name == "message")
    assert message["mime_type"] == "multi_load/iframe"
    assert message["meta_data"]["slots"]["segment"] == "business"
    source_seq = re.search(r"\[\(([^)]+)\)\]", message["content"]).group(1)
    card = _message_card(message, source_seq)
    assert _source_seqs(message["content"]) == [card["source_seq"]]
    result_data = card["content"]["resultData"]
    items = result_data["loanRecommendationItems"]
    assert result_data["recommendType"] == "LOAN_PRODUCT"
    assert items
    assert {"productId", "productName", "maxAmount", "rateRange", "termRange", "estimatedDisbursement"} <= set(items[0])
    serialized = json.dumps(message, ensure_ascii=False)
    assert "jwt" not in serialized
    assert "longitude" not in serialized
    assert "latitude" not in serialized
    assert "sku" not in serialized.lower()
    assert "elemecdn" not in serialized
    assert "myquark" not in serialized


def test_agent_message_supports_multiple_card_placeholders() -> None:
    message = card_message(
        content="先看推荐：\n\n[(card_a)]\n\n再看试算：\n\n[(card_b)]\n\n你可以继续选择。",
        intent="demo",
        state="demoing",
        slots={"amount": 200000},
        cards=[
            {"type": "loan_recommend", "source_seq": "card_a", "content": {"resultData": {}}},
            {"type": "repayment_plan", "source_seq": "card_b", "content": {"resultData": {}}},
        ],
    )
    assert _source_seqs(message["content"]) == ["card_a", "card_b"]
    assert [card["source_seq"] for card in message["meta_data"]["multi_load"]] == ["card_a", "card_b"]


def test_chat_stream_clarifies_then_reuses_dify_conversation() -> None:
    first_events = _stream_events("这个月我需要还多少", user_id=3)
    conversation_id = first_events[0][1]["conversation_id"]
    assert first_events[-1][1]["state"] == "clarifying"
    assert not any(name == "card" for name, _ in first_events)
    assert any(name == "message" for name, _ in first_events)

    second_events = _stream_events("第一笔", user_id=3, conversation_id=conversation_id)
    assert any(name == "message" for name, _ in second_events)
    assert second_events[-1][1]["intent"] == "bill_summary"


def test_view_repayment_plan_action() -> None:
    chat = _gateway_response("这个月我需要还多少")
    data = _run_action("view_repayment_plan", chat.conversation_id, {"loanId": "LN-DEMO-001"}).model_dump()
    assert data["state"] == "repayment_servicing"
    assert data["intent"] == "repayment_query"
    assert _message_card(data["messages"][0], "repayment_plan_1")["type"] == "repayment_plan"
