import type { ChatResponse, ChatStreamEvent } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000/api";

export async function sendMessage(message: string, conversationId?: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, conversation_id: conversationId }),
  });
  if (!response.ok) {
    throw new Error("Failed to send message");
  }
  return response.json();
}

export async function sendMessageStream(
  message: string,
  conversationId: string | undefined,
  onEvent: (event: ChatStreamEvent) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      client_context: { page: "chat", selected_loan_id: null, selected_application_id: null },
    }),
  });
  if (!response.ok || !response.body) {
    throw new Error("Failed to stream message");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const parsed = parseSseChunk(chunk);
      if (parsed) onEvent(parsed);
    }
  }

  if (buffer.trim()) {
    const parsed = parseSseChunk(buffer);
    if (parsed) onEvent(parsed);
  }
}

function parseSseChunk(chunk: string): ChatStreamEvent | undefined {
  const eventLine = chunk.split("\n").find((line) => line.startsWith("event:"));
  const dataLine = chunk.split("\n").find((line) => line.startsWith("data:"));
  if (!eventLine || !dataLine) return undefined;
  const event = eventLine.replace("event:", "").trim();
  const data = JSON.parse(dataLine.replace("data:", "").trim());
  return { event, data } as ChatStreamEvent;
}

export async function runAction(
  actionId: string,
  conversationId: string,
  payload?: Record<string, unknown>,
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/actions/${actionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: conversationId, payload: payload ?? {} }),
  });
  if (!response.ok) {
    throw new Error("Failed to run action");
  }
  return response.json();
}
