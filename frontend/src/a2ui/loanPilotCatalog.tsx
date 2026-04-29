import {
  AudioPlayer,
  Button,
  Card,
  CheckBox,
  ChoicePicker,
  Column,
  DateTimeInput,
  Divider,
  Icon,
  Image,
  List,
  Modal,
  Row,
  Slider,
  Tabs,
  Text,
  TextField,
  Video,
  basicCatalog,
  createComponentImplementation,
  type ReactComponentImplementation,
} from "@a2ui/react/v0_9";
import { Catalog } from "@a2ui/web_core/v0_9";
import { z } from "zod";

export const LOANPILOT_CATALOG_ID = "https://loanpilot.local/a2ui/catalog/v1";

const loanActionSchema = z.object({
  label: z.string(),
  name: z.string(),
  variant: z.enum(["primary", "default"]).optional(),
  context: z.record(z.string(), z.any()).optional(),
});

const LoanInsightCard = createComponentImplementation(
  {
    name: "LoanInsightCard",
    schema: z.object({
      eyebrow: z.string(),
      title: z.string(),
      description: z.string().optional(),
      primaryLabel: z.string().optional(),
      primaryValue: z.string().optional(),
      metrics: z.array(z.object({ label: z.string(), value: z.string() })).optional(),
      rows: z.array(z.object({ label: z.string(), value: z.string() })).optional(),
      notice: z.string().optional(),
      actions: z.array(loanActionSchema).optional(),
    }),
  },
  ({ props, context }) => {
    async function dispatch(action: z.infer<typeof loanActionSchema>) {
      await context.dispatchAction({ event: { name: action.name, context: action.context ?? {} } });
    }

    return (
      <article className="loan-insight-card">
        <header className="loan-insight-card__header">
          <span>{props.eyebrow}</span>
          <h3>{props.title}</h3>
          {props.description && <p>{props.description}</p>}
        </header>

        {props.primaryValue && (
          <section className="loan-insight-card__hero">
            <span>{props.primaryLabel}</span>
            <strong>{props.primaryValue}</strong>
          </section>
        )}

        {props.metrics?.length ? (
          <section className="loan-insight-card__metrics">
            {props.metrics.map((metric) => (
              <div key={`${metric.label}-${metric.value}`}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
              </div>
            ))}
          </section>
        ) : null}

        {props.rows?.length ? (
          <section className="loan-insight-card__rows">
            {props.rows.map((row) => (
              <div key={`${row.label}-${row.value}`}>
                <span>{row.label}</span>
                <strong>{row.value}</strong>
              </div>
            ))}
          </section>
        ) : null}

        {props.notice && <p className="loan-insight-card__notice">{props.notice}</p>}

        {props.actions?.length ? (
          <footer className="loan-insight-card__actions">
            {props.actions.map((action) => (
              <button
                className={action.variant === "primary" ? "primary" : undefined}
                key={`${action.name}-${action.label}`}
                type="button"
                onClick={() => dispatch(action)}
              >
                {action.label}
              </button>
            ))}
          </footer>
        ) : null}
      </article>
    );
  },
);

const LoanInfoCard = createComponentImplementation(
  {
    name: "LoanInfoCard",
    schema: z.object({
      eyebrow: z.string(),
      title: z.string(),
      summary: z.string().optional(),
      variant: z.enum(["brief", "timeline", "schedule", "handoff"]).optional(),
      items: z.array(z.object({ label: z.string().optional(), value: z.string() })),
      notice: z.string().optional(),
    }),
  },
  ({ props }) => {
    const variant = props.variant ?? "brief";

    return (
      <article className={`loan-info-card loan-info-card--${variant}`}>
        <header className="loan-info-card__header">
          <span>{props.eyebrow}</span>
          <h3>{props.title}</h3>
          {props.summary && <p>{props.summary}</p>}
        </header>

        <section className="loan-info-card__items">
          {props.items.map((item, index) => (
            <div className="loan-info-card__item" key={`${item.label ?? index}-${item.value}`}>
              <i>{String(index + 1).padStart(2, "0")}</i>
              <div>
                {item.label && <span>{item.label}</span>}
                <strong>{item.value}</strong>
              </div>
            </div>
          ))}
        </section>

        {props.notice && <p className="loan-info-card__notice">{props.notice}</p>}
      </article>
    );
  },
);

const LoanComparisonCard = createComponentImplementation(
  {
    name: "LoanComparisonCard",
    schema: z.object({
      eyebrow: z.string(),
      title: z.string(),
      options: z.array(
        z.object({
          name: z.string(),
          amount: z.string(),
          rate: z.string(),
          term: z.string(),
          speed: z.string(),
        }),
      ),
    }),
  },
  ({ props }) => (
    <article className="loan-comparison-card">
      <header className="loan-comparison-card__header">
        <span>{props.eyebrow}</span>
        <h3>{props.title}</h3>
      </header>

      <section className="loan-comparison-card__grid">
        {props.options.map((option, index) => (
          <div className={index === 0 ? "recommended" : undefined} key={option.name}>
            <header>
              <span>{index === 0 ? "优先推荐" : `方案 ${index + 1}`}</span>
              <h4>{option.name}</h4>
            </header>
            <dl>
              <div>
                <dt>额度</dt>
                <dd>{option.amount}</dd>
              </div>
              <div>
                <dt>利率</dt>
                <dd>{option.rate}</dd>
              </div>
              <div>
                <dt>期限</dt>
                <dd>{option.term}</dd>
              </div>
              <div>
                <dt>速度</dt>
                <dd>{option.speed}</dd>
              </div>
            </dl>
          </div>
        ))}
      </section>
    </article>
  ),
);

const LoanApplicationCard = createComponentImplementation(
  {
    name: "LoanApplicationCard",
    schema: z.object({
      eyebrow: z.string(),
      title: z.string(),
      statusLabel: z.string(),
      status: z.string(),
      documents: z.array(z.object({ name: z.string(), status: z.string() })),
      notice: z.string().optional(),
      action: loanActionSchema.optional(),
    }),
  },
  ({ props, context }) => {
    async function dispatch(action: z.infer<typeof loanActionSchema>) {
      await context.dispatchAction({ event: { name: action.name, context: action.context ?? {} } });
    }

    return (
      <article className="loan-application-card">
        <header className="loan-application-card__header">
          <span>{props.eyebrow}</span>
          <h3>{props.title}</h3>
        </header>

        <section className="loan-application-card__status">
          <span>{props.statusLabel}</span>
          <strong>{props.status}</strong>
        </section>

        <section className="loan-application-card__docs">
          {props.documents.map((doc) => (
            <div key={`${doc.name}-${doc.status}`}>
              <span>{doc.name}</span>
              <strong>{doc.status}</strong>
            </div>
          ))}
        </section>

        {props.notice && <p className="loan-application-card__notice">{props.notice}</p>}

        {props.action && (
          <button className="loan-application-card__button" type="button" onClick={() => dispatch(props.action!)}>
            {props.action.label}
          </button>
        )}
      </article>
    );
  },
);

const components: ReactComponentImplementation[] = [
  Text,
  Image,
  Icon,
  Video,
  AudioPlayer,
  Row,
  Column,
  List,
  Card,
  Tabs,
  Divider,
  Modal,
  Button,
  TextField,
  CheckBox,
  ChoicePicker,
  Slider,
  DateTimeInput,
  LoanInsightCard,
  LoanInfoCard,
  LoanComparisonCard,
  LoanApplicationCard,
];

export const loanPilotCatalog = new Catalog(
  LOANPILOT_CATALOG_ID,
  components,
  Array.from(basicCatalog.functions.values()),
);
