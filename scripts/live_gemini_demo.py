"""Sends ONE real Gemini call through the SDK's manual trace() wrapper,
proving the pipeline end to end with a genuine model response.

There's no instrument_gemini() built into the SDK yet (only OpenAI and
Anthropic have dedicated wrappers), so this uses the manual `trace()`
context manager, the documented path for any provider without one -- see
sdk/README.md.

Needs a real Gemini API key, read from the GEMINI_API_KEY environment
variable -- never pass it on the command line or hardcode it here.

Usage (backend must be running on :8000, GEMINI_API_KEY set in this shell):
    $env:GEMINI_API_KEY = "..."          # set once, in this terminal only
    sdk/.venv/Scripts/python.exe scripts\\live_gemini_demo.py
    sdk/.venv/Scripts/python.exe scripts\\live_gemini_demo.py "any prompt here"
"""

import os
import sys
import time

import requests
from google import genai

import llm_observability_sdk as obs

BASE_URL = os.environ.get("LLMOBS_DEMO_BASE_URL", "http://127.0.0.1:8000")
API = BASE_URL + "/api/v1"
DEMO_EMAIL = "demo@polaris.edu"
DEMO_PASSWORD = "DemoViva2026!"
PROJECT_ID = "bd6d6c47-7664-41e1-b60a-bcfcbe33d024"  # "LLM Observability Demo"
MODEL = "gemini-3.8-flash"  # free-tier model


def login_headers() -> dict:
    resp = requests.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    resp.raise_for_status()
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def trace_count(headers: dict) -> int:
    resp = requests.get(f"{API}/projects/{PROJECT_ID}/traces", params={"limit": 1}, headers=headers)
    resp.raise_for_status()
    return resp.json()["total"]


def main() -> None:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("GEMINI_API_KEY is not set in this shell. Set it first:")
        print('  $env:GEMINI_API_KEY = "..."')
        sys.exit(1)

    headers = login_headers()
    project = requests.get(f"{API}/projects/{PROJECT_ID}", headers=headers).json()
    before = trace_count(headers)
    print(f"Project: {project['name']} ({PROJECT_ID})")
    print(f"Traces before: {before}")

    obs.init(api_key=project["api_key"], base_url=BASE_URL)
    client = genai.Client(api_key=gemini_key)

    # Any text after the script name is the prompt (so a prompt given live
    # by someone else can be typed straight onto the command line). Falls
    # back to a fixed prompt when run with no arguments.
    prompt = " ".join(sys.argv[1:]) or "Say hello in exactly one short sentence."

    print(f"\nPrompt: {prompt}")
    print(f"Calling Gemini ({MODEL})...")
    try:
        with obs.trace(model=MODEL, provider="google", prompt=prompt) as t:
            start = time.perf_counter()
            response = client.models.generate_content(model=MODEL, contents=prompt)
            usage = response.usage_metadata
            t.set_completion(
                completion=response.text,
                prompt_tokens=getattr(usage, "prompt_token_count", 0) or 0,
                completion_tokens=getattr(usage, "candidates_token_count", 0) or 0,
                cost=0.0,  # Gemini isn't in the SDK's pricing table; left at 0 rather than guessed
            )
        print("Model replied:", response.text)
    except Exception as exc:
        print(f"\nThe Gemini call failed: {exc}")
        print("The failed call is still traced below (status=error) -- that's the SDK working correctly.")

    obs.shutdown()  # flush the background queue so the trace is actually delivered

    after = trace_count(headers)
    print(f"\nTraces after:  {after}  ({'+' if after >= before else ''}{after - before})")
    print(f"Refresh: http://localhost:5173/projects/{PROJECT_ID}/traces")


if __name__ == "__main__":
    main()
