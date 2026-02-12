#!/usr/bin/env python3
"""Generate baseline code for all 10 tasks using raw Claude API calls."""

import os
import sys
import json
import time
import subprocess

import anthropic

TASKS = [
    ("task_01", "Write a middleware that validates JWT tokens, checks expiration, handles refresh tokens, and attaches user context to the request"),
    ("task_02", "Write a sliding window rate limiter that supports per-user and per-endpoint limits with Redis-compatible storage"),
    ("task_03", "Write a webhook receiver that validates HMAC signatures, handles retries/deduplication, and processes events asynchronously"),
    ("task_04", "Write a migration system that supports up/down migrations, tracks applied migrations, and handles failures with rollback"),
    ("task_05", "Write a file upload handler that validates file types, enforces size limits, scans for malware signatures, and stores to S3-compatible storage"),
    ("task_06", "Write cursor-based pagination for a REST API that handles sorting, filtering, and returns consistent results under concurrent writes"),
    ("task_07", "Write a configuration loader that validates YAML/JSON config against a schema, supports environment variable interpolation, and provides helpful error messages"),
    ("task_08", "Write an HTTP client wrapper with exponential backoff retry, circuit breaker pattern, timeout handling, and request/response logging"),
    ("task_09", "Write an event store that appends events, rebuilds aggregate state, supports snapshots, and handles concurrent writes with optimistic locking"),
    ("task_10", "Write an input sanitization library that prevents XSS, SQL injection, and path traversal while preserving legitimate content"),
]

MODEL = "claude-sonnet-4-5-20250929"
SYSTEM_PROMPT = "You are an expert Python programmer. Generate production-quality code. Return ONLY the code. No markdown fences, no explanations. Include type hints and docstrings."


def get_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", "claude-code", "-a", "anthropic-api-key", "-w"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    raise RuntimeError("ANTHROPIC_API_KEY not found")


def generate_baseline(client, task_id, task_desc, output_dir):
    output_path = os.path.join(output_dir, f"{task_id}.py")
    meta_path = os.path.join(output_dir, f"{task_id}.meta.json")

    if os.path.exists(output_path):
        print(f"  SKIP {task_id} (already exists)")
        return

    print(f"  Generating {task_id}...")
    start = time.time()

    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Generate Python code for: {task_desc}"}],
    )

    code = response.content[0].text
    duration = time.time() - start

    # Strip markdown fences if present
    if code.startswith("```"):
        lines = code.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines)

    with open(output_path, "w") as f:
        f.write(code)

    meta = {
        "task_id": task_id,
        "task": task_desc,
        "model": MODEL,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "duration_s": round(duration, 1),
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"  OK {task_id} ({response.usage.input_tokens}+{response.usage.output_tokens} tokens, {duration:.1f}s)")


def main():
    output_dir = os.path.join(os.path.dirname(__file__), "baseline")
    os.makedirs(output_dir, exist_ok=True)

    api_key = get_api_key()
    client = anthropic.Anthropic(api_key=api_key)

    print(f"\n=== CONDITION A: RAW CLAUDE BASELINE ===")
    print(f"Model: {MODEL}")
    print(f"Output: {output_dir}\n")

    for task_id, task_desc in TASKS:
        generate_baseline(client, task_id, task_desc, output_dir)

    print(f"\nDone. {len(TASKS)} files generated.\n")


if __name__ == "__main__":
    main()
