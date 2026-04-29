export type A2UIMessage = Record<string, unknown>;

export type ChatResponse = {
  conversation_id: string;
  state: string;
  intent: string;
  surface_id: string;
  content: string;
  a2ui_messages: A2UIMessage[];
};
