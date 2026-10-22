import pytest
from mcp.server.mcpserver.exceptions import ToolError
from sqlalchemy.orm import sessionmaker

import app.mcp_server as mcp_server


class FakeContext:
    """Stand-in for mcp.server.mcpserver.Context - the tool functions only
    ever touch ctx.headers, so that's all this needs to provide."""

    def __init__(self, headers: dict[str, str]):
        self.headers = headers


@pytest.fixture()
def patched_mcp_session(db_engine, monkeypatch):
    # mcp_server.py opens its own DB sessions via app.core.db.SessionLocal
    # directly (it's called as a plain function, not through FastAPI's
    # dependency injection), which is bound to the real DATABASE_URL, not
    # this test's isolated db_engine. Point it at the same engine the
    # `client`/`project` fixtures use so a project created through the API
    # is actually visible to the MCP tool functions in the same test.
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    monkeypatch.setattr(mcp_server, "SessionLocal", testing_session_local)


def test_missing_api_key_raises_tool_error(patched_mcp_session):
    # Regression test: this used to raise a bare ValueError, which the mcp
    # library swallows into a generic "Error executing tool <name>" -
    # discarding this specific, already-written message. ToolError is what
    # actually reaches the client.
    with pytest.raises(ToolError, match="Missing X-API-Key"):
        mcp_server.get_analytics(FakeContext(headers={}))


def test_invalid_api_key_raises_tool_error(patched_mcp_session):
    with pytest.raises(ToolError, match="Invalid API key"):
        mcp_server.get_analytics(FakeContext(headers={"x-api-key": "not-a-real-key"}))


def test_invalid_time_range_raises_tool_error_with_real_message(client, auth_headers, patched_mcp_session):
    # Regression test: analytics.py raises HTTPException expecting FastAPI's
    # own handling to translate it - calling the route function directly
    # (as the MCP tool does) skips that, so the helpful validation message
    # ("time_range must be one of...") never reached the client before.
    project = client.post("/api/v1/projects", json={"name": "P"}, headers=auth_headers).json()
    with pytest.raises(ToolError, match="time_range must be one of"):
        mcp_server.get_analytics(FakeContext(headers={"x-api-key": project["api_key"]}), time_range="2d")


def test_list_traces_rejects_out_of_range_limit(patched_mcp_session):
    # Regression test: traces.py's route has Query(ge=1, le=200), which only
    # runs through FastAPI's request pipeline - calling list_traces directly
    # as the MCP tool does skipped it entirely, letting an unbounded or
    # negative limit straight through to query.offset(offset).limit(limit).
    with pytest.raises(ToolError, match="limit must be between"):
        mcp_server.list_traces(FakeContext(headers={"x-api-key": "whatever"}), limit=1_000_000)

    with pytest.raises(ToolError, match="limit must be between"):
        mcp_server.list_traces(FakeContext(headers={"x-api-key": "whatever"}), limit=-1)
