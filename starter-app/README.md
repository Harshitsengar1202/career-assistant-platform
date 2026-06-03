# AI Career Assistant Starter App

This starter app contains:

- `frontend/`: a dependency-free dashboard prototype you can open directly in a browser.
- `backend/`: a FastAPI scaffold with representative endpoints and in-memory sample data.

## Run Frontend

Open `frontend/index.html` in a browser, or serve the folder with any static server.

## Run Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Next Build Steps

1. Replace in-memory data with PostgreSQL models.
2. Add JWT auth and OAuth integrations.
3. Connect resume upload to object storage and parsing workers.
4. Add AI provider adapters and queue-backed agent runs.
5. Add Playwright worker service for controlled apply workflows.
