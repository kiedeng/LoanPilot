from __future__ import annotations

from typing import Any


ALLOWED_INTENTS = {"bill_summary", "product_recommendation", "status_query", "policy_qa"}
ALLOWED_CARD_TYPES = {"bill_summary", "product_recommendation", "application_status", "policy_qa"}


def validate_dify_result(metadata: dict[str, Any]) -> tuple[bool, str | None]:
    intent = metadata.get("intent")
    if intent not in ALLOWED_INTENTS:
        return False, f"Unsupported intent: {intent}"
    card = metadata.get("card")
    if card:
        card_type = card.get("type")
        if card_type not in ALLOWED_CARD_TYPES:
            return False, f"Unsupported card type: {card_type}"
    return True, None
