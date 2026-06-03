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

## Current Feature Endpoints

- `GET /health`: app health check.
- `GET /db/health`: Supabase/Postgres connection check.
- `GET /jobs/recommended`: list jobs from Postgres, with sample fallback.
- `POST /jobs`: create or update a job record.
- `GET /applications`: list the demo user's application pipeline.
- `POST /applications`: save a job into the pipeline.
- `PATCH /applications/{application_id}/status`: move an application between pipeline stages.
- `GET /exports/applications.csv`: download application pipeline data as CSV.

## Production URLs

- Backend: `https://career-assistant-platform-production.up.railway.app`
- Frontend: `https://career-assistant-platform-kappa.vercel.app`

Railway variables to keep configured:

```text
DATABASE_URL=postgresql://...
FRONTEND_ORIGINS=https://career-assistant-platform-kappa.vercel.app
```

Example job creation:

```bash
curl -X POST "$API_BASE/jobs" \
  -H "Content-Type: application/json" \
  -d '{"company":"Acme AI","title":"Backend Engineer","location":"Remote","salary_min":90000,"salary_max":130000,"source":"Manual","source_url":"https://example.com/acme-backend"}'
```
