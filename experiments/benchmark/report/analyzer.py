#!/usr/bin/env python3
"""
Cross-platform benchmark analysis engine.

Loads results from all platforms and tracks, computes pass rates, rankings,
LUCID improvement metrics, and exports tables for reporting.

Usage:
    from experiments.benchmark.report.analyzer import Analyzer
    a = Analyzer("results/benchmark")
    df = a.load_results()
    summary = a.compute_pass_rates(df)
"""

import json
import csv
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Data schema
# ---------------------------------------------------------------------------

TRACKS = ["humaneval", "swebench", "app_generation", "feature_addition"]

TRACK_LABELS = {
    "humaneval": "HumanEval (Function-Level)",
    "swebench": "SWE-bench Lite (Bug Fixing)",
    "app_generation": "App Generation",
    "feature_addition": "Feature Addition",
}

PLATFORMS = [
    "cursor", "windsurf", "copilot", "tabnine", "jetbrains",
    "devin", "replit", "bolt", "lovable", "v0",
]

DIFFICULTY_TIERS = ["easy", "medium", "hard"]

CONDITIONS = ["baseline", "lucid_k1", "lucid_k3"]


@dataclass
class TaskResult:
    """A single task result for one platform/track/condition."""
    platform: str
    track: str
    task_id: str
    condition: str          # baseline | lucid_k1 | lucid_k3
    passed: bool
    score: float = 0.0      # 0-1 for rubric-scored tasks (app gen)
    difficulty: str = ""     # easy | medium | hard
    error_type: str = ""    # patch_failed | test_failed | build_failed | etc.
    iterations: int = 1
    cost_usd: float = 0.0
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Bootstrap CI (following humaneval pattern)
# ---------------------------------------------------------------------------

