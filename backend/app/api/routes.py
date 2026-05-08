from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.adapters.mock_bank import MockBankingAdapter
from app.db.session import get_db
from app.schemas.chat import ActionRequest, ChatRequest, ChatResponse, ChatStreamRequest
from app.services.ai_gateway import AiGateway

router = APIRouter()


@router.post("/chat/message", response_model=ChatResponse)
def chat_message(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    stream_request = ChatStreamRequest(
        conversation_id=request.conversation_id,
        user_id=request.user_id,
        message=request.message,
        client_context={},
    )
    return AiGateway(db).chat_message(stream_request)


@router.post("/chat/stream")
def chat_stream(request: ChatStreamRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    def event_stream() -> Iterator[str]:
        try:
            for event_name, payload in AiGateway(db).stream_chat(request):
                yield f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'message': str(exc)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/actions/{action_id}", response_model=ChatResponse)
def run_action(action_id: str, request: ActionRequest, db: Session = Depends(get_db)) -> ChatResponse:
    return AiGateway(db).handle_action(request.user_id, request.conversation_id, action_id, request.payload)


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str, db: Session = Depends(get_db)) -> dict:
    from app.models.domain import Message, WorkflowState

    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.id).all()
    state = db.get(WorkflowState, conversation_id)
    return {
        "conversation_id": conversation_id,
        "state": state.state if state else "idle",
        "messages": [{"role": message.role, "content": message.content, "payload": message.payload_json} for message in messages],
    }


@router.get("/loan/products")
def loan_products(segment: str | None = None, db: Session = Depends(get_db)) -> list[dict]:
    return MockBankingAdapter(db).query_loan_products(segment)


@router.post("/loan/pre-assess")
def pre_assess(payload: dict, db: Session = Depends(get_db)) -> dict:
    return MockBankingAdapter(db).pre_assess_credit_limit(payload)


@router.post("/loan/applications")
def create_application(payload: dict, db: Session = Depends(get_db)) -> dict:
    return MockBankingAdapter(db).create_loan_application(
        user_id=int(payload.get("user_id", 1)),
        product_id=payload.get("product_id", "consumer_loan"),
        amount=float(payload.get("amount", 200000)),
        purpose=payload.get("purpose", "消费周转"),
    )


@router.get("/loan/applications/{application_id}")
def application_status(application_id: str, db: Session = Depends(get_db)) -> dict:
    return MockBankingAdapter(db).query_application_status(application_id)


@router.post("/loan/documents/upload")
def upload_document(application_id: str, document_type: str, file: UploadFile, db: Session = Depends(get_db)) -> dict:
    return MockBankingAdapter(db).upload_document(application_id, document_type, file.filename or "demo-file")


@router.get("/loan/repayment-plan/{loan_id}")
def repayment_plan(loan_id: str, db: Session = Depends(get_db)) -> dict:
    return MockBankingAdapter(db).query_repayment_plan(loan_id)


@router.get("/loan/bill-summary/{loan_id}")
def bill_summary(loan_id: str, db: Session = Depends(get_db)) -> dict:
    return MockBankingAdapter(db).query_bill_summary(loan_id)


@router.post("/ai/tools/bill-summary")
def ai_tool_bill_summary(payload: dict, db: Session = Depends(get_db)) -> dict:
    return MockBankingAdapter(db).query_bill_summary(payload.get("loan_id", "LN-DEMO-001"))


@router.post("/ai/tools/application-status")
def ai_tool_application_status(payload: dict, db: Session = Depends(get_db)) -> dict:
    return MockBankingAdapter(db).query_application_status(payload.get("application_id", "LP-DEMO-001"))


@router.post("/ai/tools/products")
def ai_tool_products(payload: dict, db: Session = Depends(get_db)) -> list[dict]:
    return MockBankingAdapter(db).recommend_products(payload.get("query", ""), payload.get("segment", "personal"))


@router.post("/loan/prepayment/quote")
def prepayment_quote(payload: dict, db: Session = Depends(get_db)) -> dict:
    return MockBankingAdapter(db).quote_prepayment(payload.get("loan_id", "LN-DEMO-001"))


@router.post("/handoff/request")
def handoff(payload: dict, db: Session = Depends(get_db)) -> dict:
    return MockBankingAdapter(db).request_human_handoff(payload.get("summary", "用户请求人工服务"))
