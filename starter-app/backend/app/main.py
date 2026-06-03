import csv
import hashlib
import io
import json
import os
import re
from collections import Counter

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .ai_service import (
    OPENAI_MODEL,
    application_kit_agent,
    full_agent_run,
    job_match_agent,
    openai_ready,
    resume_agent,
)
from .db import check_database, execute_one, fetch_all, fetch_one
from .schemas import (
    Application,
    ApplicationCreate,
    ApplicationStatusUpdate,
    AgentFullRunRequest,
    ApplicationKitRequest,
    AutoApplyRequest,
    CoverLetterResponse,
    InterviewPrepResponse,
    Job,
    JobCreate,
    OutreachResponse,
    ResumeAnalyzeRequest,
    ResumeAnalyzeResponse,
    ResumeCreate,
    ResumeRecord,
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

DEFAULT_ATS_KEYWORDS = [
    "python",
    "sql",
    "api",
    "fastapi",
    "react",
    "javascript",
    "postgresql",
    "docker",
    "cloud",
    "aws",
    "testing",
    "automation",
    "analytics",
    "leadership",
    "collaboration",
]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/agents/status")
def agent_status():
    return {
        "openai_enabled": openai_ready(),
        "model": OPENAI_MODEL,
        "mode": "openai" if openai_ready() else "deterministic_fallback",
    }


def format_salary(salary_min, salary_max):
    if salary_min and salary_max:
        return f"${int(salary_min):,}-${int(salary_max):,}"
    if salary_min:
        return f"${int(salary_min):,}+"
    return None


def normalized_hash(company: str, title: str, location: str, source_url: str) -> str:
    raw = f"{company}|{title}|{location}|{source_url}".lower().strip()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", text.lower())


def important_keywords(job_description: str) -> list[str]:
    if not job_description.strip():
        return DEFAULT_ATS_KEYWORDS

    stop_words = {
        "and", "the", "with", "for", "you", "our", "are", "will", "this", "that",
        "from", "have", "has", "your", "about", "into", "work", "team", "role",
        "experience", "years", "using", "such", "including", "across", "within",
    }
    counts = Counter(token for token in tokenize(job_description) if token not in stop_words and len(token) > 2)
    common = [word for word, _ in counts.most_common(18)]
    return common or DEFAULT_ATS_KEYWORDS


def analyze_resume_text(resume_text: str, job_description: str = "") -> ResumeAnalyzeResponse:
    resume_tokens = set(tokenize(resume_text))
    keywords = important_keywords(job_description)
    matched = [keyword for keyword in keywords if keyword.lower() in resume_tokens]
    missing = [keyword for keyword in keywords if keyword.lower() not in resume_tokens]
    word_count = len(tokenize(resume_text))

    keyword_score = round((len(matched) / max(len(keywords), 1)) * 65)
    length_score = 15 if word_count >= 350 else 10 if word_count >= 220 else 5
    structure_score = 0
    lowered = resume_text.lower()
    for section in ["experience", "skills", "projects", "education"]:
        if section in lowered:
            structure_score += 5
    ats_score = min(keyword_score + length_score + structure_score, 100)

    suggestions = []
    if missing:
        suggestions.append(f"Add evidence for these keywords where truthful: {', '.join(missing[:8])}.")
    if "projects" not in lowered:
        suggestions.append("Add a Projects section with measurable outcomes and tools used.")
    if "skills" not in lowered:
        suggestions.append("Add a Skills section grouped by language, framework, database, cloud, and tools.")
    if not re.search(r"\d+%|\d+x|\$\d+|\d+\+", resume_text):
        suggestions.append("Add quantified impact such as percentages, scale, revenue, latency, users, or automation time saved.")
    if word_count < 220:
        suggestions.append("Expand the resume with stronger experience bullets; most ATS-friendly resumes need more role evidence.")
    if not suggestions:
        suggestions.append("Resume is well structured. Tune the top summary and bullets for each target job before applying.")

    return ResumeAnalyzeResponse(
        ats_score=ats_score,
        matched_keywords=matched,
        missing_keywords=missing,
        suggestions=suggestions,
        word_count=word_count,
    )


def first_sentence(text: str, fallback: str) -> str:
    sentence = re.split(r"(?<=[.!?])\s+", text.strip())[0]
    return sentence[:220] if sentence else fallback


def top_strengths(resume_summary: str, job_description: str) -> list[str]:
    analysis = analyze_resume_text(resume_summary, job_description)
    strengths = analysis.matched_keywords[:5]
    return strengths or ["role-relevant experience", "structured problem solving", "clear communication"]


def tone_phrase(tone: str) -> str:
    return {
        "professional": "I would welcome the opportunity to discuss how my background can support your team.",
        "friendly": "I would be excited to learn more and see where I can help the team move faster.",
        "confident": "I am confident I can contribute quickly and raise the quality of execution for this role.",
        "executive": "I would appreciate the opportunity to discuss the strategic outcomes this role is expected to deliver.",
    }.get(tone, "I would welcome the opportunity to discuss the role.")


@app.post("/ai/cover-letter", response_model=CoverLetterResponse)
def generate_cover_letter(request: ApplicationKitRequest):
    strengths = ", ".join(top_strengths(request.resume_summary, request.job_description)[:4])
    role_signal = first_sentence(request.job_description, f"The {request.role} role appears focused on measurable execution and cross-functional impact.")
    resume_signal = first_sentence(request.resume_summary, "My background includes relevant execution across product, engineering, and delivery work.")
    cover_letter = (
        f"Dear {request.company} hiring team,\n\n"
        f"I am writing to express my interest in the {request.role} role at {request.company}. "
        f"{role_signal}\n\n"
        f"{resume_signal} My strongest alignment for this position is in {strengths}. "
        "I focus on turning ambiguous requirements into reliable systems, documenting decisions clearly, "
        "and delivering work that can be maintained after launch.\n\n"
        f"{tone_phrase(request.tone)}\n\n"
        "Sincerely,\n"
        "Your Name"
    )
    return CoverLetterResponse(cover_letter=cover_letter)


@app.post("/ai/interview-prep", response_model=InterviewPrepResponse)
def generate_interview_prep(request: ApplicationKitRequest):
    strengths = top_strengths(request.resume_summary, request.job_description)
    questions = [
        f"Walk me through your most relevant experience for the {request.role} role at {request.company}.",
        f"How have you used {strengths[0]} in a production or real-world project?",
        "Describe a time you improved a process, system, or workflow with measurable impact.",
        "How do you prioritize quality, speed, and maintainability when deadlines are tight?",
        "What would you do in your first 30 days if selected for this role?",
        "Tell me about a time you handled ambiguity or incomplete requirements.",
        "Which part of this job description feels strongest for you, and where would you ramp up?",
        "Why are you interested in this company and this role specifically?",
    ]
    answer_tips = [
        "Use STAR format: situation, task, action, result.",
        "Mention metrics where possible: percentage, time saved, users, revenue, reliability, or scale.",
        f"Anchor answers around these strengths: {', '.join(strengths[:5])}.",
        "Close each answer with what you learned or how you would apply it in the new role.",
    ]
    return InterviewPrepResponse(questions=questions, answer_tips=answer_tips)


@app.post("/ai/outreach", response_model=OutreachResponse)
def generate_outreach(request: ApplicationKitRequest):
    strengths = ", ".join(top_strengths(request.resume_summary, request.job_description)[:3])
    linkedin_note = (
        f"Hi, I noticed the {request.role} opening at {request.company}. "
        f"My background aligns with {strengths}, and I would appreciate a quick pointer on the best way to be considered."
    )
    cold_email = (
        f"Subject: Interest in {request.role} at {request.company}\n\n"
        "Hello,\n\n"
        f"I am reaching out about the {request.role} role at {request.company}. "
        f"My experience aligns with {strengths}, and I am especially interested in the problems described in the role. "
        "I would be grateful if you could point me to the right hiring contact or share any advice on the application process.\n\n"
        "Best,\nYour Name"
    )
    follow_up = (
        f"Hello, I wanted to follow up on my interest in the {request.role} role at {request.company}. "
        "I remain very interested and would be glad to share more context on my fit if useful."
    )
    return OutreachResponse(linkedin_note=linkedin_note, cold_email=cold_email, follow_up=follow_up)


@app.post("/agents/resume")
def run_resume_agent(request: ResumeAnalyzeRequest):
    analysis = analyze_resume_text(request.resume_text, request.job_description)
    return resume_agent(request.resume_text, request.job_description, analysis)


@app.post("/agents/job-match")
def run_job_match_agent(request: AgentFullRunRequest):
    analysis = analyze_resume_text(request.resume_text, request.job_description)
    return job_match_agent(request.company, request.role, request.resume_text, request.job_description, analysis)


@app.post("/agents/application-kit")
def run_application_kit_agent(request: AgentFullRunRequest):
    analysis = analyze_resume_text(request.resume_text, request.job_description)
    resume = resume_agent(request.resume_text, request.job_description, analysis)
    return application_kit_agent(
        request.company,
        request.role,
        resume.tailored_summary,
        request.job_description,
        request.tone,
        resume.matched_keywords,
    )


@app.post("/agents/full-run")
def run_full_agent_system(request: AgentFullRunRequest):
    analysis = analyze_resume_text(request.resume_text, request.job_description)
    result = full_agent_run(
        request.company,
        request.role,
        request.resume_text,
        request.job_description,
        request.tone,
        analysis,
    )
    decision = "ready_for_review" if result.job_match.match_score >= request.min_match_score else "needs_tailoring"
    return {
        **result.model_dump(),
        "decision": decision,
        "threshold": request.min_match_score,
    }


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


@app.post("/resumes/analyze", response_model=ResumeAnalyzeResponse)
def analyze_resume(request: ResumeAnalyzeRequest):
    return analyze_resume_text(request.resume_text, request.job_description)


@app.post("/resumes", response_model=ResumeRecord)
def create_resume(resume: ResumeCreate):
    user_id = ensure_demo_user_id()
    analysis = analyze_resume_text(resume.resume_text, resume.job_description)
    row = execute_one(
        """
        INSERT INTO resumes (user_id, title, storage_url, parsed_text, parsed_json, ats_score, is_active)
        VALUES (:user_id, :title, :storage_url, :parsed_text, CAST(:parsed_json AS jsonb), :ats_score, true)
        RETURNING id::text AS id, title, ats_score::int AS ats_score, created_at::text AS created_at
        """,
        {
            "user_id": user_id,
            "title": resume.title,
            "storage_url": f"inline://{hashlib.sha256(resume.resume_text.encode('utf-8')).hexdigest()}",
            "parsed_text": resume.resume_text,
            "parsed_json": json.dumps(analysis.model_dump()),
            "ats_score": analysis.ats_score,
        },
    )
    return ResumeRecord(**row)


@app.get("/resumes", response_model=list[ResumeRecord])
def list_resumes():
    user_id = ensure_demo_user_id()
    rows = fetch_all(
        """
        SELECT id::text AS id, title, ats_score::int AS ats_score, created_at::text AS created_at
        FROM resumes
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        LIMIT 25
        """,
        {"user_id": user_id},
    )
    return [ResumeRecord(**row) for row in rows]


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
