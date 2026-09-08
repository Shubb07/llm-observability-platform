# Backend

Planned stack: **FastAPI + SQLAlchemy + PostgreSQL**, with Celery/Redis introduced for
background workers once evaluation volume needs independently scalable workers
(see `../docs/HLD.pdf` → Scalability).

## Layout

| Folder            | Responsibility (see HLD → Components) |
|-------------------|----------------------------------------|
| `app/api/`        | Trace ingestion API, query endpoints for the dashboard, request validation |
| `app/models/`     | SQLAlchemy models: traces, spans, evaluations, alert rules, users, projects |
| `app/workers/`    | Background jobs — pick up new traces, run evaluators, check alert thresholds |
| `app/evaluation/` | Evaluation engine — relevance, faithfulness, safety, format compliance scoring (LLM-as-judge + heuristics) |
| `app/alerting/`   | Alert rule evaluation against incoming metrics, notification triggering |
| `app/auth/`       | Registration, login (JWT), role-based access control (Admin, Member, Viewer) |
| `app/core/`       | Shared config, DB session, settings |

Not implemented yet — folders exist as placeholders for the planned module boundaries.
