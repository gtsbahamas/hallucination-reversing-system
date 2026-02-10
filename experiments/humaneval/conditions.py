"""Experiment conditions: Baseline, Self-Refine, LLM-as-Judge, LUCID."""

import json
import sys
from typing import Optional

from ..common.llm_client import LLMClient
from .verifier import execute_tests

# --- Prompts ---

GENERATE_SYSTEM = """You are an expert Python programmer. Implement the function exactly as specified by the docstring. Return ONLY the complete function implementation starting with 'def'. No explanations, no markdown fences, no extra text."""

EXTRACT_SYSTEM = """You are analyzing a Python function implementation. Extract testable claims from the code.

For the given function signature/docstring and implementation, list specific claims the code makes:
- What inputs it handles (edge cases, types)
- What it returns for specific inputs
- Algorithmic approach used
- Error handling behavior

Return a JSON array of claim strings. Example:
["handles empty list by returning 0", "uses sorting to find median", "returns float for even-length lists"]

Return ONLY the JSON array. No markdown fences."""

SELF_REFINE_SYSTEM = """You are reviewing a Python function for correctness. The function should match its docstring specification exactly.

Identify any bugs, edge cases not handled, or incorrect logic. Be specific about what is wrong and how to fix it.

Structure your response as:
ISSUES FOUND:
1. [issue description]
2. [issue description]
...

If the code is correct, say "NO ISSUES FOUND"."""

LLM_JUDGE_SYSTEM = """You are a code correctness judge. Evaluate whether this function implementation matches its specification.

For each aspect of the specification, assign a verdict:
- PASS: Correctly implemented
- FAIL: Incorrectly implemented or missing

Return a JSON array:
[{"claim": "description", "verdict": "PASS|FAIL", "reasoning": "why"}]

Return ONLY the JSON array. No markdown fences."""

REMEDIATE_SYSTEM = """You are a Python debugging expert. Given a function, its specification, and feedback about what's wrong, generate a concrete fix plan.

Be specific:
- Which lines need to change
- What the fix should be
- Why this fixes the issue

Keep it concise — just the fix plan, not the implementation."""

REGENERATE_SYSTEM = """You are an expert Python programmer. You previously attempted to implement a function but there were issues. Using the feedback and fix plan provided, generate a corrected implementation.

Return ONLY the complete function implementation starting with 'def'. No explanations, no markdown fences, no extra text."""


def _clean_solution(raw: str) -> str:
    """Strip markdown fences and extra text from LLM output."""
    text = raw.strip()
    if text.startswith("```python"):
        text = text[len("```python"):].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text


def run_baseline(client: LLMClient, task: dict) -> dict:
    """Single-pass generation, no iteration."""
    prompt = task["prompt"]
    entry_point = task["entry_point"]
    test_code = task["test"]

    solution = client.complete(
        system=GENERATE_SYSTEM,
        user=f"Implement this function:\n\n{prompt}",
        temperature=0.7,
        max_tokens=2048,
        task_id=task["task_id"],
        condition="baseline",
        iteration=0,
        role="generate",
    )
    solution = _clean_solution(solution)

    test_result = execute_tests(solution, prompt, test_code, entry_point)

    return {
        "task_id": task["task_id"],
        "condition": "baseline",
        "max_iterations": 1,
        "final_passed": test_result["all_passed"],
        "final_test_output": test_result,
        "iterations": [],
        "solution": solution,
    }


def run_self_refine(client: LLMClient, task: dict, max_iter: int) -> dict:
    """Self-Refine: LLM critiques its own code without test execution."""
    prompt = task["prompt"]
    entry_point = task["entry_point"]
    test_code = task["test"]

    solution = client.complete(
        system=GENERATE_SYSTEM,
        user=f"Implement this function:\n\n{prompt}",
        temperature=0.7,
        max_tokens=2048,
        task_id=task["task_id"],
        condition="self-refine",
        iteration=0,
        role="generate",
    )
    solution = _clean_solution(solution)

    iterations = []

    for i in range(1, max_iter + 1):
        # Extract claims
        claims_raw = client.complete(
            system=EXTRACT_SYSTEM,
            user=f"Function specification:\n{prompt}\n\nImplementation:\n{solution}",
            temperature=0.0,
            max_tokens=2048,
            task_id=task["task_id"],
            condition="self-refine",
            iteration=i,
            role="extract",
        )

        # Self-critique (NO test execution)
        critique = client.complete(
            system=SELF_REFINE_SYSTEM,
            user=f"Function specification:\n{prompt}\n\nImplementation:\n{solution}",
            temperature=0.0,
            max_tokens=2048,
            task_id=task["task_id"],
            condition="self-refine",
            iteration=i,
            role="verify",
        )

        # Check if self-refine thinks it's correct
        if "NO ISSUES FOUND" in critique.upper():
            test_result = execute_tests(solution, prompt, test_code, entry_point)
            iterations.append({
                "iteration": i,
                "verification": critique,
                "passed": test_result["all_passed"],
                "early_stop": True,
            })
            break

        # Remediate
        remediation = client.complete(
            system=REMEDIATE_SYSTEM,
            user=f"Function specification:\n{prompt}\n\nCurrent implementation:\n{solution}\n\nIssues found:\n{critique}",
            temperature=0.0,
            max_tokens=2048,
            task_id=task["task_id"],
            condition="self-refine",
            iteration=i,
            role="remediate",
        )

        # Regenerate
        new_solution = client.complete(
            system=REGENERATE_SYSTEM,
            user=f"Function specification:\n{prompt}\n\nPrevious (buggy) implementation:\n{solution}\n\nFeedback:\n{critique}\n\nFix plan:\n{remediation}",
            temperature=0.7,
            max_tokens=2048,
            task_id=task["task_id"],
            condition="self-refine",
            iteration=i,
            role="regenerate",
        )
        new_solution = _clean_solution(new_solution)

        test_result = execute_tests(new_solution, prompt, test_code, entry_point)
        iterations.append({
            "iteration": i,
            "verification": critique,
            "remediation": remediation,
            "passed": test_result["all_passed"],
        })

        solution = new_solution

    final_result = execute_tests(solution, prompt, test_code, entry_point)
    return {
        "task_id": task["task_id"],
        "condition": "self-refine",
        "max_iterations": max_iter,
        "final_passed": final_result["all_passed"],
        "final_test_output": final_result,
        "iterations": iterations,
        "solution": solution,
    }


