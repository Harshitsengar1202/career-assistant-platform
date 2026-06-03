import html
import re
from datetime import datetime, timezone

import httpx


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


async def fetch_remotive_jobs(query: str, limit: int) -> list[dict]:
    url = "https://remotive.com/api/remote-jobs"
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(url, params={"search": query, "limit": limit})
        response.raise_for_status()
        data = response.json()

    jobs = []
    for item in data.get("jobs", [])[:limit]:
        jobs.append(
            {
                "company": item.get("company_name") or "Unknown Company",
                "title": item.get("title") or "Untitled Role",
                "location": item.get("candidate_required_location") or "Remote",
                "source": "Remotive",
                "source_url": item.get("url") or item.get("job_url") or "https://remotive.com",
                "description": strip_html(item.get("description")),
                "salary_min": None,
                "salary_max": None,
            }
        )
    return jobs


async def fetch_arbeitnow_jobs(query: str, limit: int) -> list[dict]:
    url = "https://www.arbeitnow.com/api/job-board-api"
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

    terms = [term for term in re.split(r"\s+", query.lower()) if term]
    raw_jobs = data.get("data", []) if isinstance(data, dict) else []
    jobs = []
    for item in raw_jobs:
        searchable = " ".join(
            [
                str(item.get("title") or ""),
                str(item.get("company_name") or ""),
                " ".join(item.get("tags") or []),
                strip_html(item.get("description")),
            ]
        ).lower()
        if terms and not any(term in searchable for term in terms):
            continue
        jobs.append(
            {
                "company": item.get("company_name") or "Unknown Company",
                "title": item.get("title") or "Untitled Role",
                "location": item.get("location") or ("Remote" if item.get("remote") else "Not specified"),
                "source": "Arbeitnow",
                "source_url": item.get("url") or "https://www.arbeitnow.com",
                "description": strip_html(item.get("description")),
                "salary_min": None,
                "salary_max": None,
            }
        )
        if len(jobs) >= limit:
            break
    return jobs


async def fetch_live_jobs(query: str, limit: int = 25) -> list[dict]:
    per_source = max(5, limit // 2)
    results = []
    for fetcher in (fetch_remotive_jobs, fetch_arbeitnow_jobs):
        try:
            results.extend(await fetcher(query, per_source))
        except Exception:
            continue

    seen = set()
    unique_jobs = []
    for job in results:
        key = f"{job['company']}|{job['title']}|{job['source_url']}".lower()
        if key in seen:
            continue
        seen.add(key)
        job["discovered_at"] = datetime.now(timezone.utc).isoformat()
        unique_jobs.append(job)
        if len(unique_jobs) >= limit:
            break
    return unique_jobs
