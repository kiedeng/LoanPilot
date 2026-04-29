from __future__ import annotations

from typing import Any


A2UI_BASIC_CATALOG_ID = "https://a2ui.org/specification/v0_9/basic_catalog.json"
LOANPILOT_CATALOG_ID = "https://loanpilot.local/a2ui/catalog/v1"


class A2UIResponseBuilder:
    """Build official A2UI v0.9 messages for @a2ui/react rendering."""

    def __init__(self, surface_id: str, content: str, data: dict[str, Any] | None = None) -> None:
        self.surface_id = surface_id
        self.content = content
        self.data = data or {}
        self.components: list[dict[str, Any]] = []

    def text(
        self,
        component_id: str,
        text: str,
        variant: str = "body",
        weight: float | None = None,
    ) -> "A2UIResponseBuilder":
        component: dict[str, Any] = {"id": component_id, "component": "Text", "text": text, "variant": variant}
        if weight is not None:
            component["weight"] = weight
        self.components.append(component)
        return self

    def button(
        self,
        component_id: str,
        label: str,
        action_name: str,
        context: dict[str, Any] | None = None,
        variant: str = "primary",
    ) -> "A2UIResponseBuilder":
        label_id = f"{component_id}_label"
        self.components.append({"id": label_id, "component": "Text", "text": label, "variant": "body"})
        self.components.append(
            {
                "id": component_id,
                "component": "Button",
                "child": label_id,
                "variant": variant,
                "action": {"event": {"name": action_name, "context": context or {}}},
            }
        )
        return self

    def column(
        self,
        component_id: str,
        children: list[str],
        align: str = "stretch",
        weight: float | None = None,
    ) -> "A2UIResponseBuilder":
        component: dict[str, Any] = {
            "id": component_id,
            "component": "Column",
            "children": children,
            "align": align,
            "justify": "start",
        }
        if weight is not None:
            component["weight"] = weight
        self.components.append(component)
        return self

    def row(
        self,
        component_id: str,
        children: list[str],
        justify: str = "start",
        align: str = "center",
        weight: float | None = None,
    ) -> "A2UIResponseBuilder":
        component: dict[str, Any] = {
            "id": component_id,
            "component": "Row",
            "children": children,
            "justify": justify,
            "align": align,
        }
        if weight is not None:
            component["weight"] = weight
        self.components.append(component)
        return self

    def list(self, component_id: str, children: list[str], direction: str = "vertical") -> "A2UIResponseBuilder":
        self.components.append(
            {"id": component_id, "component": "List", "children": children, "direction": direction, "align": "stretch"}
        )
        return self

    def divider(self, component_id: str, axis: str = "horizontal") -> "A2UIResponseBuilder":
        self.components.append({"id": component_id, "component": "Divider", "axis": axis})
        return self

    def card(self, child: str = "body") -> "A2UIResponseBuilder":
        self.components.append({"id": "root", "component": "Card", "child": child})
        return self

    def messages(self) -> list[dict[str, Any]]:
        return [
            {
                "version": "v0.9",
                "createSurface": {
                    "surfaceId": self.surface_id,
                    "catalogId": LOANPILOT_CATALOG_ID,
                    "theme": {
                        "primaryColor": "#0f5fb8",
                        "borderRadius": 8,
                    },
                },
            },
            {"version": "v0.9", "updateDataModel": {"surfaceId": self.surface_id, "path": "/", "value": self.data}},
            {"version": "v0.9", "updateComponents": {"surfaceId": self.surface_id, "components": self.components}},
        ]


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


def metric(builder: A2UIResponseBuilder, component_id: str, label: str, value: str) -> str:
    label_id = f"{component_id}_label"
    value_id = f"{component_id}_value"
    builder.text(label_id, label, "caption")
    builder.text(value_id, value, "h4")
    builder.column(component_id, [label_id, value_id], weight=1)
    return component_id


def detail_row(builder: A2UIResponseBuilder, component_id: str, label: str, value: str) -> str:
    label_id = f"{component_id}_label"
    value_id = f"{component_id}_value"
    builder.text(label_id, label, "caption", weight=1)
    builder.text(value_id, value, "body", weight=2)
    builder.row(component_id, [label_id, value_id], "spaceBetween", "start")
    return component_id


