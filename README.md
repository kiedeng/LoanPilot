# LoanPilot

LoanPilot is an open-source demo of a banking loan AI agent. It combines a conversational loan assistant, FastAPI workflow services, mock banking adapters, SQLite demo data, and A2UI-driven financial cards rendered by a React frontend.

[中文文档](README.zh-CN.md)

## Highlights

- Conversational loan workflows for product discovery, credit pre-assessment, loan application, document collection, repayment servicing, prepayment quoting, and handoff.
- Official A2UI v0.9 message flow with a custom LoanPilot frontend catalog for professional fintech-style cards.
- Deterministic workflow service shaped for future LangGraph orchestration.
- Mock banking adapter boundary for replacing demo data with real bank systems.
- FastAPI backend, React + Vite frontend, SQLAlchemy models, and focused API tests.

## Repository Layout

```text
LoanPilot/
  backend/                 FastAPI API, domain models, services, workflows, tests
  frontend/                React + Vite app and custom A2UI catalog
  docs/                    Architecture, product demo, security and development notes
  .github/                 CI workflow, issue templates, PR template
  README.md                English documentation
  README.zh-CN.md          Chinese documentation
```

## Tech Stack

- Frontend: React, Vite, TypeScript
- Agent UI: `@a2ui/react/v0_9`, `@a2ui/web_core/v0_9`, custom LoanPilot A2UI catalog
- Backend: FastAPI, SQLAlchemy, Pydantic Settings
- Database: SQLite by default; external databases can be configured through `DATABASE_URL`
- Tests: pytest, FastAPI TestClient, Vite production build

## Quick Start

### Backend

```bash
cd /mnt/d/1/LoanPilot
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8001 --reload
```

The API is available at `http://127.0.0.1:8001`. OpenAPI docs are available at `http://127.0.0.1:8001/docs`.

### Frontend

```bash
cd /mnt/d/1/LoanPilot/frontend
npm install
VITE_API_BASE=http://127.0.0.1:8001/api npm run dev -- --host 0.0.0.0 --port 5173
```

The app is available at `http://localhost:5173`.

## Environment Variables

Copy `.env.example` if you want local overrides:

```bash
cp .env.example .env
```

Available variables:

- `APP_NAME`: Application display name.
- `DATABASE_URL`: SQLAlchemy database URL. Defaults to local SQLite.
- `VITE_API_BASE`: Frontend API base URL, usually `http://127.0.0.1:8001/api`.

Do not commit `.env`, local databases, logs, credentials, or production connection strings.

## Demo Scenarios

- Personal borrower: ask for a renovation loan, run pre-assessment, create an application, upload demo materials.
- Small business owner: ask for working capital, review operating loan recommendations, check required documents.
- Existing customer: check this month’s bill, view repayment schedule, request a prepayment quote.
- Wealth customer: ask for short-term liquidity and compare options.

More details are in [docs/product/demo-script.md](docs/product/demo-script.md).

## A2UI Integration

The backend emits A2UI v0.9 messages:

- `createSurface`
- `updateDataModel`
- `updateComponents`

The frontend processes messages through `MessageProcessor` and renders surfaces with `A2uiSurface`. LoanPilot registers a custom A2UI catalog with finance-specific React components such as `LoanInsightCard`, `LoanInfoCard`, `LoanComparisonCard`, and `LoanApplicationCard`.

## Validation

```bash
pytest -q
cd frontend && npm run build
```

## Security Notice

LoanPilot is a demo system. It does not perform real credit approval, identity verification, fund transfer, document storage, or core banking operations. Review [SECURITY.md](SECURITY.md) before connecting it to any real banking system.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and open an issue or pull request.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
