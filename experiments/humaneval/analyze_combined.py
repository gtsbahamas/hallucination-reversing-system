#!/usr/bin/env python3
"""
Combined analysis of all HumanEval benchmark results across Phase A, B, and C.

Loads results from multiple output directories, deduplicates, and produces:
1. Combined scaling curve (all 4 conditions)
2. Ablation table
3. Publication-quality figures

Usage:
    python -m experiments.humaneval.analyze_combined
"""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.size'] = 11


RESULT_DIRS = [
    Path("results/humaneval"),      # Phase A: baseline + lucid
    Path("results/humaneval-b"),    # Phase B: self-refine
    Path("results/humaneval-b2"),   # Phase B: llm-judge
    Path("results/humaneval-b3"),   # Phase B: llm-judge k=5 (parallel)
    Path("results/humaneval-c"),    # Phase C: no-extract, no-remediate, learned-verify (sequential)
    Path("results/humaneval-c2"),   # Phase C: learned-verify (parallel)
    Path("results/humaneval-c3"),   # Phase C: no-context (parallel)
    Path("results/humaneval-c4"),   # Phase C: random-verify (parallel)
    Path("results/humaneval-c5"),   # Phase C: random-verify k=5 (parallel)
    Path("results/humaneval-c6"),   # Phase C: learned-verify k=5 (parallel)
]


def load_all_results() -> list[dict]:
    """Load results from all directories, deduplicating by (task_id, condition, max_iterations)."""
    seen = {}
    for d in RESULT_DIRS:
        if not d.exists():
            continue
        for path in d.glob("*.json"):
            if path.name == "cost_tracker.json":
                continue
            try:
                data = json.loads(path.read_text())
                key = (data["task_id"], data["condition"], data["max_iterations"])
                if key not in seen:
                    seen[key] = data
            except (json.JSONDecodeError, TypeError, KeyError):
                continue
    return list(seen.values())


def bootstrap_ci(scores: list, n_bootstrap: int = 10000, ci: float = 0.95):
    rng = np.random.default_rng(42)
    arr = np.array(scores, dtype=float)
    n = len(arr)
    if n == 0:
        return 0.0, 0.0, 0.0
    bootstraps = [np.mean(rng.choice(arr, size=n, replace=True)) for _ in range(n_bootstrap)]
    alpha = (1 - ci) / 2
    return float(np.mean(arr)), float(np.quantile(bootstraps, alpha)), float(np.quantile(bootstraps, 1 - alpha))


def compute_pass_rates(results: list[dict]) -> dict:
    grouped = defaultdict(list)
    for r in results:
        key = (r["condition"], r["max_iterations"])
        grouped[key].append(1 if r["final_passed"] else 0)
    rates = {}
    for (condition, max_iter), scores in grouped.items():
        mean, ci_low, ci_high = bootstrap_ci(scores)
        rates[(condition, max_iter)] = {
            "mean": mean, "ci_low": ci_low, "ci_high": ci_high,
            "n": len(scores), "passed": sum(scores),
        }
    return rates


def print_results_table(results: list[dict]):
    rates = compute_pass_rates(results)
    print(f"\n{'Condition':<25} {'k':<5} {'pass@1':<10} {'95% CI':<25} {'n':<5} {'passed':<7}")
    print("-" * 80)
    for (cond, max_iter) in sorted(rates.keys()):
        r = rates[(cond, max_iter)]
        print(f"{cond:<25} {max_iter:<5} {r['mean']*100:>6.1f}%    [{r['ci_low']*100:.1f}%, {r['ci_high']*100:.1f}%]       {r['n']:<5} {r['passed']:<7}")


def analyze_errors(results: list[dict]):
    errors = defaultdict(lambda: defaultdict(int))
    for r in results:
        if not r["final_passed"]:
            cond = r["condition"]
            err = r.get("final_test_output", {}).get("error_type", "unknown")
            errors[cond][err] += 1
    if errors:
        print(f"\nError Type Distribution:")
        print(f"{'Condition':<25} {'Error Type':<20} {'Count':<7}")
        print("-" * 55)
        for cond in sorted(errors.keys()):
            for err_type, count in sorted(errors[cond].items(), key=lambda x: -x[1]):
                print(f"{cond:<25} {err_type:<20} {count:<7}")


