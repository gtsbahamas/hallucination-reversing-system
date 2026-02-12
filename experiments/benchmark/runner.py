#!/usr/bin/env python3
"""
Cross-Platform AI Code Quality Benchmark Runner.

Runs benchmark tasks across multiple AI coding platforms, evaluates results,
and optionally applies LUCID verification. Extends the existing humaneval/
swebench runner patterns with multi-platform and multi-track support.

Usage:
    # Full benchmark (all platforms, all tracks)
    python -m experiments.benchmark.runner

    # Specific platform and track
    python -m experiments.benchmark.runner \
        --platform cursor \
        --track humaneval \
        --lucid-k 1 3

    # HumanEval only, with budget cap
    python -m experiments.benchmark.runner \
        --track humaneval \
        --platform cursor copilot \
        --budget 500 \
        --output results/benchmark/

    # Dry run (cost estimate only)
    python -m experiments.benchmark.runner --dry-run

    # Resume interrupted run
    python -m experiments.benchmark.runner --resume

    # Specific task limit (smoke test)
    python -m experiments.benchmark.runner --limit 5 --track humaneval
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from .config import BenchmarkConfig, Track, PlatformConfig, AdapterMode
from .cost_tracker import BenchmarkCostTracker
from .evaluator import Evaluator, EvalResult
from .lucid_verify import LUCIDVerifier
from .adapters.base import PlatformAdapter, ManualResultAdapter, GenerationResult


# --- Adapter factory ---

def create_adapter(
    platform_config: PlatformConfig,
    tracker: BenchmarkCostTracker,
) -> PlatformAdapter:
    """Create the appropriate adapter for a platform."""
    name = platform_config.adapter

    kwargs = {
        "tracker": tracker,
        "max_retries": platform_config.max_retries,
        "rate_limit_rpm": platform_config.rate_limit_rpm,
        "timeout_seconds": platform_config.timeout_seconds,
    }

    if name == "cursor":
        from .adapters.cursor import CursorAdapter
        return CursorAdapter(
            model=platform_config.model or "claude-sonnet-4-5-20250929",
            **kwargs,
        )
    elif name == "copilot":
        from .adapters.copilot import CopilotAdapter
        return CopilotAdapter(
            model=platform_config.model or "gpt-4o-2024-11-20",
            **kwargs,
        )
    elif name == "bolt":
        from .adapters.bolt import BoltAdapter
        return BoltAdapter(**kwargs)
    elif name == "lovable":
        from .adapters.lovable import LovableAdapter
        return LovableAdapter(**kwargs)
    elif name == "replit":
        from .adapters.replit import ReplitAdapter
        return ReplitAdapter(
            model=platform_config.model or "claude-sonnet-4-5-20250929",
            **kwargs,
        )
    else:
        # Fall back to manual adapter
        return ManualResultAdapter(
            name=name,
            results_dir=Path("results/benchmark/manual"),
            **kwargs,
        )


# --- Task loading ---

def load_humaneval_tasks(limit: int = 0) -> list[dict]:
    """Load HumanEval dataset."""
    from ..humaneval.dataset import load_dataset
    tasks = load_dataset()
    if limit > 0:
        tasks = tasks[:limit]
    return tasks


def load_swebench_tasks(limit: int = 0, offset: int = 0) -> list[dict]:
    """Load SWE-bench Lite dataset."""
    from ..swebench.dataset import load_swebench_lite
    tasks = load_swebench_lite()
    if offset > 0:
        tasks = tasks[offset:]
    if limit > 0:
        tasks = tasks[:limit]
    return tasks


def load_app_tasks(task_dir: Optional[Path] = None, limit: int = 0) -> list[dict]:
    """Load app generation task definitions."""
    if task_dir is None:
        task_dir = Path("experiments/benchmark/tasks/app_generation")
    tasks = []
    for task_file in sorted(task_dir.glob("*.json")):
        if task_file.name.startswith("_"):
            continue
        try:
            tasks.append(json.loads(task_file.read_text()))
        except (json.JSONDecodeError, IOError):
            continue
    if limit > 0:
        tasks = tasks[:limit]
    return tasks


def load_feature_tasks(task_dir: Optional[Path] = None, limit: int = 0) -> list[dict]:
    """Load feature addition task definitions."""
    if task_dir is None:
        task_dir = Path("experiments/benchmark/tasks/feature_addition")
    tasks = []
    for task_file in sorted(task_dir.glob("*.json")):
        if task_file.name.startswith("_"):
            continue
        try:
            tasks.append(json.loads(task_file.read_text()))
        except (json.JSONDecodeError, IOError):
            continue
    if limit > 0:
        tasks = tasks[:limit]
    return tasks


# --- Result storage ---

class BenchmarkResultStore:
    """Manages saving and loading benchmark results."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _result_path(
        self,
        platform: str,
        track: str,
        task_id: str,
        lucid_k: int = 0,
        run_number: int = 1,
    ) -> Path:
        safe_id = task_id.replace("/", "_")
        suffix = f"_lucid_k{lucid_k}" if lucid_k > 0 else "_baseline"
        return self.output_dir / platform / track / f"{safe_id}{suffix}_run{run_number}.json"

    def save(self, result: dict) -> None:
        path = self._result_path(
            result["platform"],
            result["track"],
            result["task_id"],
            result.get("lucid_k", 0),
            result.get("run_number", 1),
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, default=str))

    def exists(
        self,
        platform: str,
        track: str,
        task_id: str,
        lucid_k: int = 0,
        run_number: int = 1,
    ) -> bool:
        return self._result_path(platform, track, task_id, lucid_k, run_number).exists()

    def load(
        self,
        platform: str,
        track: str,
        task_id: str,
        lucid_k: int = 0,
        run_number: int = 1,
    ) -> Optional[dict]:
        path = self._result_path(platform, track, task_id, lucid_k, run_number)
        if not path.exists():
            return None
        return json.loads(path.read_text())