def bootstrap_ci(scores: list, n_bootstrap: int = 10000, ci: float = 0.95):
    """Compute mean and 95% CI via bootstrap resampling."""
    rng = np.random.default_rng(42)
    arr = np.array(scores, dtype=float)
    n = len(arr)
    if n == 0:
        return 0.0, 0.0, 0.0
    bootstraps = [np.mean(rng.choice(arr, size=n, replace=True)) for _ in range(n_bootstrap)]
    alpha = (1 - ci) / 2
    return (
        float(np.mean(arr)),
        float(np.quantile(bootstraps, alpha)),
        float(np.quantile(bootstraps, 1 - alpha)),
    )


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class Analyzer:
    """Main analysis engine for cross-platform benchmark results."""

    def __init__(self, results_dir: str | Path):
        self.results_dir = Path(results_dir)

    # -- Loading ----------------------------------------------------------

    def load_results(self) -> list[TaskResult]:
        """Load all results from the results directory.

        Expected directory structure:
            results_dir/
                {platform}/
                    {track}/
                        {task_id}_{condition}.json

        Each JSON file should contain at minimum:
            task_id, platform, track, condition, passed
        Optional: score, difficulty, error_type, iterations, cost_usd, metadata
        """
        results = []
        if not self.results_dir.exists():
            return results

        for platform_dir in sorted(self.results_dir.iterdir()):
            if not platform_dir.is_dir():
                continue
            platform = platform_dir.name

            for track_dir in sorted(platform_dir.iterdir()):
                if not track_dir.is_dir():
                    continue
                track = track_dir.name

                for filepath in sorted(track_dir.glob("*.json")):
                    if "cost_tracker" in filepath.name:
                        continue
                    try:
                        data = json.loads(filepath.read_text())
                        result = TaskResult(
                            platform=data.get("platform", platform),
                            track=data.get("track", track),
                            task_id=data["task_id"],
                            condition=data["condition"],
                            passed=data.get("passed", data.get("final_passed", False)),
                            score=float(data.get("score", 1.0 if data.get("passed", data.get("final_passed", False)) else 0.0)),
                            difficulty=data.get("difficulty", ""),
                            error_type=data.get("error_type", ""),
                            iterations=data.get("iterations_count", data.get("max_iterations", 1)),
                            cost_usd=float(data.get("cost_usd", 0.0)),
                            metadata=data.get("metadata", {}),
                        )
                        results.append(result)
                    except (json.JSONDecodeError, KeyError, TypeError):
                        continue

        return results

    # -- Pass rates -------------------------------------------------------

    def compute_pass_rates(
        self,
        results: list[TaskResult],
        group_by: Optional[list[str]] = None,
    ) -> dict[tuple, dict]:
        """Compute pass rates grouped by specified fields.

        Args:
            results: List of TaskResult objects.
            group_by: Fields to group by. Default: ['platform', 'track', 'condition']

        Returns:
            Dict mapping group key tuple to stats dict with
            mean, ci_low, ci_high, n, passed, avg_score.
        """
        if group_by is None:
            group_by = ["platform", "track", "condition"]

        grouped = defaultdict(list)
        scores_grouped = defaultdict(list)

        for r in results:
            key = tuple(getattr(r, f) for f in group_by)
            grouped[key].append(1 if r.passed else 0)
            scores_grouped[key].append(r.score)

        rates = {}
        for key, pass_scores in grouped.items():
            mean, ci_low, ci_high = bootstrap_ci(pass_scores)
            avg_score = float(np.mean(scores_grouped[key])) if scores_grouped[key] else 0.0
            rates[key] = {
                "mean": mean,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "n": len(pass_scores),
                "passed": sum(pass_scores),
                "avg_score": avg_score,
            }
        return rates

    # -- LUCID improvement ------------------------------------------------

    def compute_lucid_improvement(
        self, results: list[TaskResult]
    ) -> dict[str, dict[str, dict]]:
        """Compute per-platform, per-track LUCID improvement metrics.

        Returns:
            {platform: {track: {
                baseline_rate, lucid_k1_rate, lucid_k3_rate,
                absolute_improvement_k1, relative_improvement_k1,
                absolute_improvement_k3, relative_improvement_k3,
                n_improved, n_regressed, n_unchanged
            }}}
        """
        # Group by (platform, track, condition, task_id)
        task_map = defaultdict(dict)
        for r in results:
            task_map[(r.platform, r.track, r.task_id)][r.condition] = r

        # Aggregate per (platform, track)
        improvements = defaultdict(lambda: defaultdict(dict))

        pt_tasks = defaultdict(list)
        for (platform, track, task_id), cond_map in task_map.items():
            pt_tasks[(platform, track)].append((task_id, cond_map))

        for (platform, track), tasks in pt_tasks.items():
            baseline_passed = 0
            lucid_k1_passed = 0
            lucid_k3_passed = 0
            n_improved = 0
            n_regressed = 0
            n_unchanged = 0
            n = len(tasks)

            for task_id, cond_map in tasks:
                b = cond_map.get("baseline")
                lk1 = cond_map.get("lucid_k1")
                lk3 = cond_map.get("lucid_k3")

                b_pass = b.passed if b else False
                lk1_pass = lk1.passed if lk1 else False
                lk3_pass = lk3.passed if lk3 else lk1_pass

                if b_pass:
                    baseline_passed += 1
                if lk1_pass:
                    lucid_k1_passed += 1
                if lk3_pass:
                    lucid_k3_passed += 1

                # Head-to-head baseline vs best LUCID
                lucid_best = lk1_pass or lk3_pass
                if not b_pass and lucid_best:
                    n_improved += 1
                elif b_pass and not lucid_best:
                    n_regressed += 1
                else:
                    n_unchanged += 1

            b_rate = baseline_passed / n if n > 0 else 0
            lk1_rate = lucid_k1_passed / n if n > 0 else 0
            lk3_rate = lucid_k3_passed / n if n > 0 else 0

            improvements[platform][track] = {
                "n": n,
                "baseline_rate": b_rate,
                "lucid_k1_rate": lk1_rate,
                "lucid_k3_rate": lk3_rate,
                "absolute_improvement_k1": lk1_rate - b_rate,
                "relative_improvement_k1": (lk1_rate - b_rate) / b_rate if b_rate > 0 else 0,
                "absolute_improvement_k3": lk3_rate - b_rate,
                "relative_improvement_k3": (lk3_rate - b_rate) / b_rate if b_rate > 0 else 0,
                "n_improved": n_improved,
                "n_regressed": n_regressed,
                "n_unchanged": n_unchanged,
            }

        return dict(improvements)

    # -- Rankings ---------------------------------------------------------

    def compute_rankings(self, results: list[TaskResult]) -> list[dict]:
        """Compute overall platform rankings.

        Ranking criteria:
        1. Average baseline pass rate across all tracks
        2. Average LUCID-enhanced pass rate across all tracks
        3. Total tasks attempted

        Returns sorted list of platform ranking dicts.
        """
        platform_stats = defaultdict(lambda: {
            "baseline_scores": [],
            "lucid_scores": [],
            "total_tasks": 0,
            "tracks_tested": set(),
        })

        for r in results:
            ps = platform_stats[r.platform]
            ps["tracks_tested"].add(r.track)
            if r.condition == "baseline":
                ps["baseline_scores"].append(r.score)
                ps["total_tasks"] += 1
            elif r.condition in ("lucid_k1", "lucid_k3"):
                ps["lucid_scores"].append(r.score)

        rankings = []
        for platform, ps in platform_stats.items():
            baseline_avg = float(np.mean(ps["baseline_scores"])) if ps["baseline_scores"] else 0.0
            lucid_avg = float(np.mean(ps["lucid_scores"])) if ps["lucid_scores"] else 0.0
            improvement = lucid_avg - baseline_avg

            rankings.append({
                "platform": platform,
                "baseline_avg_score": baseline_avg,
                "lucid_avg_score": lucid_avg,
                "improvement": improvement,
                "total_tasks": ps["total_tasks"],
                "tracks_tested": len(ps["tracks_tested"]),
                "tracks": sorted(ps["tracks_tested"]),
            })

        # Sort by LUCID-enhanced score descending, then baseline descending
        rankings.sort(key=lambda r: (-r["lucid_avg_score"], -r["baseline_avg_score"]))

        # Add rank
        for i, r in enumerate(rankings):
            r["rank"] = i + 1

        return rankings

    # -- Head-to-head comparison ------------------------------------------

    def head_to_head(
        self, results: list[TaskResult], platform_a: str, platform_b: str
    ) -> dict:
        """Detailed head-to-head comparison between two platforms.

        Returns dict with per-track comparison, overall winner, and
        task-level detail.
        """
        a_tasks = defaultdict(dict)
        b_tasks = defaultdict(dict)

        for r in results:
            if r.condition != "baseline":
                continue
            if r.platform == platform_a:
                a_tasks[r.track][r.task_id] = r
            elif r.platform == platform_b:
                b_tasks[r.track][r.task_id] = r

        comparison = {
            "platform_a": platform_a,
            "platform_b": platform_b,
            "tracks": {},
            "overall": {},
        }

        total_a_wins = 0
        total_b_wins = 0
        total_ties = 0

        for track in sorted(set(list(a_tasks.keys()) + list(b_tasks.keys()))):
            a_track = a_tasks.get(track, {})
            b_track = b_tasks.get(track, {})
            common_tasks = sorted(set(a_track.keys()) & set(b_track.keys()))

            a_pass = sum(1 for t in common_tasks if a_track[t].passed)
            b_pass = sum(1 for t in common_tasks if b_track[t].passed)

            both = sum(1 for t in common_tasks if a_track[t].passed and b_track[t].passed)
            a_only = sum(1 for t in common_tasks if a_track[t].passed and not b_track[t].passed)
            b_only = sum(1 for t in common_tasks if not a_track[t].passed and b_track[t].passed)
            neither = len(common_tasks) - both - a_only - b_only

            total_a_wins += a_only
            total_b_wins += b_only
            total_ties += both + neither

            comparison["tracks"][track] = {
                "common_tasks": len(common_tasks),
                f"{platform_a}_pass": a_pass,
                f"{platform_b}_pass": b_pass,
                "both_pass": both,
                f"{platform_a}_only": a_only,
                f"{platform_b}_only": b_only,
                "neither_pass": neither,
                "winner": platform_a if a_pass > b_pass else (platform_b if b_pass > a_pass else "tie"),
            }

        comparison["overall"] = {
            f"{platform_a}_wins": total_a_wins,
            f"{platform_b}_wins": total_b_wins,
            "ties": total_ties,
            "winner": platform_a if total_a_wins > total_b_wins else (
                platform_b if total_b_wins > total_a_wins else "tie"
            ),
        }

        return comparison

    # -- Export -----------------------------------------------------------

    def export_tables(self, results: list[TaskResult], output_dir: str | Path):
        """Export results as CSV and JSON tables for the report."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Full results CSV
        csv_path = output_dir / "full_results.csv"
        fieldnames = [
            "platform", "track", "task_id", "condition", "passed",
            "score", "difficulty", "error_type", "iterations", "cost_usd",
        ]
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                row = {k: getattr(r, k) for k in fieldnames}
                writer.writerow(row)

        # 2. Pass rates summary JSON
        rates = self.compute_pass_rates(results)
        rates_export = {}
        for key, stats in rates.items():
            str_key = "|".join(str(k) for k in key)
            rates_export[str_key] = stats
        (output_dir / "pass_rates.json").write_text(
            json.dumps(rates_export, indent=2)
        )

        # 3. Rankings JSON
        rankings = self.compute_rankings(results)
        (output_dir / "rankings.json").write_text(
            json.dumps(rankings, indent=2)
        )

        # 4. LUCID improvement JSON
        improvements = self.compute_lucid_improvement(results)
        (output_dir / "lucid_improvement.json").write_text(
            json.dumps(improvements, indent=2)
        )

        # 5. Per-track summary CSV
        track_rates = self.compute_pass_rates(results, group_by=["track", "condition"])
        track_csv = output_dir / "track_summary.csv"
        with open(track_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["track", "condition", "pass_rate", "ci_low", "ci_high", "n", "passed"])
            for (track, cond), stats in sorted(track_rates.items()):
                writer.writerow([
                    track, cond,
                    f"{stats['mean']:.4f}",
                    f"{stats['ci_low']:.4f}",
                    f"{stats['ci_high']:.4f}",
                    stats["n"],
                    stats["passed"],
                ])

        return {
            "full_results": str(csv_path),
            "pass_rates": str(output_dir / "pass_rates.json"),
            "rankings": str(output_dir / "rankings.json"),
            "lucid_improvement": str(output_dir / "lucid_improvement.json"),
            "track_summary": str(track_csv),
        }
