"""Seeds a demo project with realistic-looking trace data against a running
backend. Useful before a demo/recording so the analytics view has real
percentiles and a mixed error rate instead of one lonely trace.

Usage:
    cd backend && .venv/Scripts/python -m uvicorn app.main:app --port 8000  # in one terminal
    sdk/.venv/Scripts/python scripts/seed_demo_data.py                      # in another

Requires `requests` (already in the SDK's venv, or `pip install requests`).
"""

import os
import random

import requests

BASE = os.environ.get("LLMOBS_DEMO_BASE_URL", "http://127.0.0.1:8000") + "/api/v1"
DEMO_EMAIL = "demo@polaris.edu"
DEMO_PASSWORD = "DemoViva2026!"

PROMPTS = [
    ("Summarize this quarterly report", "Revenue grew 12% QoQ, driven by the enterprise segment."),
    ("Write a product description for a wireless mouse", "Ergonomic, silent-click, 18-month battery life."),
    ("Classify this support ticket", "Category: billing. Priority: medium."),
    ("Translate 'good morning' to French", "Bonjour"),
    ("Extract the invoice total from this text", "Total: $1,240.50"),
    ("Generate a commit message for this diff", "fix: handle null pointer in user session lookup"),
    ("Answer: what is the capital of Japan?", "Tokyo"),
    ("Draft a reply to this customer complaint", "We're sorry for the inconvenience and are issuing a refund."),
]

MODELS = [
    {"name": "gpt-4o", "provider": "openai", "latency_range": (280, 650), "cost_per_1k": (0.005, 0.015)},
    {"name": "gpt-4o-mini", "provider": "openai", "latency_range": (120, 320), "cost_per_1k": (0.00015, 0.0006)},
    {"name": "claude-sonnet-5", "provider": "anthropic", "latency_range": (350, 800), "cost_per_1k": (0.002, 0.010)},
]

ERROR_MESSAGES = ["rate limited by provider", "request timed out", "context length exceeded"]


def register_and_login() -> str:
    requests.post(f"{BASE}/auth/register", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    resp = requests.post(f"{BASE}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    resp.raise_for_status()
    return resp.json()["access_token"]


def create_project(token: str) -> dict:
    resp = requests.post(
        f"{BASE}/projects",
        json={"name": "LLM Observability Demo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()


def build_trace(model_info: dict) -> dict:
    prompt, completion = random.choice(PROMPTS)
    is_error = random.random() < 0.12
    prompt_tokens = random.randint(15, 80)
    completion_tokens = 0 if is_error else random.randint(5, 60)
    input_price, output_price = model_info["cost_per_1k"]
    cost = round((prompt_tokens / 1000) * input_price + (completion_tokens / 1000) * output_price, 6)
    latency = round(random.uniform(*model_info["latency_range"]), 1)

    trace = {
        "model": model_info["name"],
        "provider": model_info["provider"],
        "prompt": prompt,
        "latency_ms": latency,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost": cost,
        "status": "error" if is_error else "success",
        "tags": {"env": "demo"},
    }
    if is_error:
        trace["error_message"] = random.choice(ERROR_MESSAGES)
    else:
        trace["completion"] = completion
    return trace


def seed_traces(api_key: str, count: int = 40) -> None:
    traces = [build_trace(random.choice(MODELS)) for _ in range(count)]
    resp = requests.post(f"{BASE}/traces", json={"traces": traces}, headers={"X-API-Key": api_key})
    resp.raise_for_status()
    print("Ingested:", resp.json())


def main() -> None:
    token = register_and_login()
    project = create_project(token)
    seed_traces(project["api_key"], count=40)

    print("\n=== Demo credentials ===")
    print(f"Email:      {DEMO_EMAIL}")
    print(f"Password:   {DEMO_PASSWORD}")
    print(f"Project ID: {project['id']}")
    print(f"API key:    {project['api_key']}")
    print(f"JWT token:  {token}")


if __name__ == "__main__":
    main()
