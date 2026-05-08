import type { AgentAction, AgentCard, AgentMessage } from "../types";
import { CardRenderer } from "./AgentCards";

type MessageRendererProps = {
  message: AgentMessage;
  onAction: (action: AgentAction) => void;
};

type Segment = { type: "text"; value: string } | { type: "card"; sourceSeq: string };

export function MessageRenderer({ message, onAction }: MessageRendererProps) {
  const cards = new Map((message.meta_data.multi_load ?? []).map((card) => [card.source_seq, card]));
  return (
    <div className="agent-message">
      {parseContent(message.content).map((segment, index) => {
        if (segment.type === "text") return <TextSegment key={`text-${index}`} value={segment.value} />;
        const card = cards.get(segment.sourceSeq);
        if (!card) return <MissingCard key={`card-${segment.sourceSeq}`} sourceSeq={segment.sourceSeq} />;
        return <CardRenderer card={card as AgentCard} key={`card-${segment.sourceSeq}`} onAction={onAction} />;
      })}
    </div>
  );
}

function TextSegment({ value }: { value: string }) {
  const paragraphs = value
    .split(/\n{2,}/)
    .map((part) => part.trim())
    .filter(Boolean);
  return (
    <>
      {paragraphs.map((paragraph, index) => (
        <p className="message-bubble" key={`${index}-${paragraph}`}>
          {paragraph}
        </p>
      ))}
    </>
  );
}

function MissingCard({ sourceSeq }: { sourceSeq: string }) {
  return (
    <article className="agent-card agent-card--fallback">
      <h3>卡片数据缺失</h3>
      <p>{sourceSeq}</p>
    </article>
  );
}

function parseContent(content: string): Segment[] {
  const segments: Segment[] = [];
  const pattern = /\[\(([^)]+)\)\]/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(content))) {
    if (match.index > lastIndex) {
      segments.push({ type: "text", value: content.slice(lastIndex, match.index) });
    }
    segments.push({ type: "card", sourceSeq: match[1] });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < content.length) {
    segments.push({ type: "text", value: content.slice(lastIndex) });
  }

  return segments.length ? segments : [{ type: "text", value: content }];
}
