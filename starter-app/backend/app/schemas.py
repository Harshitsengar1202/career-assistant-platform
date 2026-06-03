from pydantic import BaseModel, Field
from typing import Literal


class Job(BaseModel):
    id: str
    company: str
    title: str
    location: str
    match_score: int = Field(ge=0, le=100)
    salary: str | None = None
    source: str


class JobCreate(BaseModel):
    company: str
    title: str
    location: str = "Remote"
    salary_min: float | None = None
    salary_max: float | None = None
    description: str = ""
    source: str = "Manual"
    source_url: str = "https://example.com/job"


class Application(BaseModel):
    id: str
    company: str
    title: str
    status: Literal["saved", "applied", "screening", "interview", "offer", "rejected"]
    match_score: int
    notes: str = ""


class ApplicationCreate(BaseModel):
    job_id: str
    status: Literal["saved", "applied", "screening", "interview", "offer", "rejected"] = "saved"
    match_score: int = Field(default=80, ge=0, le=100)
    notes: str = ""


class ApplicationStatusUpdate(BaseModel):
    status: Literal["saved", "applied", "screening", "interview", "offer", "rejected"]
    notes: str | None = None


class AutoApplyRequest(BaseModel):
    daily_limit: int = Field(default=10, ge=1, le=100)
    approval_mode: bool = True
    min_match_score: int = Field(default=75, ge=0, le=100)
