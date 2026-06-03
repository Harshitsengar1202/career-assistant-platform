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
- `GET /jobs/live`: preview jobs from public job APIs without saving.
- `POST /jobs/refresh`: fetch jobs from public job APIs and save them into Supabase.
- `POST /resumes/analyze`: score pasted resume text against a job description.
- `POST /resumes`: save a resume score into Supabase.
- `POST /resumes/upload-pdf`: upload a PDF resume, extract text, score it, and save it.
- `POST /resumes/tailor`: generate a tailored summary and optimized resume bullets.
- `GET /resumes`: list saved resume scores.
- `POST /ai/cover-letter`: generate a tailored cover letter.
- `POST /ai/interview-prep`: generate interview questions and answer tips.
- `POST /ai/outreach`: generate LinkedIn, cold email, and follow-up messages.
- `GET /agents/status`: verify whether OpenAI agents are enabled.
- `POST /agents/resume`: run the resume agent only.
- `POST /agents/job-match`: run the job match agent only.
- `POST /agents/application-kit`: run the application kit agent only.
- `POST /agents/full-run`: run resume, job match, kit generation, and approval-mode auto-apply planning together.
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
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-mini
```

Example job creation:

```bash
curl -X POST "$API_BASE/jobs" \
  -H "Content-Type: application/json" \
  -d '{"company":"Acme AI","title":"Backend Engineer","location":"Remote","salary_min":90000,"salary_max":130000,"source":"Manual","source_url":"https://example.com/acme-backend"}'
```

Example resume analysis:

```bash
curl -X POST "$API_BASE/resumes/analyze" \
  -H "Content-Type: application/json" \
  -d '{"resume_text":"Experience: Built Python APIs with PostgreSQL, Docker, testing, and analytics dashboards. Skills: Python, SQL, FastAPI, React, cloud automation, collaboration, leadership. Projects: Reduced manual reporting by 40%. Education: Computer Science.","job_description":"We need a backend engineer with Python, FastAPI, PostgreSQL, Docker, API design, testing, analytics, and cloud experience."}'
```

Example application kit:

```bash
curl -X POST "$API_BASE/ai/cover-letter" \
  -H "Content-Type: application/json" \
  -d '{"company":"Acme AI","role":"Backend Engineer","resume_summary":"Built Python APIs with PostgreSQL, Docker, testing, analytics dashboards, and cloud automation. Reduced manual reporting by 40%.","job_description":"We need a backend engineer with Python, FastAPI, PostgreSQL, Docker, API design, testing, analytics, and cloud experience.","tone":"professional"}'
```

Example full agent run:

```bash
curl -X POST "$API_BASE/agents/full-run" \
  -H "Content-Type: application/json" \
  -d '{"company":"Acme AI","role":"Backend Engineer","resume_text":"Experience: Built Python APIs with PostgreSQL, Docker, testing, analytics dashboards, and cloud automation. Reduced manual reporting by 40%. Skills: Python, SQL, FastAPI, React, leadership, collaboration.","job_description":"We need a backend engineer with Python, FastAPI, PostgreSQL, Docker, API design, testing, analytics, and cloud experience.","tone":"professional","min_match_score":75}'
```

If `OPENAI_API_KEY` is missing, the backend stays online and uses deterministic fallback agents. Use `GET /agents/status` to confirm whether real OpenAI agents are active.

## Job Sources

The app uses public job feeds rather than scraping protected job-board pages directly:

- Remotive public remote jobs API
- Arbeitnow public job board API

Use the Jobs tab:

1. Enter a search query.
2. Click `Preview live` to see unsaved live results.
3. Click `Fetch and save` to store real jobs in Supabase.
4. Click `Save` on a stored job to add it to the Pipeline.

LinkedIn, Indeed, Glassdoor, and similar platforms may restrict scraping or automated application workflows. For production, prefer official APIs, partner feeds, permitted email/job alerts, or user-approved manual workflows.
