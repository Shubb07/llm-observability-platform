# Backend

FastAPI + SQLAlchemy + PostgreSQL. Implements the "Must" PRD features that don't depend on
the SDK or dashboard existing yet: user auth, project management, and trace ingestion/query.

## Layout

| Folder            | Status | Responsibility |
|-------------------|--------|-----------------|
| `app/api/`        | Implemented | Routers: `auth.py` (register/login/me), `projects.py` (create/list/get + member management), `traces.py` (ingest + query). `deps.py` holds JWT, API-key, and role-check (`require_admin`) auth dependencies. |
| `app/core/`       | Implemented | `config.py` (settings), `db.py` (SQLAlchemy engine/session), `security.py` (password hashing, JWT) |
| `app/models/`     | Implemented | SQLAlchemy models: `User`, `Project`, `ProjectMembership`, `Trace` |
| `app/schemas/`    | Implemented | Pydantic request/response models |
| `app/workers/`    | Placeholder | Background jobs — pick up new traces, run evaluators, check alert thresholds |
| `app/evaluation/` | Placeholder | Evaluation engine — relevance, faithfulness, safety, format compliance scoring |
| `app/alerting/`   | Placeholder | Alert rule evaluation against incoming metrics, notification triggering |
| `app/auth/`       | Placeholder | Reserved — auth is currently implemented in `app/api/auth.py` + `app/core/security.py`; split out here if it grows (e.g. OAuth) |

Table creation currently happens via `Base.metadata.create_all()` on startup — fine for a
single dev database, but replace with Alembic migrations before this needs to run against
more than one environment.

## Running locally

```bash
# 1. Start Postgres
cd infra && docker compose up -d

# 2. Install deps
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # .venv/bin/pip on macOS/Linux

# 3. Run the API
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

Then visit `http://localhost:8000/docs` for interactive API docs, or `http://localhost:8000/health`.

Configuration is read from environment variables (see `.env.example`); copy it to `.env` and
adjust `DATABASE_URL` / `JWT_SECRET` as needed.

## Testing

Tests run against an in-memory SQLite database — no Docker required:

```bash
.venv/Scripts/python -m pytest -q
```

## API summary

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /api/v1/auth/register` | none | Create a user |
| `POST /api/v1/auth/login` | none | Get a JWT |
| `GET /api/v1/auth/me` | JWT | Current user |
| `POST /api/v1/projects` | JWT | Create a project, returns its API key |
| `GET /api/v1/projects` | JWT | List projects the current user belongs to |
| `GET /api/v1/projects/{id}` | JWT | Get one project (must be a member) |
| `GET /api/v1/projects/{id}/members` | JWT | List a project's members and their roles |
| `POST /api/v1/projects/{id}/members` | JWT, Admin | Add an existing registered user to the project |
| `PATCH /api/v1/projects/{id}/members/{user_id}` | JWT, Admin | Change a member's role |
| `DELETE /api/v1/projects/{id}/members/{user_id}` | JWT, Admin | Remove a member — refuses to remove the last Admin |
| `POST /api/v1/traces` | API key (`X-API-Key`) | Ingest a batch of traces (idempotent on `client_trace_id`) — this is what the SDK calls |
| `GET /api/v1/projects/{id}/traces` | JWT | List/filter traces (by model, status), paginated |
| `GET /api/v1/projects/{id}/traces/{trace_id}` | JWT | Get one trace's full detail |
