# LoanPilot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-2f74c0)](frontend/package.json)
[![Backend](https://img.shields.io/badge/backend-FastAPI-009688)](backend/requirements.txt)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](CHANGELOG.md)

LoanPilot is an open-source demo of a banking loan AI agent. It combines a conversational loan assistant, a Dify-style AI gateway, mock banking adapters, SQLite demo data, and A2UI-driven financial cards rendered by a React frontend.

[中文文档](README.zh-CN.md)

## Features

- Conversational loan journeys for product discovery, credit pre-assessment, loan application, document collection, repayment servicing, prepayment quoting, and human handoff.
- Official A2UI v0.9 message flow with a custom LoanPilot frontend catalog for professional fintech-style cards.
- Finance-specific card components: `LoanInsightCard`, `LoanInfoCard`, `LoanComparisonCard`, and `LoanApplicationCard`.
- Dify mock orchestration with streaming responses, intent routing, clarification, and tool-call style events.
- Mock banking adapter boundary for replacing demo data with real bank systems.
- FastAPI backend, React + Vite frontend, SQLAlchemy models, and focused API tests.

## Architecture

```text
React + Vite frontend
  -> LoanPilot custom A2UI catalog
  -> @a2ui/react A2uiSurface
  -> @a2ui/web_core MessageProcessor
  -> FastAPI backend
  -> AiGateway + MockDifyClient
  -> MockBankingAdapter
  -> SQLite or configured SQLAlchemy database
```

The backend emits A2UI v0.9 messages:

- `createSurface`
- `updateDataModel`
- `updateComponents`

The frontend processes those messages with `MessageProcessor` and renders native React components through `A2uiSurface`. This keeps UI generation declarative while allowing LoanPilot to own the fintech visual language.

## Requirements

- Python 3.11+
- Node.js 22+
- npm 10+
- Git

Optional:

- A virtual environment manager such as `venv`, Conda, or uv.
- SQLite CLI for inspecting local demo data.

## Installation

Clone the repository:

```bash
git clone https://github.com/kiedeng/LoanPilot.git
cd LoanPilot
```

Install backend dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

## Configuration

Copy the example environment file if you want local overrides:

```bash
cp .env.example .env
```

Available variables:

- `APP_NAME`: Application display name.
- `DATABASE_URL`: SQLAlchemy database URL. Defaults to local SQLite.
- `VITE_API_BASE`: Frontend API base URL, usually `http://127.0.0.1:8001/api`.

Do not commit `.env`, local databases, logs, credentials, tokens, or production connection strings.

## Quick Start

Start the backend:

```bash
cd /mnt/d/1/LoanPilot
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8001 --reload
```

Start the frontend:

```bash
cd /mnt/d/1/LoanPilot/frontend
VITE_API_BASE=http://127.0.0.1:8001/api npm run dev -- --host 0.0.0.0 --port 5173
```

Open:

- Frontend: `http://localhost:5173`
- Backend API: `http://127.0.0.1:8001`
- OpenAPI: `http://127.0.0.1:8001/docs`

## Usage Examples

Try these prompts in the chat UI:

- `我想贷20万装修，多久能放款？`
- `我是开餐饮店的，想贷50万周转`
- `我这个月贷款要还多少？`
- `我有理财产品，临时需要10万周转`
- `对比一下贷款方案`

HTTP examples are available in [examples/http](examples/http).

## API Reference

Main endpoints:

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/chat/message` | Send a chat message and receive A2UI card messages. |
| `POST` | `/api/actions/{action_id}` | Run an A2UI card action. |
| `GET` | `/api/conversations/{conversation_id}` | Read conversation history and workflow state. |
| `GET` | `/api/loan/products` | List mock loan products. |
| `POST` | `/api/loan/pre-assess` | Run mock credit pre-assessment. |
| `POST` | `/api/loan/applications` | Create a mock loan application. |
| `GET` | `/api/loan/repayment-plan/{loan_id}` | Read a mock repayment plan. |
| `POST` | `/api/loan/prepayment/quote` | Generate a mock prepayment quote. |

For the full API schema, run the backend and open `http://127.0.0.1:8001/docs`.

## Project Structure

```text
LoanPilot/
  backend/                 FastAPI API, domain models, Dify mock services, tests
  frontend/                React + Vite app and custom A2UI catalog
  docs/                    Architecture, product demo, security and development notes
  examples/                Request examples and integration snippets
  .github/                 CI configuration, issue templates, PR template
  README.md                English documentation
  README.zh-CN.md          Chinese documentation
```

## Development

Backend source lives in `backend/app`. Frontend source lives in `frontend/src`.

Recommended loop:

```bash
pytest -q
cd frontend && npm run build
```

Development notes are in [docs/development/local-setup.md](docs/development/local-setup.md).

## Testing

Backend:

```bash
pytest -q
```

Frontend:

```bash
cd frontend
npm run build
```

GitHub Actions runs both checks on pushes and pull requests targeting `main`.

## Deployment

LoanPilot is a demo application. For a simple deployment:

1. Build the frontend with `npm run build`.
2. Serve `frontend/dist` through a static web server.
3. Run the FastAPI app behind a production ASGI server and reverse proxy.
4. Set `DATABASE_URL` to a managed database if local SQLite is not acceptable.
5. Configure CORS origins explicitly for your deployed frontend domain.

Do not use the demo mock adapter for production lending decisions.

## Roadmap

- Add typed API clients for frontend-to-backend contracts.
- Add Playwright smoke tests for A2UI card interactions.
- Add optional Docker Compose development environment.
- Replace MockDifyClient with a real Dify API client.
- Add adapter examples for bank product, document, and repayment systems.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md), open an issue for larger changes, and submit pull requests with validation notes.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

## Acknowledgements

- [A2UI](https://a2ui.org/) for the declarative agent UI protocol and React renderer.
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework.
- [React](https://react.dev/) and [Vite](https://vite.dev/) for the frontend development stack.
- [SQLAlchemy](https://www.sqlalchemy.org/) for the ORM layer.
