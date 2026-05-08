from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    user_id: int = 1
    message: str


class ChatStreamRequest(ChatRequest):
    client_context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    conversation_id: str
    state: str
    intent: str
    content: str
    messages: list[dict[str, Any]] = Field(default_factory=list)


class ActionRequest(BaseModel):
    conversation_id: str
    user_id: int = 1
    payload: dict[str, Any] = Field(default_factory=dict)


class StreamEvent(BaseModel):
    event: str
    data: dict[str, Any] = Field(default_factory=dict)


class DifyMockRequest(BaseModel):
    conversation_id: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    query: str
    response_mode: str = "streaming"
    user: str


class DifyMockResult(BaseModel):
    conversation_id: str
    intent: str
    state: str
    answer: str
    slots: dict[str, Any] = Field(default_factory=dict)
    card: dict[str, Any] | None = None
    memory_updates: list[dict[str, Any]] = Field(default_factory=list)
