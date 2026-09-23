# Infra

Local-dev and deployment infrastructure: docker-compose (backend + PostgreSQL + Redis),
environment variable templates, and DB migrations.

`docker-compose.yml` runs PostgreSQL for local dev. Redis is not set up yet — deferred until
background workers (evaluation/alerting) need it (see the HLD's scalability principles).

DB migrations are handled by Alembic, in `backend/alembic/` — see `backend/README.md`'s
"Database migrations" section for the commands.
