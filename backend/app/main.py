from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.transport_security import TransportSecuritySettings

from app.api import analytics, auth, projects, traces
from app.core.config import settings
from app.mcp_server import mcp

# The MCP SDK's streamable-http ASGI app owns a session manager that needs
# its own lifespan to start the task group behind it - Starlette never
# forwards lifespan startup/shutdown to a mounted sub-app on its own, so
# that lifespan has to be entered explicitly as part of this app's.
#
# transport_security defaults to allow-listing only localhost Host headers
# (DNS-rebinding protection aimed at a browser rebinding to a local stdio
# bridge) - meaningless for a publicly deployed endpoint, and it would
# reject every real request by Host header alone. The actual auth boundary
# here is the per-request X-API-Key each tool checks, so disable it rather
# than hardcode this service's hostname.
mcp_asgi_app = mcp.streamable_http_app(
    streamable_http_path="/mcp",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp_asgi_app.router.lifespan_context(mcp_asgi_app):
        yield


# Schema is managed by Alembic now (backend/alembic/versions/), not created here.
# Run `alembic upgrade head` before starting the server — see backend/README.md.
# Tests are unaffected: they build their own SQLite schema directly (see
# tests/conftest.py) and never run this app's startup.
app = FastAPI(title="LLM Observability Platform API", version="0.1.0", lifespan=lifespan)

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


# Remote MCP endpoint - point any MCP client at {base_url}/mcp with a
# project's API key (X-API-Key header) and it can call get_analytics /
# list_traces without installing anything locally. See mcp_server/README.md.
# Mounted at "/" (the sub-app already serves its own route at "/mcp") and
# registered last so it only catches paths none of the routes above matched
# - Starlette checks routes in registration order, so this can never shadow
# /health or /api/v1/*.
app.mount("/", mcp_asgi_app)
