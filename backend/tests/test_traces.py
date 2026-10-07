import pytest


@pytest.fixture()
def project(client, auth_headers):
    response = client.post(
        "/api/v1/projects", json={"name": "Trace Project"}, headers=auth_headers
    )
    return response.json()


def test_ingest_traces_requires_api_key(client):
    response = client.post(
        "/api/v1/traces",
        json={"traces": [{"model": "gpt-4o", "provider": "openai", "prompt": "hi", "latency_ms": 120.5}]},
    )
    assert response.status_code == 401


def test_ingest_traces_rejects_invalid_api_key(client):
    response = client.post(
        "/api/v1/traces",
        json={"traces": [{"model": "gpt-4o", "provider": "openai", "prompt": "hi", "latency_ms": 120.5}]},
        headers={"X-API-Key": "not-a-real-key"},
    )
    assert response.status_code == 401


def test_ingest_traces_stores_batch(client, project):
    payload = {
        "traces": [
            {
                "model": "gpt-4o",
                "provider": "openai",
                "prompt": "Summarize this document",
                "completion": "Here is a summary.",
                "prompt_tokens": 42,
                "completion_tokens": 8,
                "latency_ms": 350.2,
                "cost": 0.0012,
                "status": "success",
                "tags": {"env": "prod"},
            },
            {
                "model": "gpt-4o",
                "provider": "openai",
                "prompt": "Bad call",
                "latency_ms": 12.0,
                "status": "error",
                "error_message": "rate limited",
            },
        ]
    }

    response = client.post(
        "/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]}
    )

    assert response.status_code == 201
    assert response.json()["ingested"] == 2


def test_ingest_traces_is_idempotent_on_client_trace_id(client, auth_headers, project):
    payload = {
        "traces": [
            {
                "model": "gpt-4o",
                "provider": "openai",
                "prompt": "hi",
                "latency_ms": 100.0,
                "client_trace_id": "fixed-retry-id-1",
            }
        ]
    }

    first = client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})
    assert first.status_code == 201
    assert first.json() == {"ingested": 1, "skipped_duplicates": 0}

    # Simulates the SDK retrying the same batch after a lost response.
    retry = client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})
    assert retry.status_code == 201
    assert retry.json() == {"ingested": 0, "skipped_duplicates": 1}

    listed = client.get(f"/api/v1/projects/{project['id']}/traces", headers=auth_headers)
    assert listed.json()["total"] == 1


def test_ingest_traces_within_batch_duplicate_id_only_skips_that_one(client, auth_headers, project):
    # Regression test: a batch where one client_trace_id is repeated twice
    # (nothing to do with an earlier request — this can happen with any
    # direct caller of the ingestion API, not just our SDK, since the schema
    # doesn't forbid it). Before the fix, both copies passed the
    # already-in-DB check, both got queued for insert, and the unique
    # constraint rejected the whole `add_all` as one transaction — silently
    # dropping every trace in the batch, including the two genuinely
    # distinct ones bundled alongside the duplicate, while still returning
    # 201 with a "skipped_duplicates" count that implied they were safe.
    payload = {
        "traces": [
            {"model": "gpt-4o", "provider": "openai", "prompt": "A", "latency_ms": 1.0, "client_trace_id": "dup"},
            {"model": "gpt-4o", "provider": "openai", "prompt": "B", "latency_ms": 2.0, "client_trace_id": "unique-1"},
            {"model": "gpt-4o", "provider": "openai", "prompt": "C", "latency_ms": 3.0, "client_trace_id": "dup"},
        ]
    }

    response = client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})
    assert response.status_code == 201
    assert response.json() == {"ingested": 2, "skipped_duplicates": 1}

    listed = client.get(f"/api/v1/projects/{project['id']}/traces", headers=auth_headers)
    assert listed.json()["total"] == 2
    prompts = {t["prompt"] for t in listed.json()["items"]}
    assert prompts == {"A", "B"}  # first "dup" wins, "unique-1" is unaffected


def test_ingest_traces_without_client_trace_id_is_not_deduplicated(client, auth_headers, project):
    payload = {"traces": [{"model": "gpt-4o", "provider": "openai", "prompt": "hi", "latency_ms": 100.0}]}

    client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})
    client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})

    listed = client.get(f"/api/v1/projects/{project['id']}/traces", headers=auth_headers)
    assert listed.json()["total"] == 2


