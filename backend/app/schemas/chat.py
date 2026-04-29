from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    user_id: int = 1
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    state: str
    intent: str
    surface_id: str
    content: str
    a2ui_messages: list[dict[str, Any]] = Field(default_factory=list)


class ActionRequest(BaseModel):
    conversation_id: str
    user_id: int = 1
    surface_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
