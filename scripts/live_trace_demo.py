"""Sends ONE trace through the real SDK -> backend -> database path and shows the
project's trace count before and after. Meant for a live demo: run it, then
refresh the dashboard's Trace Explorer and the count goes up by one.

The "model call" is a stand-in (a short sleep) so no provider API key is needed;
everything else - the SDK's trace() wrapper, background batching, the ingestion
API, Postgres, the dashboard - is the real pipeline.

Usage (backend must be running on :8000):
    sdk/.venv/Scripts/python scripts/live_trace_demo.py            # newest demo project
    sdk/.venv/Scripts/python scripts/live_trace_demo.py --error    # send a failed call instead
    sdk/.venv/Scripts/python scripts/live_trace_demo.py <project-id>
"""

import os
import sys
import time

import requests

import llm_observability_sdk as obs

BASE_URL = os.environ.get("LLMOBS_DEMO_BASE_URL", "http://127.0.0.1:8000")
API = BASE_URL + "/api/v1"
DEMO_EMAIL = "demo@polaris.edu"
DEMO_PASSWORD = "DemoViva2026!"
DASHBOARD_URL = os.environ.get("LLMOBS_DASHBOARD_URL", "http://localhost:5173")


def login() -> dict:
    resp = requests.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    resp.raise_for_status()
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def pick_project(headers: dict, project_id: str | None) -> dict:
    if project_id:
        resp = requests.get(f"{API}/projects/{project_id}", headers=headers)
        resp.raise_for_status()
        return resp.json()
    projects = requests.get(f"{API}/projects", headers=headers).json()
    newest = max((p for p in projects if p["name"] == "LLM Observability Demo"), key=lambda p: p["created_at"])
    resp = requests.get(f"{API}/projects/{newest['id']}", headers=headers)
    resp.raise_for_status()
    return resp.json()


def trace_count(headers: dict, project_id: str) -> int:
    resp = requests.get(f"{API}/projects/{project_id}/traces", params={"limit": 1}, headers=headers)
    resp.raise_for_status()
    return resp.json()["total"]


def main() -> None:
    fail = "--error" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    headers = login()
    project = pick_project(headers, args[0] if args else None)
    before = trace_count(headers, project["id"])
    print(f"Project: {project['name']} ({project['id']})")
    print(f"Traces before: {before}")

    obs.init(api_key=project["api_key"], base_url=BASE_URL)

    prompt = "Live demo: explain what an LLM trace is in one sentence."
    try:
        with obs.trace(model="demo-model", provider="custom", prompt=prompt, tags={"env": "live-demo"}) as t:
            time.sleep(0.35)  # stand-in for a real model call
            if fail:
                raise TimeoutError("simulated provider timeout")
            t.set_completion(
                "A trace is the record of one LLM call: prompt, response, latency, tokens and cost.",
                prompt_tokens=14,
                completion_tokens=22,
                cost=0.00018,
            )
    except TimeoutError:
        pass  # trace() already recorded it as a failed trace and re-raised

    obs.shutdown()  # flushes the background queue so the trace is actually delivered

    after = trace_count(headers, project["id"])
    print(f"Traces after:  {after}  ({'+' if after >= before else ''}{after - before})")
    print(f"Refresh: {DASHBOARD_URL}/projects/{project['id']}/traces")


if __name__ == "__main__":
    main()