def test_list_traces_filters_by_status(client, auth_headers, project):
    payload = {
        "traces": [
            {"model": "gpt-4o", "provider": "openai", "prompt": "ok", "latency_ms": 100.0, "status": "success"},
            {"model": "gpt-4o", "provider": "openai", "prompt": "bad", "latency_ms": 50.0, "status": "error"},
        ]
    }
    client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})

    response = client.get(
        f"/api/v1/projects/{project['id']}/traces",
        params={"status": "error"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "error"


def test_list_traces_requires_membership(client, project):
    other_payload = {"email": "viewer@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=other_payload)
    other_login = client.post("/api/v1/auth/login", json=other_payload).json()
    other_headers = {"Authorization": f"Bearer {other_login['access_token']}"}

    response = client.get(f"/api/v1/projects/{project['id']}/traces", headers=other_headers)

    assert response.status_code == 403


def test_get_single_trace_not_found(client, auth_headers, project):
    response = client.get(
        f"/api/v1/projects/{project['id']}/traces/does-not-exist",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_export_traces_csv_contains_all_rows_and_header(client, auth_headers, project):
    payload = {
        "traces": [
            {"model": "gpt-4o", "provider": "openai", "prompt": "a", "latency_ms": 10.0, "status": "success"},
            {"model": "gpt-4o", "provider": "openai", "prompt": "b", "latency_ms": 20.0, "status": "error", "error_message": "boom"},
        ]
    }
    client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})

    response = client.get(f"/api/v1/projects/{project['id']}/traces/export", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]

    lines = response.text.strip().splitlines()
    assert lines[0] == (
        "id,client_trace_id,model,provider,prompt,completion,prompt_tokens,"
        "completion_tokens,latency_ms,cost,status,error_message,tags,created_at"
    )
    assert len(lines) == 3  # header + 2 rows
    assert "boom" in response.text


def test_export_traces_json_format(client, auth_headers, project):
    payload = {"traces": [{"model": "gpt-4o", "provider": "openai", "prompt": "hi", "latency_ms": 10.0}]}
    client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})

    response = client.get(
        f"/api/v1/projects/{project['id']}/traces/export",
        params={"format": "json"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert len(body) == 1
    assert body[0]["prompt"] == "hi"


def test_export_traces_applies_status_filter(client, auth_headers, project):
    payload = {
        "traces": [
            {"model": "gpt-4o", "provider": "openai", "prompt": "ok", "latency_ms": 10.0, "status": "success"},
            {"model": "gpt-4o", "provider": "openai", "prompt": "bad", "latency_ms": 10.0, "status": "error", "error_message": "x"},
        ]
    }
    client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})

    response = client.get(
        f"/api/v1/projects/{project['id']}/traces/export",
        params={"format": "json", "status": "error"},
        headers=auth_headers,
    )

    body = response.json()
    assert len(body) == 1
    assert body[0]["prompt"] == "bad"


def test_export_traces_not_capped_at_default_page_size(client, auth_headers, project):
    # The list endpoint defaults to 50 results per page - export must not
    # inherit that cap, since "export everything" is the whole point.
    traces = [
        {"model": "gpt-4o", "provider": "openai", "prompt": f"trace {i}", "latency_ms": 1.0}
        for i in range(55)
    ]
    client.post("/api/v1/traces", json={"traces": traces}, headers={"X-API-Key": project["api_key"]})

    response = client.get(
        f"/api/v1/projects/{project['id']}/traces/export",
        params={"format": "json"},
        headers=auth_headers,
    )

    assert len(response.json()) == 55


def test_export_traces_requires_membership(client, project):
    other_payload = {"email": "export-outsider@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=other_payload)
    other_login = client.post("/api/v1/auth/login", json=other_payload).json()
    other_headers = {"Authorization": f"Bearer {other_login['access_token']}"}

    response = client.get(f"/api/v1/projects/{project['id']}/traces/export", headers=other_headers)

    assert response.status_code == 403


def test_export_traces_rejects_unknown_format(client, auth_headers, project):
    response = client.get(
        f"/api/v1/projects/{project['id']}/traces/export",
        params={"format": "xml"},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_filtered_traces_query_has_no_order_by_before_count(client, project):
    # Regression test for a Postgres-only bug: list_traces reuses this query
    # for both COUNT(*) and the paginated SELECT. Postgres rejects an
    # ORDER BY on a column that isn't in the SELECT list of an aggregate
    # query ("column must appear in the GROUP BY clause or be used in an
    # aggregate function") - SQLite accepts it silently, so this broke the
    # Trace Explorer against the real database without failing any test here.
    # Asserting on the compiled SQL catches it without needing a live
    # Postgres connection.
    from app.api.traces import _filtered_traces_query
    from app.core.db import SessionLocal

    db = SessionLocal()
    query = _filtered_traces_query(db, project["id"], None, None)
    compiled = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
    db.close()

    assert "ORDER BY" not in compiled.upper()
