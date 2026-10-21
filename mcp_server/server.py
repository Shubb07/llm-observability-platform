"""MCP server for the LLM Observability Platform.

Exposes our existing backend API as tools an MCP client (Claude Desktop,
or any other MCP-compatible assistant) can call directly, so a question
like "what's my error rate this week" is answered by calling our real
analytics endpoint, no dashboard, no script, no manual steps.

This is a thin wrapper, not a reimplementation: every tool below calls the
same FastAPI endpoints the dashboard and SDK already use. There's no new
business logic here on purpose - the backend stays the single source of
truth, this just gives an LLM assistant a way to reach it.

Auth: logs in once at startup using LLMOBS_MCP_EMAIL / LLMOBS_MCP_PASSWORD
(falls back to the demo account), and reuses that JWT for every tool call.
Never hardcode real credentials here - set them as environment variables
in the MCP client's own server config (see mcp_server/README.md).

Run directly for a quick smoke test:
    mcp_server/.venv/Scripts/python.exe mcp_server/server.py
Or point an MCP client (e.g. Claude Desktop's config) at this file - see
mcp_server/README.md for the exact config block.
"""

import os

import requests
from mcp.server.mcpserver import MCPServer

BASE_URL = os.environ.get("LLMOBS_MCP_BASE_URL", "http://127.0.0.1:8000")
API = BASE_URL + "/api/v1"
EMAIL = os.environ.get("LLMOBS_MCP_EMAIL", "demo@polaris.edu")
PASSWORD = os.environ.get("LLMOBS_MCP_PASSWORD", "DemoViva2026!")

mcp = MCPServer("llm-observability")

_token: str | None = None


def _auth_headers() -> dict:
    """Logs in lazily, once, and reuses the JWT for every subsequent call -
    matches how the dashboard itself behaves after a login."""
    global _token
    if _token is None:
        resp = requests.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=10)
        resp.raise_for_status()
        _token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {_token}"}


@mcp.tool()
def list_projects() -> list[dict]:
    """List every project the authenticated account belongs to, with each
    project's id, name, status and role. Use this first to find a
    project_id before calling the other tools."""
    resp = requests.get(f"{API}/projects", headers=_auth_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def get_analytics(project_id: str, time_range: str = "24h") -> dict:
    """Get aggregate metrics for a project: request volume, error rate,
    p50/p95/p99 latency, total tokens and total cost.

    time_range: one of "24h", "7d", "30d".
    """
    resp = requests.get(
        f"{API}/projects/{project_id}/analytics",
        params={"time_range": time_range},
        headers=_auth_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def list_traces(project_id: str, status: str | None = None, model: str | None = None, limit: int = 20) -> dict:
    """List recent LLM call traces for a project, newest first. Optionally
    filter by status ("success" or "error") or by model name."""
    params = {"limit": limit}
    if status:
        params["status"] = status
    if model:
        params["model"] = model
    resp = requests.get(
        f"{API}/projects/{project_id}/traces",
        params=params,
        headers=_auth_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    mcp.run()
