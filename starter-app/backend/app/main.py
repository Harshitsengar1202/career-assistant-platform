from fastapi import FastAPI
from .schemas import Application, AutoApplyRequest, Job

app = FastAPI(title="AI Career Assistant API", version="0.1.0")

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


@app.get("/jobs/recommended", response_model=list[Job])
def recommended_jobs():
    return SAMPLE_JOBS


@app.get("/applications", response_model=list[Application])
def applications():
    return SAMPLE_APPLICATIONS


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
