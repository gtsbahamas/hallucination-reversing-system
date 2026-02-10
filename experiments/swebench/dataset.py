"""Load and prepare SWE-bench Lite dataset."""

import json
from datasets import load_dataset


def load_swebench_lite() -> list[dict]:
    """Load SWE-bench Lite test split (300 tasks)."""
    ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    tasks = []
    for row in ds:
        tasks.append({
            "instance_id": row["instance_id"],
            "repo": row["repo"],
            "base_commit": row["base_commit"],
            "problem_statement": row["problem_statement"],
            "hints_text": row["hints_text"],
            "patch": row["patch"],  # gold patch (for reference only, not given to model)
            "test_patch": row["test_patch"],
            "fail_to_pass": json.loads(row["FAIL_TO_PASS"]) if isinstance(row["FAIL_TO_PASS"], str) else row["FAIL_TO_PASS"],
            "pass_to_pass": json.loads(row["PASS_TO_PASS"]) if isinstance(row["PASS_TO_PASS"], str) else row["PASS_TO_PASS"],
            "version": row["version"],
            "environment_setup_commit": row["environment_setup_commit"],
        })
    return tasks
