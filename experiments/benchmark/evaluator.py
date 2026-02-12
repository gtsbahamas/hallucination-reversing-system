"""Unified evaluation for cross-platform benchmark.

Provides evaluation functions for all four benchmark tracks:
  - Track 1 (HumanEval): Execute Python tests
  - Track 2 (SWE-bench): Docker-based test execution
  - Track 3 (App Generation): Rubric-based scoring
  - Track 4 (Feature Addition): Test suite pass/fail
"""

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class EvalResult:
    """Result of evaluating generated code."""
    task_id: str
    platform: str
    track: str
    passed: bool
    score: float  # 0.0-1.0 for rubric-based, 0 or 1 for binary
    details: dict = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "platform": self.platform,
            "track": self.track,
            "passed": self.passed,
            "score": self.score,
            "details": self.details,
            "error": self.error,
        }


class Evaluator:
    """Unified evaluator for all benchmark tracks."""

    def evaluate_humaneval(
        self,
        code: str,
        task: dict,
        platform: str,
    ) -> EvalResult:
        """Evaluate HumanEval function generation (Track 1).

        Runs the code against the HumanEval test cases via subprocess.
        Reuses the same execution pattern as experiments/humaneval/verifier.py.

        Args:
            code: Generated function code.
            task: HumanEval task dict with 'prompt', 'test', 'entry_point'.
            platform: Platform name for reporting.

        Returns:
            EvalResult with pass/fail and test output.
        """
        task_id = task["task_id"]
        prompt = task["prompt"]
        test_code = task["test"]
        entry_point = task["entry_point"]

        # Clean code: strip markdown fences
        cleaned = _clean_code(code)

        # Build test script
        # Preserve preamble (imports before function definition)
        preamble = ""
        if not cleaned.lstrip().startswith("def "):
            lines = prompt.split("\n")
            preamble_lines = []
            for line in lines:
                if line.strip().startswith("def "):
                    break
                preamble_lines.append(line)
            preamble = "\n".join(preamble_lines)

        test_script = f"""{preamble}

{cleaned}

{test_code}

check({entry_point})
"""
        try:
            result = subprocess.run(
                [sys.executable, "-c", test_script],
                capture_output=True,
                text=True,
                timeout=30,
            )
            passed = result.returncode == 0
            return EvalResult(
                task_id=task_id,
                platform=platform,
                track="humaneval",
                passed=passed,
                score=1.0 if passed else 0.0,
                details={
                    "returncode": result.returncode,
                    "stdout": result.stdout[:2000],
                    "stderr": result.stderr[:2000],
                },
            )
        except subprocess.TimeoutExpired:
            return EvalResult(
                task_id=task_id,
                platform=platform,
                track="humaneval",
                passed=False,
                score=0.0,
                details={"error_type": "timeout"},
                error="Test execution timed out (30s)",
            )
        except Exception as e:
            return EvalResult(
                task_id=task_id,
                platform=platform,
                track="humaneval",
                passed=False,
                score=0.0,
                error=str(e),
            )

    def evaluate_swebench(
        self,
        patch: str,
        instance_id: str,
        platform: str,
        model_name: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> EvalResult:
        """Evaluate SWE-bench patch via Docker test execution (Track 2).

        Delegates to the existing SWE-bench verifier infrastructure.

        Args:
            patch: Unified diff patch.
            instance_id: SWE-bench instance ID.
            platform: Platform name for reporting.
            model_name: Model name for SWE-bench evaluation directory.
            run_id: Unique run ID.

        Returns:
            EvalResult with pass/fail and test output.
        """
        try:
            from ..swebench.verifier import evaluate_single
            model = model_name or f"benchmark_{platform}"
            rid = run_id or f"benchmark_{platform}"
            result = evaluate_single(instance_id, patch, model_name=model, run_id=rid)
            return EvalResult(
                task_id=instance_id,
                platform=platform,
                track="swebench",
                passed=result.get("resolved", False),
                score=1.0 if result.get("resolved", False) else 0.0,
                details=result,
            )
        except Exception as e:
            return EvalResult(
                task_id=instance_id,
                platform=platform,
                track="swebench",
                passed=False,
                score=0.0,
                error=str(e),
            )

    def evaluate_app(
        self,
        code: str,
        task: dict,
        platform: str,
    ) -> EvalResult:
        """Evaluate a generated application against its rubric (Track 3).

        Scoring rubric (from benchmark design doc):
          - Builds (20%):    0 = won't compile, 1 = warnings, 2 = clean
          - Renders (15%):   0 = blank/error, 1 = partial, 2 = full
          - Core func (35%): 0 = nothing, 1 = partial, 2 = all requirements
          - Edge cases (15%): 0 = crashes, 1 = handles some, 2 = handles all
          - Error handling (15%): 0 = unhandled, 1 = some, 2 = graceful

        For automated evaluation, we check if the code can be parsed and
        if any provided test suites pass. Full rubric scoring requires
        running the app and testing interactively (deferred to test suites).

        Args:
            code: Generated application source code.
            task: App generation task dict.
            platform: Platform name for reporting.

        Returns:
            EvalResult with rubric score.
        """
        task_id = task.get("id", "unknown")
        rubric = {
            "builds": 0,
            "renders": 0,
            "core_functionality": 0,
            "edge_cases": 0,
            "error_handling": 0,
        }

        if not code or not code.strip():
            return EvalResult(
                task_id=task_id,
                platform=platform,
                track="app_gen",
                passed=False,
                score=0.0,
                details={"rubric": rubric},
                error="No code generated",
            )

        # Check if code looks parseable (basic heuristic)
        has_code = len(code.strip()) > 50
        if has_code:
            rubric["builds"] = 1  # At minimum, code exists

        # If task has a test_suite path, run it
        test_suite = task.get("test_suite")
        if test_suite and Path(test_suite).exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(test_suite), "--code", code],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode == 0:
                    try:
                        test_results = json.loads(result.stdout)
                        rubric.update(test_results.get("rubric", {}))
                    except json.JSONDecodeError:
                        if "PASS" in result.stdout:
                            rubric["core_functionality"] = 2
            except subprocess.TimeoutExpired:
                rubric["core_functionality"] = 0
            except Exception:
                pass

        # Compute weighted score
        weights = {
            "builds": 0.20,
            "renders": 0.15,
            "core_functionality": 0.35,
            "edge_cases": 0.15,
            "error_handling": 0.15,
        }
        max_per_criterion = 2.0
        score = sum(
            rubric.get(k, 0) / max_per_criterion * w
            for k, w in weights.items()
        )

        return EvalResult(
            task_id=task_id,
            platform=platform,
            track="app_gen",
            passed=score >= 0.7,  # 70% threshold for "pass"
            score=score,
            details={"rubric": rubric},
        )

    def evaluate_feature(
        self,
        patch_or_code: str,
        task: dict,
        platform: str,
    ) -> EvalResult:
        """Evaluate a feature addition against test suites (Track 4).

        Success = all existing tests still pass (no regression) AND
        the new feature tests pass.

        Args:
            patch_or_code: Unified diff patch or modified code.
            task: Feature addition task dict with 'base_repo', 'test_suite'.
            platform: Platform name for reporting.

        Returns:
            EvalResult with pass/fail and partial credit.
        """
        task_id = task.get("id", "unknown")

        if not patch_or_code or not patch_or_code.strip():
            return EvalResult(
                task_id=task_id,
                platform=platform,
                track="feature",
                passed=False,
                score=0.0,
                error="No code generated",
            )

        # If task has regression and feature test suites, run them
        regression_tests = task.get("regression_tests")
        feature_tests = task.get("feature_tests")

        if not regression_tests and not feature_tests:
            # No test suites defined — can only check that code exists
            return EvalResult(
                task_id=task_id,
                platform=platform,
                track="feature",
                passed=False,
                score=0.0,
                details={"note": "No test suites defined for this task"},
                error="Cannot evaluate without test suites",
            )

        details = {
            "regression_passed": None,
            "feature_passed": None,
            "regression_total": 0,
            "regression_pass_count": 0,
            "feature_total": 0,
            "feature_pass_count": 0,
        }

        # Apply patch to a temp copy of the base repo and run tests
        base_repo = task.get("base_repo")
        if base_repo and Path(base_repo).exists():
            with tempfile.TemporaryDirectory() as tmpdir:
                # Copy base repo
                subprocess.run(
                    ["cp", "-r", str(base_repo), tmpdir],
                    capture_output=True,
                )
                repo_dir = Path(tmpdir) / Path(base_repo).name

                # Apply patch
                patch_result = subprocess.run(
                    ["git", "apply", "--stat", "-"],
                    input=patch_or_code,
                    capture_output=True,
                    text=True,
                    cwd=str(repo_dir),
                )
                if patch_result.returncode != 0:
                    return EvalResult(
                        task_id=task_id,
                        platform=platform,
                        track="feature",
                        passed=False,
                        score=0.0,
                        details={"patch_apply": "failed", "stderr": patch_result.stderr[:1000]},
                        error="Patch failed to apply",
                    )

                # Actually apply it
                subprocess.run(
                    ["git", "apply", "-"],
                    input=patch_or_code,
                    capture_output=True,
                    text=True,
                    cwd=str(repo_dir),
                )

                # Run test suites if paths are defined
                # (test suite execution is project-specific — placeholder for now)
                details["patch_apply"] = "success"

        # Compute partial credit
        total = details.get("regression_total", 0) + details.get("feature_total", 0)
        passed_count = details.get("regression_pass_count", 0) + details.get("feature_pass_count", 0)
        score = passed_count / total if total > 0 else 0.0
        all_passed = (
            details.get("regression_passed", False) and
            details.get("feature_passed", False)
        )

        return EvalResult(
            task_id=task_id,
            platform=platform,
            track="feature",
            passed=all_passed,
            score=score,
            details=details,
        )


def _clean_code(raw: str) -> str:
    """Strip markdown fences and extra text from generated code."""
    text = raw.strip()
    if text.startswith("```python"):
        text = text[len("```python"):].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text
