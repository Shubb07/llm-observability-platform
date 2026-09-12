# High-Level Design (HLD) — v2

LLM Observability Platform · Polaris School of Technology OJT
Team: Shuban Mutagi, Sagar Halladakeri · Mentor: Tanmay

> Supersedes `HLD.pdf` (v1.0, the original mentor-approved draft, kept as-is for the record).
> This version reflects the architecture actually being built, pinned down once real
> implementation decisions had to be made. Product scope and priorities are unchanged from
> the PRD — this is only a design refinement.

## What changed from v1.0, and why

| v1.0 said | v2 says | Why |
|---|---|---|
| "Backend API" (framework unstated) | FastAPI + SQLAlchemy | Python end-to-end with the SDK; async-native; fastest path to working endpoints |
| "PostgreSQL" (no local-dev story) | Postgres via Docker Compose for dev/prod, SQLite in-memory for tests | Tests shouldn't need Docker running; schema is portable across both |
| Redis/Celery implied early | Explicitly deferred to Phase 4/5, APScheduler as the interim scheduler for alert checks | HLD v1.0's own scalability principle — "introduce a message queue only when evaluation volume requires it" — wasn't being followed by default; this version follows it |
| One "Auth Service" component | Auth lives in `app/api/auth.py` + `app/core/security.py`; `app/auth/` reserved as a placeholder only if it grows (e.g. OAuth) | Reflects the actual module boundary chosen once code existed |
| No phasing | Explicit build order (below), matching PRD Must → Should → Could | Original HLD described the end state but not how to get there incrementally |

## Architecture (unchanged shape, now with real components)

Same telemetry-pipeline shape as v1.0: SDK captures at the source → backend ingests →
workers evaluate/alert → dashboard surfaces it. What's different is every box below now
names a real technology and, where built, a real file.

```
Developer's app
   |  wrapped call
   v
Python SDK  --batched traces-->  FastAPI backend  --write-->  PostgreSQL
   ^                                  |  query                    |
   +--views----------------------  React dashboard <-------------+
                                      |
                             (Phase 4+) background workers
                             --evaluate--> Evaluation Engine
                             --check rules--> Alerting --> Email/Webhook
```

### Components

| Component | Tech | Status |
|---|---|---|
| Python SDK | `pip`-installable package, wraps LLM provider calls, async batching + local buffering with retry/backoff | Not started (Phase 1) |
| Backend API | FastAPI, routers in `backend/app/api/` | **Built** — auth, projects, trace ingestion/query |
| Storage | PostgreSQL (prod/dev via `infra/docker-compose.yml`), SQLite in-memory (tests) | **Built** |
| ORM / models | SQLAlchemy 2.0 (`backend/app/models/`) | **Built** — `User`, `Project`, `ProjectMembership`, `Trace` |
| Auth | JWT (HS256, `python-jose`) for dashboard users; per-project API key for SDK ingestion; `bcrypt` for password hashing | **Built** |
| Dashboard | React (Vite), TanStack Query for data fetching, Recharts for analytics charts | Not started (Phase 2–3) |
| Background workers | APScheduler in-process initially → Celery + Redis once evaluation volume needs independently scalable workers | Not started (Phase 4/5) |
| Evaluation Engine | Heuristic checks (format/regex) + LLM-as-judge scoring against a configurable rubric | Not started (Phase 4) |
| Alerting Service | Rule evaluation (metric, operator, threshold, time window) against recent trace metrics | Not started (Phase 5) |
| Notification Channels | Email (SMTP) + generic webhook POST | Not started (Phase 5) |

## Build order

Phased to match the PRD's Must → Should → Could priorities, and so each phase produces
something the next phase needs (no phase depends on something not yet built).

1. **Backend v1 (built)** — auth, projects (API keys, RBAC), trace ingestion + query. This exists
   so every later phase has something real to talk to.
2. **SDK** — wraps LLM calls, posts to the ingestion endpoint built in step 1. Smallest
   PRD Must-have not yet done; unblocks real trace data for everything after it.
3. **Dashboard: auth + Trace Explorer** — login, project switcher, trace list/filter/detail.
   Needs the SDK generating real traces to be worth building against.
4. **Analytics dashboard** — backend aggregation endpoints (p50/p95/p99 latency, error rate,
   token/cost over time, grouped by model/tag) + Recharts views. Needs trace volume from
   step 2 to be meaningful to look at.
