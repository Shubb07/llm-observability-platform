"""Remote MCP endpoint, mounted into the main FastAPI app at /mcp.

Lets any MCP client (Claude, or any other MCP-compatible assistant) ask
about a project's traces and analytics without installing anything
locally - point the client at this deployed URL with the project's own
API key, same key ingest_traces already accepts.

Each tool call authenticates with the X-API-Key header the MCP client
sends, resolves it straight to a Project, and calls the *same* route
functions analytics.py/traces.py already expose over plain HTTP - no
second copy of the aggregation logic, just a different transport in
front of it. (mcp_server/server.py is the older, local-only version of
this, for running against your own machine's backend over stdio.)
"""

from fastapi import HTTPException
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from app.api import analytics as analytics_api
from app.api import traces as traces_api
from app.core.db import SessionLocal
from app.models.project import Project

mcp = MCPServer("llm-observability")

TRACES_MIN_LIMIT = 1
TRACES_MAX_LIMIT = 200  # mirrors Query(ge=1, le=200) on GET /projects/{id}/traces


def _project_from_request(ctx: Context) -> tuple[Project, object]:
    # ToolError (not a bare exception) is what the mcp library actually
    # forwards to the client - anything else gets swallowed into a generic
    # "Error executing tool <name>" with no indication of what went wrong,
    # discarding the specific, already-written messages below.
    headers = ctx.headers or {}
    api_key = headers.get("x-api-key")
    if not api_key:
        raise ToolError("Missing X-API-Key header - pass the project's API key from its dashboard page")

    db = SessionLocal()
    project = db.query(Project).filter_by(api_key=api_key).first()
    if project is None:
        db.close()
        raise ToolError("Invalid API key")
    if project.status != "ACTIVE":
        db.close()
        raise ToolError("Project is not active")
    return project, db


@mcp.tool()
def get_analytics(ctx: Context, time_range: str = "24h", model: str | None = None) -> dict:
    """Get aggregate metrics for the project this API key belongs to:
    request volume, error rate, p50/p95/p99 latency, total tokens and
    total cost.

    time_range: one of "24h", "7d", "30d".
    model: optional, restrict to one model name.
    """
    project, db = _project_from_request(ctx)
    try:
        result = analytics_api.get_analytics(
            project_id=project.id, time_range=time_range, model=model, group_by=None, project=project, db=db
        )
        return result.model_dump(mode="json")
    except HTTPException as exc:
        # analytics.py raises this expecting FastAPI's own exception
        # handling to turn it into a structured response - calling the
        # route function directly (not through a real HTTP request) skips
        # that, so without this the client-facing text ("time_range must
        # be one of...") never reaches the client either.
        raise ToolError(str(exc.detail)) from exc
    finally:
        db.close()


@mcp.tool()
def list_traces(
    ctx: Context, status: str | None = None, model: str | None = None, limit: int = 20
) -> dict:
    """List recent LLM call traces for the project this API key belongs
    to, newest first. Optionally filter by status ("success" or "error")
    or by model name."""
    # list_traces is called directly as a plain function below, not through
    # a real HTTP request, so FastAPI's Query(ge=1, le=200) on the route
    # itself never runs - without this check an MCP client could ask for
    # an unbounded or negative limit that the HTTP API would reject outright.
    if not (TRACES_MIN_LIMIT <= limit <= TRACES_MAX_LIMIT):
        raise ToolError(f"limit must be between {TRACES_MIN_LIMIT} and {TRACES_MAX_LIMIT}")

    project, db = _project_from_request(ctx)
    try:
        result = traces_api.list_traces(
            project_id=project.id,
            model=model,
            status_filter=status,
            limit=limit,
            offset=0,
            project=project,
            db=db,
        )
        return result.model_dump(mode="json")
    except HTTPException as exc:
        raise ToolError(str(exc.detail)) from exc
    finally:
        db.close()
