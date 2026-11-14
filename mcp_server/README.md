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

## Using it remotely, as a new user (no setup)

The backend itself serves this same MCP server directly over HTTP at `{base_url}/mcp`
(see `app/main.py`) — any new user of the platform can point an MCP client at it with
nothing to clone or install:

1. Log in, create a project, and copy its API key from the project's **Settings** tab.
2. Add this to your MCP client's config:
   ```json
   {
     "mcpServers": {
       "llm-observability": {
         "type": "http",
         "url": "https://llm-observability-backend-48ov.onrender.com/mcp",
         "headers": { "X-API-Key": "your-project-api-key" }
       }
     }
   }
   ```
3. Restart the client.

Auth here is the project's own API key as an `X-API-Key` header, not the
`LLMOBS_MCP_EMAIL`/`LLMOBS_MCP_PASSWORD` login the local script below uses - simpler,
and it's the same key the SDK already uses to send traces in.

## Using the local script instead (contributing to this repo)

Everything below is for developing against a local backend, not for an end user of the
platform — prefer the remote endpoint above unless you're actually working on this
codebase.

### Setup

```bash
cd mcp_server
python -m venv .venv
.venv/Scripts/pip install "mcp[cli]" requests   # .venv/bin/pip on macOS/Linux
```

Authenticates once at startup using `LLMOBS_MCP_EMAIL` / `LLMOBS_MCP_PASSWORD`
(defaults to the demo account if unset — set real credentials as environment variables
in whichever client config runs this server, never hardcode them here).

### From Claude Code (this project)

A `.mcp.json` at the repo root already registers this server for this project. **Start a
new Claude Code session in this folder** (or restart this one) to pick it up — it'll ask
you to approve the new MCP server once. After that, the three tools above are just
available to ask about directly, e.g. "what's the error rate on the LLM Observability
Demo project this week?"

### From the standalone Claude Desktop app, or another MCP client

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