# --- Main runner ---

def run_benchmark(
    config: BenchmarkConfig,
    platforms: Optional[list[str]] = None,
    tracks: Optional[list[str]] = None,
    lucid_k_values: Optional[list[int]] = None,
    limit: int = 0,
    offset: int = 0,
):
    """Run the cross-platform benchmark.

    Args:
        config: Full benchmark configuration.
        platforms: Subset of platform names to run (None = all).
        tracks: Subset of track names to run (None = all).
        lucid_k_values: LUCID verification iterations (None = no LUCID).
        limit: Max tasks per track (0 = all).
        offset: Skip first N tasks.
    """
    # Initialize
    tracker = BenchmarkCostTracker(budget_limit=config.budget, chunk_id=config.chunk_id)
    store = BenchmarkResultStore(config.output_dir)
    evaluator = Evaluator()
    lucid = None  # Created lazily after dry-run check

    # Load existing tracker if resuming
    tracker_suffix = f"_{config.chunk_id}" if config.chunk_id else ""
    tracker_path = config.output_dir / f"cost_tracker{tracker_suffix}.json"
    if config.resume and tracker_path.exists():
        tracker = BenchmarkCostTracker.load(tracker_path)
        tracker.budget_limit = config.budget
        print(f"Resumed: ${tracker.total_cost:.2f} spent so far")

    # Filter platforms and tracks
    active_platforms = config.platforms
    if platforms:
        active_platforms = [p for p in config.platforms if p.adapter in platforms]

    track_map = {
        "humaneval": Track.HUMANEVAL,
        "swebench": Track.SWEBENCH,
        "app_gen": Track.APP_GENERATION,
        "feature": Track.FEATURE_ADDITION,
    }
    active_tracks = [tc.track for tc in config.tracks]
    if tracks:
        active_tracks = [track_map[t] for t in tracks if t in track_map]

    # Header
    print(f"Cross-Platform AI Code Quality Benchmark")
    print(f"{'=' * 60}")
    print(f"Platforms: {', '.join(p.name for p in active_platforms)}")
    print(f"Tracks: {', '.join(t.value for t in active_tracks)}")
    print(f"LUCID k: {lucid_k_values or 'disabled'}")
    print(f"Output: {config.output_dir}")
    print(f"Budget: ${config.budget:.2f}")
    print(f"Resume: {config.resume}")
    print(f"Limit: {limit or 'all'}")
    print(f"{'=' * 60}")

    if config.dry_run:
        _print_cost_estimate(active_platforms, active_tracks, limit, lucid_k_values)
        return

    # Create LUCID verifier (after dry-run check so API key not needed for estimates)
    if lucid_k_values:
        lucid = LUCIDVerifier(
            model=config.model,
            tracker=tracker,
            api_url=config.lucid_api_url,
        )

    # Build work items
    work_items = []

    for track in active_tracks:
        # Load tasks for this track
        if track == Track.HUMANEVAL:
            tasks = load_humaneval_tasks(limit)
        elif track == Track.SWEBENCH:
            tasks = load_swebench_tasks(limit, offset)
        elif track == Track.APP_GENERATION:
            tc = config.track_config(track)
            tasks = load_app_tasks(tc.task_dir if tc else None, limit)
        elif track == Track.FEATURE_ADDITION:
            tc = config.track_config(track)
            tasks = load_feature_tasks(tc.task_dir if tc else None, limit)
        else:
            continue

        if not tasks:
            print(f"No tasks found for track {track.value}, skipping")
            continue

        # Get platforms that support this track
        platforms_for_track = [p for p in active_platforms if track in p.tracks]

        for platform_config in platforms_for_track:
            tc = config.track_config(track)
            num_runs = tc.num_runs if tc else 1

            for task in tasks:
                task_id = _get_task_id(task, track)

                for run_num in range(1, num_runs + 1):
                    # Baseline run
                    if not (config.resume and store.exists(
                        platform_config.adapter, track.value, task_id, 0, run_num
                    )):
                        work_items.append({
                            "platform_config": platform_config,
                            "track": track,
                            "task": task,
                            "task_id": task_id,
                            "lucid_k": 0,  # baseline
                            "run_number": run_num,
                        })

                    # LUCID verification runs
                    if lucid_k_values:
                        for k in lucid_k_values:
                            if not (config.resume and store.exists(
                                platform_config.adapter, track.value, task_id, k, run_num
                            )):
                                work_items.append({
                                    "platform_config": platform_config,
                                    "track": track,
                                    "task": task,
                                    "task_id": task_id,
                                    "lucid_k": k,
                                    "run_number": run_num,
                                })

    if not work_items:
        print("All results already exist. Nothing to do.")
        return

    skipped = 0  # Count items skipped during resume
    print(f"Work items: {len(work_items)}")
    print()

    # Run
    passed_count = 0
    failed_count = 0
    error_count = 0

    pbar = tqdm(work_items, desc="Benchmarking", unit="task")
    for item in pbar:
        platform_config = item["platform_config"]
        track = item["track"]
        task = item["task"]
        task_id = item["task_id"]
        lucid_k = item["lucid_k"]
        run_number = item["run_number"]

        label = f"{platform_config.adapter} {track.value} k={lucid_k} #{run_number}"
        pbar.set_postfix_str(f"{label} {task_id[:30]}")

        try:
            # Create adapter
            adapter = create_adapter(platform_config, tracker)

            if lucid_k == 0:
                # BASELINE: generate and evaluate
                gen_result = _generate(adapter, track, task, task_id, run_number)

                if not gen_result.success:
                    error_count += 1
                    store.save({
                        "platform": platform_config.adapter,
                        "track": track.value,
                        "task_id": task_id,
                        "lucid_k": 0,
                        "run_number": run_number,
                        "generation": gen_result.to_dict(),
                        "evaluation": None,
                        "passed": False,
                        "error": gen_result.error,
                    })
                    continue

                eval_result = _evaluate(evaluator, gen_result.code, track, task, platform_config.adapter)

                store.save({
                    "platform": platform_config.adapter,
                    "track": track.value,
                    "task_id": task_id,
                    "lucid_k": 0,
                    "run_number": run_number,
                    "generation": gen_result.to_dict(),
                    "evaluation": eval_result.to_dict(),
                    "passed": eval_result.passed,
                    "score": eval_result.score,
                })

                if eval_result.passed:
                    passed_count += 1
                else:
                    failed_count += 1

            else:
                # LUCID VERIFICATION: load baseline, verify, evaluate
                baseline = store.load(
                    platform_config.adapter, track.value, task_id, 0, run_number
                )
                if not baseline:
                    # Need baseline first — skip this LUCID run
                    error_count += 1
                    continue

                baseline_code = baseline.get("generation", {}).get("code", "")
                if not baseline_code:
                    error_count += 1
                    continue

                # Run LUCID verification
                if track == Track.HUMANEVAL:
                    lucid_result = lucid.verify_humaneval(
                        baseline_code, task, platform_config.adapter, k=lucid_k,
                    )
                elif track == Track.SWEBENCH:
                    lucid_result = lucid.verify_swebench(
                        baseline_code, task, platform_config.adapter, k=lucid_k,
                    )
                elif track == Track.APP_GENERATION:
                    lucid_result = lucid.verify_app(
                        baseline_code, task, platform_config.adapter, k=lucid_k,
                    )
                else:
                    error_count += 1
                    continue

                # Evaluate the LUCID-verified output
                verified_code = lucid_result.get("verified_code", baseline_code)
                eval_result = _evaluate(
                    evaluator, verified_code, track, task, platform_config.adapter,
                )

                store.save({
                    "platform": platform_config.adapter,
                    "track": track.value,
                    "task_id": task_id,
                    "lucid_k": lucid_k,
                    "run_number": run_number,
                    "lucid_result": lucid_result,
                    "evaluation": eval_result.to_dict(),
                    "passed": eval_result.passed,
                    "score": eval_result.score,
                })

                if eval_result.passed:
                    passed_count += 1
                else:
                    failed_count += 1

        except Exception as e:
            error_count += 1
            print(f"\nERROR: {label} {task_id}: {e}", file=sys.stderr)
            continue

        # Budget check every 10 items
        if (passed_count + failed_count + error_count) % 10 == 0:
            tracker.save(tracker_path)
            if tracker.total_cost > config.budget * 0.9:
                print(f"\n WARNING: Approaching budget (${tracker.total_cost:.2f} / ${config.budget:.2f})")
            if tracker.is_over_budget():
                print(f"\n BUDGET EXCEEDED (${tracker.total_cost:.2f} / ${config.budget:.2f}). Stopping.")
                break

    # Final save
    tracker.save(tracker_path)

    # Summary
    total = passed_count + failed_count
    print(f"\n{'=' * 60}")
    print(f"RESULTS")
    print(f"{'=' * 60}")
    if total > 0:
        print(f"Passed: {passed_count}/{total} ({100*passed_count/total:.1f}%)")
        print(f"Failed: {failed_count}/{total}")
    print(f"Errors: {error_count}")
    print()
    print(tracker.summary())


