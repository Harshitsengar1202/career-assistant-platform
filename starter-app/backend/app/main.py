import csv
import hashlib
import io
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .db import check_database, execute_one, fetch_all, fetch_one
from .schemas import (
    Application,
    ApplicationCreate,
    ApplicationStatusUpdate,
    AutoApplyRequest,
    Job,
    JobCreate,
)

app = FastAPI(title="AI Career Assistant API", version="0.1.0")
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "https://career-assistant-platform-kappa.vercel.app",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_EMAIL = "demo@career-assistant.local"

SAMPLE_JOBS = [
    Job(id="job_1", company="Northstar AI", title="Machine Learning Engineer", location="Remote", match_score=92, salary="$140k-$180k", source="LinkedIn"),
    Job(id="job_2", company="CloudPath", title="Backend Engineer", location="Bengaluru", match_score=86, salary="$80k-$120k", source="Company Portal"),
    Job(id="job_3", company="TalentOS", title="Full Stack Developer", location="Hybrid", match_score=81, salary="$95k-$130k", source="Indeed"),
]

SAMPLE_APPLICATIONS = [
    Application(id="app_1", company="Northstar AI", title="Machine Learning Engineer", status="applied", match_score=92, notes="Tailored resume submitted."),
    Application(id="app_2", company="CloudPath", title="Backend Engineer", status="interview", match_score=86, notes="Technical screen scheduled."),
]


@app.get("/health")
def health():
    return {"status": "ok"}


def format_salary(salary_min, salary_max):
    if salary_min and salary_max:
        return f"${int(salary_min):,}-${int(salary_max):,}"
    if salary_min:
        return f"${int(salary_min):,}+"
    return None


def normalized_hash(company: str, title: str, location: str, source_url: str) -> str:
    raw = f"{company}|{title}|{location}|{source_url}".lower().strip()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ensure_demo_user_id() -> str:
    row = execute_one(
        """
        INSERT INTO users (email, full_name)
        VALUES (:email, 'Demo User')
        ON CONFLICT (email) DO UPDATE SET updated_at = now()
        RETURNING id::text AS id
        """,
        {"email": DEMO_EMAIL},
    )
    return row["id"]


@app.get("/jobs/recommended", response_model=list[Job])
def recommended_jobs():
    try:
        rows = fetch_all(
            """
            SELECT
              id::text AS id,
              company,
              title,
              COALESCE(location, 'Remote') AS location,
              salary_min,
              salary_max,
              source_platform AS source,
              85 AS match_score
            FROM jobs
            ORDER BY discovered_at DESC
            LIMIT 50
            """
        )
    except Exception:
        return SAMPLE_JOBS

    if not rows:
        return SAMPLE_JOBS

    return [
        Job(
            id=row["id"],
            company=row["company"],
            title=row["title"],
            location=row["location"],
            match_score=row["match_score"],
            salary=format_salary(row["salary_min"], row["salary_max"]),
            source=row["source"],
        )
        for row in rows
    ]


@app.post("/jobs", response_model=Job)
def create_job(job: JobCreate):
    source_url = str(job.source_url)
    row = execute_one(
        """
        INSERT INTO jobs (
          source_platform,
          source_url,
          company,
          title,
          location,
          salary_min,
          salary_max,
          description,
          normalized_hash
        )
        VALUES (
          :source_platform,
          :source_url,
          :company,
          :title,
          :location,
          :salary_min,
          :salary_max,
          :description,
          :normalized_hash
        )
        ON CONFLICT (normalized_hash) DO UPDATE SET discovered_at = now()
        RETURNING id::text AS id, company, title, location, salary_min, salary_max, source_platform AS source
        """,
        {
            "source_platform": job.source,
            "source_url": source_url,
            "company": job.company,
            "title": job.title,
            "location": job.location,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "description": job.description,
            "normalized_hash": normalized_hash(job.company, job.title, job.location, source_url),
        },
    )
    return Job(
        id=row["id"],
        company=row["company"],
        title=row["title"],
        location=row["location"],
        match_score=85,
        salary=format_salary(row["salary_min"], row["salary_max"]),
        source=row["source"],
    )


@app.get("/applications", response_model=list[Application])
def applications():
    try:
        user_id = ensure_demo_user_id()
        rows = fetch_all(
            """
            SELECT
              a.id::text AS id,
              j.company,
              j.title,
              a.status,
              COALESCE(a.match_score, 80)::int AS match_score,
              COALESCE(a.notes, '') AS notes
            FROM applications a
            JOIN jobs j ON j.id = a.job_id
            WHERE a.user_id = :user_id
            ORDER BY a.updated_at DESC
            """,
            {"user_id": user_id},
        )
    except Exception:
        return SAMPLE_APPLICATIONS

    return [Application(**row) for row in rows] or SAMPLE_APPLICATIONS


@app.post("/applications", response_model=Application)
def save_application(application: ApplicationCreate):
    user_id = ensure_demo_user_id()
    job = fetch_one(
        "SELECT id::text AS id, company, title FROM jobs WHERE id = :job_id",
        {"job_id": application.job_id},
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    row = execute_one(
        """
        INSERT INTO applications (user_id, job_id, status, match_score, notes)
        VALUES (:user_id, :job_id, :status, :match_score, :notes)
        ON CONFLICT (user_id, job_id)
        DO UPDATE SET
          status = EXCLUDED.status,
          match_score = EXCLUDED.match_score,
          notes = EXCLUDED.notes,
          updated_at = now()
        RETURNING id::text AS id, status, match_score::int AS match_score, COALESCE(notes, '') AS notes
        """,
        {
            "user_id": user_id,
            "job_id": application.job_id,
            "status": application.status,
            "match_score": application.match_score,
            "notes": application.notes,
        },
    )
    return Application(
        id=row["id"],
        company=job["company"],
        title=job["title"],
        status=row["status"],
        match_score=row["match_score"],
        notes=row["notes"],
    )


@app.patch("/applications/{application_id}/status", response_model=Application)
def update_application_status(application_id: str, update: ApplicationStatusUpdate):
    user_id = ensure_demo_user_id()
    row = execute_one(
        """
        UPDATE applications a
        SET
          status = :status,
          notes = COALESCE(:notes, a.notes),
          updated_at = now()
        FROM jobs j
        WHERE a.job_id = j.id
          AND a.id = :application_id
          AND a.user_id = :user_id
        RETURNING
          a.id::text AS id,
          j.company,
          j.title,
          a.status,
          COALESCE(a.match_score, 80)::int AS match_score,
          COALESCE(a.notes, '') AS notes
        """,
        {
            "application_id": application_id,
            "user_id": user_id,
            "status": update.status,
            "notes": update.notes,
        },
    )
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    return Application(**row)


@app.get("/exports/applications.csv")
def export_applications_csv():
    rows = [item.model_dump() for item in applications()]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "company", "title", "status", "match_score", "notes"])
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=applications.csv"},
    )


@app.post("/agents/auto-apply/run")
def run_auto_apply(request: AutoApplyRequest):
    eligible = [job for job in SAMPLE_JOBS if job.match_score >= request.min_match_score]
    return {
        "status": "queued",
        "approval_mode": request.approval_mode,
        "daily_limit": request.daily_limit,
        "eligible_jobs": len(eligible),
        "message": "Controlled auto-apply run queued. Human approval is enabled by default.",
    }

@app.get("/db/health")
def db_health():
    try:
        return {
            "status": "connected",
            "database_time": str(check_database()),
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
