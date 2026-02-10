#!/usr/bin/env python3
"""
Analyze HumanEval benchmark results and generate charts.

Usage:
    python -m experiments.humaneval.analyze --results results/humaneval/ --output figures/
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.size'] = 11


def load_results(results_dir: Path) -> list[dict]:
    """Load all result JSON files from a directory."""
    results = []
    for path in results_dir.glob("*.json"):
        if path.name == "cost_tracker.json":
            continue
        try:
            data = json.loads(path.read_text())
            results.append(data)
        except (json.JSONDecodeError, TypeError):
            continue
    return results


def bootstrap_ci(scores: list, n_bootstrap: int = 10000, ci: float = 0.95):
    """Bootstrap confidence interval for a proportion."""
    rng = np.random.default_rng(42)
    arr = np.array(scores, dtype=float)
    n = len(arr)
    if n == 0:
        return 0.0, 0.0, 0.0
    bootstraps = [np.mean(rng.choice(arr, size=n, replace=True)) for _ in range(n_bootstrap)]
    alpha = (1 - ci) / 2
    return float(np.mean(arr)), float(np.quantile(bootstraps, alpha)), float(np.quantile(bootstraps, 1 - alpha))


def compute_pass_rates(results: list[dict]) -> dict:
    """Compute pass@1 for each (condition, max_iterations) pair."""
    grouped = defaultdict(list)
    for r in results:
        key = (r["condition"], r["max_iterations"])
        grouped[key].append(1 if r["final_passed"] else 0)

    rates = {}
    for (condition, max_iter), scores in grouped.items():
        mean, ci_low, ci_high = bootstrap_ci(scores)
        rates[(condition, max_iter)] = {
            "mean": mean,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "n": len(scores),
            "passed": sum(scores),
        }
    return rates


def plot_scaling_curve(results: list[dict], output_dir: Path, title: str = "HumanEval"):
    """Generate the scaling curve chart."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rates = compute_pass_rates(results)

    fig, ax = plt.subplots(figsize=(8, 5.5))

    conditions = {
        "baseline": {"color": "#888888", "marker": "s", "label": "Baseline (single pass)", "ls": "--"},
        "self-refine": {"color": "#e74c3c", "marker": "^", "label": "Self-Refine"},
        "llm-judge": {"color": "#f39c12", "marker": "D", "label": "LLM-as-Judge"},
        "lucid": {"color": "#2ecc71", "marker": "o", "label": "LUCID (formal verification)", "lw": 2.5},
    }

    iterations = sorted(set(mi for (_, mi) in rates.keys()))

    for cond_name, style in conditions.items():
        cond_rates = {mi: rates[(cond_name, mi)] for (c, mi) in rates if c == cond_name}
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
                   label=style["label"], linewidth=lw, markersize=7)
            ax.fill_between(iters, ci_lows, ci_highs, color=style["color"], alpha=0.12)

    ax.set_xlabel("LUCID Loop Iterations", fontsize=12)
    ax.set_ylabel("pass@1 (%)", fontsize=12)
    ax.set_title(f"{title}: Formal Verification Enables Monotonic Convergence",
                fontsize=13, fontweight="bold")
    ax.set_xticks(iterations)
    ax.legend(fontsize=9, loc="lower right")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(output_dir / "scaling_curve.pdf", bbox_inches="tight", dpi=300)
    plt.savefig(output_dir / "scaling_curve.png", bbox_inches="tight", dpi=300)
    print(f"Saved: {output_dir / 'scaling_curve.pdf'}")
    print(f"Saved: {output_dir / 'scaling_curve.png'}")
    plt.close()


def plot_cost_efficiency(results: list[dict], cost_data: dict, output_dir: Path):
    """Generate cost-efficiency frontier chart."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rates = compute_pass_rates(results)

    fig, ax = plt.subplots(figsize=(8, 5.5))

    conditions = {
        "baseline": {"color": "#888888", "marker": "s"},
        "self-refine": {"color": "#e74c3c", "marker": "^"},
        "llm-judge": {"color": "#f39c12", "marker": "D"},
        "lucid": {"color": "#2ecc71", "marker": "o"},
    }

    for (cond, max_iter), rate_info in rates.items():
        if cond not in conditions:
            continue
        style = conditions[cond]
        cost_key = f"{cond}_k{max_iter}"
        cost = cost_data.get(cost_key, 0)
        ax.scatter(cost, rate_info["mean"] * 100, color=style["color"],
                  marker=style["marker"], s=80, zorder=5)
        ax.annotate(f"k={max_iter}", (cost, rate_info["mean"] * 100),
                   textcoords="offset points", xytext=(5, 5), fontsize=7)

    # Legend
    for cond, style in conditions.items():
        ax.scatter([], [], color=style["color"], marker=style["marker"], label=cond, s=60)
    ax.legend(fontsize=9)

    ax.set_xlabel("Total API Cost ($)", fontsize=12)
    ax.set_ylabel("pass@1 (%)", fontsize=12)
    ax.set_title("Cost-Efficiency Frontier", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "cost_efficiency.pdf", bbox_inches="tight", dpi=300)
    plt.savefig(output_dir / "cost_efficiency.png", bbox_inches="tight", dpi=300)
    print(f"Saved: {output_dir / 'cost_efficiency.png'}")
    plt.close()


def print_results_table(results: list[dict]):
    """Print a summary table of results."""
    rates = compute_pass_rates(results)

    print(f"\n{'Condition':<15} {'k':<5} {'pass@1':<10} {'95% CI':<20} {'n':<5} {'passed':<7}")
    print("-" * 65)

    for (cond, max_iter) in sorted(rates.keys()):
        r = rates[(cond, max_iter)]
        print(f"{cond:<15} {max_iter:<5} {r['mean']*100:>6.1f}%    [{r['ci_low']*100:.1f}%, {r['ci_high']*100:.1f}%]    {r['n']:<5} {r['passed']:<7}")


def analyze_error_types(results: list[dict]):
    """Analyze distribution of error types across conditions."""
    errors = defaultdict(lambda: defaultdict(int))
    for r in results:
        if not r["final_passed"]:
            cond = r["condition"]
            err = r.get("final_test_output", {}).get("error_type", "unknown")
            errors[cond][err] += 1

    print(f"\nError Type Distribution:")
    print(f"{'Condition':<15} {'Error Type':<20} {'Count':<7}")
    print("-" * 45)
    for cond in sorted(errors.keys()):
        for err_type, count in sorted(errors[cond].items(), key=lambda x: -x[1]):
            print(f"{cond:<15} {err_type:<20} {count:<7}")


def main():
    parser = argparse.ArgumentParser(description="Analyze HumanEval benchmark results")
    parser.add_argument("--results", type=Path, required=True, help="Results directory")
    parser.add_argument("--output", type=Path, default=Path("figures/"), help="Output directory for charts")
    parser.add_argument("--cost-data", type=Path, help="Cost tracker JSON file")

    args = parser.parse_args()

    results = load_results(args.results)
    if not results:
        print(f"No results found in {args.results}")
        return

    print(f"Loaded {len(results)} results from {args.results}")

    print_results_table(results)
    analyze_error_types(results)

    plot_scaling_curve(results, args.output)

    if args.cost_data and args.cost_data.exists():
        cost_data = json.loads(args.cost_data.read_text())
        plot_cost_efficiency(results, cost_data.get("summary", {}).get("cost_by_condition", {}), args.output)

    print(f"\nCharts saved to {args.output}")


if __name__ == "__main__":
    main()
