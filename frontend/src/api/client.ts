import type { ChatResponse } from "../types";

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

export async function runAction(
  actionId: string,
  conversationId: string,
  payload?: Record<string, unknown>,
  surfaceId?: string,
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/actions/${actionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: conversationId, surface_id: surfaceId, payload: payload ?? {} }),
  });
  if (!response.ok) {
    throw new Error("Failed to run action");
  }
  return response.json();
}
