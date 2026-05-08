from __future__ import annotations

import json
import re
import time
from collections.abc import Iterator
from uuid import uuid4

from sqlalchemy.orm import Session

from app.agent_messages import (
    application_message,
    application_status_message,
    assessment_message,
    bill_summary_message,
    comparison_message,
    info_message,
    loan_recommendation_message,
    prepayment_quote_message,
    repayment_plan_message,
    text_message,
)
from app.adapters.mock_bank import MockBankingAdapter
from app.models.domain import AiToolCallLog, Conversation, Message, ResponseCard, User, WorkflowState
from app.schemas.chat import ChatResponse, ChatStreamRequest, DifyMockRequest
from app.services.ai_governance import validate_dify_result
from app.services.audit import write_audit_log
from app.services.dify_client import DifyClient, MockDifyClient


class AiGateway:
    def __init__(self, db: Session, dify_client: DifyClient | None = None) -> None:
        self.db = db
        self.bank = MockBankingAdapter(db)
        self.dify_client = dify_client or MockDifyClient()

    def stream_chat(self, request: ChatStreamRequest) -> Iterator[tuple[str, dict]]:
        conversation_id = request.conversation_id or uuid4().hex
        self._ensure_conversation(request.user_id, conversation_id)
        self._save_message(conversation_id, "user", request.message)

        dify_conversation_id = self._get_dify_conversation_id(conversation_id)
        dify_request = DifyMockRequest(
            conversation_id=dify_conversation_id,
            inputs=self._build_inputs(request, conversation_id),
            query=request.message,
            user=f"user:{request.user_id}",
        )

        yield "conversation", {"conversation_id": conversation_id}

        answer_parts: list[str] = []
        final_metadata: dict | None = None
        actual_dify_conversation_id = dify_conversation_id

        for event in self.dify_client.stream_chat(dify_request):
            event_name = event.get("event")
            if event_name == "message":
                token = event.get("answer", "")
                if token:
                    answer_parts.append(token)
            elif event_name == "tool_call":
                self._save_tool_call(
                    conversation_id,
                    actual_dify_conversation_id or "",
                    event.get("tool", "unknown"),
                    event.get("arguments", {}),
                )
            elif event_name == "message_end":
                final_metadata = event.get("metadata", {})
                actual_dify_conversation_id = final_metadata.get("conversation_id", actual_dify_conversation_id)

        if not final_metadata:
            yield "error", {"message": "Dify mock did not return a final event."}
            return

        valid, reason = validate_dify_result(final_metadata)
        if not valid:
            content = "这个请求暂时不能由 AI 助手处理，我已经为你转人工或保留记录。"
            message = text_message(content, intent="policy_qa", state="blocked", slots={"governance_error": reason})
            assistant_message = self._save_message(conversation_id, "assistant", message["content"], {"message": message})
            self._save_workflow_state(conversation_id, actual_dify_conversation_id, "blocked", "policy_qa", {})
            write_audit_log(self.db, f"user:{request.user_id}", "chat.blocked", {"conversation_id": conversation_id, "reason": reason})
            yield from self._token_events(message["content"])
            yield "message", {"message": message}
            yield "done", {"state": "blocked", "intent": "policy_qa", "message_id": assistant_message.id}
            return

        content = final_metadata.get("answer") or "".join(answer_parts)
        if final_metadata.get("requires_clarification"):
            message = text_message(
                content,
                intent=final_metadata.get("intent", "policy_qa"),
                state=final_metadata.get("state", "clarifying"),
                slots=final_metadata.get("slots", {}),
            )
            assistant_message = self._save_message(conversation_id, "assistant", message["content"], {"message": message, "dify": final_metadata})
            self._save_workflow_state(
                conversation_id,
                actual_dify_conversation_id,
                final_metadata.get("state", "clarifying"),
                final_metadata.get("intent", "policy_qa"),
                {"dify_managed_slots": final_metadata.get("slots", {})},
            )
            write_audit_log(self.db, f"user:{request.user_id}", "chat.clarification", {"conversation_id": conversation_id})
            yield from self._token_events(message["content"])
            yield "message", {"message": message}
            yield "done", {
                "state": final_metadata.get("state", "clarifying"),
                "intent": final_metadata.get("intent", "policy_qa"),
                "message_id": assistant_message.id,
            }
            return

        message = self._build_agent_message(final_metadata)
        assistant_message = self._save_message(
            conversation_id,
            "assistant",
            message["content"],
            {"message": message, "dify": final_metadata},
        )
        self._save_cards(conversation_id, assistant_message.id, message)
        self._save_workflow_state(
            conversation_id,
            actual_dify_conversation_id,
            final_metadata.get("state", "consulting"),
            final_metadata.get("intent", "policy_qa"),
            {"last_dify_result": final_metadata},
        )
        write_audit_log(
            self.db,
            f"user:{request.user_id}",
            f"chat.{final_metadata.get('intent', 'policy_qa')}",
            {"conversation_id": conversation_id, "dify_conversation_id": actual_dify_conversation_id},
        )

        yield from self._token_events(message["content"])
        yield "message", {"message": message}
        yield "done", {
            "state": final_metadata.get("state", "consulting"),
            "intent": final_metadata.get("intent", "policy_qa"),
            "message_id": assistant_message.id,
        }

    def chat_message(self, request: ChatStreamRequest) -> ChatResponse:
        content_parts: list[str] = []
        conversation_id = request.conversation_id or ""
        state = "consulting"
        intent = "policy_qa"
        messages: list[dict] = []

        for event_name, payload in self.stream_chat(request):
            if event_name == "conversation":
                conversation_id = payload["conversation_id"]
            elif event_name == "token":
                content_parts.append(payload.get("content", ""))
            elif event_name == "message":
                messages.append(payload["message"])
            elif event_name == "done":
                state = payload.get("state", state)
                intent = payload.get("intent", intent)

        return ChatResponse(
            conversation_id=conversation_id,
            state=state,
            intent=intent,
            content=messages[-1]["content"] if messages else "".join(content_parts),
            messages=messages,
        )

    def handle_action(self, user_id: int, conversation_id: str, action_id: str, payload: dict) -> ChatResponse:
        self._ensure_conversation(user_id, conversation_id)
        segment = payload.get("segment", "personal")

        if action_id == "pre_assess":
            assessment = self.bank.pre_assess_credit_limit(
                {"segment": segment, "requested_amount": payload.get("amount", 200000)}
            )
            message = assessment_message(assessment, payload, intent="pre_assessment", state="pre_assessing")
            state, intent = "pre_assessing", "pre_assessment"
        elif action_id == "apply_now":
            application = self.bank.create_loan_application(
                user_id=user_id,
                product_id=payload.get("productId", "consumer_loan"),
                amount=float(payload.get("amount", 200000)),
                purpose=payload.get("purpose", "消费周转"),
            )
            checklist = self.bank.get_document_checklist(segment, application["applicationId"])
            status = self.bank.query_application_status(application["applicationId"])
            message = application_message(status, checklist, intent="application_creation", state="collecting_materials")
            state, intent = "collecting_materials", "application_creation"
        elif action_id == "upload_document":
            upload = self.bank.upload_document(payload.get("applicationId", "LP-DEMO"), "身份证", "demo-id-card.png")
            message = info_message(
                "材料上传状态",
                [
                    f"申请单：{upload['applicationId']}",
                    "身份证已模拟上传",
                    "Mock OCR 识别状态：recognized",
                    "下一步：等待银行审批或补充材料通知",
                ],
                "材料已模拟上传并完成 OCR 识别。",
                intent="document_collection",
                state="under_review",
            )
            state, intent = "under_review", "document_collection"
        elif action_id == "view_repayment_plan":
            plan = self.bank.query_repayment_plan(payload.get("loanId", "LN-DEMO-001"))
            message = repayment_plan_message(plan, intent="repayment_query", state="repayment_servicing")
            state, intent = "repayment_servicing", "repayment_query"
        elif action_id == "prepay":
            quote = self.bank.quote_prepayment(payload.get("loanId", "LN-DEMO-001"))
            message = prepayment_quote_message(quote, intent="prepayment_quote", state="prepayment_quoting")
            state, intent = "prepayment_quoting", "prepayment_quote"
        elif action_id == "compare_options":
            message = comparison_message(self.bank.compare_loan_options()["options"], intent="option_comparison", state="comparing_options")
            state, intent = "comparing_options", "option_comparison"
        else:
            handoff = self.bank.request_human_handoff(f"用户触发动作：{action_id}")
            message = info_message(
                "人工接管",
                [f"工单号：{handoff['ticketId']}", "已进入人工服务队列。"],
                "该动作已转人工处理。",
                intent="human_handoff",
                state="human_handoff",
            )
            state, intent = "human_handoff", "human_handoff"

        assistant_message = self._save_message(
            conversation_id,
            "assistant",
            message["content"],
            {"message": message, "action_id": action_id},
        )
        self._save_cards(conversation_id, assistant_message.id, message)
        self._save_workflow_state(conversation_id, self._get_dify_conversation_id(conversation_id), state, intent, {"action_id": action_id})
        write_audit_log(self.db, f"user:{user_id}", f"action.{action_id}", payload)

        return ChatResponse(
            conversation_id=conversation_id,
            state=state,
            intent=intent,
            content=message["content"],
            messages=[message],
        )

    def _build_inputs(self, request: ChatStreamRequest, conversation_id: str) -> dict:
        user = self.db.get(User, request.user_id)
        client_context = request.client_context or {}
        return {
            "user_id": str(request.user_id),
            "role": user.segment if user else "borrower",
            "tenant_id": "demo",
            "conversation_id": conversation_id,
            "current_page": client_context.get("page", "chat"),
            "selected_loan_id": client_context.get("selected_loan_id"),
            "selected_application_id": client_context.get("selected_application_id"),
            "allowed_tool_scopes": ["loan.read", "bill.read", "application.read"],
        }

    def _build_agent_message(self, metadata: dict) -> dict:
        card = metadata.get("card") or {}
        card_type = card.get("type")
        slots = card.get("slots") or metadata.get("slots") or {}
        intent = metadata.get("intent", "policy_qa")
        state = metadata.get("state", "consulting")

        if card_type == "bill_summary":
            return bill_summary_message(self.bank.query_bill_summary(slots.get("loan_id", "LN-DEMO-001")), intent=intent, state=state)
        if card_type == "product_recommendation":
            segment = slots.get("segment", "personal")
            products = self.bank.recommend_products(slots.get("query", ""), segment)
            return loan_recommendation_message(products, intent=intent, state=state, slots=slots)
        if card_type == "application_status":
            status = self.bank.query_application_status(slots.get("application_id", "LP-DEMO-001"))
            return application_status_message(status, intent=intent, state=state)
        return text_message(metadata.get("answer", "我可以继续帮你处理贷款问题。"), intent=intent, state=state, slots=slots)

    def _ensure_conversation(self, user_id: int, conversation_id: str) -> None:
        if not self.db.get(Conversation, conversation_id):
            self.db.add(Conversation(id=conversation_id, user_id=user_id))
            self.db.commit()

    def _save_message(self, conversation_id: str, role: str, content: str, payload: dict | None = None) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            payload_json=json.dumps(payload or {}, ensure_ascii=False),
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def _save_cards(self, conversation_id: str, message_id: int, message: dict) -> None:
        for card in message.get("meta_data", {}).get("multi_load", []):
            self.db.add(
                ResponseCard(
                    conversation_id=conversation_id,
                    message_id=message_id,
                    surface_id=card.get("source_seq", uuid4().hex),
                    card_type=card.get("type", "agent_card"),
                    card_json=json.dumps(card, ensure_ascii=False),
                )
            )
        self.db.commit()

    @staticmethod
    def _visible_content(content: str) -> str:
        without_placeholders = re.sub(r"\[\([^)]+\)\]", "", content)
        return re.sub(r"\n{3,}", "\n\n", without_placeholders).strip()

    @staticmethod
    def _streamable_content(content: str) -> str:
        first_placeholder = re.search(r"\[\([^)]+\)\]", content)
        if not first_placeholder:
            return AiGateway._visible_content(content)
        return content[: first_placeholder.start()].strip()

    def _token_events(self, content: str) -> Iterator[tuple[str, dict]]:
        streamable_content = self._streamable_content(content)
        for index in range(0, len(streamable_content), 6):
            time.sleep(0.06)
            yield "token", {"content": streamable_content[index : index + 6]}

    def _save_tool_call(self, conversation_id: str, dify_conversation_id: str, tool_name: str, arguments: dict) -> None:
        self.db.add(
            AiToolCallLog(
                conversation_id=conversation_id,
                dify_conversation_id=dify_conversation_id,
                tool_name=tool_name,
                arguments_json=json.dumps(arguments, ensure_ascii=False),
                result_json="{}",
            )
        )
        self.db.commit()

    def _get_dify_conversation_id(self, conversation_id: str) -> str | None:
        workflow_state = self.db.get(WorkflowState, conversation_id)
        if not workflow_state:
            return None
        try:
            context = json.loads(workflow_state.context_json or "{}")
        except json.JSONDecodeError:
            return None
        dify_id = context.get("dify_conversation_id")
        return dify_id if isinstance(dify_id, str) and dify_id else None

    def _save_workflow_state(self, conversation_id: str, dify_conversation_id: str | None, state: str, intent: str, context: dict) -> None:
        workflow_state = self.db.get(WorkflowState, conversation_id)
        payload = {**context, "dify_conversation_id": dify_conversation_id}
        if workflow_state:
            workflow_state.state = state
            workflow_state.intent = intent
            workflow_state.context_json = json.dumps(payload, ensure_ascii=False)
        else:
            self.db.add(
                WorkflowState(
                    conversation_id=conversation_id,
                    state=state,
                    intent=intent,
                    context_json=json.dumps(payload, ensure_ascii=False),
                )
            )
        self.db.commit()
