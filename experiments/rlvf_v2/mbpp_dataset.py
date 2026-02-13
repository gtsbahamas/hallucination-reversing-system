"""
MBPP Dataset Loader
Downloads and parses MBPP from HuggingFace for DPO pair generation.

Usage:
    from experiments.rlvf_v2.mbpp_dataset import load_mbpp, load_mbpp_test_split
"""

import json
import urllib.request
from pathlib import Path
from typing import Optional

DATASET_DIR = Path(__file__).parent.parent.parent / "data" / "mbpp"

# HuggingFace raw URLs for MBPP dataset
MBPP_URL = "https://raw.githubusercontent.com/google-research/google-research/master/mbpp/mbpp.jsonl"

# Task ID ranges per official split
# Training: 11-510 (500 tasks), but we use all sanitized + train for candidate generation
# Test: 11-510 are "test" in the original paper
# Prompt: 1-10 (few-shot examples)
PROMPT_IDS = set(range(1, 11))        # 10 few-shot prompt tasks
TRAIN_IDS = set(range(11, 511))       # 500 training/test tasks
VALIDATION_IDS = set(range(511, 601)) # 90 validation tasks
EXTRA_IDS = set(range(601, 975))      # 374 additional tasks

# For our experiment:
# - Candidate generation: ALL tasks (974 total, excluding prompt tasks)
# - Training data: pairs generated from all tasks
# - MBPP test evaluation: tasks 11-510 (held-out from training if needed)


def download_dataset() -> Path:
    """Download MBPP dataset if not already cached."""
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATASET_DIR / "mbpp.jsonl"

    if output_path.exists():
        return output_path

    print(f"Downloading MBPP dataset to {output_path}...")
    urllib.request.urlretrieve(MBPP_URL, output_path)
    print(f"  Downloaded {output_path.stat().st_size:,} bytes")
    return output_path


def load_mbpp(subset: Optional[str] = None) -> list[dict]:
    """
    Load MBPP dataset.

    Args:
        subset: Optional filter - "train" (11-510), "validation" (511-600),
                "extra" (601-974), "all" or None (all non-prompt tasks)

    Returns:
        List of task dicts with keys:
            - task_id: int
            - text: str (task description / prompt)
            - code: str (reference solution)
            - test_list: list[str] (assertion strings)
            - test_setup_code: str (setup code to run before tests)
    """
    dataset_path = download_dataset()

    tasks = []
    with open(dataset_path) as f:
        for line in f:
            task = json.loads(line)
            task_id = task["task_id"]

            # Skip few-shot prompt tasks
            if task_id in PROMPT_IDS:
                continue

            # Apply subset filter
            if subset == "train" and task_id not in TRAIN_IDS:
                continue
            elif subset == "validation" and task_id not in VALIDATION_IDS:
                continue
            elif subset == "extra" and task_id not in EXTRA_IDS:
                continue

            # Normalize fields
            tasks.append({
                "task_id": task_id,
                "text": task["text"],
                "code": task["code"],
                "test_list": task.get("test_list", []),
                "test_setup_code": task.get("test_setup_code", ""),
            })

    return tasks


def load_mbpp_test_split() -> list[dict]:
    """Load the standard MBPP test split (tasks 11-510) for evaluation."""
    return load_mbpp(subset="train")


def load_all_for_generation() -> list[dict]:
    """Load all MBPP tasks for candidate solution generation."""
    return load_mbpp(subset=None)


def get_task_count(subset: Optional[str] = None) -> int:
    """Get number of tasks without loading full data."""
    return len(load_mbpp(subset=subset))


def main():
    """Print dataset statistics."""
    all_tasks = load_mbpp()
    train = load_mbpp("train")
    validation = load_mbpp("validation")
    extra = load_mbpp("extra")

    print(f"MBPP Dataset Statistics:")
    print(f"  All tasks (non-prompt): {len(all_tasks)}")
    print(f"  Train split (11-510):   {len(train)}")
    print(f"  Validation (511-600):   {len(validation)}")
    print(f"  Extra (601-974):        {len(extra)}")
    print()

    # Sample task
    if all_tasks:
        t = all_tasks[0]
        print(f"Sample task (ID {t['task_id']}):")
        print(f"  Text: {t['text'][:100]}...")
        print(f"  Tests: {len(t['test_list'])} assertions")
        for test in t['test_list'][:3]:
            print(f"    {test}")


if __name__ == "__main__":
    main()
