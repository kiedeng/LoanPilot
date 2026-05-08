export type AgentAction = {
  label: string;
  name: string;
  variant?: "primary" | "default";
  context?: Record<string, unknown>;
};

export type AgentCard = {
  type: string;
  source_seq: string;
  content: {
    cardType?: string;
    resultData?: Record<string, unknown>;
  };
};

export type AgentMessage = {
  mime_type: string;
  status?: "processing" | "complete" | string;
  action?: string;
  content: string;
  meta_data: {
    intent_data?: Record<string, unknown>;
    slots?: Record<string, unknown>;
    multi_load?: AgentCard[];
    [key: string]: unknown;
  };
};

export type ChatResponse = {
  conversation_id: string;
  state: string;
  intent: string;
  content: string;
  messages: AgentMessage[];
};

export type ChatStreamEvent =
  | { event: "conversation"; data: { conversation_id: string } }
  | { event: "token"; data: { content: string } }
  | { event: "message"; data: { message: AgentMessage } }
  | { event: "done"; data: { state: string; intent: string } }
  | { event: "error"; data: { message: string } };
