#!/usr/bin/env python3
"""
HumanEval Benchmark Runner for LUCID Architecture Proof.

Usage:
    # Primary experiment (all conditions, all iterations)
    python -m experiments.humaneval.runner \
        --conditions baseline self-refine llm-judge lucid \
        --iterations 1 2 3 5 10 \
        --model claude-sonnet-4-5-20250929 \
        --output results/humaneval/

    # Quick smoke test (2 tasks, 1 iteration)
    python -m experiments.humaneval.runner \
        --conditions baseline lucid \
        --iterations 1 \
        --model claude-sonnet-4-5-20250929 \
        --output results/humaneval-smoke/ \
        --limit 2

    # Ablation study
    python -m experiments.humaneval.runner \
        --conditions lucid \
        --iterations 1 3 5 \
        --ablation no-extract \
        --model claude-sonnet-4-5-20250929 \
        --output results/ablations/no-extract/

    # Resume interrupted run (skips existing results)
    python -m experiments.humaneval.runner \
        --conditions baseline self-refine llm-judge lucid \
        --iterations 1 2 3 5 10 \
        --model claude-sonnet-4-5-20250929 \
        --output results/humaneval/ \
        --resume

Budget tracking: The runner tracks API costs in real-time and will warn
when approaching the budget limit ($481 for Phase 1).
"""

import argparse
import json
import sys
import time
from pathlib import Path

from tqdm import tqdm

from ..common.cost_tracker import CostTracker
from ..common.llm_client import LLMClient
from ..common.results import ResultStore, TaskResult
from .dataset import load_dataset
from .conditions import run_baseline, run_self_refine, run_llm_judge, run_lucid


def run_experiment(
    conditions: list[str],
    iterations: list[int],
    model: str,
    output_dir: Path,
    limit: int = 0,
    resume: bool = False,
    ablation: str | None = None,
    budget: float = 481.0,
    dry_run: bool = False,
):
    """Run the full HumanEval experiment."""

    # Load dataset
    tasks = load_dataset()
    if limit > 0:
        tasks = tasks[:limit]

    print(f"HumanEval Benchmark Runner")
    print(f"{'=' * 60}")
    print(f"Model: {model}")
    print(f"Tasks: {len(tasks)}")
    print(f"Conditions: {', '.join(conditions)}")
    print(f"Iterations: {iterations}")
    print(f"Ablation: {ablation or 'none'}")
    print(f"Output: {output_dir}")
    print(f"Budget: ${budget:.2f}")
    print(f"Resume: {resume}")
    print(f"{'=' * 60}")

    if dry_run:
        _print_cost_estimate(tasks, conditions, iterations, ablation)
        return

    # Initialize
    tracker = CostTracker(budget_limit=budget)
    store = ResultStore(output_dir)
    client = LLMClient(model=model, tracker=tracker)

    # Load existing tracker if resuming
    tracker_path = output_dir / "cost_tracker.json"
    if resume and tracker_path.exists():
        tracker = CostTracker.load(tracker_path)
        tracker.budget_limit = budget
        client = LLMClient(model=model, tracker=tracker)
        print(f"Resumed: ${tracker.total_cost:.2f} spent so far")

    # Build work items
    work_items = []
    for condition in conditions:
        iters_for_cond = [1] if condition == "baseline" else iterations
        for max_iter in iters_for_cond:
            for task in tasks:
                if resume and store.exists(task["task_id"], condition, max_iter, ablation):
                    continue
                work_items.append((condition, max_iter, task))

    if not work_items:
        print("All results already exist. Nothing to do.")
        print(tracker.summary())
        return

    print(f"Work items: {len(work_items)} (skipped {len(tasks) * sum(len([1] if c == 'baseline' else iterations) for c in conditions) - len(work_items)} existing)")
    print()

    # Run experiments
    passed_count = 0
    failed_count = 0
    error_count = 0

    pbar = tqdm(work_items, desc="Running", unit="task")
    for condition, max_iter, task in pbar:
        task_id = task["task_id"]
        pbar.set_postfix_str(f"{condition} k={max_iter} {task_id}")

        try:
            if condition == "baseline":
                result = run_baseline(client, task)
            elif condition == "self-refine":
                result = run_self_refine(client, task, max_iter)
            elif condition == "llm-judge":
                result = run_llm_judge(client, task, max_iter)
            elif condition == "lucid":
                result = run_lucid(client, task, max_iter, ablation=ablation)
            else:
                raise ValueError(f"Unknown condition: {condition}")

            # Save result
            task_result = TaskResult(
                task_id=result["task_id"],
                condition=result["condition"],
                max_iterations=result["max_iterations"],
                model=model,
                final_passed=result["final_passed"],
                final_test_output=result["final_test_output"],
                iterations=result["iterations"],
                ablation=result.get("ablation"),
            )
            store.save(task_result)

            if result["final_passed"]:
                passed_count += 1
            else:
                failed_count += 1

        except Exception as e:
            error_count += 1
            print(f"\nERROR: {task_id} {condition} k={max_iter}: {e}", file=sys.stderr)
            continue

        # Budget check every 10 items
        if (passed_count + failed_count + error_count) % 10 == 0:
            tracker.save(tracker_path)
            if tracker.total_cost > budget * 0.9:
                print(f"\n WARNING: Approaching budget limit (${tracker.total_cost:.2f} / ${budget:.2f})")
            if tracker.is_over_budget():
                print(f"\n BUDGET EXCEEDED (${tracker.total_cost:.2f} / ${budget:.2f}). Stopping.")
                break

    # Final save
    tracker.save(tracker_path)

    # Summary
    total = passed_count + failed_count
    print(f"\n{'=' * 60}")
    print(f"RESULTS")
    print(f"{'=' * 60}")
    print(f"Passed: {passed_count}/{total} ({100*passed_count/total:.1f}%)" if total > 0 else "No results")
    print(f"Failed: {failed_count}/{total}")
    print(f"Errors: {error_count}")
    print()
    print(tracker.summary())


