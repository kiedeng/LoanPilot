# Contributing to LoanPilot

Thank you for considering a contribution to LoanPilot.

## Fork and Clone

1. Fork the repository on GitHub.
2. Clone your fork:

```bash
git clone https://github.com/<your-account>/LoanPilot.git
cd LoanPilot
```

3. Add the upstream remote if needed:

```bash
git remote add upstream https://github.com/kiedeng/LoanPilot.git
```

## Create a Branch

Use a short, descriptive branch name:

```bash
git checkout -b feature/a2ui-card-tests
git checkout -b fix/cors-local-origin
git checkout -b docs/readme-update
```

## Local Development

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

Run the backend:

```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8001 --reload
```

Run the frontend:

```bash
cd frontend
VITE_API_BASE=http://127.0.0.1:8001/api npm run dev -- --host 0.0.0.0 --port 5173
```

## Commit Message Suggestions

Prefer concise, imperative commit messages:

```text
Add repayment schedule card
Fix local CORS origin matching
Document A2UI catalog architecture
```

For larger changes, use a prefix:

```text
feat: add application checklist card
fix: dispatch custom A2UI actions correctly
docs: expand Chinese README
test: cover pre-assessment actions
```

## Quality Checks

Before opening a pull request, run:

```bash
pytest -q
cd frontend && npm run build
```

## Pull Request Process

1. Keep the pull request focused on one topic.
2. Include a short summary of what changed and why.
3. Include validation results.
4. Add screenshots or screen recordings for UI changes when useful.
5. Update documentation for changed behavior, setup, APIs, or architecture.
6. Do not commit `.env`, local databases, logs, credentials, tokens, `node_modules`, or build output.

## Issue Guidelines

For bug reports, include:

- Reproduction steps.
- Expected behavior.
- Actual behavior.
- Environment details.
- Logs or screenshots if useful.

For feature requests, include:

- Problem statement.
- Proposed solution.
- Alternatives considered.
- Expected user or developer impact.

## Security

Do not open public issues for vulnerabilities or leaked credentials. Follow [SECURITY.md](SECURITY.md).
