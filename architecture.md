# Architecture Package

## Context

```mermaid
flowchart LR
  User[Job Seeker] --> Web[Web App]
  Web --> API[API Gateway / Backend]
  API --> DB[(PostgreSQL)]
  API --> Files[(Object Storage)]
  API --> Queue[(Redis / RabbitMQ)]
  Queue --> Workers[AI + Automation Workers]
  Workers --> AI[AI Provider APIs]
  Workers --> Browser[Playwright Browser Workers]
  Workers --> JobSites[Job Platforms]
  API --> Email[Email APIs]
  API --> Calendar[Calendar APIs]
```

## AI Agent Flow

```mermaid
sequenceDiagram
  participant U as User
  participant API as Backend API
  participant Q as Queue
  participant R as Resume Agent
  participant J as Job Agent
  participant A as Apply Agent
  participant Log as Audit Log

  U->>API: Upload resume + preferences
  API->>Q: enqueue resume_parse
  Q->>R: run parsing and ATS analysis
  R->>Log: store score, gaps, source trace
  API->>Q: enqueue job_discovery
  Q->>J: ingest, dedupe, rank jobs
  J->>Log: store match rationale
  U->>API: approve auto-apply policy
  API->>Q: enqueue controlled_apply
  Q->>A: prepare application package
  A->>Log: record attempt, result, artifacts
```

## Logical Components

```mermaid
graph TD
  Dashboard --> RecommendationUI
  Dashboard --> Kanban
  Dashboard --> ResumeAnalyzer
  API --> Auth
  API --> ResumeService
  API --> JobService
  API --> ApplicationService
  API --> AgentOrchestrator
  AgentOrchestrator --> ResumeIntelligence
  AgentOrchestrator --> JobMatching
  AgentOrchestrator --> AutoApply
  AgentOrchestrator --> InterviewPrep
  AgentOrchestrator --> Outreach
```

## Deployment

```mermaid
flowchart TB
  CDN[CDN / Frontend Hosting] --> LB[Load Balancer]
  LB --> API1[API Pod]
  LB --> API2[API Pod]
  API1 --> PG[(Managed PostgreSQL)]
  API2 --> PG
  API1 --> Redis[(Redis)]
  API2 --> Redis
  Redis --> Worker1[Worker Pod]
  Redis --> Worker2[Browser Worker Pod]
  Worker2 --> Chromium[Headless Chromium]
  API1 --> S3[(S3 / R2)]
  Worker1 --> S3
  Observability[Prometheus / Grafana / Sentry] --> API1
  Observability --> Worker1
```

## Governance Notes

- Default to approval-mode application automation until site-specific compliance is validated.
- Store every agent run with input hashes, outputs, status, cost, latency, and error details.
- Use provider abstraction for AI calls so models can be swapped without changing product workflows.
- Separate browser workers from API pods for security, cost control, and blast-radius containment.
