# Team Roles & Progress Log

## Roles

| Person | Owns |
|---|---|
| Shuban Mutagi | Backend (FastAPI + PostgreSQL), Python SDK, infra (Docker Compose, CI later) |
| Sagar Halladakeri | Dashboard (React) — Trace Explorer, analytics, evaluation/alert UI once those exist |

**Why this split:** the backend and SDK are one continuous piece of work — the SDK's
`TraceEvent` schema mirrors the backend's `TraceIn` schema directly, so keeping both with
one person avoids a two-way sync tax on every schema change. The dashboard is the cleanest
fully-separable piece: it only talks to the backend over its documented REST API
(see `backend/README.md` → API summary), so it can be built independently once that API
exists — which it now does.

This isn't fixed — re-split any time it stops making sense (e.g. once the dashboard needs
a backend change, or once evaluation/alerting starts and needs picking up).

## Daily Log

Add an entry each day so end-of-day reporting is just copying this section. Format:
`- <name>: <what shipped, referencing PR/commit or file if useful>`

### 2026-09-08

- **Shuban:** repo scaffold + GitHub repo; backend v1 (JWT auth, project management with
  API keys, trace ingestion/query) — 17 tests, verified end-to-end against real Postgres;
  HLD v2 (`docs/HLD.md`) reflecting the actual stack and phased build order; SDK
  (background transport with batching/retry/backoff, cost estimation, manual `trace()`,
  OpenAI + Anthropic auto-instrumentation) — verified end-to-end against the live backend
- **Sagar:** _pending_

### 2026-09-10

- **Shuban:** closed the idempotency gap flagged in the HLD's Reliability section — trace
  ingestion now dedups on a `client_trace_id` the SDK generates once per event, so a retried
  batch (network blip, lost response) can't create a duplicate trace. Backend: unique
  constraint + dedup check in `POST /api/v1/traces`. SDK: `TraceEvent` now carries a stable
  id across retries. 5 new tests (19 backend / 20 SDK total, all passing); verified live
  against real Postgres (send same batch twice → stored once, not twice)
- **Sagar:** _pending_

### 2026-09-12

- **Shuban:** closed the other HLD-flagged gap — roles existed but were never enforced past
  "is a member." Added project member management (`GET/POST /api/v1/projects/{id}/members`,
  `PATCH/DELETE .../members/{user_id}`), gated writes to Admin only via a new `require_admin`
  dependency, and blocked removing/demoting a project's last Admin so a project can't end up
  with zero Admins. 9 new tests (28 backend total, all passing); verified live against
  Postgres including the 403 (Viewer tries to write) and 409 (remove last Admin) cases.
  Also added `docs/DASHBOARD_ONBOARDING.md` for Sagar; enabled CORS
  (`CORS_ALLOWED_ORIGINS`) for the dashboard's dev server so his first browser `fetch()`
  call to the API doesn't fail with an opaque CORS error; and built the analytics endpoint
  (`GET /api/v1/projects/{id}/analytics` — request volume, error rate, p50/p95/p99 latency,
  tokens, cost, optional per-model breakdown) ahead of him needing it, per PRD US-004.
  7 more tests (36 backend total, all passing); verified live against Postgres
- **Sagar:** _pending_
