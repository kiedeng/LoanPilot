from __future__ import annotations

import json
from collections.abc import Iterator
from uuid import uuid4

from sqlalchemy.orm import Session

from app.a2ui.builder import (
    application_surface,
    assessment_surface,
    bill_surface,
    comparison_surface,
    prepayment_surface,
    product_surface,
    repayment_surface,
    simple_info_surface,
)
from app.adapters.mock_bank import MockBankingAdapter
from app.models.domain import AiToolCallLog, Conversation, Message, ResponseCard, User, WorkflowState
from app.schemas.chat import ActionRequest, ChatResponse, ChatStreamRequest, DifyMockRequest
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
                    yield "token", {"content": token}
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
            assistant_message = self._save_message(conversation_id, "assistant", content, {"governance_error": reason})
            self._save_workflow_state(conversation_id, actual_dify_conversation_id, "blocked", "policy_qa", {})
            write_audit_log(self.db, f"user:{request.user_id}", "chat.blocked", {"conversation_id": conversation_id, "reason": reason})
            yield "token", {"content": content}
            yield "done", {"state": "blocked", "intent": "policy_qa", "message_id": assistant_message.id}
            return

        content = final_metadata.get("answer") or "".join(answer_parts)
        if final_metadata.get("requires_clarification"):
            assistant_message = self._save_message(conversation_id, "assistant", content, {"dify": final_metadata})
            self._save_workflow_state(
                conversation_id,
                actual_dify_conversation_id,
                final_metadata.get("state", "clarifying"),
                final_metadata.get("intent", "policy_qa"),
                {"dify_managed_slots": final_metadata.get("slots", {})},
            )
            write_audit_log(self.db, f"user:{request.user_id}", "chat.clarification", {"conversation_id": conversation_id})
            yield "done", {
                "state": final_metadata.get("state", "clarifying"),
                "intent": final_metadata.get("intent", "policy_qa"),
                "message_id": assistant_message.id,
            }
            return

        surface_id = f"loanpilot-{uuid4().hex}"
        a2ui_messages = self._build_a2ui(surface_id, final_metadata)
        assistant_message = self._save_message(
            conversation_id,
            "assistant",
            content,
            {"surface_id": surface_id, "a2ui_messages": a2ui_messages, "dify": final_metadata},
        )
        self._save_card(conversation_id, assistant_message.id, surface_id, a2ui_messages)
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

        yield "card", {"surface_id": surface_id, "a2ui_messages": a2ui_messages}
        yield "done", {
            "state": final_metadata.get("state", "consulting"),
            "intent": final_metadata.get("intent", "policy_qa"),
            "surface_id": surface_id,
            "message_id": assistant_message.id,
        }

    def chat_message(self, request: ChatStreamRequest) -> ChatResponse:
        content_parts: list[str] = []
        conversation_id = request.conversation_id or ""
        state = "consulting"
        intent = "policy_qa"
        surface_id = ""
        a2ui_messages: list[dict] = []

        for event_name, payload in self.stream_chat(request):
            if event_name == "conversation":
                conversation_id = payload["conversation_id"]
            elif event_name == "token":
                content_parts.append(payload.get("content", ""))
            elif event_name == "card":
                surface_id = payload.get("surface_id", "")
                a2ui_messages = payload.get("a2ui_messages", [])
            elif event_name == "done":
                state = payload.get("state", state)
                intent = payload.get("intent", intent)
                surface_id = payload.get("surface_id", surface_id)

        return ChatResponse(
            conversation_id=conversation_id,
            state=state,
            intent=intent,
            surface_id=surface_id,
            content="".join(content_parts),
            a2ui_messages=a2ui_messages,
        )

    def handle_action(self, user_id: int, conversation_id: str, action_id: str, payload: dict) -> ChatResponse:
        self._ensure_conversation(user_id, conversation_id)
        surface_id = f"loanpilot-{uuid4().hex}"
        segment = payload.get("segment", "personal")

        if action_id == "pre_assess":
            assessment = self.bank.pre_assess_credit_limit(
                {"segment": segment, "requested_amount": payload.get("amount", 200000)}
            )
            content, a2ui_messages = assessment_surface(surface_id, assessment, payload)
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
            content, a2ui_messages = application_surface(surface_id, status, checklist)
            state, intent = "collecting_materials", "application_creation"
        elif action_id == "upload_document":
            upload = self.bank.upload_document(payload.get("applicationId", "LP-DEMO"), "身份证", "demo-id-card.png")
            content, a2ui_messages = simple_info_surface(
                surface_id,
                "材料上传状态",
                [
                    f"申请单：{upload['applicationId']}",
                    "身份证已模拟上传",
                    "Mock OCR 识别状态：recognized",
                    "下一步：等待银行审批或补充材料通知",
                ],
                "材料已模拟上传并完成 OCR 识别。",
            )
            state, intent = "under_review", "document_collection"
        elif action_id == "view_repayment_plan":
            plan = self.bank.query_repayment_plan(payload.get("loanId", "LN-DEMO-001"))
            content, a2ui_messages = repayment_surface(surface_id, plan)
            state, intent = "repayment_servicing", "repayment_query"
        elif action_id == "prepay":
            quote = self.bank.quote_prepayment(payload.get("loanId", "LN-DEMO-001"))
            content, a2ui_messages = prepayment_surface(surface_id, quote)
            state, intent = "prepayment_quoting", "prepayment_quote"
        elif action_id == "compare_options":
            content, a2ui_messages = comparison_surface(surface_id, self.bank.compare_loan_options()["options"])
            state, intent = "comparing_options", "option_comparison"
        else:
            handoff = self.bank.request_human_handoff(f"用户触发动作：{action_id}")
            content, a2ui_messages = simple_info_surface(
                surface_id,
                "人工接管",
                [f"工单号：{handoff['ticketId']}", "已进入人工服务队列。"],
                "该动作已转人工处理。",
            )
            state, intent = "human_handoff", "human_handoff"

        assistant_message = self._save_message(
            conversation_id,
            "assistant",
            content,
            {"surface_id": surface_id, "a2ui_messages": a2ui_messages, "action_id": action_id},
        )
        self._save_card(conversation_id, assistant_message.id, surface_id, a2ui_messages)
        self._save_workflow_state(conversation_id, self._get_dify_conversation_id(conversation_id), state, intent, {"action_id": action_id})
        write_audit_log(self.db, f"user:{user_id}", f"action.{action_id}", payload)

        return ChatResponse(
            conversation_id=conversation_id,
            state=state,
            intent=intent,
            surface_id=surface_id,
            content=content,
            a2ui_messages=a2ui_messages,
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

    def _build_a2ui(self, surface_id: str, metadata: dict) -> list[dict]:
        card = metadata.get("card") or {}
        card_type = card.get("type")
        slots = card.get("slots") or metadata.get("slots") or {}

        if card_type == "bill_summary":
            return bill_surface(surface_id, self.bank.query_bill_summary(slots.get("loan_id", "LN-DEMO-001")))[1]
        if card_type == "product_recommendation":
            segment = slots.get("segment", "personal")
            products = self.bank.recommend_products(slots.get("query", ""), segment)
            return product_surface(surface_id, products[0])[1]
        if card_type == "application_status":
            status = self.bank.query_application_status(slots.get("application_id", "LP-DEMO-001"))
            lines = [f"{step['name']}: {step['status']}" for step in status["steps"]]
            return simple_info_surface(surface_id, "申请进度", lines, "这是当前演示申请的进度。")[1]
        return simple_info_surface(surface_id, "LoanPilot", [metadata.get("answer", "我可以继续帮你处理贷款问题。")])[1]

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

    def _save_card(self, conversation_id: str, message_id: int, surface_id: str, a2ui_messages: list[dict]) -> None:
        self.db.add(
            ResponseCard(
                conversation_id=conversation_id,
                message_id=message_id,
                surface_id=surface_id,
                card_type="a2ui",
                card_json=json.dumps({"a2ui_messages": a2ui_messages}, ensure_ascii=False),
            )
        )
        self.db.commit()

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
