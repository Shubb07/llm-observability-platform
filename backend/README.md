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

Schema is managed by Alembic (`alembic/versions/`) — see "Database migrations" below.

## Running locally

```bash
# 1. Start Postgres
cd infra && docker compose up -d

# 2. Install deps
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # .venv/bin/pip on macOS/Linux

# 3. Configure the database connection (required — there is no built-in default)
cp .env.example .env

# 4. Apply migrations (creates the schema — see "Database migrations" below)
.venv/Scripts/python -m alembic upgrade head

# 5. Run the API
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

Then visit `http://localhost:8000/docs` for interactive API docs, or `http://localhost:8000/health`.

Configuration is read from environment variables / `.env` (see `.env.example`). `DATABASE_URL` is
required and the app will not start without it; adjust `JWT_SECRET` and the rest as needed.
`.env` is gitignored — never commit it.

## Testing

Tests run against an in-memory SQLite database — no Docker required:

```bash
.venv/Scripts/python -m pytest -q
```

Tests build their own SQLite schema directly in `tests/conftest.py` and never touch
Alembic or the real Postgres database, so they don't need migrations applied first.

## Database migrations

Schema changes go through Alembic instead of `Base.metadata.create_all()`, so changes are
versioned and reviewable instead of silently regenerated from the models on every startup.

```bash
# Apply all pending migrations (run this after pulling new migrations, and before
# starting the server for the first time)
.venv/Scripts/python -m alembic upgrade head

# After changing a model in app/models/, generate a migration for it
.venv/Scripts/python -m alembic revision --autogenerate -m "describe the change"

# Always read the generated file before committing it — autogenerate detects column/
# table/index changes but not everything (e.g. renames show up as drop + add; data
# migrations are never generated). Then apply and verify it:
.venv/Scripts/python -m alembic upgrade head

# Roll back one migration if something's wrong
.venv/Scripts/python -m alembic downgrade -1
```

`alembic/env.py` reads `DATABASE_URL` from the same `Settings`/`.env` the API uses — there's
no second connection string to keep in sync. The `baseline_schema` revision is the starting
point, generated from the models as they existed once Alembic was introduced (`projects`,
`users`, `project_memberships`, `traces` — matches what `create_all()` had already been
building, so applying it to an existing dev database is a no-op stamp, not new DDL).

## API summary

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /api/v1/auth/register` | none | Create a user |
| `POST /api/v1/auth/login` | none | Get a JWT |
| `GET /api/v1/auth/me` | JWT | Current user |
| `POST /api/v1/projects` | JWT | Create a project, returns its API key |
| `GET /api/v1/projects` | JWT | List projects the current user belongs to |
| `GET /api/v1/projects/{id}` | JWT | Get one project (must be a member) |
| `POST /api/v1/projects/{id}/archive` | JWT, Admin | Stop new trace ingestion (existing traces stay readable). Idempotent. |
| `POST /api/v1/projects/{id}/unarchive` | JWT, Admin | Resume ingestion for an archived project. Idempotent. |
| `GET /api/v1/projects/{id}/members` | JWT | List a project's members and their roles |
| `POST /api/v1/projects/{id}/members` | JWT, Admin | Add an existing registered user to the project |
| `PATCH /api/v1/projects/{id}/members/{user_id}` | JWT, Admin | Change a member's role |
| `DELETE /api/v1/projects/{id}/members/{user_id}` | JWT, Admin | Remove a member — refuses to remove the last Admin |
| `POST /api/v1/traces` | API key (`X-API-Key`) | Ingest a batch of traces (idempotent on `client_trace_id`) — this is what the SDK calls |
| `GET /api/v1/projects/{id}/traces` | JWT | List/filter traces (by model, status), paginated |
| `GET /api/v1/projects/{id}/traces/{trace_id}` | JWT | Get one trace's full detail |
| `GET /api/v1/projects/{id}/analytics` | JWT | Request volume, error rate, p50/p95/p99 latency, tokens, cost over `time_range` (`24h`\|`7d`\|`30d`), optional `group_by=model` |
