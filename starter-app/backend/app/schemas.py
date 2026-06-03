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


class Application(BaseModel):
    id: str
    company: str
    title: str
    status: Literal["saved", "applied", "screening", "interview", "offer", "rejected"]
    match_score: int
    notes: str = ""


class AutoApplyRequest(BaseModel):
    daily_limit: int = Field(default=10, ge=1, le=100)
    approval_mode: bool = True
    min_match_score: int = Field(default=75, ge=0, le=100)
