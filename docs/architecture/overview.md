# LoanPilot Architecture

LoanPilot uses a controlled agent UI architecture. The backend owns workflow and banking state. The frontend owns rendering, interaction, and the visual language of cards.

```text
React + Vite frontend
  -> LoanPilot custom A2UI catalog
  -> @a2ui/react A2uiSurface
  -> @a2ui/web_core MessageProcessor
  -> FastAPI backend
  -> LoanWorkflow
  -> MockBankingAdapter
  -> SQLite or configured SQLAlchemy database
```

## A2UI Message Flow

The backend emits official A2UI v0.9 messages:

- `createSurface`: creates a surface using the LoanPilot catalog ID.
- `updateDataModel`: attaches structured business data to the surface.
- `updateComponents`: declares the root custom card component and its props.

The frontend registers a custom catalog at `https://loanpilot.local/a2ui/catalog/v1`. It includes the official basic components plus LoanPilot-specific business components:

- `LoanInsightCard`: product, credit assessment, bill, and prepayment summary cards.
- `LoanInfoCard`: policy, progress, repayment schedule, renewal, upload, and handoff cards.
- `LoanComparisonCard`: loan option comparison matrix.
- `LoanApplicationCard`: application status and document checklist.

This keeps the A2UI protocol declarative while allowing the client to render professional fintech-style native React components.

## Backend Boundaries

The backend is organized around clear boundaries:

- `api/`: HTTP routes and request/response conversion.
- `workflows/`: deterministic conversation workflow and action handling.
- `adapters/`: banking capability interfaces and mock implementations.
- `models/`: SQLAlchemy domain entities.
- `services/`: seed data and audit utilities.
- `a2ui/`: A2UI response builders.

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
