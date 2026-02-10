"""Load HumanEval dataset from the official JSONL file."""

import json
from pathlib import Path
from typing import Optional


DATASET_URL = "https://raw.githubusercontent.com/openai/human-eval/master/data/HumanEval.jsonl.gz"
DATASET_DIR = Path(__file__).parent.parent.parent / "data" / "humaneval"


def download_dataset() -> Path:
    """Download HumanEval dataset if not already cached."""
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    jsonl_path = DATASET_DIR / "HumanEval.jsonl"

    if jsonl_path.exists():
        return jsonl_path

    import urllib.request
    import gzip

    gz_path = DATASET_DIR / "HumanEval.jsonl.gz"
    print(f"Downloading HumanEval dataset to {gz_path}...")
    urllib.request.urlretrieve(DATASET_URL, gz_path)

    with gzip.open(gz_path, "rt") as f_in:
        jsonl_path.write_text(f_in.read())

    gz_path.unlink()
    print(f"Dataset saved: {jsonl_path} ({count_tasks(jsonl_path)} tasks)")
    return jsonl_path


def count_tasks(path: Path) -> int:
    return sum(1 for _ in path.open())


def load_dataset(subset: Optional[list[str]] = None) -> list[dict]:
    """Load HumanEval tasks. Optionally filter by task_id list."""
    path = download_dataset()
    tasks = []
    for line in path.open():
        task = json.loads(line)
        if subset and task["task_id"] not in subset:
            continue
        tasks.append(task)
    return tasks


def get_task_ids() -> list[str]:
    """Return all task IDs in order."""
    return [t["task_id"] for t in load_dataset()]
