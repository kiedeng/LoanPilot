import { Send, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { runAction, sendMessageStream } from "../api/client";
import type { AgentAction, AgentMessage, ChatResponse } from "../types";
import { MessageRenderer } from "./MessageRenderer";

type ChatItem = {
  id?: string;
  role: "user" | "assistant";
  content?: string;
  messages?: AgentMessage[];
};

const starterPrompts = [
  "我想贷20万装修，多久能放款？",
  "我是开餐饮店的，想贷50万周转",
  "我这个月贷款要还多少？",
  "我有理财产品，临时需要30万周转",
];

const welcomeMessage: AgentMessage = {
  mime_type: "text/markdown",
  status: "complete",
  content: "我是 LoanPilot 贷航员，可以帮你咨询贷款、测算额度、提交演示申请、查询进度和处理还款服务。",
  meta_data: { multi_load: [] },
};

export function ChatPanel() {
  const [conversationId, setConversationId] = useState<string>();
  const conversationIdRef = useRef<string | undefined>(undefined);
  const [input, setInput] = useState("");
  const [items, setItems] = useState<ChatItem[]>([{ role: "assistant", messages: [welcomeMessage] }]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    conversationIdRef.current = conversationId;
  }, [conversationId]);

  function appendResponse(response: ChatResponse) {
    setConversationId(response.conversation_id);
    conversationIdRef.current = response.conversation_id;
    setItems((current) => [...current, { role: "assistant", messages: response.messages }]);
  }

  async function handleAction(action: AgentAction) {
    const currentConversationId = conversationIdRef.current;
    if (!currentConversationId) return;
    if (action.context?.requiresConfirm && !window.confirm("确认执行该演示动作？")) return;
    setLoading(true);
    try {
      const response = await runAction(action.name, currentConversationId, action.context);
      appendResponse(response);
    } finally {
      setLoading(false);
    }
  }

  async function submit(text = input) {
    const value = text.trim();
    if (!value) return;
    setInput("");
    const assistantId = `assistant-${Date.now()}`;
    setItems((current) => [...current, { role: "user", content: value }, { id: assistantId, role: "assistant", content: "" }]);
    setLoading(true);
    try {
      await sendMessageStream(value, conversationId, (event) => {
        if (event.event === "conversation") {
          setConversationId(event.data.conversation_id);
          conversationIdRef.current = event.data.conversation_id;
          return;
        }
        if (event.event === "token") {
          setItems((current) =>
            current.map((item) => (item.id === assistantId ? { ...item, content: `${item.content ?? ""}${event.data.content}` } : item)),
          );
          return;
        }
        if (event.event === "message") {
          setItems((current) =>
            current.map((item) => (item.id === assistantId ? { ...item, content: undefined, messages: [event.data.message] } : item)),
          );
          return;
        }
        if (event.event === "error") {
          setItems((current) =>
            current.map((item) => (item.id === assistantId ? { ...item, content: event.data.message || "处理失败，请稍后再试。" } : item)),
          );
        }
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="chat-shell">
      <section className="sidebar">
        <div className="brand">
          <Sparkles size={22} />
          <div>
            <h1>LoanPilot</h1>
            <span>对话式银行贷款智能体</span>
          </div>
        </div>
        <div className="scenario-list">
          {starterPrompts.map((prompt) => (
            <button key={prompt} type="button" onClick={() => submit(prompt)}>
              {prompt}
            </button>
          ))}
        </div>
      </section>

      <section className="conversation">
        <div className="messages">
          {items.map((item, index) => (
            <div className={`message ${item.role}`} key={`${item.role}-${index}-${item.id ?? ""}`}>
              {item.messages?.map((message, messageIndex) => (
                <MessageRenderer key={`${message.mime_type}-${messageIndex}`} message={message} onAction={handleAction} />
              ))}
              {item.content !== undefined &&
                (item.role === "assistant" ? (
                  <div className="agent-message">
                    <p className="message-bubble">{item.content}</p>
                  </div>
                ) : (
                  <p className="message-bubble">{item.content}</p>
                ))}
            </div>
          ))}
          {loading && (
            <div className="message assistant">
              <p className="message-bubble">正在处理...</p>
            </div>
          )}
        </div>
        <form
          className="composer"
          onSubmit={(event) => {
            event.preventDefault();
            submit();
          }}
        >
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="输入贷款问题、额度测算或还款查询..." />
          <button type="submit" disabled={loading} aria-label="发送">
            <Send size={18} />
          </button>
        </form>
      </section>
    </main>
  );
}
