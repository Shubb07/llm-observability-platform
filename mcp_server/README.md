# MCP server

Exposes the backend's analytics and trace data as tools an MCP client (Claude, or any
other MCP-compatible assistant) can call directly — so "what's the error rate on my
project this week" is answered by a real API call, not a manual script or dashboard click.

This is a thin wrapper, not a reimplementation. Every tool here calls the same FastAPI
endpoints the dashboard and SDK already use — there's no new business logic, the backend
stays the single source of truth.

## Tools

| Tool | Calls | Purpose |
|---|---|---|
| `list_projects` | `GET /api/v1/projects` | Find a project's id before calling the others |
| `get_analytics(project_id, time_range)` | `GET /api/v1/projects/{id}/analytics` | Request volume, error rate, p50/p95/p99 latency, tokens, cost |
| `list_traces(project_id, status, model, limit)` | `GET /api/v1/projects/{id}/traces` | Recent traces, optionally filtered |

## Setup

```bash
cd mcp_server
python -m venv .venv
.venv/Scripts/pip install "mcp[cli]" requests   # .venv/bin/pip on macOS/Linux
```

Authenticates once at startup using `LLMOBS_MCP_EMAIL` / `LLMOBS_MCP_PASSWORD`
(defaults to the demo account if unset — set real credentials as environment variables
in whichever client config runs this server, never hardcode them here).

## Using it from Claude Code (this project)

A `.mcp.json` at the repo root already registers this server for this project. **Start a
new Claude Code session in this folder** (or restart this one) to pick it up — it'll ask
you to approve the new MCP server once. After that, the three tools above are just
available to ask about directly, e.g. "what's the error rate on the LLM Observability
Demo project this week?"

## Using it from the standalone Claude Desktop app, or another MCP client

Add this block to that app's own MCP server config (for the classic Claude Desktop app,
that's `claude_desktop_config.json` under its settings — not anything in this repo):

```json
{
  "mcpServers": {
    "llm-observability": {
      "command": "C:\\Users\\shuba\\llm-observability-platform\\mcp_server\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\shuba\\llm-observability-platform\\mcp_server\\server.py"]
    }
  }
}
```

Restart that app after saving. The backend (and Postgres) must be running at
`http://localhost:8000` for the tools to work — set `LLMOBS_MCP_BASE_URL` if it's
somewhere else.

## Tested

Each tool function was called directly against the real backend (not just syntax-checked):
`list_projects` returned real projects, `get_analytics` returned real percentiles for the
demo project, `list_traces` returned real trace rows. Not yet tested through an actual
MCP client end to end — that's the next step, from either Claude Code or Claude Desktop
as described above.
