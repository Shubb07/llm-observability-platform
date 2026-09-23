from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, auth, projects, traces
from app.core.config import settings

# Schema is managed by Alembic now (backend/alembic/versions/), not created here.
# Run `alembic upgrade head` before starting the server — see backend/README.md.
# Tests are unaffected: they build their own SQLite schema directly (see
# tests/conftest.py) and never run this app's startup.
app = FastAPI(title="LLM Observability Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(traces.router)
app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok"}
