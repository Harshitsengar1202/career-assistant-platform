const jobs = [
  { company: "Northstar AI", title: "Machine Learning Engineer", location: "Remote", score: 92, source: "LinkedIn" },
  { company: "CloudPath", title: "Backend Engineer", location: "Bengaluru", score: 86, source: "Company Portal" },
  { company: "TalentOS", title: "Full Stack Developer", location: "Hybrid", score: 81, source: "Indeed" }
];

const API_BASE = "https://career-assistant-platform-production.up.railway.app";

const response = await fetch(`${API_BASE}/jobs/recommended`);
const jobs = await response.json();
const root = document.querySelector("#jobs");
root.innerHTML = jobs.map(job => `
  <article class="job">
    <div>
      <h2>${job.title}</h2>
      <p>${job.company} · ${job.location} · ${job.source}</p>
    </div>
    <div class="score">${job.score}</div>
  </article>
`).join("");
