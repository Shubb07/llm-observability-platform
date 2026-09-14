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

### 2026-09-13 (Week 1 — Dashboard Foundation)

- **Sagar:** Dashboard foundation and authentication — Week 1 OJT deliverable.

  **What was implemented:**
  - React 19 + Vite 8 + TypeScript 6 project scaffold
  - Axios API client (`src/api/client.ts`) with JWT request interceptor (auto-attaches `Authorization: Bearer <token>` to every request) and global 401 response interceptor (clears stale token, redirects to login)
  - TanStack Query v5 setup with a module-level `QueryClient` (30s staleTime, no refetch-on-focus, 1 retry)
  - `AuthContext` + `useAuth()` hook: token persisted in localStorage, validated against `GET /api/v1/auth/me` on startup, `login()`/`logout()` functions
  - `ProtectedRoute` component: React Router v6 layout route pattern, blocks unauthenticated users, shows spinner during JWT validation
  - `LoginPage`: controlled inputs, `useMutation`, loading/disabled state, FastAPI error extraction
  - `RegisterPage`: register → auto-login chain, client-side password validation (match + min 8 chars matches backend `Field(min_length=8)`)
  - Already-authenticated redirect on both auth pages (logged-in user hitting `/login` or `/register` is redirected to `/projects`)
  - `AppLayout`: sidebar shell with brand, nav links (NavLink for active highlighting), user email, logout button; `<Outlet />` renders page content
  - `ProjectsPage`: Week 1 placeholder with correct page-header/page-body structure (real list in Week 2)
  - Complete design system (`index.css`, 878 lines): CSS custom properties, auth forms, buttons, sidebar, tables, badges, loading/error states
  - TypeScript interfaces for all backend schemas verified against actual Pydantic schemas line-by-line
  - API functions pre-built for projects and traces, verified correct against backend

  **APIs integrated:**
  - `POST /api/v1/auth/register` — registration
  - `POST /api/v1/auth/login` — login, returns JWT
  - `GET /api/v1/auth/me` — token validation on startup

  **Tested:**
  - TypeScript build: passes with strict `noUnusedLocals` + `noUnusedParameters` checks
  - Auth flow verified: Register → Login → JWT stored → ProtectedRoute allows access → Logout → redirect to /login

  **Issues found and fixed:**
  - Login/register pages had no already-authenticated redirect (fixed)
  - ProtectedRoute returned `null` during token validation causing blank screen (fixed — now shows spinner)

  **What remains for Week 2:**
  - Real `ProjectsPage`: `GET /api/v1/projects` list, project cards, create project form
  - `CreateProjectPage`: `POST /api/v1/projects`, display returned `api_key`
  - Project context (active project for sidebar switcher)

- **Shuban:** reviewed Sagar's Week 1 push — pulled it, ran `npm install` + full
  build, and clicked through the live register → login → protected-route flow against
  the real backend rather than just reading the diff. Architecture (Context, TanStack
  Query, layout-route auth guard) is correct and the API calls match the backend schemas
  exactly. Found one real bug via the browser console: both `LoginPage` and
  `RegisterPage` had their already-authenticated `if (token) return <Navigate />` guard
  placed *before* their `useState`/`useMutation` calls — a Rules of Hooks violation that
  threw "Rendered fewer hooks than expected" on every successful login (React silently
  recovered, which is why it wasn't obvious). Fixed by moving the guard after all hooks
  in both files; verified with a fresh browser tab that the console is now clean.
