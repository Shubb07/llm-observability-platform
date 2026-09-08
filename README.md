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
developers and AI teams. See [`docs/PRD.pdf`](docs/PRD.pdf) for product requirements and
[`docs/HLD.md`](docs/HLD.md) for the current architecture and build order
(supersedes the original [`docs/HLD.pdf`](docs/HLD.pdf) draft).

## Repository layout

```
llm-observability-platform/
├── sdk/          Python SDK — wraps LLM provider calls, captures + batches telemetry
├── backend/      Backend API, storage models, background workers, evaluation, alerting, auth
├── dashboard/    React dashboard — Trace Explorer, analytics, evaluations, alert config
├── infra/        Deployment/local-dev infra (docker-compose, DB migrations, etc.)
└── docs/         PRD, HLD, and other design docs
```

## Stack

- **SDK:** Python — **built**: OpenAI/Anthropic auto-instrumentation, manual `trace()` for
  other providers, background batching with retry/backoff
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL — **built**: auth, projects, trace
  ingestion/query. Celery/Redis for background workers deferred until evaluation volume
  needs independently scalable workers (see `docs/HLD.md` → Scalability)
- **Dashboard:** React (Vite) — not started
- **Auth:** JWT for dashboard users, API keys for SDK → backend ingestion — **built**

## Status

Backend v1 and the SDK are implemented and tested (see [`backend/README.md`](backend/README.md)
and [`sdk/README.md`](sdk/README.md) for how to run each). Dashboard has not been started.
See [`docs/HLD.md`](docs/HLD.md#build-order) for the planned build order.
