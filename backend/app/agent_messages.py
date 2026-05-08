from __future__ import annotations

from typing import Any


def fmt_money(value: float | int | str | None) -> str:
    if value is None:
        return "-"
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return str(value)
    if amount >= 10000:
        return f"{amount / 10000:.0f} 万元"
    return f"{amount:.2f} 元"


def action(label: str, name: str, context: dict[str, Any] | None = None, variant: str = "default") -> dict[str, Any]:
    return {"label": label, "name": name, "context": context or {}, "variant": variant}


def text_message(content: str, *, intent: str, state: str, slots: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "mime_type": "text/markdown",
        "status": "complete",
        "content": content,
        "meta_data": {
            "intent_data": {"intent": intent, "state": state},
            "slots": slots or {},
            "multi_load": [],
        },
    }


def card_message(
    *,
    content: str,
    intent: str,
    state: str,
    slots: dict[str, Any] | None,
    cards: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "mime_type": "multi_load/iframe",
        "status": "complete",
        "action": "",
        "content": content,
        "meta_data": {
            "intent_data": {"intent": intent, "state": state},
            "slots": slots or {},
            "multi_load": cards,
        },
    }


def product_action_context(product: dict[str, Any]) -> dict[str, Any]:
    return {"productId": product["productId"], "segment": product["segment"], "amount": product["maxAmount"]}


def loan_recommendation_message(products: list[dict[str, Any]], *, intent: str, state: str, slots: dict[str, Any]) -> dict[str, Any]:
    source_seq = "loan_recommend_1"
    items = []
    for product in products:
        context = product_action_context(product)
        items.append(
            {
                "productId": product["productId"],
                "productName": product["productName"],
                "segment": product["segment"],
                "maxAmount": product["maxAmount"],
                "maxAmountText": fmt_money(product["maxAmount"]),
                "rateRange": product["rateRange"],
                "termRange": product["termRange"],
                "estimatedDisbursement": product["estimatedDisbursement"],
                "description": product["description"],
                "actions": [
                    action("测一测额度", "pre_assess", context, "primary"),
                    action("立即申请", "apply_now", {**context, "requiresConfirm": True}),
                ],
            }
        )
    return card_message(
        content=(
            "我先根据你的用途和客群，给你匹配一个合适的贷款产品。\n\n"
            f"[({source_seq})]\n\n"
            "你可以先看额度、利率和放款速度。如果你更看重低利率或快放款，我可以继续帮你筛。"
        ),
        intent=intent,
        state=state,
        slots=slots,
        cards=[{
            "type": "loan_recommend",
            "source_seq": source_seq,
            "content": {
                "cardType": "RECOMMEND",
                "resultData": {
                    "loanRecommendationItems": items,
                    "recommendType": "LOAN_PRODUCT",
                    "notice": "额度、利率和放款时间仅为演示预估，最终以银行审批结果为准。",
                },
            },
        }],
    )


def assessment_message(assessment: dict[str, Any], context: dict[str, Any], *, intent: str, state: str) -> dict[str, Any]:
    source_seq = "assessment_result_1"
    return card_message(
        content=f"根据演示规则，预估额度为 {fmt_money(assessment['estimatedAmount'])}。\n\n[({source_seq})]",
        intent=intent,
        state=state,
        slots=context,
        cards=[{
            "type": "assessment_result",
            "source_seq": source_seq,
            "content": {
                "cardType": "ASSESSMENT",
                "resultData": {
                    "estimatedAmount": assessment["estimatedAmount"],
                    "estimatedAmountText": fmt_money(assessment["estimatedAmount"]),
                    "rateRange": assessment["rateRange"],
                    "termRange": assessment["termRange"],
                    "estimatedDisbursement": assessment["estimatedDisbursement"],
                    "notice": assessment["disclaimer"],
                    "actions": [
                        action("创建演示申请", "apply_now", context, "primary"),
                        action("对比方案", "compare_options", {}),
                    ],
                },
            },
        }],
    )


def bill_summary_message(bill: dict[str, Any], *, intent: str, state: str) -> dict[str, Any]:
    loan_id = bill["loanId"]
    source_seq = "bill_summary_1"
    return card_message(
        content=f"我帮你查到了本月账单摘要。\n\n[({source_seq})]\n\n你可以继续查看还款计划，或做提前还款试算。",
        intent=intent,
        state=state,
        slots={"loan_id": loan_id},
        cards=[{
            "type": "bill_summary",
            "source_seq": source_seq,
            "content": {
                "cardType": "BILL",
                "resultData": {
                    "loanId": loan_id,
                    "productName": bill.get("productName", "贷款账单"),
                    "dueAmount": bill["dueAmount"],
                    "dueAmountText": fmt_money(bill["dueAmount"]),
                    "dueDate": bill["dueDate"],
                    "outstandingBalance": bill["outstandingBalance"],
                    "outstandingBalanceText": fmt_money(bill["outstandingBalance"]),
                    "actions": [
                        action("查看还款计划", "view_repayment_plan", {"loanId": loan_id}, "primary"),
                        action("提前还款试算", "prepay", {"loanId": loan_id}),
                    ],
                },
            },
        }],
    )