# --- Helpers ---

def _get_task_id(task: dict, track: Track) -> str:
    """Extract task ID from task dict based on track type."""
    if track == Track.HUMANEVAL:
        return task.get("task_id", "unknown")
    elif track == Track.SWEBENCH:
        return task.get("instance_id", "unknown")
    else:
        return task.get("id", task.get("task_id", "unknown"))


def _generate(
    adapter: PlatformAdapter,
    track: Track,
    task: dict,
    task_id: str,
    run_number: int,
) -> GenerationResult:
    """Generate code using the platform adapter for the given track."""
    if track == Track.HUMANEVAL:
        result = adapter.generate_function(task["prompt"])
        result.task_id = task_id
        result.run_number = run_number
        return result
    elif track == Track.SWEBENCH:
        # Build source files dict from task context
        source_files = {}
        # Use oracle retrieval from task patch (standard SWE-bench practice)
        from ..swebench.conditions import _get_affected_files, _fetch_file_from_github
        affected = _get_affected_files(task.get("patch", ""))
        for filepath in affected[:5]:
            content = _fetch_file_from_github(
                task["repo"], task["base_commit"], filepath
            )
            if content:
                source_files[filepath] = content
        result = adapter.generate_patch(task["problem_statement"], source_files)
        result.task_id = task_id
        result.run_number = run_number
        return result
    elif track == Track.APP_GENERATION:
        spec = task.get("spec", task.get("description", ""))
        result = adapter.generate_app(spec)
        result.task_id = task_id
        result.run_number = run_number
        return result
    elif track == Track.FEATURE_ADDITION:
        feature = task.get("feature_request", task.get("description", ""))
        codebase = task.get("codebase", {})
        result = adapter.add_feature(feature, codebase)
        result.task_id = task_id
        result.run_number = run_number
        return result
    else:
        return GenerationResult(
            platform=adapter.name,
            task_id=task_id,
            track=track.value,
            code="",
            success=False,
            error=f"Unknown track: {track}",
        )


