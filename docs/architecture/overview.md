# LoanPilot Architecture

LoanPilot uses a controlled agent UI architecture. The backend owns the Dify-style gateway, banking state, and card governance. The frontend owns rendering, interaction, and the visual language of cards.

```text
React + Vite frontend
  -> MessageRenderer parses content and placeholders
  -> CardRenderer dispatches to React business cards
  -> FastAPI backend
  -> AiGateway + MockDifyClient
  -> MockBankingAdapter
  -> SQLite or configured SQLAlchemy database
```

## Agent Message Flow

The backend emits Qwen-style agent messages:

- `content`: assistant-visible text with placeholders such as `[(loan_recommend_1)]`.
- `meta_data.intent_data`: intent and workflow state.
- `meta_data.slots`: structured business slots such as amount, purpose, segment, loan ID, or application ID.
- `meta_data.multi_load`: business card payloads keyed by `source_seq`.

The frontend parses `content`, replaces each placeholder with the matching `multi_load` entry, and renders the card with native React business components:

- `loan_recommend`: product recommendations.
- `assessment_result`: credit pre-assessment result.
- `bill_summary`: current bill summary.
- `application_status`: application status and document checklist.
- `repayment_plan`: repayment schedule.
- `prepayment_quote`: early repayment quote.
- `loan_comparison`: option comparison.

This keeps the backend focused on business data and lets the frontend own layout, interaction, responsive behavior, and visual polish.

## Backend Boundaries

The backend is organized around clear boundaries:

- `api/`: HTTP routes and request/response conversion.
- `services/`: Dify mock gateway, banking actions, seed data, and audit utilities.
- `adapters/`: banking capability interfaces and mock implementations.
- `models/`: SQLAlchemy domain entities.
- `agent_messages.py`: Qwen-style message and business card builders.

## Bank Integration Boundary

All bank-specific behavior is behind adapter methods. The demo uses `MockBankingAdapter`; production integrations can replace it with concrete adapters such as:

- `BankLoanProductAdapter`
- `BankCreditAssessmentAdapter`
- `BankLoanApplicationAdapter`
- `BankDocumentAdapter`
- `BankContractAdapter`
- `BankRepaymentAdapter`
- `BankNotificationAdapter`

Frontend cards and workflow contracts should not depend on individual bank system details.

## Safety Model

LoanPilot does not perform real approval, final pricing, contract signing, fund transfer, or document storage. Critical actions are audit logged in the demo database, but production usage requires a full authentication, authorization, audit, encryption, and regulatory compliance design.