def application_message(status: dict[str, Any], checklist: dict[str, Any], *, intent: str, state: str) -> dict[str, Any]:
    application_id = status["applicationId"]
    source_seq = "application_status_1"
    return card_message(
        content=f"申请单已创建，请先按清单准备演示材料。\n\n[({source_seq})]",
        intent=intent,
        state=state,
        slots={"application_id": application_id},
        cards=[{
            "type": "application_status",
            "source_seq": source_seq,
            "content": {
                "cardType": "APPLICATION",
                "resultData": {
                    "applicationId": application_id,
                    "status": status["status"],
                    "steps": status.get("steps", []),
                    "documents": checklist["documents"],
                    "notice": "演示上传不会保存真实证件；真实接入时需走银行影像与授权系统。",
                    "actions": [action("模拟上传材料", "upload_document", {"applicationId": application_id}, "primary")],
                },
            },
        }],
    )


def application_status_message(status: dict[str, Any], *, intent: str, state: str) -> dict[str, Any]:
    application_id = status["applicationId"]
    source_seq = "application_status_1"
    return card_message(
        content=f"这是当前演示申请的进度。\n\n[({source_seq})]",
        intent=intent,
        state=state,
        slots={"application_id": application_id},
        cards=[{
            "type": "application_status",
            "source_seq": source_seq,
            "content": {
                "cardType": "APPLICATION_STATUS",
                "resultData": {"applicationId": application_id, "status": status["status"], "steps": status["steps"]},
            },
        }],
    )


def repayment_plan_message(plan: dict[str, Any], *, intent: str, state: str) -> dict[str, Any]:
    source_seq = "repayment_plan_1"
    return card_message(
        content=f"这是当前贷款的近期还款计划。\n\n[({source_seq})]",
        intent=intent,
        state=state,
        slots={"loan_id": plan["loanId"]},
        cards=[{
            "type": "repayment_plan",
            "source_seq": source_seq,
            "content": {
                "cardType": "REPAYMENT_PLAN",
                "resultData": {
                    "loanId": plan["loanId"],
                    "items": [
                        {
                            **item,
                            "amountText": fmt_money(item["amount"]),
                            "principalText": fmt_money(item["principal"]),
                            "interestText": fmt_money(item["interest"]),
                        }
                        for item in plan["items"]
                    ],
                },
            },
        }],
    )


def prepayment_quote_message(quote: dict[str, Any], *, intent: str, state: str) -> dict[str, Any]:
    source_seq = "prepayment_quote_1"
    return card_message(
        content=f"提前还款试算如下，演示环境不会发起真实扣款。\n\n[({source_seq})]",
        intent=intent,
        state=state,
        slots={"loan_id": quote["loanId"]},
        cards=[{
            "type": "prepayment_quote",
            "source_seq": source_seq,
            "content": {
                "cardType": "PREPAYMENT",
                "resultData": {
                    "loanId": quote["loanId"],
                    "payoffAmount": quote["payoffAmount"],
                    "payoffAmountText": fmt_money(quote["payoffAmount"]),
                    "fee": quote["fee"],
                    "feeText": fmt_money(quote["fee"]),
                    "validUntil": quote["validUntil"],
                    "notice": "此为演示试算，不会触发真实扣款；真实金额以银行核心系统为准。",
                    "actions": [action("确认演示动作", "confirm_prepayment", {"loanId": quote["loanId"], "requiresConfirm": True}, "primary")],
                },
            },
        }],
    )


def comparison_message(options: list[dict[str, Any]], *, intent: str, state: str) -> dict[str, Any]:
    source_seq = "loan_comparison_1"
    return card_message(
        content=f"我把常见方案放在一起，便于你对比。\n\n[({source_seq})]",
        intent=intent,
        state=state,
        slots={},
        cards=[{
            "type": "loan_comparison",
            "source_seq": source_seq,
            "content": {
                "cardType": "COMPARISON",
                "resultData": {
                    "options": [
                        {
                            "name": option["name"],
                            "amount": option["estimatedAmount"],
                            "amountText": fmt_money(option["estimatedAmount"]),
                            "rate": option["rateRange"],
                            "term": option["termRange"],
                            "speed": option["estimatedDisbursement"],
                        }
                        for option in options
                    ]
                },
            },
        }],
    )


def info_message(title: str, lines: list[str], content: str | None = None, *, intent: str, state: str) -> dict[str, Any]:
    source_seq = "info_1"
    return card_message(
        content=f"{content or title}\n\n[({source_seq})]",
        intent=intent,
        state=state,
        slots={},
        cards=[{
            "type": "info",
            "source_seq": source_seq,
            "content": {
                "cardType": "INFO",
                "resultData": {"title": title, "items": [{"value": line} for line in lines]},
            },
        }],
    )
