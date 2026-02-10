"""Formal verification for HumanEval: execute tests in isolated subprocess."""

import subprocess
import tempfile
from pathlib import Path


def execute_tests(solution: str, prompt: str, test_code: str, entry_point: str, timeout: int = 30) -> dict:
    """
    Execute HumanEval tests against a generated solution.
    This is the FORMAL VERIFIER — the incorruptible oracle.

    Args:
        solution: Generated function body (may include the full function or just body)
        prompt: Original function signature + docstring
        test_code: Test cases from the dataset
        entry_point: Function name to test
        timeout: Max execution time in seconds

    Returns:
        dict with all_passed, stdout, stderr, returncode, error_type
    """
    # Build the full test program
    # The prompt contains the function signature; solution should complete it
    if solution.strip().startswith("def "):
        # Solution includes the full function definition.
        # Extract the preamble from prompt (imports, helper functions defined
        # before the entry point function) so they remain in scope.
        preamble = ""
        entry_marker = f"def {entry_point}("
        idx = prompt.find(entry_marker)
        if idx > 0:
            preamble = prompt[:idx]
        full_code = f"{preamble}{solution}\n\n{test_code}\n\ncheck({entry_point})"
    else:
        # Solution is just the function body, prepend the prompt
        full_code = f"{prompt}{solution}\n\n{test_code}\n\ncheck({entry_point})"

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
    return "runtime_error"
