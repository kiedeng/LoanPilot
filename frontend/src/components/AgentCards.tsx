import type { AgentAction, AgentCard } from "../types";

type CardProps = {
  card: AgentCard;
  onAction: (action: AgentAction) => void;
};

type RecordValue = Record<string, unknown>;

export function CardRenderer({ card, onAction }: CardProps) {
  const data = (card.content.resultData ?? {}) as RecordValue;

  if (card.type === "loan_recommend") return <LoanRecommendationCard data={data} onAction={onAction} />;
  if (card.type === "assessment_result") return <AssessmentCard data={data} onAction={onAction} />;
  if (card.type === "bill_summary") return <BillSummaryCard data={data} onAction={onAction} />;
  if (card.type === "application_status") return <ApplicationStatusCard data={data} onAction={onAction} />;
  if (card.type === "repayment_plan") return <RepaymentPlanCard data={data} />;
  if (card.type === "prepayment_quote") return <PrepaymentQuoteCard data={data} onAction={onAction} />;
  if (card.type === "loan_comparison") return <LoanComparisonCard data={data} />;
  if (card.type === "info") return <InfoCard data={data} />;

  return (
    <article className="agent-card agent-card--fallback">
      <h3>暂不支持的卡片</h3>
      <p>{card.type}</p>
    </article>
  );
}

function LoanRecommendationCard({ data, onAction }: { data: RecordValue; onAction: (action: AgentAction) => void }) {
  const items = getArray<RecordValue>(data.loanRecommendationItems);
  return (
    <article className="loan-recommendation-feed">
      <header className="loan-recommendation-feed__header">
        <span>智能推荐</span>
        <h3>为你推荐几款匹配的贷款方案</h3>
      </header>
      <section className="loan-recommendation-feed__items">
        {items.map((item, index) => (
          <article className={index === 0 ? "featured" : undefined} key={String(item.productId ?? index)}>
            <header>
              <span>{index === 0 ? "优先匹配" : String(item.segment ?? "方案")}</span>
              <h4>{String(item.productName ?? "贷款方案")}</h4>
            </header>
            <p>{String(item.description ?? "")}</p>
            <MetricGrid
              metrics={[
                ["最高额度", String(item.maxAmountText ?? item.maxAmount ?? "-")],
                ["参考年化", String(item.rateRange ?? "-")],
                ["期限", String(item.termRange ?? "-")],
                ["放款", String(item.estimatedDisbursement ?? "-")],
              ]}
            />
            <ActionButtons actions={getArray<AgentAction>(item.actions)} onAction={onAction} />
          </article>
        ))}
      </section>
      {typeof data.notice === "string" && <p className="loan-recommendation-feed__notice">{data.notice}</p>}
    </article>
  );
}

function AssessmentCard({ data, onAction }: { data: RecordValue; onAction: (action: AgentAction) => void }) {
  return (
    <InsightCard
      eyebrow="资质预评估"
      title="额度预估结果"
      primaryLabel="预估可贷额度"
      primaryValue={String(data.estimatedAmountText ?? "-")}
      rows={[
        ["参考年化利率", String(data.rateRange ?? "-")],
        ["可选期限", String(data.termRange ?? "-")],
        ["预计放款", String(data.estimatedDisbursement ?? "-")],
      ]}
      notice={typeof data.notice === "string" ? data.notice : undefined}
      actions={getArray<AgentAction>(data.actions)}
      onAction={onAction}
    />
  );
}

function BillSummaryCard({ data, onAction }: { data: RecordValue; onAction: (action: AgentAction) => void }) {
  return (
    <InsightCard
      eyebrow="服务管理"
      title={String(data.productName ?? "贷款账单")}
      primaryLabel="本期应还"
      primaryValue={String(data.dueAmountText ?? "-")}
      rows={[
        ["还款日", String(data.dueDate ?? "-")],
        ["剩余本金", String(data.outstandingBalanceText ?? "-")],
      ]}
      actions={getArray<AgentAction>(data.actions)}
      onAction={onAction}
    />
  );
}

function ApplicationStatusCard({ data, onAction }: { data: RecordValue; onAction: (action: AgentAction) => void }) {
  const steps = getArray<RecordValue>(data.steps);
  const documents = getArray<RecordValue>(data.documents);
  return (
    <article className="loan-application-card">
      <header className="loan-application-card__header">
        <span>业务办理</span>
        <h3>申请单 {String(data.applicationId ?? "-")}</h3>
      </header>
      <section className="loan-application-card__status">
        <span>当前状态</span>
        <strong>{String(data.status ?? "-")}</strong>
      </section>
      {steps.length ? (
        <section className="loan-info-card__items">
          {steps.map((step, index) => (
            <div className="loan-info-card__item" key={`${String(step.name ?? index)}-${String(step.status ?? "")}`}>
              <i>{String(index + 1).padStart(2, "0")}</i>
              <div>
                <span>{String(step.status ?? "")}</span>
                <strong>{String(step.name ?? "")}</strong>
              </div>
            </div>
          ))}
        </section>
      ) : null}
      {documents.length ? (
        <section className="loan-application-card__docs">
          {documents.map((doc, index) => (
            <div key={`${String(doc.name ?? index)}-${String(doc.status ?? "")}`}>
              <span>{String(doc.name ?? "")}</span>
              <strong>{String(doc.status ?? "")}</strong>
            </div>
          ))}
        </section>
      ) : null}
      {typeof data.notice === "string" && <p className="loan-application-card__notice">{data.notice}</p>}
      <ActionButtons actions={getArray<AgentAction>(data.actions)} onAction={onAction} className="loan-application-card__actions" />
    </article>
  );
}

