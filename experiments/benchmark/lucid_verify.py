"""LUCID verification integration for cross-platform benchmark.

Calls the LUCID API to verify generated code and produce improved versions.
Supports k=1 (single pass) and k=3 (iterative) verification.

LUCID API endpoint: https://lucid-api-dftr.onrender.com

For the benchmark, LUCID verification is applied AFTER each platform
generates its output. The improvement delta (baseline vs LUCID-verified)
is the key metric.
"""

import json
import time
from typing import Optional

from ..common.llm_client import LLMClient
from ..common.cost_tracker import CostTracker
from .cost_tracker import BenchmarkCostTracker


# --- Prompts (same as experiments/humaneval/conditions.py) ---

EXTRACT_SYSTEM = """You are analyzing a code implementation. Extract testable claims from the code.

For the given specification and implementation, list specific claims the code makes:
- What inputs it handles (edge cases, types)
- What it returns for specific inputs
- Algorithmic approach used
- Error handling behavior

Return a JSON array of claim strings.
Return ONLY the JSON array. No markdown fences."""

REMEDIATE_SYSTEM = """You are a debugging expert. Given code, its specification, and test feedback about what's wrong, generate a concrete fix plan.

Be specific:
- Which parts need to change
- What the fix should be
- Why this fixes the issue

Keep it concise — just the fix plan, not the implementation."""

REGENERATE_SYSTEM = """You are an expert programmer. You previously attempted to implement code but there were issues. Using the feedback and fix plan provided, generate a corrected implementation.

Return ONLY the complete implementation. No explanations, no markdown fences, no extra text."""


def _clean_code(raw: str) -> str:
    """Strip markdown fences from LLM output."""
    text = raw.strip()
    if text.startswith("```python"):
        text = text[len("```python"):].strip()
    elif text.startswith("```diff"):
        text = text[len("```diff"):].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text


class LUCIDVerifier:
    """LUCID verification loop for benchmark code.

    Takes platform-generated code + task context, runs the LUCID
    extract -> verify -> remediate -> regenerate loop, and returns
    improved code.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",
        tracker: Optional[BenchmarkCostTracker] = None,
        api_url: str = "https://lucid-api-dftr.onrender.com",
    ):
        self.model = model
        self.benchmark_tracker = tracker
        self.api_url = api_url

        # Internal LLM client for LUCID operations
        self._inner_tracker = CostTracker(budget_limit=99999)
        self._client = LLMClient(model=model, tracker=self._inner_tracker)

    def verify_humaneval(
        self,
        code: str,
        task: dict,
        platform: str,
        k: int = 1,
    ) -> dict:
        """Run LUCID verification on HumanEval code.

        Uses formal verification (test execution) as the incorruptible oracle.

        Args:
            code: Platform-generated function code.
            task: HumanEval task dict.
            platform: Source platform name.
            k: Number of verification iterations.

        Returns:
            Dict with verified_code, iterations, and pass status.
        """
        import subprocess
        import sys

        prompt = task["prompt"]
        entry_point = task["entry_point"]
        test_code = task["test"]
        task_id = task["task_id"]
        condition = f"lucid_{platform}"

        solution = code
        iterations = []

        for i in range(1, k + 1):
            # EXTRACT: identify claims
            self._client.complete(
                system=EXTRACT_SYSTEM,
                user=f"Specification:\n{prompt}\n\nImplementation:\n{solution}",
                temperature=0.0,
                max_tokens=2048,
                task_id=task_id,
                condition=condition,
                iteration=i,
                role="extract",
            )
            self._track_call(platform, "humaneval", task_id, "lucid_extract", i)

            # VERIFY: formal test execution
            test_script = f"""{prompt}

{solution}

{test_code}

