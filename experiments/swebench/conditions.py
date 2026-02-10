"""SWE-bench experiment conditions: Baseline and LUCID."""

import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from ..common.llm_client import LLMClient
from .verifier import evaluate_single


# --- Prompts ---

SWEBENCH_GENERATE_SYSTEM = """You are an expert software engineer. You will be given a GitHub issue description and the current source code of relevant files from the repository. Your task is to generate a patch that fixes the issue.

Generate a unified diff patch (like `git diff` output) that can be applied with `git apply`. Include all necessary changes.

Rules:
- Output ONLY the patch in unified diff format
- Include proper file paths (a/ and b/ prefixes)
- Match the existing code EXACTLY — your diff context lines must match the source files provided
- Include at least 3 lines of context before and after each change
- Do not include any explanatory text before or after the patch
- Fix the specific issue described, nothing more"""

SWEBENCH_REMEDIATE_SYSTEM = """You are a debugging expert. Given a GitHub issue, a previous patch attempt, and the test results showing why it failed, generate a concrete fix plan.

Be specific:
- What was wrong with the previous patch
- What needs to change
- Key insights from the test output

Keep it concise — just the analysis and fix plan."""

SWEBENCH_REGENERATE_SYSTEM = """You are an expert software engineer. Your previous patch for a GitHub issue failed tests. Using the test feedback and fix plan, generate a corrected patch.

Generate a unified diff patch (like `git diff` output) that can be applied with `git apply`.

Rules:
- Output ONLY the corrected patch in unified diff format
- Include proper file paths (a/ and b/ prefixes)
- Include enough context lines
- Do not include any explanatory text
- Address the specific test failures mentioned in the feedback"""


def _clean_patch(raw: str) -> str:
    """Extract patch from LLM output, stripping markdown fences."""
    text = raw.strip()
    if text.startswith("```diff"):
        text = text[len("```diff"):].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    # Ensure it starts with diff
    lines = text.split("\n")
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("diff --git") or line.startswith("---") or line.startswith("+++"):
            start = i
            break
    return "\n".join(lines[start:])


def _get_affected_files(patch: str) -> list[str]:
    """Extract file paths from a unified diff patch."""
    files = []
    for line in patch.split("\n"):
        if line.startswith("diff --git"):
            # Extract b/ path
            parts = line.split(" b/")
            if len(parts) >= 2:
                files.append(parts[-1])
        elif line.startswith("+++ b/"):
            files.append(line[6:])
    return list(dict.fromkeys(files))  # dedupe preserving order