def run_llm_judge(client: LLMClient, task: dict, max_iter: int) -> dict:
    """LLM-as-Judge: separate LLM instance judges correctness."""
    prompt = task["prompt"]
    entry_point = task["entry_point"]
    test_code = task["test"]

    solution = client.complete(
        system=GENERATE_SYSTEM,
        user=f"Implement this function:\n\n{prompt}",
        temperature=0.7,
        max_tokens=2048,
        task_id=task["task_id"],
        condition="llm-judge",
        iteration=0,
        role="generate",
    )
    solution = _clean_solution(solution)

    iterations = []

    for i in range(1, max_iter + 1):
        # Extract claims
        claims_raw = client.complete(
            system=EXTRACT_SYSTEM,
            user=f"Function specification:\n{prompt}\n\nImplementation:\n{solution}",
            temperature=0.0,
            max_tokens=2048,
            task_id=task["task_id"],
            condition="llm-judge",
            iteration=i,
            role="extract",
        )

        # LLM Judge (NO test execution)
        judgment = client.complete(
            system=LLM_JUDGE_SYSTEM,
            user=f"Function specification:\n{prompt}\n\nImplementation:\n{solution}",
            temperature=0.0,
            max_tokens=2048,
            task_id=task["task_id"],
            condition="llm-judge",
            iteration=i,
            role="verify",
        )

        # Check if all verdicts are PASS
        all_pass = False
        try:
            verdicts = json.loads(judgment.strip().strip("`").strip())
            if isinstance(verdicts, list):
                all_pass = all(v.get("verdict") == "PASS" for v in verdicts)
        except (json.JSONDecodeError, AttributeError):
            pass

        if all_pass:
            test_result = execute_tests(solution, prompt, test_code, entry_point)
            iterations.append({
                "iteration": i,
                "verification": judgment,
                "passed": test_result["all_passed"],
                "early_stop": True,
            })
            break

        # Remediate
        remediation = client.complete(
            system=REMEDIATE_SYSTEM,
            user=f"Function specification:\n{prompt}\n\nCurrent implementation:\n{solution}\n\nJudge assessment:\n{judgment}",
            temperature=0.0,
            max_tokens=2048,
            task_id=task["task_id"],
            condition="llm-judge",
            iteration=i,
            role="remediate",
        )

        # Regenerate
        new_solution = client.complete(
            system=REGENERATE_SYSTEM,
            user=f"Function specification:\n{prompt}\n\nPrevious implementation:\n{solution}\n\nJudge feedback:\n{judgment}\n\nFix plan:\n{remediation}",
            temperature=0.7,
            max_tokens=2048,
            task_id=task["task_id"],
            condition="llm-judge",
            iteration=i,
            role="regenerate",
        )
        new_solution = _clean_solution(new_solution)

        test_result = execute_tests(new_solution, prompt, test_code, entry_point)
        iterations.append({
            "iteration": i,
            "verification": judgment,
            "remediation": remediation,
            "passed": test_result["all_passed"],
        })

        solution = new_solution

    final_result = execute_tests(solution, prompt, test_code, entry_point)
    return {
        "task_id": task["task_id"],
        "condition": "llm-judge",
        "max_iterations": max_iter,
        "final_passed": final_result["all_passed"],
        "final_test_output": final_result,
        "iterations": iterations,
        "solution": solution,
    }