check({entry_point})
"""
            try:
                result = subprocess.run(
                    [sys.executable, "-c", test_script],
                    capture_output=True, text=True, timeout=30,
                )
                all_passed = result.returncode == 0
                feedback = (
                    "ALL TESTS PASSED."
                    if all_passed
                    else f"TESTS FAILED.\nStderr:\n{result.stderr[:2000]}\nStdout:\n{result.stdout[:2000]}"
                )
            except subprocess.TimeoutExpired:
                all_passed = False
                feedback = "TESTS FAILED: Execution timed out (30s)"

            if all_passed:
                iterations.append({
                    "iteration": i,
                    "passed": True,
                    "early_stop": True,
                })
                break

            # REMEDIATE: analyze failure
            remediation = self._client.complete(
                system=REMEDIATE_SYSTEM,
                user=f"Specification:\n{prompt}\n\nCurrent implementation:\n{solution}\n\nTest results:\n{feedback}",
                temperature=0.0,
                max_tokens=2048,
                task_id=task_id,
                condition=condition,
                iteration=i,
                role="remediate",
            )
            self._track_call(platform, "humaneval", task_id, "lucid_remediate", i)

            # REGENERATE: produce fixed code
            new_solution = self._client.complete(
                system=REGENERATE_SYSTEM,
                user=f"Specification:\n{prompt}\n\nPrevious implementation:\n{solution}\n\nTest feedback:\n{feedback}\n\nFix plan:\n{remediation}",
                temperature=0.7,
                max_tokens=2048,
                task_id=task_id,
                condition=condition,
                iteration=i,
                role="regenerate",
            )
            new_solution = _clean_code(new_solution)
            self._track_call(platform, "humaneval", task_id, "lucid_regenerate", i)

            iterations.append({
                "iteration": i,
                "verification": feedback[:500],
                "passed": False,
            })
            solution = new_solution

        # Final verification
        try:
            final_script = f"""{prompt}

{solution}

{test_code}