5. **Evaluation engine** — heuristics run synchronously post-ingest at first; LLM-as-judge
   runs via APScheduler polling `PENDING` evaluation jobs. Needs traces (step 2) and a place
   to show scores (step 3's trace detail view).
6. **Alerting** — rule CRUD + APScheduler job checking rules against recent metrics from
   step 4; email/webhook delivery.
7. **Celery + Redis** — only introduced here, if/when evaluation or alert-check volume makes
   the APScheduler in-process approach a bottleneck. Not scheduled by default.
8. **Could-haves** — trace comparison, batch re-evaluation, Slack/Discord-formatted webhooks.

## Data flow

Unchanged from v1.0:

1. App makes an LLM call, wrapped by the SDK.
2. SDK captures telemetry (prompt, completion, tokens, latency, cost) and buffers it locally.
3. SDK flushes buffered traces to the backend in batches, authenticated via the project's API key.
4. Backend validates the payload, calculates cost from token counts, writes trace + spans to Postgres.
5. (Phase 5+) Background workers pick up new traces and run configured evaluators.
6. Evaluation results are written back to Postgres, linked to their source trace.
7. (Phase 6+) Background workers check active alert rules against recent metrics; a breach
   triggers a notification via email or webhook.
8. The dashboard queries the backend to render the Trace Explorer, analytics, and evaluation views.
9. User reviews traces, scores, and analytics, and adjusts alert rules or prompts as needed.

## Scalability

- SDK batches and compresses traces client-side to reduce request volume (Phase 2).
- Trace ingestion is append-only and horizontally scalable behind the API layer — already
  true of the built ingestion endpoint, since it holds no in-request state.
- Background workers (once they exist, Phase 5+) are decoupled from the request path —
  evaluation and alerting must never block trace ingestion.
- APScheduler is the default scheduler until evaluation/alert volume requires independently
  scalable workers — at that point, and not before, introduce Celery + a Redis broker.
- Dashboard queries are paginated and indexed by project, time range, and trace ID
  (`Trace.project_id`, `Trace.created_at`, `Trace.status` are already indexed) to keep
  response times flat as data grows.

## Reliability

- SDK buffers traces locally and retries with backoff if the backend is unreachable —
  no silent data loss on the client side (Phase 2 requirement).
- Trace ingestion is idempotent — **built**. The SDK generates a `client_trace_id` once per
  event (not per HTTP attempt), and the backend skips any trace whose `client_trace_id`
  already exists for that project, backed by a unique constraint for the concurrent-request
  case. Verified against real Postgres: resending an identical batch stores it once, not twice.
- Evaluation and alerting failures must not affect trace storage — a trace persists regardless
  of whether evaluation succeeds (design constraint for Phase 5, not yet applicable).
- Evaluation job status (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`) tracked once the
  evaluation engine exists, so failures are visible rather than silent.

## Security

- JWT (HS256) for dashboard users, 24h expiry by default (`JWT_EXPIRE_MINUTES`); API keys
  (`llmobs_<random>`) for SDK-to-backend trace ingestion — **built**.
- Role-based access control — Admin/Member/Viewer, scoped per project via
  `ProjectMembership` — **built and enforced**. Project member management
  (`GET/POST /api/v1/projects/{id}/members`, `PATCH/DELETE .../members/{user_id}`) requires
  Admin for any write; a project's last Admin can't be removed or demoted, so a project can
  never end up with zero Admins. Verified live: a Viewer attempting to add a member gets 403.
- Traces are isolated per project — every trace and query is scoped by `project_id`,
  and cross-project access is rejected at the membership-check dependency — **built**.
- Passwords hashed with `bcrypt`, rejected outright above 72 bytes (bcrypt's own limit)
  rather than silently truncated — **built**.
- All traffic encrypted in transit (HTTPS) — deployment-time concern, not yet applicable
  (currently local dev only).
- Secrets (JWT secret, DB credentials, future LLM provider keys) via environment
  variables (`.env`, gitignored) — **built**; `.env.example` documents required vars.
- Prompt/completion text stored as-is for now (`Trace.prompt`, `Trace.completion` are plain
  `Text` columns) — future redaction/masking policy is a Could-have, not scheduled.
