import os

from pydantic import BaseModel, Field


OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class AgentResumeOutput(BaseModel):
    ats_score: int = Field(ge=0, le=100)
    matched_keywords: list[str]
    missing_keywords: list[str]
    suggestions: list[str]
    tailored_summary: str
    optimized_bullets: list[str]
    provider: str


class AgentApplicationKitOutput(BaseModel):
    cover_letter: str
    interview_questions: list[str]
    answer_tips: list[str]
    linkedin_note: str
    cold_email: str
    follow_up: str
    provider: str


class AgentJobMatchOutput(BaseModel):
    match_score: int = Field(ge=0, le=100)
    fit_summary: str
    strengths: list[str]
    gaps: list[str]
    recommended_action: str
    provider: str


class AgentRunOutput(BaseModel):
    resume: AgentResumeOutput
    application_kit: AgentApplicationKitOutput
    job_match: AgentJobMatchOutput
    auto_apply_plan: list[str]
    safety_checks: list[str]
    provider: str


def openai_ready() -> bool:
    return bool(OPENAI_API_KEY)


def call_openai_structured(prompt: str, output_model: type[BaseModel]):
    if not openai_ready():
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.responses.parse(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are an enterprise career assistant AI. Return accurate, concise, "
                        "job-search material grounded only in the user's resume and job description. "
                        "Do not invent credentials, employers, degrees, certifications, or metrics. "
                        "Set provider to 'openai'."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            text_format=output_model,
            store=False,
        )
        parsed = response.output_parsed
        parsed.provider = f"openai:{OPENAI_MODEL}"
        return parsed
    except Exception:
        return None


def fallback_resume_agent(resume_text: str, job_description: str, analysis) -> AgentResumeOutput:
    summary_keywords = ", ".join(analysis.matched_keywords[:5]) or "relevant experience"
    tailored_summary = (
        f"Candidate with experience aligned to {summary_keywords}, focused on measurable delivery, "
        "clear communication, and maintainable execution."
    )
    optimized_bullets = [
        f"Applied {keyword} to deliver role-relevant outcomes for business and technical stakeholders."
        for keyword in analysis.matched_keywords[:5]
    ] or [
        "Delivered measurable improvements by translating requirements into reliable implementation.",
        "Collaborated with stakeholders to prioritize work, reduce ambiguity, and improve execution quality.",
    ]
    return AgentResumeOutput(
        ats_score=analysis.ats_score,
        matched_keywords=analysis.matched_keywords,
        missing_keywords=analysis.missing_keywords,
        suggestions=analysis.suggestions,
        tailored_summary=tailored_summary,
        optimized_bullets=optimized_bullets,
        provider="fallback",
    )


def fallback_application_kit(company: str, role: str, resume_summary: str, job_description: str, tone: str, strengths: list[str]) -> AgentApplicationKitOutput:
    strength_text = ", ".join(strengths[:4]) or "role-relevant execution"
    cover_letter = (
        f"Dear {company} hiring team,\n\n"
        f"I am interested in the {role} role at {company}. My background aligns with {strength_text}, "
        "and I am comfortable turning requirements into reliable, maintainable outcomes.\n\n"
        "I would welcome the opportunity to discuss how my experience can support your team.\n\n"
        "Sincerely,\nYour Name"
    )
    questions = [
        f"Why are you interested in the {role} role at {company}?",
        f"Which past project best proves your ability to succeed as a {role}?",
        f"How have you used {strengths[0] if strengths else 'your core skills'} in a real project?",
        "Tell me about a time you improved quality, speed, or reliability.",
        "What would you prioritize in your first 30 days?",
        "Where would you need to ramp up for this role?",
        "Describe a time you handled ambiguity.",
        "How do you collaborate with non-technical stakeholders?",
    ]
    tips = [
        "Use STAR format and end each answer with the result.",
        "Use only truthful metrics and concrete examples.",
        "Connect each answer to the target role's responsibilities.",
        "Prepare one story for impact, conflict, failure, leadership, and technical depth.",
    ]
    return AgentApplicationKitOutput(
        cover_letter=cover_letter,
        interview_questions=questions,
        answer_tips=tips,
        linkedin_note=(
            f"Hi, I noticed the {role} opening at {company}. My background aligns with {strength_text}. "
            "I would appreciate any advice on the best way to be considered."
        ),
        cold_email=(
            f"Subject: Interest in {role} at {company}\n\n"
            f"Hello,\n\nI am reaching out about the {role} role at {company}. "
            f"My experience aligns with {strength_text}, and I would be grateful for any guidance on the hiring process.\n\n"
            "Best,\nYour Name"
        ),
        follow_up=(
            f"Hello, I wanted to follow up on my interest in the {role} role at {company}. "
            "I remain interested and would be glad to share more context on my fit."
        ),
        provider="fallback",
    )


