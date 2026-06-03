const API_BASE = "https://career-assistant-platform-production.up.railway.app";

const fallbackJobs = [
  { company: "Northstar AI", title: "Machine Learning Engineer", location: "Remote", match_score: 92, source: "LinkedIn" },
  { company: "CloudPath", title: "Backend Engineer", location: "Bengaluru", match_score: 86, source: "Company Portal" },
  { company: "TalentOS", title: "Full Stack Developer", location: "Hybrid", match_score: 81, source: "Indeed" }
];

async function loadJobs() {
  try {
    const response = await fetch(`${API_BASE}/jobs/recommended`);
    if (!response.ok) throw new Error(`API returned ${response.status}`);
    return await response.json();
  } catch (error) {
    console.warn("Using local sample jobs:", error);
    return fallbackJobs;
  }
}

async function saveApplication(job) {
  if (!job.id || job.id.startsWith("job_")) {
    alert("This sample job is not in your database yet. Add real jobs through the API first.");
    return;
  }

  const response = await fetch(`${API_BASE}/applications`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_id: job.id,
      status: "saved",
      match_score: job.match_score,
      notes: "Saved from dashboard"
    })
  });

  if (!response.ok) {
    alert("Could not save application. Check the backend logs.");
    return;
  }

  alert("Saved to pipeline.");
}

function renderJobs(jobs) {
  const root = document.querySelector("#jobs");
  root.innerHTML = jobs.map((job, index) => `
    <article class="job">
      <div>
        <h2>${job.title}</h2>
        <p>${job.company} - ${job.location} - ${job.source}${job.salary ? ` - ${job.salary}` : ""}</p>
      </div>
      <div class="job-actions">
        <div class="score">${job.match_score}</div>
        <button data-job-index="${index}">Save</button>
      </div>
    </article>
  `).join("");

  root.querySelectorAll("[data-job-index]").forEach((button) => {
    button.addEventListener("click", () => saveApplication(jobs[Number(button.dataset.jobIndex)]));
  });
}

async function analyzeResume(save = false) {
  const resumeText = document.querySelector("#resume-text").value.trim();
  const jobDescription = document.querySelector("#job-description").value.trim();

  if (resumeText.length < 50) {
    alert("Paste at least 50 characters of resume text.");
    return;
  }

  const endpoint = save ? "/resumes" : "/resumes/analyze";
  const body = save
    ? { title: "Dashboard Resume", resume_text: resumeText, job_description: jobDescription }
    : { resume_text: resumeText, job_description: jobDescription };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    alert("Resume analysis failed. Check the backend logs.");
    return;
  }

  const result = await response.json();
  if (save) {
    alert(`Saved resume score: ${result.ats_score ?? "ready"}`);
    return;
  }

  document.querySelector("#resume-score").textContent = result.ats_score;
  document.querySelector("#resume-summary").textContent =
    `${result.word_count} words. Matched ${result.matched_keywords.length} keywords, missing ${result.missing_keywords.length}.`;
  document.querySelector("#resume-suggestions").innerHTML =
    result.suggestions.map((suggestion) => `<li>${suggestion}</li>`).join("");
}

document.querySelector("#analyze-resume").addEventListener("click", () => analyzeResume(false));
document.querySelector("#save-resume").addEventListener("click", () => analyzeResume(true));

loadJobs().then(renderJobs);
