"""Sends ONE real OpenAI call through the SDK's instrument_openai() wrapper,
proving the whole pipeline end to end with a genuine model response instead
of the simulated call in live_trace_demo.py.

Needs a real OpenAI API key, read from the OPENAI_API_KEY environment
variable -- never pass it on the command line or hardcode it here.

Usage (backend must be running on :8000, OPENAI_API_KEY set in this shell):
    $env:OPENAI_API_KEY = "sk-..."          # set once, in this terminal only
    sdk/.venv/Scripts/python.exe scripts/live_openai_demo.py
"""

import os
import sys

import openai
import requests

import llm_observability_sdk as obs
from llm_observability_sdk.integrations.openai import instrument_openai

BASE_URL = os.environ.get("LLMOBS_DEMO_BASE_URL", "http://127.0.0.1:8000")
API = BASE_URL + "/api/v1"
DEMO_EMAIL = "demo@polaris.edu"
DEMO_PASSWORD = "DemoViva2026!"
PROJECT_ID = "bd6d6c47-7664-41e1-b60a-bcfcbe33d024"  # "LLM Observability Demo"


def login_headers() -> dict:
    resp = requests.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    resp.raise_for_status()
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def trace_count(headers: dict) -> int:
    resp = requests.get(f"{API}/projects/{PROJECT_ID}/traces", params={"limit": 1}, headers=headers)
    resp.raise_for_status()
    return resp.json()["total"]


def main() -> None:
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("OPENAI_API_KEY is not set in this shell. Set it first:")
        print('  $env:OPENAI_API_KEY = "sk-..."')
        sys.exit(1)

    headers = login_headers()
    project = requests.get(f"{API}/projects/{PROJECT_ID}", headers=headers).json()
    before = trace_count(headers)
    print(f"Project: {project['name']} ({PROJECT_ID})")
    print(f"Traces before: {before}")

    obs.init(api_key=project["api_key"], base_url=BASE_URL)
    client = instrument_openai(openai.OpenAI(api_key=openai_key))

    print("\nCalling OpenAI (gpt-4o-mini)...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello in exactly one short sentence."}],
        )
        print("Model replied:", response.choices[0].message.content)
    except Exception as exc:
        print(f"\nThe OpenAI call failed: {exc}")
        print("This is usually a billing/quota issue on the OpenAI account, not an SDK bug.")
        print("The failed call is still traced below (status=error) -- that's the SDK working correctly.")

    obs.shutdown()  # flush the background queue so the trace is actually delivered

    after = trace_count(headers)
    print(f"\nTraces after:  {after}  ({'+' if after >= before else ''}{after - before})")
    print(f"Refresh: http://localhost:5173/projects/{PROJECT_ID}/traces")


if __name__ == "__main__":
    main()
