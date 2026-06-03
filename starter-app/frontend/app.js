const API_BASE = "https://career-assistant-platform-production.up.railway.app";

const titles = {
  dashboard: ["Dashboard", "Ranked jobs, resume intelligence, and controlled AI application workflows."],
  resume: ["Resume", "Upload a PDF, analyze ATS fit, and generate a tailored resume draft."],
  jobs: ["Jobs", "Fetch realtime jobs from public job APIs and save matches to your database."],
  pipeline: ["Pipeline", "Track saved, applied, screening, interview, offer, and rejected applications."],
  agents: ["Agents", "Generate cover letters, interview prep, outreach, and approval-mode action plans."]
};

const fallbackJobs = [
  { id: "job_1", company: "Northstar AI", title: "Machine Learning Engineer", location: "Remote", match_score: 92, source: "Sample" },
  { id: "job_2", company: "CloudPath", title: "Backend Engineer", location: "Bengaluru", match_score: 86, source: "Sample" },
  { id: "job_3", company: "TalentOS", title: "Full Stack Developer", location: "Hybrid", match_score: 81, source: "Sample" }
];

const stages = ["saved", "applied", "screening", "interview", "offer", "rejected"];
let currentJobs = [];
let currentApplications = [];
let latestAtsScore = "--";

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `API returned ${response.status}`);
  }
  return response;
}

function showView(view) {
  document.querySelectorAll(".view").forEach((section) => section.classList.remove("active"));
  document.querySelector(`#view-${view}`).classList.add("active");
  document.querySelectorAll("nav button").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  document.querySelector("#page-title").textContent = titles[view][0];
  document.querySelector("#page-subtitle").textContent = titles[view][1];

  if (view === "pipeline") loadApplications();
  if (view === "jobs") loadSavedJobs();
}

async function loadAgentStatus() {
  try {
    const response = await api("/agents/status");
    const status = await response.json();
    document.querySelector("#metric-ai").textContent = status.openai_enabled ? "OpenAI" : "Fallback";
    return status;
  } catch {
    document.querySelector("#metric-ai").textContent = "Offline";
    return null;
  }
}

async function loadSavedJobs() {
  try {
    const response = await api("/jobs/recommended");
    currentJobs = await response.json();
  } catch {
    currentJobs = fallbackJobs;
  }
  renderJobs(currentJobs, "#jobs");
  renderJobs(currentJobs.slice(0, 3), "#dashboard-jobs");
  document.querySelector("#metric-jobs").textContent = currentJobs.length;
}

async function loadLiveJobs(save = false) {
  const query = document.querySelector("#job-query").value.trim() || "software engineer";
  const encodedQuery = encodeURIComponent(query);
  const limit = Number(document.querySelector("#job-limit").value || 25);
  try {
    if (save) {
      const response = await api("/jobs/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, location: document.querySelector("#job-location").value, limit })
      });
      currentJobs = await response.json();
    } else {
      const response = await api(`/jobs/live?query=${encodedQuery}&limit=${limit}`);
      currentJobs = await response.json();
    }
    renderJobs(currentJobs, "#jobs");
    document.querySelector("#metric-jobs").textContent = currentJobs.length;
  } catch (error) {
    alert(`Could not fetch live jobs: ${error.message}`);
  }
}

function renderJobs(jobs, selector) {
  const root = document.querySelector(selector);
  root.innerHTML = jobs.length ? jobs.map((job, index) => `
    <article class="job">
      <div>
        <h2>${job.title}</h2>
        <p>${job.company} - ${job.location} - ${job.source}${job.salary ? ` - ${job.salary}` : ""}</p>
      </div>
      <div class="job-actions">
        <div class="score">${job.match_score}</div>
        <button data-save-job="${index}">Save</button>
      </div>
    </article>
  `).join("") : `<p>No jobs loaded yet. Use Fetch and save.</p>`;

  root.querySelectorAll("[data-save-job]").forEach((button) => {
    button.addEventListener("click", () => saveApplication(jobs[Number(button.dataset.saveJob)]));
  });
}

async function saveApplication(job) {
  if (!job.id || job.id.startsWith("job_") || job.id.startsWith("live_")) {
    alert("Preview/sample jobs must be fetched and saved first. Use Jobs > Fetch and save.");
    return;
  }

  try {
    await api("/applications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_id: job.id,
        status: "saved",
        match_score: job.match_score,
        notes: "Saved from dashboard"
      })
    });
    alert("Saved to pipeline.");
    await loadApplications();
  } catch (error) {
    alert(`Could not save application: ${error.message}`);
  }
}

async function loadApplications() {
  try {
    const response = await api("/applications");
    currentApplications = await response.json();
  } catch {
    currentApplications = [];
  }
  document.querySelector("#metric-apps").textContent = currentApplications.length;
  renderPipeline();
  renderDashboardPipeline();
}