def action(label: str, name: str, context: dict[str, Any] | None = None, variant: str = "default") -> dict[str, Any]:
    return {"label": label, "name": name, "context": context or {}, "variant": variant}


def loan_card(
    builder: A2UIResponseBuilder,
    *,
    eyebrow: str,
    title: str,
    description: str | None = None,
    primary_label: str | None = None,
    primary_value: str | None = None,
    metrics: list[dict[str, str]] | None = None,
    rows: list[dict[str, str]] | None = None,
    notice: str | None = None,
    actions: list[dict[str, Any]] | None = None,
) -> A2UIResponseBuilder:
    component: dict[str, Any] = {
        "id": "root",
        "component": "LoanInsightCard",
        "eyebrow": eyebrow,
        "title": title,
    }
    if description:
        component["description"] = description
    if primary_label:
        component["primaryLabel"] = primary_label
    if primary_value:
        component["primaryValue"] = primary_value
    if metrics:
        component["metrics"] = metrics
    if rows:
        component["rows"] = rows
    if notice:
        component["notice"] = notice
    if actions:
        component["actions"] = actions
    builder.components.append(component)
    return builder


def info_item(value: str, label: str | None = None) -> dict[str, str]:
    item = {"value": value}
    if label:
        item["label"] = label
    return item


def info_card(
    builder: A2UIResponseBuilder,
    *,
    eyebrow: str,
    title: str,
    items: list[dict[str, str]],
    summary: str | None = None,
    variant: str = "brief",
    notice: str | None = None,
) -> A2UIResponseBuilder:
    component: dict[str, Any] = {
        "id": "root",
        "component": "LoanInfoCard",
        "eyebrow": eyebrow,
        "title": title,
        "items": items,
        "variant": variant,
    }
    if summary:
        component["summary"] = summary
    if notice:
        component["notice"] = notice
    builder.components.append(component)
    return builder


