from __future__ import annotations

import json
from dataclasses import dataclass
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
from app.models.domain import Conversation, Message, WorkflowState
from app.services.audit import write_audit_log


@dataclass
class WorkflowResult:
    conversation_id: str
    state: str
    intent: str
    surface_id: str
    content: str
    a2ui_messages: list[dict]


class LoanWorkflow:
    """Deterministic LangGraph-ready workflow for the LoanPilot demo."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.bank = MockBankingAdapter(db)

    def handle_message(self, user_id: int, text: str, conversation_id: str | None = None) -> WorkflowResult:
        conversation_id = conversation_id or uuid4().hex
        self._ensure_conversation(user_id, conversation_id)
        self._save_message(conversation_id, "user", text)

        intent = self._detect_intent(text)
        segment = self._detect_segment(text, user_id)
        surface_id = self._new_surface_id()
        content, a2ui_messages = self._build_response(surface_id, intent, text, segment)
        state = self._state_for_intent(intent)

        self._save_message(conversation_id, "assistant", content, {"surface_id": surface_id, "a2ui_messages": a2ui_messages})
        self._save_workflow_state(conversation_id, state, intent, {"segment": segment})
        write_audit_log(self.db, f"user:{user_id}", f"chat.{intent}", {"conversation_id": conversation_id})
        return WorkflowResult(conversation_id, state, intent, surface_id, content, a2ui_messages)

    def handle_action(self, user_id: int, conversation_id: str, action_id: str, payload: dict) -> WorkflowResult:
        self._ensure_conversation(user_id, conversation_id)
        segment = payload.get("segment", "personal")
        surface_id = self._new_surface_id()

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

        self._save_message(conversation_id, "assistant", content, {"surface_id": surface_id, "a2ui_messages": a2ui_messages})
        self._save_workflow_state(conversation_id, state, intent, payload)
        write_audit_log(self.db, f"user:{user_id}", f"action.{action_id}", payload)
        return WorkflowResult(conversation_id, state, intent, surface_id, content, a2ui_messages)

    def _build_response(self, surface_id: str, intent: str, text: str, segment: str) -> tuple[str, list[dict]]:
        if intent == "product_recommendation":
            products = self.bank.recommend_products(text, segment)
            return product_surface(surface_id, products[0])
        if intent == "pre_assessment":
            assessment = self.bank.pre_assess_credit_limit({"segment": segment, "requested_amount": self._extract_amount(text)})
            return assessment_surface(surface_id, assessment, {"segment": segment, "amount": assessment["estimatedAmount"]})
        if intent == "rate_explanation":
            rate = self.bank.explain_rate()
            return simple_info_surface(
                surface_id,
                "利率说明",
                [f"参考利率区间：{rate['rateRange']}", f"影响因素：{'、'.join(rate['factors'])}", rate["disclaimer"]],
                "利率会受到客户资质、期限、用途和审批结果影响。",
            )
        if intent == "policy_qa":
            answer = self.bank.answer_policy_question(text)
            return simple_info_surface(surface_id, "政策答疑", [answer["answer"]], "这是演示版政策答疑结果。")
        if intent == "option_comparison":
            return comparison_surface(surface_id, self.bank.compare_loan_options()["options"])
        if intent == "status_query":
            status = self.bank.query_application_status("LP-DEMO-001")
            lines = [f"{step['name']}：{step['status']}" for step in status["steps"]]
            return simple_info_surface(surface_id, "申请进度", lines, "这是当前演示申请的进度。")
        if intent == "bill_summary":
            return bill_surface(surface_id, self.bank.query_bill_summary())
        if intent == "prepayment_quote":
            return prepayment_surface(surface_id, self.bank.quote_prepayment())
        if intent == "renewal_check":
            eligibility = self.bank.check_renewal_eligibility()
            return simple_info_surface(
                surface_id,
                "续贷资格查询",
                [f"是否可续贷：{'是' if eligibility['eligible'] else '否'}", eligibility["reason"], "续贷仍需银行最终审批。"],
                "这是基于 Mock 规则生成的续贷资格结果。",
            )
        if intent == "human_handoff":
            handoff = self.bank.request_human_handoff(text)
            return simple_info_surface(
                surface_id,
                "人工接管",
                [f"工单号：{handoff['ticketId']}", "涉及投诉、拒贷争议或高风险问题时，LoanPilot 会交由人工处理。"],
                "我已为你创建人工服务请求。",
            )
        return simple_info_surface(
            surface_id,
            "我可以帮你办理贷款相关服务",
            ["你可以咨询贷款产品、测算额度、创建申请、查询进度或查看还款计划。"],
        )

    @staticmethod
    def _detect_intent(text: str) -> str:
        if any(word in text for word in ["人工", "客服", "投诉", "拒贷"]):
            return "human_handoff"
        if any(word in text for word in ["提前还", "结清"]):
            return "prepayment_quote"
        if any(word in text for word in ["账单", "本月", "还多少"]):
            return "bill_summary"
        if any(word in text for word in ["还款计划", "每期"]):
            return "bill_summary"
        if "续贷" in text:
            return "renewal_check"
        if any(word in text for word in ["进度", "到哪", "审批"]):
            return "status_query"
        if any(word in text for word in ["利率", "利息"]):
            return "rate_explanation"
        if any(word in text for word in ["对比", "比较", "区别", "竞品"]):
            return "option_comparison"
        if any(word in text for word in ["能贷", "额度", "测算", "评估"]):
            return "pre_assessment"
        if any(word in text for word in ["政策", "材料", "需要什么", "条件"]):
            return "policy_qa"
        if any(word in text for word in ["贷款", "贷", "周转", "装修", "理财"]):
            return "product_recommendation"
        return "policy_qa"

    @staticmethod
    def _detect_segment(text: str, user_id: int) -> str:
        if any(word in text for word in ["小微", "企业", "经营", "流水", "周转", "餐饮"]):
            return "business"
        if any(word in text for word in ["理财", "资产", "质押"]):
            return "wealth"
        if user_id == 3:
            return "existing"
        return "personal"

    @staticmethod
    def _state_for_intent(intent: str) -> str:
        return {
            "product_recommendation": "product_matching",
            "pre_assessment": "pre_assessing",
            "option_comparison": "comparing_options",
            "status_query": "under_review",
            "bill_summary": "repayment_servicing",
            "prepayment_quote": "prepayment_quoting",
            "renewal_check": "renewal_checking",
            "human_handoff": "human_handoff",
        }.get(intent, "consulting")

    @staticmethod
    def _extract_amount(text: str) -> float:
        for marker in ["万", "w", "W"]:
            if marker in text:
                prefix = text.split(marker)[0]
                digits = "".join(ch for ch in prefix if ch.isdigit())
                if digits:
                    return float(digits[-3:]) * 10000
        return 200000

    @staticmethod
    def _new_surface_id() -> str:
        return f"loanpilot-{uuid4().hex}"

    def _ensure_conversation(self, user_id: int, conversation_id: str) -> None:
        if not self.db.get(Conversation, conversation_id):
            self.db.add(Conversation(id=conversation_id, user_id=user_id))
            self.db.commit()

    def _save_message(self, conversation_id: str, role: str, content: str, payload: dict | None = None) -> None:
        self.db.add(
            Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                payload_json=json.dumps(payload or {}, ensure_ascii=False),
            )
        )
        self.db.commit()

    def _save_workflow_state(self, conversation_id: str, state: str, intent: str, context: dict) -> None:
        workflow_state = self.db.get(WorkflowState, conversation_id)
        payload = json.dumps(context, ensure_ascii=False)
        if workflow_state:
            workflow_state.state = state
            workflow_state.intent = intent
            workflow_state.context_json = payload
        else:
            self.db.add(WorkflowState(conversation_id=conversation_id, state=state, intent=intent, context_json=payload))
        self.db.commit()