def _print_cost_estimate(tasks, conditions, iterations, ablation):
    """Print estimated cost without running anything."""
    per_task_costs = {
        "baseline": {1: 0.005},
        "self-refine": {},
        "llm-judge": {},
        "lucid": {},
    }

    # Estimate per task per iteration
    for k in iterations:
        per_task_costs["self-refine"][k] = 0.005 + k * (0.007 + 0.007 + 0.009 + 0.007)
        per_task_costs["llm-judge"][k] = 0.005 + k * (0.007 + 0.009 + 0.009 + 0.007)
        per_task_costs["lucid"][k] = 0.005 + k * (0.007 + 0.0 + 0.009 + 0.007)

    total = 0
    print("\nCost Estimate:")
    print(f"{'Condition':<15} {'k':<5} {'Per Task':<10} {'Total':<10}")
    print("-" * 45)
    for condition in conditions:
        iters_for_cond = [1] if condition == "baseline" else iterations
        for k in iters_for_cond:
            per_task = per_task_costs.get(condition, {}).get(k, 0)
            subtotal = per_task * len(tasks)
            total += subtotal
            print(f"{condition:<15} {k:<5} ${per_task:<9.3f} ${subtotal:<9.2f}")

    print("-" * 45)
    print(f"{'TOTAL':<21} {'':10} ${total:.2f}")


def main():
    parser = argparse.ArgumentParser(description="HumanEval Benchmark Runner for LUCID")
    parser.add_argument("--conditions", nargs="+", default=["baseline", "self-refine", "llm-judge", "lucid"],
                       choices=["baseline", "self-refine", "llm-judge", "lucid"])
    parser.add_argument("--iterations", nargs="+", type=int, default=[1, 2, 3, 5, 10])
    parser.add_argument("--model", default="claude-sonnet-4-5-20250929")
    parser.add_argument("--output", type=Path, default=Path("results/humaneval/"))
    parser.add_argument("--limit", type=int, default=0, help="Limit number of tasks (0 = all)")
    parser.add_argument("--resume", action="store_true", help="Skip existing results")
    parser.add_argument("--ablation", type=str, default=None,
                       choices=["no-extract", "no-remediate", "learned-verify", "no-context", "random-verify"])
    parser.add_argument("--budget", type=float, default=481.0, help="Budget limit in dollars")
    parser.add_argument("--dry-run", action="store_true", help="Print cost estimate only")

    args = parser.parse_args()

    run_experiment(
        conditions=args.conditions,
        iterations=args.iterations,
        model=args.model,
        output_dir=args.output,
        limit=args.limit,
        resume=args.resume,
        ablation=args.ablation,
        budget=args.budget,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