function renderPipeline() {
  const board = document.querySelector("#pipeline-board");
  board.innerHTML = stages.map((stage) => {
    const items = currentApplications.filter((application) => application.status === stage);
    return `
      <div class="stage">
        <h3>${stage}</h3>
        ${items.map((item) => `
          <article class="pipeline-card">
            <strong>${item.company}</strong>
            <p>${item.title}</p>
            <small>Match ${item.match_score}</small>
            <select data-application-status="${item.id}">
              ${stages.map((option) => `<option value="${option}" ${option === item.status ? "selected" : ""}>${option}</option>`).join("")}
            </select>
          </article>
        `).join("") || "<p>No applications</p>"}
      </div>
    `;
  }).join("");

  board.querySelectorAll("[data-application-status]").forEach((select) => {
    select.addEventListener("change", () => updateApplicationStatus(select.dataset.applicationStatus, select.value));
  });
}

function renderDashboardPipeline() {
  const root = document.querySelector("#dashboard-pipeline");
  root.innerHTML = currentApplications.slice(0, 5).map((item) => `
    <article class="mini-item">
      <strong>${item.company}</strong>
      <span>${item.title} - ${item.status}</span>
    </article>
  `).join("") || "<p>No pipeline records yet.</p>";
}

async function updateApplicationStatus(id, status) {
  try {
    await api(`/applications/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status })
    });
    await loadApplications();
  } catch (error) {
    alert(`Could not update status: ${error.message}`);
  }
}

async function analyzeResume(save = false) {
  const resumeText = document.querySelector("#resume-text").value.trim();
  const jobDescription = document.querySelector("#job-description").value.trim();
  if (resumeText.length < 50) {
    alert("Paste at least 50 characters of resume text or upload a PDF.");
    return;
  }

  const endpoint = save ? "/resumes" : "/resumes/analyze";
  const body = save
    ? { title: "Dashboard Resume", resume_text: resumeText, job_description: jobDescription }
    : { resume_text: resumeText, job_description: jobDescription };

  try {
    const response = await api(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const result = await response.json();
    if (save) {
      alert(`Saved resume score: ${result.ats_score ?? "ready"}`);
      return;
    }
    renderResumeAnalysis(result);
  } catch (error) {
    alert(`Resume analysis failed: ${error.message}`);
  }
}

function renderResumeAnalysis(result) {
  latestAtsScore = result.ats_score;
  document.querySelector("#metric-ats").textContent = latestAtsScore;
  document.querySelector("#resume-score").textContent = result.ats_score;
  document.querySelector("#resume-summary").textContent =
    `${result.word_count} words. Matched ${result.matched_keywords.length} keywords, missing ${result.missing_keywords.length}.`;
  document.querySelector("#resume-suggestions").innerHTML =
    result.suggestions.map((suggestion) => `<li>${suggestion}</li>`).join("");
}

async function uploadResumePdf() {
  const file = document.querySelector("#resume-pdf").files[0];
  if (!file) {
    alert("Choose a PDF resume first.");
    return;
  }
  const formData = new FormData();
  formData.append("file", file);
  formData.append("title", file.name.replace(/\.pdf$/i, ""));
  formData.append("job_description", document.querySelector("#job-description").value.trim());

  try {
    const response = await api("/resumes/upload-pdf", { method: "POST", body: formData });
    const result = await response.json();
    document.querySelector("#resume-text").value = result.extracted_text;
    renderResumeAnalysis(result.analysis);
    alert("PDF uploaded and analyzed.");
  } catch (error) {
    alert(`PDF upload failed: ${error.message}`);
  }
}

async function tailorResume() {
  const resumeText = document.querySelector("#resume-text").value.trim();
  const jobDescription = document.querySelector("#job-description").value.trim();
  if (resumeText.length < 50 || jobDescription.length < 30) {
    alert("Add resume text and a job description before tailoring.");
    return;
  }

  try {
    const response = await api("/resumes/tailor", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_text: resumeText, job_description: jobDescription })
    });
    const result = await response.json();
    document.querySelector("#tailored-output").textContent = [
      `Provider: ${result.provider}`,
      `ATS score: ${result.ats_score}`,
      "",
      "Tailored Summary",
      result.tailored_summary,
      "",
      "Optimized Bullets",
      ...result.optimized_bullets.map((item) => `- ${item}`),
      "",
      "Missing Keywords",
      result.missing_keywords.join(", ") || "None"
    ].join("\n");
  } catch (error) {
    alert(`Tailoring failed: ${error.message}`);
  }
}

function kitPayload() {
  const company = document.querySelector("#kit-company").value.trim();
  const role = document.querySelector("#kit-role").value.trim();
  const resumeSummary = document.querySelector("#resume-text").value.trim();
  const jobDescription = document.querySelector("#job-description").value.trim();
  const tone = document.querySelector("#kit-tone").value;

  if (company.length < 2 || role.length < 2) {
    alert("Add a company and role first.");
    return null;
  }
  if (resumeSummary.length < 30 || jobDescription.length < 30) {
    alert("Paste resume text and job description before generating.");
    return null;
  }
  return { company, role, resume_summary: resumeSummary, job_description: jobDescription, tone };
}

async function generateKit(endpoint, render) {
  const payload = kitPayload();
  if (!payload) return;
  try {
    const response = await api(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    render(await response.json());
  } catch (error) {
    alert(`Generation failed: ${error.message}`);
  }
}

async function runAgents() {
  const payload = kitPayload();
  if (!payload) return;
  try {
    const response = await api("/agents/full-run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company: payload.company,
        role: payload.role,
        resume_text: payload.resume_summary,
        job_description: payload.job_description,
        tone: payload.tone,
        min_match_score: 75
      })
    });
    const result = await response.json();
    document.querySelector("#agent-output").textContent = [
      `Provider: ${result.provider}`,
      `Decision: ${result.decision}`,
      `Match score: ${result.job_match.match_score}/${result.threshold}`,
      "",
      "Fit Summary",
      result.job_match.fit_summary,
      "",
      "Tailored Summary",
      result.resume.tailored_summary,
      "",
      "Optimized Resume Bullets",
      ...result.resume.optimized_bullets.map((item) => `- ${item}`),
      "",
      "Cover Letter",
      result.application_kit.cover_letter,
      "",
      "Interview Questions",
      ...result.application_kit.interview_questions.map((item, index) => `${index + 1}. ${item}`),
      "",
      "Auto-Apply Plan",
      ...result.auto_apply_plan.map((item) => `- ${item}`),
      "",
      "Safety Checks",
      ...result.safety_checks.map((item) => `- ${item}`)
    ].join("\n");
  } catch (error) {
    alert(`Agent run failed: ${error.message}`);
  }
}

async function checkAgentStatus() {
  const status = await loadAgentStatus();
  if (status) {
    document.querySelector("#agent-output").textContent =
      `AI mode: ${status.mode}\nOpenAI enabled: ${status.openai_enabled}\nModel: ${status.model}`;
  }
}

function bindEvents() {
  document.querySelectorAll("nav button[data-view]").forEach((button) => {
    button.addEventListener("click", () => showView(button.dataset.view));
  });
  document.querySelectorAll("[data-view-jump]").forEach((button) => {
    button.addEventListener("click", () => showView(button.dataset.viewJump));
  });
  document.querySelector("#refresh-all").addEventListener("click", refreshAll);
  document.querySelector("#load-live-jobs").addEventListener("click", () => loadLiveJobs(false));
  document.querySelector("#refresh-jobs").addEventListener("click", () => loadLiveJobs(true));
  document.querySelector("#export-pipeline").addEventListener("click", () => {
    window.location.href = `${API_BASE}/exports/applications.csv`;
  });
  document.querySelector("#upload-resume").addEventListener("click", uploadResumePdf);
  document.querySelector("#analyze-resume").addEventListener("click", () => analyzeResume(false));
  document.querySelector("#save-resume").addEventListener("click", () => analyzeResume(true));
  document.querySelector("#tailor-resume").addEventListener("click", tailorResume);
  document.querySelector("#generate-cover").addEventListener("click", () => {
    generateKit("/ai/cover-letter", (result) => {
      document.querySelector("#kit-output").textContent = result.cover_letter;
    });
  });
  document.querySelector("#generate-interview").addEventListener("click", () => {
    generateKit("/ai/interview-prep", (result) => {
      document.querySelector("#kit-output").textContent = [
        "Interview Questions",
        ...result.questions.map((question, index) => `${index + 1}. ${question}`),
        "",
        "Answer Tips",
        ...result.answer_tips.map((tip) => `- ${tip}`)
      ].join("\n");
    });
  });
  document.querySelector("#generate-outreach").addEventListener("click", () => {
    generateKit("/ai/outreach", (result) => {
      document.querySelector("#kit-output").textContent =
        `LinkedIn Note\n\n${result.linkedin_note}\n\nCold Email\n\n${result.cold_email}\n\nFollow Up\n\n${result.follow_up}`;
    });
  });
  document.querySelector("#run-agents").addEventListener("click", runAgents);
  document.querySelector("#check-agent-status").addEventListener("click", checkAgentStatus);
}

async function refreshAll() {
  await Promise.allSettled([loadAgentStatus(), loadSavedJobs(), loadApplications()]);
}

bindEvents();
refreshAll();
