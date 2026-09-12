# Dashboard Onboarding (Sagar)

Everything you need to get oriented and start building — read this once, then use it as a
reference.

## What this project is

An **LLM Observability Platform** — like Google Analytics, but for AI API calls instead of
website visitors. When a company's app calls an LLM (OpenAI, Anthropic, etc.), this platform
captures what happened: the prompt, the response, how long it took, how many tokens it used,
how much it cost, and whether it errored. That data gets stored and shown on a dashboard so
developers can spot cost spikes, slow calls, and failures without digging through logs.

Full product requirements: [`PRD.pdf`](PRD.pdf). Architecture and why things are built the way
they are: [`HLD.md`](HLD.md) — **read this one, it's kept up to date as we build, unlike the PDF.**

## Current status

| Piece | Status | Owner |
|---|---|---|
| Backend (FastAPI + PostgreSQL) | **Built** — auth, project management + roles, trace ingestion/query, all tested | Shuban |
| SDK (Python) | **Built** — auto-captures OpenAI/Anthropic calls, sends them to the backend | Shuban |
| **Dashboard (React)** | **Not started — this is you** | Sagar |
| Evaluation engine, alerting | Not started, comes after the dashboard | TBD |

See [`PROGRESS.md`](PROGRESS.md) for the day-by-day log of what's shipped.

## Your role

You own the **dashboard** end-to-end: everything the user sees and clicks. It's a clean,
separable piece of work — it only talks to the backend over its REST API (documented below),
so you don't need to touch backend or SDK code to build it. If you ever *do* need a backend
change (a new endpoint, a field the frontend needs that isn't returned yet), flag it — that's
a quick addition on the backend side, not something you need to build yourself.

## Tech stack

- **Backend** (already running, you'll just call it): FastAPI + PostgreSQL
- **Dashboard** (what you're building): **React** (Vite), **TanStack Query** for talking to
  the API, **Recharts** for the analytics charts later. These aren't locked in stone if you
  have a strong preference — flag it before you start if so.
- **Local backend infra**: Docker Compose runs Postgres for you — you don't need to install
  Postgres yourself.

## Step 1 — Get the backend running locally

You need this running so the dashboard has something real to talk to.

```bash
git clone https://github.com/Shubb07/llm-observability-platform.git
cd llm-observability-platform

# Start Postgres
cd infra
docker compose up -d

# Set up and run the backend
cd ../backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt    # .venv/bin/pip on macOS/Linux
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/docs** — that's an interactive page listing every API endpoint.
Click through it once: register a user, log in, create a project, send a test trace, list
traces back. That's the whole loop the dashboard needs to replicate visually. Full details
and troubleshooting: [`../backend/README.md`](../backend/README.md).

## Step 2 — Know the API you're building against

Full table: [`../backend/README.md`](../backend/README.md) → "API summary". The short version:

| What | Endpoint | Needs |
|---|---|---|
| Register | `POST /api/v1/auth/register` | — |
| Log in | `POST /api/v1/auth/login` → returns a JWT | — |
| Create a project | `POST /api/v1/projects` → returns an API key | JWT |
| List your projects | `GET /api/v1/projects` | JWT |
| List a project's members | `GET /api/v1/projects/{id}/members` | JWT |
| List traces (with filters) | `GET /api/v1/projects/{id}/traces?status=&model=` | JWT |
| Get one trace's full detail | `GET /api/v1/projects/{id}/traces/{trace_id}` | JWT |
| Analytics (latency %iles, error rate, cost, tokens) | `GET /api/v1/projects/{id}/analytics?time_range=24h\|7d\|30d&group_by=model` | JWT |

Every dashboard request except register/login needs the JWT in an `Authorization: Bearer
<token>` header. Traces are always scoped to a project — there's no "see everything" view.

## Step 3 — Scaffold the React app

Nothing exists yet in `dashboard/` beyond a placeholder README. Suggested start:

```bash
cd dashboard
npm create vite@latest . -- --template react-ts
npm install
npm install @tanstack/react-query axios react-router-dom
```

(React Router because you'll need at least: login page, project list/switcher, trace list,
trace detail. Axios or plain `fetch` — your call.)

## Step 4 — Build in this order

Matches the HLD's phasing — build the thing that's useful sooner before the thing that needs
more data to be meaningful:

1. **Login/register page** — call the two auth endpoints, store the JWT (localStorage is fine
   for now), redirect to the project list on success.
2. **Project list + "create project" form** — after login, show the user's projects; let them
   create one and see the generated API key (they'll need it to actually send traces via the
   SDK later).
3. **Trace Explorer** — the core view. A table of traces for a selected project (model,
   status, latency, cost, timestamp), with filters for model/status. Clicking a row opens the
   full trace detail (prompt, completion, all metadata).
4. **Analytics view** — the `/analytics` endpoint is built (request volume, error rate,
   p50/p95/p99 latency, tokens, cost, with a time-range picker and optional per-model
   breakdown). Recharts for the charts. You can start this as soon as the Trace Explorer works.
5. Stop here and check in — evaluation scores and alert config still depend on backend pieces
   that don't exist yet (Phase 5/6 in the HLD). Don't build UI for data that isn't there.

## Where to ask when stuck

- Backend behaving unexpectedly, or you need a new/changed endpoint → tell Shuban, it's a fast
  backend change
- Confused about *why* something's built a certain way → [`HLD.md`](HLD.md) has the reasoning,
  not just the "what"
- Confused about what a feature is *for* → [`PRD.pdf`](PRD.pdf) has the user stories and
  acceptance criteria

## When you make progress

Add a line to your row in [`PROGRESS.md`](PROGRESS.md)'s daily log — that file doubles as your
end-of-day report to the mentor, so keeping it current saves you from writing that up twice.
