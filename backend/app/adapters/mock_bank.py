from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.adapters.base import BankingAdapter
from app.models.domain import LoanAccount, LoanApplication, LoanProduct, RepaymentPlan


class MockBankingAdapter(BankingAdapter):
    def __init__(self, db: Session) -> None:
        self.db = db

    def query_loan_products(self, segment: str | None = None) -> list[dict[str, Any]]:
        query = self.db.query(LoanProduct)
        if segment:
            query = query.filter(LoanProduct.segment.in_([segment, "all"]))
        return [self._product_to_dict(product) for product in query.all()]

    def recommend_products(self, message: str, segment: str = "personal") -> list[dict[str, Any]]:
        if any(word in message for word in ["经营", "周转", "流水", "小微", "企业", "餐饮"]):
            segment = "business"
        if any(word in message for word in ["理财", "资产", "流动性", "质押"]):
            segment = "wealth"
        products = self.query_loan_products(segment)
        return products[:2] if products else self.query_loan_products()[:2]

    def explain_rate(self, product_id: str | None = None) -> dict[str, Any]:
        product = self.db.get(LoanProduct, product_id) if product_id else None
        return {
            "rateRange": product.rate_range if product else "3.6%-8.5%",
            "factors": ["客户资质", "贷款用途", "期限", "负债水平", "银行审批结果"],
            "disclaimer": "利率区间仅用于演示，最终利率以银行审批结果为准。",
        }

    def answer_policy_question(self, question: str) -> dict[str, Any]:
        return {
            "question": question,
            "answer": "演示版政策答疑来自 Mock 知识库。实际接入时可由 Dify 知识库或银行政策库返回。",
        }

    def compare_loan_options(self) -> dict[str, Any]:
        return {
            "options": [
                {
                    "name": "个人消费贷",
                    "estimatedAmount": 200000,
                    "rateRange": "3.8%-7.2%",
                    "termRange": "12-60个月",
                    "estimatedDisbursement": "最快1个工作日",
                },
                {
                    "name": "小微经营贷",
                    "estimatedAmount": 500000,
                    "rateRange": "4.0%-8.5%",
                    "termRange": "6-36个月",
                    "estimatedDisbursement": "2-3个工作日",
                },
            ]
        }

    def pre_assess_credit_limit(self, profile: dict[str, Any]) -> dict[str, Any]:
        segment = profile.get("segment", "personal")
        requested = float(profile.get("requested_amount") or 200000)
        monthly_income = float(profile.get("monthly_income") or 18000)
        monthly_revenue = float(profile.get("monthly_revenue") or 120000)
        liabilities = float(profile.get("liabilities") or 3000)

        base = monthly_revenue * 4 if segment == "business" else monthly_income * 10
        amount = max(50000, min(requested, base - liabilities * 8))
        if segment == "wealth":
            amount = max(amount, 300000)
        return {
            "estimatedAmount": round(amount, 2),
            "rateRange": "3.8%-7.8%" if segment != "business" else "4.0%-8.5%",
            "termRange": "12-60个月" if segment != "business" else "6-36个月",
            "estimatedDisbursement": "最快1个工作日",
            "riskLevel": "medium",
            "disclaimer": "该额度仅为预估，最终额度和利率以银行审批结果为准。",
        }

    def quote_interest_rate(self, segment: str = "personal") -> dict[str, Any]:
        return {"rateRange": "4.0%-8.5%" if segment == "business" else "3.8%-7.8%"}

    def create_loan_application(self, user_id: int, product_id: str, amount: float, purpose: str) -> dict[str, Any]:
        application_id = f"LP{datetime.utcnow().strftime('%Y%m%d')}{uuid4().hex[:6].upper()}"
        application = LoanApplication(
            id=application_id,
            user_id=user_id,
            product_id=product_id,
            amount=amount,
            purpose=purpose,
            status="under_review",
        )
        self.db.add(application)
        self.db.commit()
        return {"applicationId": application_id, "status": "under_review", "amount": amount, "purpose": purpose}

    def get_document_checklist(self, segment: str = "personal", application_id: str = "demo") -> dict[str, Any]:
        docs = ["身份证", "收入证明", "贷款用途说明"]
        if segment == "business":
            docs = ["法人身份证", "营业执照", "近6个月经营流水", "纳税证明"]
        return {
            "applicationId": application_id,
            "documents": [{"name": doc, "required": True, "status": "pending"} for doc in docs],
        }

    def upload_document(self, application_id: str, document_type: str, file_name: str) -> dict[str, Any]:
        return {"applicationId": application_id, "documents": [{"name": document_type, "fileName": file_name, "status": "recognized"}]}

    def mock_ocr_document(self, document_type: str) -> dict[str, Any]:
        return {"documentType": document_type, "status": "recognized", "confidence": 0.96}

    def query_application_status(self, application_id: str) -> dict[str, Any]:
        application = self.db.get(LoanApplication, application_id)
        status = application.status if application else "under_review"
        return {
            "applicationId": application_id,
            "status": status,
            "steps": [
                {"name": "申请提交", "status": "done"},
                {"name": "材料校验", "status": "done"},
                {"name": "审批中", "status": "current" if status == "under_review" else "done"},
                {"name": "签约", "status": "pending"},
                {"name": "放款", "status": "pending"},
            ],
        }

    def get_contract_guidance(self, application_id: str) -> dict[str, Any]:
        return {"applicationId": application_id, "steps": ["核对合同信息", "确认利率和期限", "完成电子签约"]}

    def mock_disbursement_notice(self, application_id: str, amount: float = 200000) -> dict[str, Any]:
        return {"applicationId": application_id, "amount": amount, "expectedTime": "预计1个工作日内到账"}

    def query_repayment_plan(self, loan_id: str) -> dict[str, Any]:
        items = (
            self.db.query(RepaymentPlan)
            .filter(RepaymentPlan.loan_account_id == loan_id)
            .order_by(RepaymentPlan.period)
            .limit(6)
            .all()
        )
        return {
            "loanId": loan_id,
            "items": [
                {
                    "period": item.period,
                    "dueDate": item.due_date,
                    "amount": item.amount,
                    "principal": item.principal,
                    "interest": item.interest,
                    "status": item.status,
                }
                for item in items
            ],
        }

    def query_bill_summary(self, loan_id: str = "LN-DEMO-001") -> dict[str, Any]:
        account = self.db.get(LoanAccount, loan_id)
        if not account:
            return {"loanId": loan_id, "dueAmount": 0, "dueDate": "", "outstandingBalance": 0}
        return {
            "loanId": account.id,
            "dueAmount": account.next_due_amount,
            "dueDate": account.next_due_date,
            "outstandingBalance": account.outstanding_balance,
            "productName": account.product_name,
        }

    def quote_prepayment(self, loan_id: str = "LN-DEMO-001") -> dict[str, Any]:
        account = self.db.get(LoanAccount, loan_id)
        balance = account.outstanding_balance if account else 120000
        return {
            "loanId": loan_id,
            "payoffAmount": round(balance + 280, 2),
            "fee": 280,
            "validUntil": (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d"),
        }

    def check_renewal_eligibility(self, loan_id: str = "LN-DEMO-001") -> dict[str, Any]:
        return {"eligible": True, "reason": "还款记录良好，演示规则判断可发起续贷测算。"}

    def request_human_handoff(self, summary: str) -> dict[str, Any]:
        return {"ticketId": f"HD-{uuid4().hex[:8].upper()}", "summary": summary}

    @staticmethod
    def _product_to_dict(product: LoanProduct) -> dict[str, Any]:
        return {
            "productId": product.id,
            "productName": product.name,
            "segment": product.segment,
            "maxAmount": product.max_amount,
            "rateRange": product.rate_range,
            "termRange": product.term_range,
            "estimatedDisbursement": product.disbursement,
            "description": product.description,
        }