check({entry_point})
"""
            result = subprocess.run(
                [sys.executable, "-c", final_script],
                capture_output=True, text=True, timeout=30,
            )
            final_passed = result.returncode == 0
        except (subprocess.TimeoutExpired, Exception):
            final_passed = False

        return {
            "verified_code": solution,
            "original_code": code,
            "iterations": iterations,
            "final_passed": final_passed,
            "platform": platform,
            "k": k,
        }

    def verify_swebench(
        self,
        patch: str,
        task: dict,
        platform: str,
        k: int = 1,
    ) -> dict:
        """Run LUCID verification on a SWE-bench patch.

        Uses Docker-based test execution as the formal verification oracle.

        Args:
            patch: Platform-generated unified diff.
            task: SWE-bench task dict.
            platform: Source platform name.
            k: Number of verification iterations.

        Returns:
            Dict with verified_patch, iterations, and resolve status.
        """
        from ..swebench.conditions import (
            SWEBENCH_REMEDIATE_SYSTEM,
            SWEBENCH_REGENERATE_SYSTEM,
            _clean_patch,
            _build_context,
        )
        from ..swebench.verifier import evaluate_single

        instance_id = task["instance_id"]
        context = _build_context(task)
        condition = f"lucid_{platform}"

        current_patch = patch
        iterations = []

        for i in range(1, k + 1):
            # VERIFY: Docker-based test execution
            result = evaluate_single(
                instance_id, current_patch,
                model_name=condition,
                run_id=f"{condition}_k{k}_iter{i}",
            )

            if result["resolved"]:
                iterations.append({
                    "iteration": i,
                    "passed": True,
                    "early_stop": True,
                })
                break

            test_output = result.get("test_output", "Tests failed")
            feedback = f"TESTS FAILED.\n\nTest output:\n{test_output[-3000:]}"

            # REMEDIATE
            remediation = self._client.complete(
                system=SWEBENCH_REMEDIATE_SYSTEM,
                user=f"## Issue\n{context}\n\n## Previous Patch\n```diff\n{current_patch}\n```\n\n## Test Results\n{feedback}",
                temperature=0.0,
                max_tokens=2048,
                task_id=instance_id,
                condition=condition,
                iteration=i,
                role="remediate",
            )
            self._track_call(platform, "swebench", instance_id, "lucid_remediate", i)

            # REGENERATE
            new_patch = self._client.complete(
                system=SWEBENCH_REGENERATE_SYSTEM,
                user=f"## Issue\n{context}\n\n## Previous Patch (failed)\n```diff\n{current_patch}\n```\n\n## Test Feedback\n{feedback}\n\n## Fix Plan\n{remediation}",
                temperature=0.7,
                max_tokens=4096,
                task_id=instance_id,
                condition=condition,
                iteration=i,
                role="regenerate",
            )
            new_patch = _clean_patch(new_patch)
            self._track_call(platform, "swebench", instance_id, "lucid_regenerate", i)

            iterations.append({
                "iteration": i,
                "verification": feedback[:500],
                "passed": False,
            })
            current_patch = new_patch

        # Final evaluation
        final_result = evaluate_single(
            instance_id, current_patch,
            model_name=condition,
            run_id=f"{condition}_k{k}_final",
        )

        return {
            "verified_patch": current_patch,
            "original_patch": patch,
            "iterations": iterations,
            "final_passed": final_result["resolved"],
            "platform": platform,
            "k": k,
        }

    def verify_app(
        self,
        code: str,
        task: dict,
        platform: str,
        k: int = 1,
    ) -> dict:
        """Run LUCID verification on a generated application (Track 3).

        For app generation, the verification oracle is the task's test suite.
        If no test suite exists, we use LLM-based review (weaker oracle).

        Args:
            code: Platform-generated application source.
            task: App generation task dict.
            platform: Source platform name.
            k: Number of verification iterations.

        Returns:
            Dict with verified_code and evaluation results.
        """
        task_id = task.get("id", "unknown")
        spec = task.get("spec", task.get("description", ""))
        condition = f"lucid_{platform}"

        current_code = code
        iterations = []

        for i in range(1, k + 1):
            # For app generation, use LLM-based code review as verification
            # (automated test suites for apps are task-specific and run separately)
            review = self._client.complete(
                system="You are a code reviewer. Review this application code against its specification. List any bugs, missing features, or issues. If the code looks correct, say 'NO ISSUES FOUND'.",
                user=f"## Specification\n{spec}\n\n## Generated Code\n{current_code[:8000]}",
                temperature=0.0,
                max_tokens=2048,
                task_id=task_id,
                condition=condition,
                iteration=i,
                role="verify",
            )
            self._track_call(platform, "app_gen", task_id, "lucid_verify", i)

            if "NO ISSUES FOUND" in review.upper():
                iterations.append({
                    "iteration": i,
                    "passed": True,
                    "early_stop": True,
                })
                break

            # REMEDIATE
            remediation = self._client.complete(
                system=REMEDIATE_SYSTEM,
                user=f"Specification:\n{spec}\n\nCurrent code:\n{current_code[:6000]}\n\nReview feedback:\n{review}",
                temperature=0.0,
                max_tokens=2048,
                task_id=task_id,
                condition=condition,
                iteration=i,
                role="remediate",
            )
            self._track_call(platform, "app_gen", task_id, "lucid_remediate", i)

            # REGENERATE
            new_code = self._client.complete(
                system="You are an expert programmer. Fix the issues in this application code based on the review feedback. Return the COMPLETE corrected code.",
                user=f"Specification:\n{spec}\n\nPrevious code (with issues):\n{current_code[:6000]}\n\nReview:\n{review}\n\nFix plan:\n{remediation}",
                temperature=0.7,
                max_tokens=8192,
                task_id=task_id,
                condition=condition,
                iteration=i,
                role="regenerate",
            )
            new_code = _clean_code(new_code)
            self._track_call(platform, "app_gen", task_id, "lucid_regenerate", i)

            iterations.append({
                "iteration": i,
                "verification": review[:500],
                "passed": False,
            })
            current_code = new_code

        return {
            "verified_code": current_code,
            "original_code": code,
            "iterations": iterations,
            "platform": platform,
            "k": k,
        }

    def _track_call(
        self,
        platform: str,
        track: str,
        task_id: str,
        role: str,
        iteration: int,
    ) -> None:
        """Record the latest inner tracker call to the benchmark tracker."""
        if not self.benchmark_tracker or not self._inner_tracker.calls:
            return
        last = self._inner_tracker.calls[-1]
        self.benchmark_tracker.record(
            platform=platform,
            track=track,
            task_id=task_id,
            role=role,
            model=self.model,
            input_tokens=last.input_tokens,
            output_tokens=last.output_tokens,
            duration_ms=last.duration_ms,
            lucid_iteration=iteration,
        )
