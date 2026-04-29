# Contributing to LoanPilot

Thank you for considering a contribution to LoanPilot.

## Development Setup

1. Fork and clone the repository.
2. Install backend dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

3. Install frontend dependencies:

```bash
cd frontend
npm install
```

4. Run the backend and frontend as described in `README.md`.

## Quality Checks

Before opening a pull request, run:

```bash
pytest -q
cd frontend && npm run build
```

## Pull Request Guidelines

- Keep changes focused and easy to review.
- Include documentation updates for behavior, setup, API, or architecture changes.
- Do not commit `.env`, local databases, logs, credentials, tokens, or generated build output.
- For UI changes, include a short description of the affected workflow.
- For backend changes, describe the affected API or workflow state.

## Security

Do not open public issues for vulnerabilities or leaked credentials. Follow `SECURITY.md`.
