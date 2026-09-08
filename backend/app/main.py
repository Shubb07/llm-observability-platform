from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import auth, projects, traces
from app.core.db import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Table creation for local development only. Once schema changes stop being
    # trivial, replace this with Alembic migrations (see infra/README.md).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="LLM Observability Platform API", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(traces.router)


@app.get("/health")
def health():
    return {"status": "ok"}
