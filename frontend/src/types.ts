export type A2UIMessage = Record<string, unknown>;

export type ChatResponse = {
  conversation_id: string;
  state: string;
  intent: string;
  surface_id: string;
  content: string;
  a2ui_messages: A2UIMessage[];
};

export type ChatStreamEvent =
  | { event: "conversation"; data: { conversation_id: string } }
  | { event: "token"; data: { content: string } }
  | { event: "card"; data: { surface_id: string; a2ui_messages: A2UIMessage[] } }
  | { event: "done"; data: { state: string; intent: string; surface_id?: string } }
  | { event: "error"; data: { message: string } };