def run_lucid(client: LLMClient, task: dict, max_iter: int, ablation: Optional[str] = None) -> dict:
    """
    LUCID: Formal verification via test execution.
    This is the key condition — the incorruptible oracle.

    Ablation variants:
    - None: Full LUCID loop
    - "no-extract": Skip claim extraction, pass raw output to verifier
    - "no-remediate": Skip remediation, pass raw test results to regenerator
    - "learned-verify": Replace test execution with LLM judgment
    - "no-context": Regenerate from scratch each iteration
    - "random-verify": Replace verifier with random pass/fail
    """
    prompt = task["prompt"]
    entry_point = task["entry_point"]
    test_code = task["test"]

    solution = client.complete(
        system=GENERATE_SYSTEM,
        user=f"Implement this function:\n\n{prompt}",
        temperature=0.7,
        max_tokens=2048,
        task_id=task["task_id"],
        condition="lucid" if not ablation else f"lucid-{ablation}",
        iteration=0,
        role="generate",
    )
    solution = _clean_solution(solution)

    iterations = []
    condition_name = "lucid" if not ablation else f"lucid-{ablation}"

    for i in range(1, max_iter + 1):
        # Step 1: Extract claims (skip if ablation == "no-extract")
        if ablation != "no-extract":
            claims_raw = client.complete(
                system=EXTRACT_SYSTEM,
                user=f"Function specification:\n{prompt}\n\nImplementation:\n{solution}",
                temperature=0.0,
                max_tokens=2048,
                task_id=task["task_id"],
                condition=condition_name,
                iteration=i,
                role="extract",
            )

        # Step 2: FORMAL VERIFICATION — execute tests
        if ablation == "learned-verify":
            # Ablation: use LLM judgment instead of test execution
            verification_text = client.complete(
                system=LLM_JUDGE_SYSTEM,
                user=f"Function specification:\n{prompt}\n\nImplementation:\n{solution}",
                temperature=0.0,
                max_tokens=2048,
                task_id=task["task_id"],
                condition=condition_name,
                iteration=i,
                role="verify",
            )
            test_result = execute_tests(solution, prompt, test_code, entry_point)
            verification_feedback = verification_text
        elif ablation == "random-verify":
            # Ablation: random feedback
            import random
            test_result = execute_tests(solution, prompt, test_code, entry_point)
            verification_feedback = random.choice([
                "The implementation looks correct.",
                "FAIL: The implementation has bugs in edge case handling.",
                "FAIL: The return type is incorrect for some inputs.",
            ])
        else:
            # REAL formal verification
            test_result = execute_tests(solution, prompt, test_code, entry_point)
            if test_result["all_passed"]:
                verification_feedback = "ALL TESTS PASSED. Implementation is correct."
            else:
                verification_feedback = f"TESTS FAILED.\nReturn code: {test_result['returncode']}\nError type: {test_result.get('error_type', 'unknown')}\nStderr:\n{test_result['stderr']}\nStdout:\n{test_result['stdout']}"

        # Early stop if all tests pass (for real verification only)
        if ablation not in ("learned-verify", "random-verify") and test_result["all_passed"]:
            iterations.append({
                "iteration": i,
                "verification": verification_feedback,
                "passed": True,
                "early_stop": True,
            })
            break

        # Step 3: Remediate (skip if ablation == "no-remediate")
        if ablation != "no-remediate":
            remediation = client.complete(
                system=REMEDIATE_SYSTEM,
                user=f"Function specification:\n{prompt}\n\nCurrent implementation:\n{solution}\n\nTest results:\n{verification_feedback}",
                temperature=0.0,
                max_tokens=2048,
                task_id=task["task_id"],
                condition=condition_name,
                iteration=i,
                role="remediate",
            )
        else:
            remediation = verification_feedback  # Pass raw feedback

        # Step 4: Regenerate
        if ablation == "no-context":
            # Ablation: regenerate from scratch (no previous solution context)
            regen_prompt = f"Function specification:\n{prompt}\n\nPrevious attempt had these issues:\n{verification_feedback}\n\nFix plan:\n{remediation}"
        else:
            regen_prompt = f"Function specification:\n{prompt}\n\nPrevious implementation:\n{solution}\n\nTest feedback:\n{verification_feedback}\n\nFix plan:\n{remediation}"

        new_solution = client.complete(
            system=REGENERATE_SYSTEM,
            user=regen_prompt,
            temperature=0.7,
            max_tokens=2048,
            task_id=task["task_id"],
            condition=condition_name,
            iteration=i,
            role="regenerate",
        )
        new_solution = _clean_solution(new_solution)

        iterations.append({
            "iteration": i,
            "verification": verification_feedback,
            "remediation": remediation if ablation != "no-remediate" else None,
            "passed": test_result["all_passed"],
        })

        solution = new_solution

    final_result = execute_tests(solution, prompt, test_code, entry_point)
    return {
        "task_id": task["task_id"],
        "condition": condition_name,
        "max_iterations": max_iter,
        "final_passed": final_result["all_passed"],
        "final_test_output": final_result,
        "iterations": iterations,
        "solution": solution,
        "ablation": ablation,
    }


# Dispatch table
CONDITION_RUNNERS = {
    "baseline": run_baseline,
    "self-refine": run_self_refine,
    "llm-judge": run_llm_judge,
    "lucid": run_lucid,
}