def product_surface(surface_id: str, product: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    content = f"为你推荐 {product['productName']}，最高可申请 {fmt_money(product['maxAmount'])}。"
    builder = A2UIResponseBuilder(surface_id, content, {"product": product})
    context = {"productId": product["productId"], "segment": product["segment"], "amount": product["maxAmount"]}
    loan_card(
        builder,
        eyebrow="推荐产品",
        title=product["productName"],
        description=product["description"],
        primary_label="最高额度",
        primary_value=fmt_money(product["maxAmount"]),
        metrics=[
            {"label": "参考年化利率", "value": product["rateRange"]},
            {"label": "期限", "value": product["termRange"]},
            {"label": "预计放款", "value": product["estimatedDisbursement"]},
        ],
        notice="额度和利率仅为演示预估，最终以银行审批结果为准。",
        actions=[
            action("测一测额度", "pre_assess", context, "primary"),
            action("立即申请", "apply_now", {**context, "requiresConfirm": True}),
        ],
    )
    return content, builder.messages()


def assessment_surface(surface_id: str, assessment: dict[str, Any], context: dict[str, Any] | None = None) -> tuple[str, list[dict[str, Any]]]:
    content = f"根据演示规则，预估额度为 {fmt_money(assessment['estimatedAmount'])}。"
    builder = A2UIResponseBuilder(surface_id, content, {"assessment": assessment})
    loan_card(
        builder,
        eyebrow="资质预评估",
        title="额度预估结果",
        primary_label="预估可贷额度",
        primary_value=fmt_money(assessment["estimatedAmount"]),
        rows=[
            {"label": "参考年化利率", "value": assessment["rateRange"]},
            {"label": "可选期限", "value": assessment["termRange"]},
            {"label": "预计放款", "value": assessment["estimatedDisbursement"]},
        ],
        notice=assessment["disclaimer"],
        actions=[
            action("创建演示申请", "apply_now", context or {}, "primary"),
            action("对比方案", "compare_options", {}),
        ],
    )
    return content, builder.messages()


def simple_info_surface(surface_id: str, title: str, lines: list[str], content: str | None = None) -> tuple[str, list[dict[str, Any]]]:
    builder = A2UIResponseBuilder(surface_id, content or title, {"lines": lines})
    variant = "handoff" if "人工" in title else "timeline" if "进度" in title or "状态" in title else "brief"
    info_card(
        builder,
        eyebrow="LoanPilot",
        title=title,
        summary=content,
        variant=variant,
        items=[info_item(line) for line in lines],
    )
    return content or title, builder.messages()


def comparison_surface(surface_id: str, options: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    builder = A2UIResponseBuilder(surface_id, "我把常见方案放在一起，便于你对比。", {"options": options})
    builder.components.append(
        {
            "id": "root",
            "component": "LoanComparisonCard",
            "eyebrow": "方案比较",
            "title": "贷款方案对比",
            "options": [
                {
                    "name": option["name"],
                    "amount": fmt_money(option["estimatedAmount"]),
                    "rate": option["rateRange"],
                    "term": option["termRange"],
                    "speed": option["estimatedDisbursement"],
                }
                for option in options
            ],
        }
    )
    return "我把常见方案放在一起，便于你对比。", builder.messages()


def application_surface(surface_id: str, status: dict[str, Any], checklist: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    builder = A2UIResponseBuilder(surface_id, "申请单已创建，请先按清单准备演示材料。", {"status": status, "checklist": checklist})
    builder.components.append(
        {
            "id": "root",
            "component": "LoanApplicationCard",
            "eyebrow": "业务办理",
            "title": f"申请单 {status['applicationId']}",
            "statusLabel": "当前状态",
            "status": status["status"],
            "documents": [
                {"name": doc["name"], "status": doc["status"]}
                for doc in checklist["documents"]
            ],
            "notice": "演示上传不会保存真实证件；真实接入时需走银行影像与授权系统。",
            "action": action("模拟上传材料", "upload_document", {"applicationId": status["applicationId"]}, "primary"),
        }
    )
    return "申请单已创建，请先按清单准备演示材料。", builder.messages()


def bill_surface(surface_id: str, bill: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    builder = A2UIResponseBuilder(surface_id, "这是你的本月账单摘要。", {"bill": bill})
    context = {"loanId": bill["loanId"]}
    loan_card(
        builder,
        eyebrow="服务管理",
        title=bill.get("productName", "贷款账单"),
        primary_label="本期应还",
        primary_value=fmt_money(bill["dueAmount"]),
        rows=[
            {"label": "还款日", "value": bill["dueDate"]},
            {"label": "剩余本金", "value": fmt_money(bill["outstandingBalance"])},
        ],
        actions=[
            action("查看还款计划", "view_repayment_plan", context, "primary"),
            action("提前还款试算", "prepay", context),
        ],
    )
    return "这是你的本月账单摘要。", builder.messages()


def repayment_surface(surface_id: str, plan: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    builder = A2UIResponseBuilder(surface_id, "这是当前贷款的近期还款计划。", {"plan": plan})
    info_card(
        builder,
        eyebrow="还款计划",
        title=f"贷款 {plan['loanId']}",
        summary="这是当前贷款的近期还款计划。",
        variant="schedule",
        items=[
            info_item(
                f"{item['dueDate']} 应还 {fmt_money(item['amount'])}，本金 {fmt_money(item['principal'])}，利息 {fmt_money(item['interest'])}",
                f"第 {item['period']} 期",
            )
            for item in plan["items"]
        ],
    )
    return "这是当前贷款的近期还款计划。", builder.messages()


def prepayment_surface(surface_id: str, quote: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    builder = A2UIResponseBuilder(surface_id, "提前还款试算如下，演示环境不会发起真实扣款。", {"quote": quote})
    loan_card(
        builder,
        eyebrow="提前还款",
        title=f"贷款 {quote['loanId']}",
        primary_label="试算结清金额",
        primary_value=fmt_money(quote["payoffAmount"]),
        rows=[
            {"label": "其中手续费", "value": fmt_money(quote["fee"])},
            {"label": "报价有效期至", "value": quote["validUntil"]},
        ],
        notice="此为演示试算，不会触发真实扣款；真实金额以银行核心系统为准。",
        actions=[action("确认演示动作", "confirm_prepayment", {"loanId": quote["loanId"], "requiresConfirm": True}, "primary")],
    )
    return "提前还款试算如下，演示环境不会发起真实扣款。", builder.messages()
