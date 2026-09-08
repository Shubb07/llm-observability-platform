# LLM Observability Platform

Polaris School of Technology — On-the-Job Training (OJT) Project
B.Tech CSE (AI/ML), Batch 2025–2029

**Team:** Shuban Mutagi, Sagar Halladakeri
**Mentor:** Tanmay
**Track:** AI/ML — Generative AI

## What this is

A telemetry platform for LLM-powered applications: a Python SDK captures every LLM call
(prompt, completion, tokens, latency, cost), a backend ingests and stores traces, background
workers run quality evaluations and alert checks, and a dashboard surfaces all of it to
developers and AI teams. See [`docs/PRD.pdf`](docs/PRD.pdf) and [`docs/HLD.pdf`](docs/HLD.pdf)
for the full product requirements and architecture.

## Repository layout

```
llm-observability-platform/
├── sdk/          Python SDK — wraps LLM provider calls, captures + batches telemetry
├── backend/      Backend API, storage models, background workers, evaluation, alerting, auth
├── dashboard/    React dashboard — Trace Explorer, analytics, evaluations, alert config
├── infra/        Deployment/local-dev infra (docker-compose, DB migrations, etc.)
└── docs/         PRD, HLD, and other design docs
```

## Planned stack

- **SDK:** Python (pip-installable, async, provider-agnostic wrapper)
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL, with Celery/Redis for background workers
  once evaluation volume needs independently scalable workers (see HLD → Scalability)
- **Dashboard:** React
- **Auth:** JWT for dashboard users, API keys for SDK → backend ingestion

## Status

Repository scaffold only — implementation has not started yet. See each subfolder's README
for what belongs there.