def _evaluate(
    evaluator: Evaluator,
    code: str,
    track: Track,
    task: dict,
    platform: str,
) -> EvalResult:
    """Evaluate generated code using the appropriate evaluator."""
    if track == Track.HUMANEVAL:
        return evaluator.evaluate_humaneval(code, task, platform)
    elif track == Track.SWEBENCH:
        return evaluator.evaluate_swebench(
            code, task.get("instance_id", "unknown"), platform,
        )
    elif track == Track.APP_GENERATION:
        return evaluator.evaluate_app(code, task, platform)
    elif track == Track.FEATURE_ADDITION:
        return evaluator.evaluate_feature(code, task, platform)
    else:
        return EvalResult(
            task_id=_get_task_id(task, track),
            platform=platform,
            track=track.value,
            passed=False,
            score=0.0,
            error=f"Unknown track: {track}",
        )


def _print_cost_estimate(
    platforms: list[PlatformConfig],
    tracks: list[Track],
    limit: int,
    lucid_k_values: Optional[list[int]],
):
    """Print estimated cost without running anything."""
    # Rough per-task cost estimates
    track_costs = {
        Track.HUMANEVAL: 0.05,
        Track.SWEBENCH: 0.50,
        Track.APP_GENERATION: 0.15,
        Track.FEATURE_ADDITION: 0.20,
    }
    track_task_counts = {
        Track.HUMANEVAL: min(164, limit) if limit else 164,
        Track.SWEBENCH: min(300, limit) if limit else 300,
        Track.APP_GENERATION: min(20, limit) if limit else 20,
        Track.FEATURE_ADDITION: min(15, limit) if limit else 15,
    }
    lucid_multiplier = 1.0
    if lucid_k_values:
        lucid_multiplier += len(lucid_k_values) * 0.8  # LUCID is ~80% of baseline cost per k

    print("\nCost Estimate:")
    print(f"{'Platform':<15} {'Track':<15} {'Tasks':<8} {'Per Task':<10} {'Subtotal':<10}")
    print("-" * 60)

    total = 0
    for plat in platforms:
        for track in tracks:
            if track not in plat.tracks:
                continue
            n_tasks = track_task_counts.get(track, 0)
            per_task = track_costs.get(track, 0.10) * lucid_multiplier
            subtotal = n_tasks * per_task
            total += subtotal
            print(f"{plat.name:<15} {track.value:<15} {n_tasks:<8} ${per_task:<9.3f} ${subtotal:<9.2f}")

    print("-" * 60)
    print(f"{'TOTAL':<39} ${total:.2f}")
    if lucid_k_values:
        print(f"  (includes LUCID verification at k={lucid_k_values})")


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="Cross-Platform AI Code Quality Benchmark Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--platform", nargs="+", default=None,
        help="Platform(s) to benchmark (default: all). Options: cursor, bolt, lovable, replit, copilot",
    )
    parser.add_argument(
        "--track", nargs="+", default=None,
        help="Track(s) to run (default: all). Options: humaneval, swebench, app_gen, feature",
    )
    parser.add_argument(
        "--lucid-k", nargs="+", type=int, default=None,
        help="LUCID verification iterations (e.g., 1 3). Omit for baseline only.",
    )
    parser.add_argument(
        "--model", default="claude-sonnet-4-5-20250929",
        help="Model for LUCID verification and API-based adapters",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/benchmark/"),
        help="Output directory for results",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit tasks per track (0 = all)")
    parser.add_argument("--offset", type=int, default=0, help="Skip first N tasks (for chunking)")
    parser.add_argument("--resume", action="store_true", help="Skip existing results")
    parser.add_argument("--budget", type=float, default=2000.0, help="Budget limit in dollars")
    parser.add_argument("--dry-run", action="store_true", help="Print cost estimate only")
    parser.add_argument("--chunk-id", default="", help="Chunk ID for parallel cost tracking")

    args = parser.parse_args()

    config = BenchmarkConfig.default()
    config.output_dir = args.output
    config.model = args.model
    config.budget = args.budget
    config.resume = args.resume
    config.dry_run = args.dry_run
    config.chunk_id = args.chunk_id

    # Override platform models if specified
    if args.model:
        for p in config.platforms:
            if p.adapter in ("cursor", "replit"):
                p.model = args.model

    run_benchmark(
        config=config,
        platforms=args.platform,
        tracks=args.track,
        lucid_k_values=args.lucid_k,
        limit=args.limit,
        offset=args.offset,
    )


if __name__ == "__main__":
    main()
