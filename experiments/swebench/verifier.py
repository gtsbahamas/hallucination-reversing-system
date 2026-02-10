"""
SWE-bench verification using the official swebench harness.

Writes predictions to a temp JSONL file, runs swebench evaluation via Docker,
and returns per-instance pass/fail results with test output.
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def evaluate_predictions(
    predictions: list[dict],
    run_id: str = "lucid",
    timeout: int = 900,
    max_workers: int = 4,
) -> dict[str, dict]:
    """
    Evaluate a batch of SWE-bench predictions using the official harness.

    Args:
        predictions: List of {"instance_id": str, "model_name_or_path": str, "model_patch": str}
        run_id: Identifier for this evaluation run
        timeout: Per-instance timeout in seconds
        max_workers: Number of parallel Docker containers

    Returns:
        Dict mapping instance_id -> {"resolved": bool, "test_output": str}
    """
    if not predictions:
        return {}

    # Write predictions to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for pred in predictions:
            f.write(json.dumps(pred) + "\n")
        pred_path = f.name

    # Run swebench evaluation
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "swebench.harness.run_evaluation",
                "--dataset_name", "princeton-nlp/SWE-bench_Lite",
                "--split", "test",
                "--predictions_path", pred_path,
                "--max_workers", str(max_workers),
                "--run_id", run_id,
                "--timeout", str(timeout),
                "--cache_level", "instance",
            ],
            capture_output=True,
            text=True,
            timeout=timeout * len(predictions) + 600,
        )
    except subprocess.TimeoutExpired:
        return {p["instance_id"]: {"resolved": False, "test_output": "TIMEOUT"} for p in predictions}

    combined_output = f"stdout: {result.stdout[-3000:]}\nstderr: {result.stderr[-2000:]}"

    # Parse results from report files
    # swebench writes to: logs/run_evaluation/{run_id}/{model_name}/{instance_id}/report.json
    results = {}

    for pred in predictions:
        iid = pred["instance_id"]
        model_name = pred.get("model_name_or_path", "lucid")

        # Primary: per-instance report in logs directory
        report_file = Path("logs/run_evaluation") / run_id / model_name / iid / "report.json"
        if report_file.exists():
            report = json.loads(report_file.read_text())
            instance_report = report.get(iid, {})
            results[iid] = {
                "resolved": instance_report.get("resolved", False),
                "test_output": json.dumps(instance_report, indent=2)[:5000],
            }
            continue

        # Fallback: summary report in working directory ({model_name}.{run_id}.json)
        summary_file = Path(f"{model_name}.{run_id}.json")
        if summary_file.exists():
            summary = json.loads(summary_file.read_text())
            if iid in summary.get("resolved_ids", summary.get("completed_ids", [])):
                results[iid] = {
                    "resolved": True,
                    "test_output": json.dumps(summary, indent=2)[:5000],
                }
                continue

        # Fallback: parse stdout for resolved count
        resolved = _parse_resolved_from_output(result.stdout, iid)
        if resolved is not None:
            results[iid] = {
                "resolved": resolved,
                "test_output": combined_output,
            }
        else:
            results[iid] = {
                "resolved": False,
                "test_output": combined_output,
            }

    return results


def _parse_resolved_from_output(stdout: str, instance_id: str) -> bool | None:
    """Parse resolution status from swebench stdout as a fallback."""
    # For single-instance runs, check "Instances resolved: N"
    m = re.search(r"Instances resolved:\s*(\d+)", stdout)
    if m:
        return int(m.group(1)) > 0
    return None


def evaluate_single(
    instance_id: str,
    model_patch: str,
    model_name: str = "lucid",
    run_id: str = "lucid",
    timeout: int = 900,
) -> dict:
    """
    Evaluate a single prediction.

    Returns:
        {"resolved": bool, "test_output": str}
    """
    prediction = {
        "instance_id": instance_id,
        "model_name_or_path": model_name,
        "model_patch": model_patch,
    }
    results = evaluate_predictions([prediction], run_id=f"{run_id}_{instance_id}", timeout=timeout)
    return results.get(instance_id, {"resolved": False, "test_output": "Evaluation failed"})


def get_test_output_from_logs(instance_id: str, run_id: str) -> str:
    """Extract test output from swebench evaluation logs."""
    log_dir = Path(f"/tmp/swebench_reports/{run_id}")

    # Check for evaluation log
    log_file = log_dir / f"{instance_id}.eval.log"
    if log_file.exists():
        return log_file.read_text()[-5000:]  # Last 5K chars

    # Check for test output in report
    report_file = log_dir / f"{run_id}.{instance_id}.json"
    if report_file.exists():
        return report_file.read_text()

    return "No test output available"
