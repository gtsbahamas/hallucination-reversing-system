#!/usr/bin/env python3
"""
SWE-bench Lite Benchmark Runner for LUCID.

Usage:
    # Baseline (300 tasks, single pass)
    python -m experiments.swebench.runner \
        --conditions baseline \
        --output results/swebench/

    # LUCID with iterations
    python -m experiments.swebench.runner \
        --conditions baseline lucid \
        --iterations 1 3 5 \
        --output results/swebench/

    # Quick smoke test (5 tasks)
    python -m experiments.swebench.runner \
        --conditions baseline lucid \
        --iterations 1 \
        --output results/swebench-smoke/ \
        --limit 5

    # Resume interrupted run
    python -m experiments.swebench.runner \
        --conditions baseline lucid \
        --iterations 1 3 \
        --output results/swebench/ \
        --resume
"""

import argparse
import json
import sys
from pathlib import Path

from tqdm import tqdm

from ..common.cost_tracker import CostTracker
from ..common.llm_client import LLMClient
from ..common.results import ResultStore, TaskResult
from .dataset import load_swebench_lite
from .conditions import run_baseline_swe, run_lucid_swe


def run_experiment(
    conditions: list[str],
    iterations: list[int],
    model: str,
    output_dir: Path,
    limit: int = 0,
    offset: int = 0,
    resume: bool = False,
    budget: float = 3000.0,
    smart_skip: bool = False,
    chunk_id: str = "",
):
    """Run SWE-bench Lite experiment."""

    tasks = load_swebench_lite()
    if offset > 0:
        tasks = tasks[offset:]
    if limit > 0:
        tasks = tasks[:limit]

    chunk_label = f" (chunk {chunk_id})" if chunk_id else ""
    print(f"SWE-bench Lite Benchmark Runner{chunk_label}")
    print(f"{'=' * 60}")
    print(f"Model: {model}")
    print(f"Tasks: {len(tasks)} (offset={offset}, limit={limit})")
    print(f"Conditions: {', '.join(conditions)}")
    print(f"Iterations: {iterations}")
    print(f"Output: {output_dir}")
    print(f"Budget: ${budget:.2f}")
    print(f"Resume: {resume}")
    print(f"Smart skip: {smart_skip}")
    print(f"{'=' * 60}")

    # Initialize
    tracker = CostTracker(budget_limit=budget)
    store = ResultStore(output_dir)
    client = LLMClient(model=model, tracker=tracker)

    # Load existing tracker if resuming (use chunk-specific tracker if parallel)
    tracker_suffix = f"_{chunk_id}" if chunk_id else ""
    tracker_path = output_dir / f"cost_tracker{tracker_suffix}.json"
    if resume and tracker_path.exists():
        tracker = CostTracker.load(tracker_path)
        tracker.budget_limit = budget
        client = LLMClient(model=model, tracker=tracker)
        print(f"Resumed: ${tracker.total_cost:.2f} spent so far")

    # Build work items — INTERLEAVED per task so Docker images stay cached.
    # For each task, run all conditions before moving to the next task.
    skipped_resume = 0
    work_items = []
    for task in tasks:
        tid = task["instance_id"]
        for condition in conditions:
            iters_for_cond = [1] if condition == "baseline" else iterations
            for max_iter in iters_for_cond:
                if resume and store.exists(tid, condition, max_iter):
                    skipped_resume += 1
                    continue
                work_items.append((condition, max_iter, task))

    if not work_items:
        print("All results already exist. Nothing to do.")
        return

    print(f"Work items: {len(work_items)} (skipped {skipped_resume} existing)")
    print()

    # Run experiments
    passed_count = 0
    failed_count = 0
    error_count = 0
    skipped_smart = 0

    pbar = tqdm(work_items, desc="Running", unit="task")
    for condition, max_iter, task in pbar:
        instance_id = task["instance_id"]
        pbar.set_postfix_str(f"{condition} k={max_iter} {instance_id[:30]}")

        # Runtime smart skip: check if k=1 passed (results may have been
        # written earlier in this same run, or by a parallel runner)
        if smart_skip and condition == "lucid" and max_iter > 1:
            k1_result = store.load(instance_id, "lucid", 1)
            if k1_result and k1_result.final_passed:
                skipped_smart += 1
                continue

        try:
            if condition == "baseline":
                result = run_baseline_swe(client, task)
            elif condition == "lucid":
                result = run_lucid_swe(client, task, max_iter)
            else:
                raise ValueError(f"Unknown condition: {condition}")

            # Save result (including solution/patch for re-verification)
            task_result = TaskResult(
                task_id=result["task_id"],
                condition=result["condition"],
                max_iterations=result["max_iterations"],
                model=model,
                final_passed=result["final_passed"],
                final_test_output=result["final_test_output"],
                iterations=result["iterations"],
                ablation=result.get("ablation"),
                solution=result.get("solution"),
            )
            store.save(task_result)

            if result["final_passed"]:
                passed_count += 1
            else:
                failed_count += 1

        except Exception as e:
            error_count += 1
            print(f"\nERROR: {instance_id} {condition} k={max_iter}: {e}", file=sys.stderr)
            continue

        # Budget check every 5 items
        if (passed_count + failed_count + error_count) % 5 == 0:
            tracker.save(tracker_path)
            if tracker.is_over_budget():
                print(f"\nBUDGET EXCEEDED (${tracker.total_cost:.2f} / ${budget:.2f}). Stopping.")
                break

    # Final save
    tracker.save(tracker_path)

    # Summary
    total = passed_count + failed_count
    print(f"\n{'=' * 60}")
    print(f"RESULTS")
    print(f"{'=' * 60}")
    if total > 0:
        print(f"Resolved: {passed_count}/{total} ({100*passed_count/total:.1f}%)")
        print(f"Failed: {failed_count}/{total}")
    print(f"Errors: {error_count}")
    if skipped_smart > 0:
        print(f"Smart skipped: {skipped_smart} (k=1 already passed)")
    print()
    print(tracker.summary())


def main():
    parser = argparse.ArgumentParser(description="SWE-bench Lite Runner for LUCID")
    parser.add_argument("--conditions", nargs="+", default=["baseline", "lucid"],
                       choices=["baseline", "lucid"])
    parser.add_argument("--iterations", nargs="+", type=int, default=[1, 3, 5])
    parser.add_argument("--model", default="claude-sonnet-4-5-20250929")
    parser.add_argument("--output", type=Path, default=Path("results/swebench/"))
    parser.add_argument("--limit", type=int, default=0, help="Limit number of tasks (0 = all)")
    parser.add_argument("--offset", type=int, default=0, help="Skip first N tasks (for parallel chunking)")
    parser.add_argument("--resume", action="store_true", help="Skip existing results")
    parser.add_argument("--budget", type=float, default=3000.0, help="Budget limit in dollars")
    parser.add_argument("--smart-skip", action="store_true", help="Skip k=3/k=5 if k=1 already passed")
    parser.add_argument("--chunk-id", default="", help="Chunk ID for parallel cost tracking")

    args = parser.parse_args()

    run_experiment(
        conditions=args.conditions,
        iterations=args.iterations,
        model=args.model,
        output_dir=args.output,
        limit=args.limit,
        offset=args.offset,
        resume=args.resume,
        budget=args.budget,
        smart_skip=args.smart_skip,
        chunk_id=args.chunk_id,
    )


if __name__ == "__main__":
    main()