def _fetch_file_from_github(repo: str, commit: str, filepath: str) -> str | None:
    """Fetch a file from GitHub at a specific commit."""
    url = f"https://raw.githubusercontent.com/{repo}/{commit}/{filepath}"
    try:
        result = subprocess.run(
            ["curl", "-sL", "-f", url],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return result.stdout
    except subprocess.TimeoutExpired:
        pass
    return None


def _build_context(task: dict) -> str:
    """Build context string for the model from the task, including source files."""
    ctx = f"""Repository: {task['repo']}

## Issue Description

{task['problem_statement']}"""

    if task.get("hints_text"):
        ctx += f"\n\n## Hints\n\n{task['hints_text']}"

    # Oracle retrieval: get affected file paths from gold patch
    # This is standard practice in SWE-bench (reported as "oracle retrieval")
    affected_files = _get_affected_files(task.get("patch", ""))

    if affected_files:
        ctx += "\n\n## Relevant Source Files\n"
        for filepath in affected_files[:5]:  # Limit to 5 files
            content = _fetch_file_from_github(
                task["repo"], task["base_commit"], filepath
            )
            if content:
                # Truncate very large files
                if len(content) > 15000:
                    content = content[:15000] + "\n... (truncated)"
                ctx += f"\n### {filepath}\n```python\n{content}\n```\n"

    # Include the test names that need to pass (gives the model a target)
    if task.get("fail_to_pass"):
        tests = task["fail_to_pass"]
        if isinstance(tests, str):
            tests = json.loads(tests)
        ctx += f"\n\n## Tests That Must Pass After Fix\n\n"
        for t in tests:
            ctx += f"- {t}\n"

    return ctx


def run_baseline_swe(client: LLMClient, task: dict) -> dict:
    """Single-pass patch generation for SWE-bench."""
    context = _build_context(task)
    instance_id = task["instance_id"]

    patch = client.complete(
        system=SWEBENCH_GENERATE_SYSTEM,
        user=context,
        temperature=0.7,
        max_tokens=4096,
        task_id=instance_id,
        condition="baseline",
        iteration=0,
        role="generate",
    )
    patch = _clean_patch(patch)

    # Evaluate
    result = evaluate_single(instance_id, patch, model_name="baseline")

    return {
        "task_id": instance_id,
        "condition": "baseline",
        "max_iterations": 1,
        "final_passed": result["resolved"],
        "final_test_output": result,
        "iterations": [],
        "solution": patch,
    }


def run_lucid_swe(
    client: LLMClient,
    task: dict,
    max_iter: int,
    ablation: Optional[str] = None,
) -> dict:
    """LUCID loop for SWE-bench: generate patch → run tests → remediate → regenerate."""
    context = _build_context(task)
    instance_id = task["instance_id"]
    condition_name = "lucid" if not ablation else f"lucid-{ablation}"

    # Initial generation
    patch = client.complete(
        system=SWEBENCH_GENERATE_SYSTEM,
        user=context,
        temperature=0.7,
        max_tokens=4096,
        task_id=instance_id,
        condition=condition_name,
        iteration=0,
        role="generate",
    )
    patch = _clean_patch(patch)

    iterations = []

    for i in range(1, max_iter + 1):
        # FORMAL VERIFICATION: run tests via Docker
        result = evaluate_single(
            instance_id,
            patch,
            model_name=condition_name,
            run_id=f"{condition_name}_k{max_iter}_iter{i}",
        )

        if result["resolved"]:
            iterations.append({
                "iteration": i,
                "verification": "ALL TESTS PASSED",
                "passed": True,
                "early_stop": True,
            })
            break

        # Build feedback from test output
        test_output = result.get("test_output", "Tests failed (no output)")
        verification_feedback = f"TESTS FAILED.\n\nTest output:\n{test_output[-3000:]}"

        # REMEDIATE: analyze failure
        remediation = client.complete(
            system=SWEBENCH_REMEDIATE_SYSTEM,
            user=f"## Issue\n{context}\n\n## Previous Patch\n```diff\n{patch}\n```\n\n## Test Results\n{verification_feedback}",
            temperature=0.0,
            max_tokens=2048,
            task_id=instance_id,
            condition=condition_name,
            iteration=i,
            role="remediate",
        )

        # REGENERATE: new patch attempt
        new_patch = client.complete(
            system=SWEBENCH_REGENERATE_SYSTEM,
            user=f"## Issue\n{context}\n\n## Previous Patch (failed)\n```diff\n{patch}\n```\n\n## Test Feedback\n{verification_feedback}\n\n## Fix Plan\n{remediation}",
            temperature=0.7,
            max_tokens=4096,
            task_id=instance_id,
            condition=condition_name,
            iteration=i,
            role="regenerate",
        )
        new_patch = _clean_patch(new_patch)

        iterations.append({
            "iteration": i,
            "verification": verification_feedback[:1000],
            "remediation": remediation[:1000],
            "passed": False,
        })

        patch = new_patch

    # Final evaluation
    final_result = evaluate_single(
        instance_id,
        patch,
        model_name=condition_name,
        run_id=f"{condition_name}_k{max_iter}_final",
    )

    return {
        "task_id": instance_id,
        "condition": condition_name,
        "max_iterations": max_iter,
        "final_passed": final_result["resolved"],
        "final_test_output": final_result,
        "iterations": iterations,
        "solution": patch,
        "ablation": ablation,
    }