def plot_killer_chart(results: list[dict], output_dir: Path):
    """The killer chart: all 4 conditions on one scaling curve."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rates = compute_pass_rates(results)

    # Only include the main 4 conditions (not ablations)
    main_conditions = {
        "baseline": {"color": "#888888", "marker": "s", "label": "Baseline (single pass)", "ls": "--"},
        "self-refine": {"color": "#e74c3c", "marker": "^", "label": "Self-Refine (LLM self-critique)"},
        "llm-judge": {"color": "#f39c12", "marker": "D", "label": "LLM-as-Judge (separate evaluator)"},
        "lucid": {"color": "#2ecc71", "marker": "o", "label": "LUCID (formal verification)", "lw": 2.5},
    }

    fig, ax = plt.subplots(figsize=(9, 6))

    for cond_name, style in main_conditions.items():
        cond_rates = {mi: rates[(c, mi)] for (c, mi) in rates if c == cond_name}
        if not cond_rates:
            continue

        if cond_name == "baseline":
            if 1 in cond_rates:
                val = cond_rates[1]
                ax.axhline(y=val["mean"] * 100, color=style["color"], linestyle="--",
                          alpha=0.7, label=style["label"], linewidth=1.5)
                ax.axhspan(val["ci_low"] * 100, val["ci_high"] * 100,
                          color=style["color"], alpha=0.08)
        else:
            iters = sorted(cond_rates.keys())
            means = [cond_rates[k]["mean"] * 100 for k in iters]
            ci_lows = [cond_rates[k]["ci_low"] * 100 for k in iters]
            ci_highs = [cond_rates[k]["ci_high"] * 100 for k in iters]

            lw = style.get("lw", 1.8)
            ax.plot(iters, means, color=style["color"], marker=style["marker"],
                   label=style["label"], linewidth=lw, markersize=8)
            ax.fill_between(iters, ci_lows, ci_highs, color=style["color"], alpha=0.12)

    ax.set_xlabel("Loop Iterations (k)", fontsize=13)
    ax.set_ylabel("pass@1 (%)", fontsize=13)
    ax.set_title("HumanEval: Only Formal Verification Converges to Perfection",
                fontsize=14, fontweight="bold")
    ax.set_xticks([1, 3, 5])
    ax.legend(fontsize=10, loc="lower right")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(80, 101)

    plt.tight_layout()
    plt.savefig(output_dir / "killer_chart.pdf", bbox_inches="tight", dpi=300)
    plt.savefig(output_dir / "killer_chart.png", bbox_inches="tight", dpi=300)
    print(f"Saved: {output_dir / 'killer_chart.png'}")
    plt.close()


def plot_ablation_chart(results: list[dict], output_dir: Path):
    """Ablation study chart: LUCID full vs each ablation variant."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rates = compute_pass_rates(results)

    ablation_conditions = {
        "lucid": {"color": "#2ecc71", "marker": "o", "label": "LUCID (full)", "lw": 2.5},
        "lucid-no-extract": {"color": "#9b59b6", "marker": "v", "label": "- code extraction"},
        "lucid-no-remediate": {"color": "#e74c3c", "marker": "^", "label": "- structured remediation"},
        "lucid-learned-verify": {"color": "#3498db", "marker": "D", "label": "LLM verifier (replace formal)"},
        "lucid-no-context": {"color": "#f39c12", "marker": "s", "label": "- error context"},
        "lucid-random-verify": {"color": "#95a5a6", "marker": "x", "label": "Random verifier (control)"},
    }

    fig, ax = plt.subplots(figsize=(9, 6))

    for cond_name, style in ablation_conditions.items():
        cond_rates = {mi: rates[(c, mi)] for (c, mi) in rates if c == cond_name}
        if not cond_rates:
            continue

        iters = sorted(cond_rates.keys())
        means = [cond_rates[k]["mean"] * 100 for k in iters]
        ci_lows = [cond_rates[k]["ci_low"] * 100 for k in iters]
        ci_highs = [cond_rates[k]["ci_high"] * 100 for k in iters]

        lw = style.get("lw", 1.5)
        ax.plot(iters, means, color=style["color"], marker=style["marker"],
               label=style["label"], linewidth=lw, markersize=7)
        ax.fill_between(iters, ci_lows, ci_highs, color=style["color"], alpha=0.1)

    ax.set_xlabel("Loop Iterations (k)", fontsize=13)
    ax.set_ylabel("pass@1 (%)", fontsize=13)
    ax.set_title("Ablation Study: Every LUCID Component Matters",
                fontsize=14, fontweight="bold")
    ax.set_xticks([1, 3, 5])
    ax.legend(fontsize=9, loc="lower right")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(70, 101)

    plt.tight_layout()
    plt.savefig(output_dir / "ablation_chart.pdf", bbox_inches="tight", dpi=300)
    plt.savefig(output_dir / "ablation_chart.png", bbox_inches="tight", dpi=300)
    print(f"Saved: {output_dir / 'ablation_chart.png'}")
    plt.close()


def compute_total_cost():
    """Sum cost trackers across all directories."""
    total = 0.0
    for d in RESULT_DIRS:
        ct = d / "cost_tracker.json"
        if ct.exists():
            try:
                data = json.loads(ct.read_text())
                total += data.get("summary", {}).get("total_cost", 0.0)
            except (json.JSONDecodeError, TypeError):
                pass
    return total


def main():
    results = load_all_results()
    print(f"Loaded {len(results)} unique results from {len(RESULT_DIRS)} directories")

    # Separate main conditions and ablations
    main_conds = ["baseline", "self-refine", "llm-judge", "lucid"]
    main_results = [r for r in results if r["condition"] in main_conds]
    ablation_results = [r for r in results if r["condition"].startswith("lucid")]

    print("\n=== MAIN CONDITIONS ===")
    print_results_table(main_results)
    analyze_errors(main_results)

    print("\n=== ABLATION STUDIES ===")
    ablation_only = [r for r in results if r["condition"] not in main_conds]
    if ablation_only:
        print_results_table(ablation_only)
        analyze_errors(ablation_only)
    else:
        print("No ablation results yet")

    print(f"\n=== COST ===")
    print(f"Total cost (all phases): ${compute_total_cost():.2f}")

    output_dir = Path("figures")

    # Generate killer chart if we have at least 2 main conditions
    available_main = set(r["condition"] for r in main_results)
    if len(available_main) >= 2:
        plot_killer_chart(main_results, output_dir)

    # Generate ablation chart if we have ablation data
    if ablation_only:
        plot_ablation_chart(ablation_results, output_dir)

    print(f"\nDone. Charts in {output_dir}/")


if __name__ == "__main__":
    main()
