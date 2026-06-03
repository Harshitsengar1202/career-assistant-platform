# User Stories and Acceptance Criteria

## Epic 1: Account and Profile

- As a job seeker, I want to create an account with email or OAuth so that my career data is saved securely.
  - Acceptance: registration validates email, stores hashed password, creates profile, and sends verification.
  - Acceptance: Google OAuth creates or links an account with explicit consent.

- As a job seeker, I want to maintain skills, experience, education, links, and preferences so that recommendations match my background.
  - Acceptance: profile changes are versioned and reflected in future job ranking.

## Epic 2: Resume Intelligence

- As a job seeker, I want to upload multiple resumes so that I can reuse role-specific versions.
  - Acceptance: upload stores the file, parses sections, extracts keywords, and marks the active version.

- As a job seeker, I want an ATS score and missing keyword list so that I can improve my resume before applying.
  - Acceptance: score includes rationale, missing terms, and recommended edits.

- As a job seeker, I want to tailor a resume to a job description so that my application is more relevant.
  - Acceptance: tailored version can be compared against the original and edited before export.

## Epic 3: Job Discovery and Ranking

- As a job seeker, I want fresh jobs discovered continuously so that I do not miss early postings.
  - Acceptance: new jobs are timestamped, deduplicated, and filtered by user preferences.

- As a job seeker, I want ranked recommendations so that I can focus on the best-fit roles.
  - Acceptance: each recommendation shows match score, matching skills, missing skills, location fit, and salary fit when available.

## Epic 4: Controlled Auto-Apply

- As a job seeker, I want to set daily application limits so that automation stays within my preferences.
  - Acceptance: workers stop when limits are reached and record skipped jobs.

- As a job seeker, I want the system to fill application forms and prepare answers so that I can approve faster.
  - Acceptance: application packages include selected resume, generated responses, and a pre-submit review state.

- As a job seeker, I want duplicate prevention so that I never apply twice to the same role.
  - Acceptance: duplicate detection checks normalized company, role, location, source URL, and external ID.

## Epic 5: Pipeline Management

- As a job seeker, I want a Kanban board so that I can track application progress.
  - Acceptance: stages include Saved, Applied, Screening, Interview, Offer, and Rejected.

- As a job seeker, I want notes and activity history so that every interaction is traceable.
  - Acceptance: status changes, notes, agent actions, and interview events appear in chronological history.

## Epic 6: Interview and Outreach

- As a job seeker, I want interview Q&A generated from the job and my resume so that I can prepare efficiently.
  - Acceptance: generated packs include behavioral, HR, and technical questions with editable answers.

- As a job seeker, I want outreach templates so that I can contact recruiters and request referrals.
  - Acceptance: templates support LinkedIn note, cold email, referral request, and follow-up.

## Epic 7: Admin, Observability, and Compliance

- As an administrator, I want agent run logs so that failures and costs can be investigated.
  - Acceptance: every run stores status, task type, timestamps, tokens/cost estimate, and error trace.

- As a user, I want export and deletion controls so that I can manage my personal data.
  - Acceptance: exports include application records, notes, and generated assets; deletion removes or anonymizes personal data according to policy.