function RepaymentPlanCard({ data }: { data: RecordValue }) {
  const items = getArray<RecordValue>(data.items);
  return (
    <InfoCard
      data={{
        title: `贷款 ${String(data.loanId ?? "-")}`,
        items: items.map((item) => ({
          label: `第 ${String(item.period ?? "-")} 期`,
          value: `${String(item.dueDate ?? "-")} 应还 ${String(item.amountText ?? "-")}，本金 ${String(item.principalText ?? "-")}，利息 ${String(item.interestText ?? "-")}`,
        })),
      }}
    />
  );
}

function PrepaymentQuoteCard({ data, onAction }: { data: RecordValue; onAction: (action: AgentAction) => void }) {
  return (
    <InsightCard
      eyebrow="提前还款"
      title={`贷款 ${String(data.loanId ?? "-")}`}
      primaryLabel="试算结清金额"
      primaryValue={String(data.payoffAmountText ?? "-")}
      rows={[
        ["其中手续费", String(data.feeText ?? "-")],
        ["报价有效期至", String(data.validUntil ?? "-")],
      ]}
      notice={typeof data.notice === "string" ? data.notice : undefined}
      actions={getArray<AgentAction>(data.actions)}
      onAction={onAction}
    />
  );
}

function LoanComparisonCard({ data }: { data: RecordValue }) {
  const options = getArray<RecordValue>(data.options);
  return (
    <article className="loan-comparison-card">
      <header className="loan-comparison-card__header">
        <span>方案比较</span>
        <h3>贷款方案对比</h3>
      </header>
      <section className="loan-comparison-card__grid">
        {options.map((option, index) => (
          <div className={index === 0 ? "recommended" : undefined} key={String(option.name ?? index)}>
            <header>
              <span>{index === 0 ? "优先推荐" : `方案 ${index + 1}`}</span>
              <h4>{String(option.name ?? "")}</h4>
            </header>
            <MetricRows
              rows={[
                ["额度", String(option.amountText ?? "-")],
                ["利率", String(option.rate ?? "-")],
                ["期限", String(option.term ?? "-")],
                ["速度", String(option.speed ?? "-")],
              ]}
            />
          </div>
        ))}
      </section>
    </article>
  );
}

function InfoCard({ data }: { data: RecordValue }) {
  const items = getArray<RecordValue>(data.items);
  return (
    <article className="loan-info-card">
      <header className="loan-info-card__header">
        <span>LoanPilot</span>
        <h3>{String(data.title ?? "信息")}</h3>
      </header>
      <section className="loan-info-card__items">
        {items.map((item, index) => (
          <div className="loan-info-card__item" key={`${String(item.label ?? index)}-${String(item.value ?? "")}`}>
            <i>{String(index + 1).padStart(2, "0")}</i>
            <div>
              {item.label ? <span>{String(item.label)}</span> : null}
              <strong>{String(item.value ?? "")}</strong>
            </div>
          </div>
        ))}
      </section>
    </article>
  );
}

function InsightCard({
  eyebrow,
  title,
  primaryLabel,
  primaryValue,
  rows,
  notice,
  actions,
  onAction,
}: {
  eyebrow: string;
  title: string;
  primaryLabel: string;
  primaryValue: string;
  rows: Array<[string, string]>;
  notice?: string;
  actions?: AgentAction[];
  onAction: (action: AgentAction) => void;
}) {
  return (
    <article className="loan-insight-card">
      <header className="loan-insight-card__header">
        <span>{eyebrow}</span>
        <h3>{title}</h3>
      </header>
      <section className="loan-insight-card__hero">
        <span>{primaryLabel}</span>
        <strong>{primaryValue}</strong>
      </section>
      <section className="loan-insight-card__rows">
        {rows.map(([label, value]) => (
          <div key={`${label}-${value}`}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </section>
      {notice && <p className="loan-insight-card__notice">{notice}</p>}
      <ActionButtons actions={actions ?? []} onAction={onAction} className="loan-insight-card__actions" />
    </article>
  );
}

function ActionButtons({
  actions,
  onAction,
  className,
}: {
  actions: AgentAction[];
  onAction: (action: AgentAction) => void;
  className?: string;
}) {
  if (!actions.length) return null;
  return (
    <footer className={className}>
      {actions.map((action) => (
        <button className={action.variant === "primary" ? "primary" : undefined} key={`${action.name}-${action.label}`} type="button" onClick={() => onAction(action)}>
          {action.label}
        </button>
      ))}
    </footer>
  );
}

function MetricGrid({ metrics }: { metrics: Array<[string, string]> }) {
  return (
    <dl>
      {metrics.map(([label, value]) => (
        <div key={`${label}-${value}`}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function MetricRows({ rows }: { rows: Array<[string, string]> }) {
  return (
    <dl>
      {rows.map(([label, value]) => (
        <div key={`${label}-${value}`}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function getArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}
