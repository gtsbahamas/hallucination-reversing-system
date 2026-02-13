"""
MBPP Test Verifier
Executes MBPP test assertions against candidate solutions in isolated subprocesses.

Adapted from experiments/humaneval/verifier.py pattern.

Usage:
    from experiments.rlvf_v2.mbpp_verifier import verify_solution
    result = verify_solution(solution_code, task)
"""

import subprocess
import tempfile
from pathlib import Path


def verify_solution(solution: str, task: dict, timeout: int = 30) -> dict:
    """
    Verify a candidate solution against MBPP test assertions.

    Args:
        solution: Generated Python code (complete function definition)
        task: MBPP task dict with test_list and test_setup_code
        timeout: Max execution time in seconds

    Returns:
        dict with all_passed, stdout, stderr, returncode, error_type
    """
    test_setup = task.get("test_setup_code", "") or ""
    test_list = task.get("test_list", [])

    # Build the test program:
    # 1. Setup code (if any)
    # 2. The candidate solution
    # 3. All test assertions
    parts = []
    if test_setup.strip():
        parts.append(test_setup.strip())
    parts.append(solution.strip())
    parts.append("")  # blank line before tests
    for test in test_list:
        parts.append(test.strip())

    full_code = "\n".join(parts)

    with tempfile.NamedTemporaryFile(
        suffix=".py", mode="w", delete=False, dir="/tmp"
    ) as f:
        f.write(full_code)
        f.flush()
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["python3", tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "all_passed": result.returncode == 0,
            "stdout": result.stdout[:2000],
            "stderr": result.stderr[:2000],
            "returncode": result.returncode,
            "error_type": _classify_error(result.stderr) if result.returncode != 0 else None,
        }
    except subprocess.TimeoutExpired:
        return {
            "all_passed": False,
            "stdout": "",
            "stderr": f"Timeout after {timeout}s",
            "returncode": -1,
            "error_type": "timeout",
        }
    except Exception as e:
        return {
            "all_passed": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "error_type": "execution_error",
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def verify_batch(solutions: list[str], task: dict, timeout: int = 30) -> list[dict]:
    """Verify multiple solutions for the same task."""
    return [verify_solution(sol, task, timeout) for sol in solutions]


def _classify_error(stderr: str) -> str:
    """Classify the error type from stderr."""
    stderr_lower = stderr.lower()
    if "syntaxerror" in stderr_lower:
        return "syntax_error"
    if "nameerror" in stderr_lower:
        return "name_error"
    if "typeerror" in stderr_lower:
        return "type_error"
    if "indexerror" in stderr_lower:
        return "index_error"
    if "keyerror" in stderr_lower:
        return "key_error"
    if "valueerror" in stderr_lower:
        return "value_error"
    if "assertionerror" in stderr_lower:
        return "assertion_error"
    if "recursionerror" in stderr_lower:
        return "recursion_error"
    if "attributeerror" in stderr_lower:
        return "attribute_error"
    if "importerror" in stderr_lower or "modulenotfounderror" in stderr_lower:
        return "import_error"
    return "runtime_error"
