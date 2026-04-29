import { A2uiSurface, type ReactComponentImplementation } from "@a2ui/react/v0_9";
import { MessageProcessor, type A2uiClientAction, type SurfaceModel } from "@a2ui/web_core/v0_9";
import { Send, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { loanPilotCatalog } from "../a2ui/loanPilotCatalog";
import { runAction, sendMessage } from "../api/client";
import type { ChatResponse } from "../types";

type ChatItem = {
  role: "user" | "assistant";
  content: string;
  surfaceId?: string;
};

const starterPrompts = [
  "我想贷20万装修，多久能放款？",
  "我是开餐饮店的，想贷50万周转",
  "我这个月贷款要还多少？",
  "我有理财产品，临时需要30万周转",
];

export function ChatPanel() {
  const [conversationId, setConversationId] = useState<string>();
  const conversationIdRef = useRef<string | undefined>(undefined);
  const [input, setInput] = useState("");
  const [items, setItems] = useState<ChatItem[]>([
    {
      role: "assistant",
      content: "我是 LoanPilot 贷航员，可以帮你咨询贷款、测算额度、提交演示申请、查询进度和处理还款服务。",
    },
  ]);
  const [surfaces, setSurfaces] = useState<Record<string, SurfaceModel<ReactComponentImplementation>>>({});
  const [loading, setLoading] = useState(false);

  const processorRef = useRef<MessageProcessor<ReactComponentImplementation> | undefined>(undefined);

  if (!processorRef.current) {
    processorRef.current = new MessageProcessor([loanPilotCatalog], async (event: A2uiClientAction) => {
      const currentConversationId = conversationIdRef.current;
      if (!currentConversationId) return;
      if (event.context?.requiresConfirm && !window.confirm("确认执行该演示动作？")) return;
      setLoading(true);
      try {
        const response = await runAction(event.name, currentConversationId, event.context, event.surfaceId);
        processResponse(response);
      } finally {
        setLoading(false);
      }
    });
  }

  useEffect(() => {
    conversationIdRef.current = conversationId;
  }, [conversationId]);

  useEffect(() => {
    const processor = processorRef.current;
    if (!processor) return;
    const created = processor.onSurfaceCreated((surface) => {
      setSurfaces((current) => ({ ...current, [surface.id]: surface }));
    });
    const deleted = processor.onSurfaceDeleted((surfaceId) => {
      setSurfaces((current) => {
        const next = { ...current };
        delete next[surfaceId];
        return next;
      });
    });
    return () => {
      created.unsubscribe();
      deleted.unsubscribe();
    };
  }, []);

  function processResponse(response: ChatResponse) {
    setConversationId(response.conversation_id);
    conversationIdRef.current = response.conversation_id;
    processorRef.current?.processMessages(response.a2ui_messages as never);
    setItems((current) => [...current, { role: "assistant", content: response.content, surfaceId: response.surface_id }]);
  }

  async function submit(text = input) {
    const value = text.trim();
    if (!value) return;
    setInput("");
    setItems((current) => [...current, { role: "user", content: value }]);
    setLoading(true);
    try {
      const response = await sendMessage(value, conversationId);
      processResponse(response);
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
            <div className={`message ${item.role}`} key={`${item.role}-${index}`}>
              <p>{item.content}</p>
              {item.surfaceId && surfaces[item.surfaceId] && (
                <div className="a2ui-card-host">
                  <A2uiSurface surface={surfaces[item.surfaceId]} />
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="message assistant">
              <p>正在处理...</p>
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
