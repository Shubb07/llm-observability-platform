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
