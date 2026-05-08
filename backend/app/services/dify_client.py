from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any, Protocol
from uuid import uuid4

from app.schemas.chat import DifyMockRequest


class DifyClient(Protocol):
    def stream_chat(self, request: DifyMockRequest) -> Iterator[dict[str, Any]]:
        """Stream Dify-compatible events."""


class MockDifyClient:
    """Local stand-in for Dify workflow streaming.

    Intent detection, pending slot handling, and conversation variables live here
    to keep the backend shaped like a Dify proxy instead of a local intent router.
    """

    _conversation_vars: dict[str, dict[str, Any]] = {}

    def stream_chat(self, request: DifyMockRequest) -> Iterator[dict[str, Any]]:
        dify_conversation_id = request.conversation_id or f"dify-{uuid4().hex}"
        variables = self._conversation_vars.setdefault(dify_conversation_id, {})
        query = request.query.strip()
        inputs = request.inputs

        if variables.get("pending_intent") == "bill_summary":
            loan_id = self._resolve_loan_id(query, inputs, variables)
            if loan_id:
                variables.pop("pending_intent", None)
                variables["last_intent"] = "bill_summary"
                variables["loan_id"] = loan_id
                yield from self._bill_summary_events(dify_conversation_id, loan_id)
                return

        intent = self._detect_intent(query)
        variables["last_intent"] = intent

        if intent == "bill_summary":
            loan_id = self._resolve_loan_id(query, inputs, variables)
            if not loan_id:
                variables["pending_intent"] = "bill_summary"
                variables["pending_slots"] = {"loan_id": None}
                answer = "你名下有两笔贷款，请问要查哪一笔？可以回复“第一笔”或直接告诉我贷款编号。"
                yield from self._message_chunks(answer)
                yield {
                    "event": "message_end",
                    "metadata": {
                        "conversation_id": dify_conversation_id,
                        "intent": "bill_summary",
                        "state": "clarifying",
                        "answer": answer,
                        "slots": {"missing": ["loan_id"]},
                        "requires_clarification": True,
                    },
                }
                return
            variables["loan_id"] = loan_id
            yield from self._bill_summary_events(dify_conversation_id, loan_id)
            return

        if intent == "product_recommendation":
            segment = self._detect_segment(query, inputs)
            answer = "我先根据你的用途和客群，给你匹配一个合适的贷款产品。"
            yield from self._message_chunks(answer)
            yield {
                "event": "tool_call",
                "tool": "recommend_products",
                "arguments": {"segment": segment, "query": query},
            }
            yield {
                "event": "message_end",
                "metadata": {
                    "conversation_id": dify_conversation_id,
                    "intent": "product_recommendation",
                    "state": "product_matching",
                    "answer": answer,
                    "slots": {"segment": segment},
                    "card": {"type": "product_recommendation", "slots": {"segment": segment, "query": query}},
                },
            }
            return

        if intent == "status_query":
            answer = "我帮你查看当前申请进度。"
            yield from self._message_chunks(answer)
            yield {"event": "tool_call", "tool": "application_status", "arguments": {"application_id": "LP-DEMO-001"}}
            yield {
                "event": "message_end",
                "metadata": {
                    "conversation_id": dify_conversation_id,
                    "intent": "status_query",
                    "state": "under_review",
                    "answer": answer,
                    "slots": {"application_id": "LP-DEMO-001"},
                    "card": {"type": "application_status", "slots": {"application_id": "LP-DEMO-001"}},
                },
            }
            return

        answer = "我可以帮你解答贷款政策、申请材料、还款账单和审批进度。你可以把问题说得更具体一点。"
        yield from self._message_chunks(answer)
        yield {
            "event": "message_end",
            "metadata": {
                "conversation_id": dify_conversation_id,
                "intent": "policy_qa",
                "state": "consulting",
                "answer": answer,
                "slots": {},
                "card": {"type": "policy_qa", "slots": {"answer": answer}},
            },
        }

    def _bill_summary_events(self, dify_conversation_id: str, loan_id: str) -> Iterator[dict[str, Any]]:
        first = "我帮你查一下本月账单。"
        yield from self._message_chunks(first)
        yield {"event": "tool_call", "tool": "bill_summary", "arguments": {"loan_id": loan_id}}
        yield {
            "event": "message_end",
            "metadata": {
                "conversation_id": dify_conversation_id,
                "intent": "bill_summary",
                "state": "repayment_servicing",
                "answer": first,
                "slots": {"loan_id": loan_id},
                "card": {"type": "bill_summary", "slots": {"loan_id": loan_id}},
                "memory_updates": [{"key": "default_loan_id", "value": loan_id, "scope": "dify_conversation"}],
            },
        }

    @staticmethod
    def _detect_intent(query: str) -> str:
        if any(word in query for word in ["账单", "本月", "还多少", "还款", "月供", "应还"]):
            return "bill_summary"
        if any(word in query for word in ["进度", "审批", "到哪", "申请状态"]):
            return "status_query"
        if any(word in query for word in ["贷款", "额度", "装修", "经营", "周转", "产品"]):
            return "product_recommendation"
        return "policy_qa"

    @staticmethod
    def _message_chunks(answer: str) -> Iterator[dict[str, Any]]:
        for index in range(0, len(answer), 6):
            yield {"event": "message", "answer": answer[index : index + 6]}
            time.sleep(0.06)

    @staticmethod
    def _detect_segment(query: str, inputs: dict[str, Any]) -> str:
        if inputs.get("role") == "existing":
            return "existing"
        if any(word in query for word in ["经营", "周转", "企业", "流水", "餐饮"]):
            return "business"
        if any(word in query for word in ["理财", "资产", "质押"]):
            return "wealth"
        return "personal"

    @staticmethod
    def _resolve_loan_id(query: str, inputs: dict[str, Any], variables: dict[str, Any]) -> str | None:
        selected = inputs.get("selected_loan_id")
        if isinstance(selected, str) and selected:
            return selected
        remembered = variables.get("loan_id")
        if isinstance(remembered, str) and remembered:
            return remembered
        if "LN-" in query:
            return query[query.index("LN-") :].split()[0].strip("，。,.")
        if any(word in query for word in ["第一", "1", "一笔", "默认"]):
            return "LN-DEMO-001"
        return None
