# Local Development

## Backend

```bash
cd /mnt/d/1/LoanPilot
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8001 --reload
```

## Frontend

```bash
cd /mnt/d/1/LoanPilot/frontend
npm install
VITE_API_BASE=http://127.0.0.1:8001/api npm run dev -- --host 0.0.0.0 --port 5173
```

## Checks

```bash
pytest -q
cd frontend && npm run build
```

## Common Issues

### CORS error

Use a local origin such as `http://localhost:5173` or `http://127.0.0.1:5173`. The backend allows local development origins.

### Unknown A2UI component

Restart the frontend dev server after adding custom catalog components. A stale Vite process can keep an old catalog in memory.

### Port already in use

Find and stop old development processes:

```bash
lsof -nP -iTCP:8001 -iTCP:5173 -sTCP:LISTEN
```