def fallback_job_match(company: str, role: str, analysis) -> AgentJobMatchOutput:
    gaps = analysis.missing_keywords[:6]
    strengths = analysis.matched_keywords[:6]
    if analysis.ats_score >= 80:
        action = "Apply now with tailored resume and targeted cover letter."
    elif analysis.ats_score >= 60:
        action = "Tailor resume before applying, then submit after reviewing keyword gaps."
    else:
        action = "Do not auto-apply yet; improve resume alignment first."
    return AgentJobMatchOutput(
        match_score=analysis.ats_score,
        fit_summary=f"Fit for {role} at {company} is estimated at {analysis.ats_score}/100 based on keyword and structure alignment.",
        strengths=strengths,
        gaps=gaps,
        recommended_action=action,
        provider="fallback",
    )


def resume_agent(resume_text: str, job_description: str, analysis) -> AgentResumeOutput:
    prompt = f"""
    Resume:
    {resume_text}

    Job description:
    {job_description}

    Current deterministic analysis:
    ATS score: {analysis.ats_score}
    Matched keywords: {analysis.matched_keywords}
    Missing keywords: {analysis.missing_keywords}

    Produce ATS scoring, truthful missing keywords, targeted suggestions, a tailored summary, and optimized resume bullets.
    """
    return call_openai_structured(prompt, AgentResumeOutput) or fallback_resume_agent(resume_text, job_description, analysis)


def application_kit_agent(company: str, role: str, resume_summary: str, job_description: str, tone: str, strengths: list[str]) -> AgentApplicationKitOutput:
    prompt = f"""
    Company: {company}
    Role: {role}
    Tone: {tone}

    Resume summary:
    {resume_summary}

    Job description:
    {job_description}

    Generate a truthful cover letter, interview prep, LinkedIn note, cold email, and follow-up.
    """
    return call_openai_structured(prompt, AgentApplicationKitOutput) or fallback_application_kit(
        company, role, resume_summary, job_description, tone, strengths
    )


def job_match_agent(company: str, role: str, resume_text: str, job_description: str, analysis) -> AgentJobMatchOutput:
    prompt = f"""
    Company: {company}
    Role: {role}

    Resume:
    {resume_text}

    Job description:
    {job_description}

    Score fit, explain strengths and gaps, and recommend whether to apply now, tailor first, or skip.
    """
    return call_openai_structured(prompt, AgentJobMatchOutput) or fallback_job_match(company, role, analysis)


def full_agent_run(company: str, role: str, resume_text: str, job_description: str, tone: str, analysis) -> AgentRunOutput:
    resume = resume_agent(resume_text, job_description, analysis)
    job_match = job_match_agent(company, role, resume_text, job_description, analysis)
    application_kit = application_kit_agent(
        company,
        role,
        resume.tailored_summary,
        job_description,
        tone,
        resume.matched_keywords,
    )
    auto_apply_plan = [
        "Confirm the job source URL and verify the role is still open.",
        "Review tailored summary and optimized bullets for truthfulness.",
        "Submit only if match score meets your threshold and no missing must-have requirement is critical.",
        "Save the application to the pipeline before or immediately after submission.",
        "Schedule follow-up reminder for 5-7 business days after applying.",
    ]
    safety_checks = [
        "Human approval required before any external submission.",
        "No invented credentials, certifications, employers, or metrics.",
        "Duplicate application check required before submit.",
        "Respect job-site terms and do not bypass anti-bot protections.",
    ]
    provider = "openai" if openai_ready() else "fallback"
    return AgentRunOutput(
        resume=resume,
        application_kit=application_kit,
        job_match=job_match,
        auto_apply_plan=auto_apply_plan,
        safety_checks=safety_checks,
        provider=provider,
    )
