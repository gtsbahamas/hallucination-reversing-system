#!/usr/bin/env python3
"""
Publication-quality chart generation for the cross-platform benchmark.

Uses matplotlib with a consistent color palette and professional styling.
Each platform gets a consistent color across all charts.

Usage:
    from experiments.benchmark.report.charts import ChartGenerator
    gen = ChartGenerator()
    gen.platform_comparison_chart(results, "humaneval", "figures/humaneval_comparison.png")
"""

from pathlib import Path
from collections import defaultdict

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches

matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.size'] = 11
matplotlib.rcParams['axes.spines.top'] = False
matplotlib.rcParams['axes.spines.right'] = False

# ---------------------------------------------------------------------------
# Consistent color palette
# ---------------------------------------------------------------------------

PLATFORM_COLORS = {
    "cursor":     "#2563eb",  # Blue
    "windsurf":   "#7c3aed",  # Purple
    "copilot":    "#059669",  # Emerald
    "tabnine":    "#d97706",  # Amber
    "jetbrains":  "#dc2626",  # Red
    "devin":      "#0891b2",  # Cyan
    "replit":     "#ea580c",  # Orange
    "bolt":       "#4f46e5",  # Indigo
    "lovable":    "#db2777",  # Pink
    "v0":         "#65a30d",  # Lime
}

CONDITION_COLORS = {
    "baseline":  "#94a3b8",  # Slate
    "lucid_k1":  "#3b82f6",  # Blue
    "lucid_k3":  "#22c55e",  # Green
}

DIFFICULTY_COLORS = {
    "easy":   "#86efac",
    "medium": "#fbbf24",
    "hard":   "#f87171",
}

TRACK_LABELS = {
    "humaneval": "HumanEval",
    "swebench": "SWE-bench Lite",
    "app_generation": "App Generation",
    "feature_addition": "Feature Addition",
}


def _get_platform_color(platform: str) -> str:
    return PLATFORM_COLORS.get(platform.lower(), "#6b7280")


def _save_chart(fig, output_path: str | Path):
    """Save chart as both PNG and PDF."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight", dpi=300)
    pdf_path = output_path.with_suffix(".pdf")
    fig.savefig(pdf_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return str(output_path)


# ---------------------------------------------------------------------------
# Chart functions
# ---------------------------------------------------------------------------

class ChartGenerator:
    """Generates all charts for the benchmark report."""

    def platform_comparison_chart(
        self,
        results: list,
        track: str,
        output_path: str | Path,
    ) -> str:
        """Bar chart comparing all platforms on a single track (baseline only).

        Args:
            results: List of TaskResult objects.
            track: Track name (humaneval, swebench, etc.).
            output_path: Where to save the chart.
        """
        # Aggregate pass rates per platform for this track
        platform_stats = defaultdict(lambda: {"scores": [], "n": 0})
        for r in results:
            if r.track == track and r.condition == "baseline":
                platform_stats[r.platform]["scores"].append(1 if r.passed else 0)
                platform_stats[r.platform]["n"] += 1

        if not platform_stats:
            return ""

        # Sort by pass rate descending
        platforms = sorted(
            platform_stats.keys(),
            key=lambda p: np.mean(platform_stats[p]["scores"]),
            reverse=True,
        )

        rates = [np.mean(platform_stats[p]["scores"]) * 100 for p in platforms]
        colors = [_get_platform_color(p) for p in platforms]
        n_tasks = [platform_stats[p]["n"] for p in platforms]

        fig, ax = plt.subplots(figsize=(max(8, len(platforms) * 1.2), 6))
        bars = ax.bar(
            range(len(platforms)), rates,
            color=colors, width=0.6,
            edgecolor="white", linewidth=1.5,
        )

        ax.set_xticks(range(len(platforms)))
        ax.set_xticklabels(
            [f"{p.title()}\n(n={n})" for p, n in zip(platforms, n_tasks)],
            fontsize=10,
        )
        ax.set_ylabel("Pass Rate (%)", fontsize=13)
        track_label = TRACK_LABELS.get(track, track)
        ax.set_title(
            f"{track_label}: Platform Comparison (Baseline)",
            fontsize=14, fontweight="bold",
        )
        ax.set_ylim(0, max(rates) * 1.2 if rates else 100)
        ax.grid(True, alpha=0.2, axis="y")

        for bar, rate in zip(bars, rates):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{rate:.1f}%",
                ha="center", fontsize=10, fontweight="bold",
            )

        return _save_chart(fig, output_path)

    def lucid_improvement_chart(
        self,
        results: list,
        output_path: str | Path,
    ) -> str:
        """Grouped bars: baseline vs LUCID-enhanced per platform.

        Shows all platforms side-by-side with baseline, LUCID k=1, LUCID k=3.
        """
        # Aggregate per platform across all tracks
        platform_cond = defaultdict(lambda: defaultdict(list))
        for r in results:
            platform_cond[r.platform][r.condition].append(1 if r.passed else 0)

        platforms = sorted(platform_cond.keys())
        if not platforms:
            return ""

        x = np.arange(len(platforms))
        width = 0.25

        baseline_rates = []
        k1_rates = []
        k3_rates = []

        for p in platforms:
            b = platform_cond[p].get("baseline", [])
            k1 = platform_cond[p].get("lucid_k1", [])
            k3 = platform_cond[p].get("lucid_k3", [])
            baseline_rates.append(np.mean(b) * 100 if b else 0)
            k1_rates.append(np.mean(k1) * 100 if k1 else 0)
            k3_rates.append(np.mean(k3) * 100 if k3 else 0)

        fig, ax = plt.subplots(figsize=(max(10, len(platforms) * 1.5), 6))

        ax.bar(x - width, baseline_rates, width, label="Baseline",
               color=CONDITION_COLORS["baseline"], edgecolor="white", linewidth=1.5)
        ax.bar(x, k1_rates, width, label="LUCID (k=1)",
               color=CONDITION_COLORS["lucid_k1"], edgecolor="white", linewidth=1.5)
        ax.bar(x + width, k3_rates, width, label="LUCID (k=3)",
               color=CONDITION_COLORS["lucid_k3"], edgecolor="white", linewidth=1.5)

        ax.set_xticks(x)
        ax.set_xticklabels([p.title() for p in platforms], fontsize=11)
        ax.set_ylabel("Pass Rate (%)", fontsize=13)
        ax.set_title(
            "LUCID Improvement by Platform\n(All Tracks Combined)",
            fontsize=14, fontweight="bold",
        )
        ax.legend(fontsize=11, loc="upper right")
        ax.grid(True, alpha=0.2, axis="y")

        all_rates = baseline_rates + k1_rates + k3_rates
        ax.set_ylim(0, max(all_rates) * 1.15 if all_rates else 100)

        # Add improvement annotation for each platform
        for i, p in enumerate(platforms):
            if baseline_rates[i] > 0:
                best = max(k1_rates[i], k3_rates[i])
                improvement = best - baseline_rates[i]
                if improvement > 0:
                    ax.annotate(
                        f"+{improvement:.1f}pp",
                        xy=(i + width, best),
                        xytext=(i + width + 0.1, best + 3),
                        fontsize=8, color="#16a34a", fontweight="bold",
                    )

        return _save_chart(fig, output_path)

    def convergence_chart(
        self,
        results: list,
        output_path: str | Path,
    ) -> str:
        """Line chart showing k=1 vs k=3 convergence per platform.

        Demonstrates whether iterative LUCID verification converges
        or diverges for each platform.
        """
        # Group by platform
        platform_data = defaultdict(lambda: defaultdict(list))
        for r in results:
            if r.condition in ("lucid_k1", "lucid_k3"):
                platform_data[r.platform][r.condition].append(1 if r.passed else 0)

        platforms = sorted(platform_data.keys())
        if not platforms:
            return ""

        fig, ax = plt.subplots(figsize=(8, 6))

        for p in platforms:
            k1_scores = platform_data[p].get("lucid_k1", [])
            k3_scores = platform_data[p].get("lucid_k3", [])

            k1_rate = np.mean(k1_scores) * 100 if k1_scores else 0
            k3_rate = np.mean(k3_scores) * 100 if k3_scores else 0

            color = _get_platform_color(p)
            ax.plot(
                [1, 3], [k1_rate, k3_rate],
                marker="o", color=color, linewidth=2, markersize=8,
                label=f"{p.title()}",
            )

        ax.set_xlabel("LUCID Iterations (k)", fontsize=13)
        ax.set_ylabel("Pass Rate (%)", fontsize=13)
        ax.set_title(
            "LUCID Convergence by Platform\n(k=1 to k=3)",
            fontsize=14, fontweight="bold",
        )
        ax.set_xticks([1, 3])
        ax.legend(fontsize=10, loc="best")
        ax.grid(True, alpha=0.3)

        return _save_chart(fig, output_path)

    def difficulty_breakdown_chart(
        self,
        results: list,
        output_path: str | Path,
    ) -> str:
        """Stacked bars showing pass rate by difficulty tier per platform."""
        # Group by platform and difficulty
        platform_diff = defaultdict(lambda: defaultdict(list))
        for r in results:
            if r.condition == "baseline" and r.difficulty:
                platform_diff[r.platform][r.difficulty].append(1 if r.passed else 0)

        platforms = sorted(platform_diff.keys())
        if not platforms:
            return ""

        difficulties = ["easy", "medium", "hard"]
        x = np.arange(len(platforms))
        width = 0.6

        fig, ax = plt.subplots(figsize=(max(8, len(platforms) * 1.2), 6))

        bottom = np.zeros(len(platforms))
        for diff in difficulties:
            rates = []
            for p in platforms:
                scores = platform_diff[p].get(diff, [])
                # Use count as the bar height (not rate)
                rates.append(sum(scores))
            rates_arr = np.array(rates, dtype=float)
            ax.bar(
                x, rates_arr, width,
                bottom=bottom,
                label=diff.title(),
                color=DIFFICULTY_COLORS.get(diff, "#6b7280"),
                edgecolor="white", linewidth=1,
            )
            bottom += rates_arr

        ax.set_xticks(x)
        ax.set_xticklabels([p.title() for p in platforms], fontsize=11)
        ax.set_ylabel("Tasks Passed", fontsize=13)
        ax.set_title(
            "Tasks Passed by Difficulty Tier",
            fontsize=14, fontweight="bold",
        )
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.2, axis="y")

        return _save_chart(fig, output_path)

    def radar_chart(
        self,
        platform: str,
        scores: dict[str, float],
        output_path: str | Path,
    ) -> str:
        """Per-platform strength/weakness radar chart.

        Args:
            platform: Platform name.
            scores: Dict mapping dimension name to 0-1 score.
                    e.g. {"HumanEval": 0.85, "SWE-bench": 0.25, ...}
            output_path: Where to save.
        """
        categories = list(scores.keys())
        values = list(scores.values())
        n = len(categories)

        if n < 3:
            return ""

        # Close the radar polygon
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
        values_closed = values + [values[0]]
        angles_closed = angles + [angles[0]]

        fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

        color = _get_platform_color(platform)
        ax.fill(angles_closed, values_closed, color=color, alpha=0.2)
        ax.plot(angles_closed, values_closed, color=color, linewidth=2, marker="o", markersize=6)

        ax.set_xticks(angles)
        ax.set_xticklabels(categories, fontsize=11)
        ax.set_ylim(0, 1.0)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"], fontsize=8, color="#6b7280")
        ax.set_title(
            f"{platform.title()} — Capability Profile",
            fontsize=14, fontweight="bold", pad=20,
        )

        # Add value labels at each point
        for angle, val, cat in zip(angles, values, categories):
            ax.annotate(
                f"{val*100:.0f}%",
                xy=(angle, val),
                xytext=(angle, val + 0.08),
                ha="center", fontsize=9, fontweight="bold", color=color,
            )

        return _save_chart(fig, output_path)

    def killer_comparison_chart(
        self,
        results: list,
        output_path: str | Path,
    ) -> str:
        """The hero chart: all platforms, all tracks, baseline vs LUCID.

        Grid layout: one sub-chart per track, platforms on x-axis,
        baseline vs LUCID k=1 vs LUCID k=3 grouped bars.
        """
        # Group by track
        track_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for r in results:
            track_data[r.track][r.platform][r.condition].append(1 if r.passed else 0)

        active_tracks = [t for t in ["humaneval", "swebench", "app_generation", "feature_addition"]
                         if t in track_data]
        n_tracks = len(active_tracks)
        if n_tracks == 0:
            return ""

        fig, axes = plt.subplots(
            1, n_tracks,
            figsize=(5 * n_tracks, 6),
            sharey=False,
        )
        if n_tracks == 1:
            axes = [axes]

        for ax, track in zip(axes, active_tracks):
            platforms = sorted(track_data[track].keys())
            x = np.arange(len(platforms))
            width = 0.25

            b_rates = []
            k1_rates = []
            k3_rates = []

            for p in platforms:
                b = track_data[track][p].get("baseline", [])
                k1 = track_data[track][p].get("lucid_k1", [])
                k3 = track_data[track][p].get("lucid_k3", [])
                b_rates.append(np.mean(b) * 100 if b else 0)
                k1_rates.append(np.mean(k1) * 100 if k1 else 0)
                k3_rates.append(np.mean(k3) * 100 if k3 else 0)

            ax.bar(x - width, b_rates, width, label="Baseline",
                   color=CONDITION_COLORS["baseline"], edgecolor="white", linewidth=1)
            ax.bar(x, k1_rates, width, label="LUCID k=1",
                   color=CONDITION_COLORS["lucid_k1"], edgecolor="white", linewidth=1)
            ax.bar(x + width, k3_rates, width, label="LUCID k=3",
                   color=CONDITION_COLORS["lucid_k3"], edgecolor="white", linewidth=1)

            ax.set_xticks(x)
            ax.set_xticklabels([p.title() for p in platforms], fontsize=9, rotation=30, ha="right")
            ax.set_ylabel("Pass Rate (%)", fontsize=11)
            track_label = TRACK_LABELS.get(track, track)
            ax.set_title(track_label, fontsize=12, fontweight="bold")
            ax.grid(True, alpha=0.2, axis="y")

            all_rates = b_rates + k1_rates + k3_rates
            ax.set_ylim(0, max(all_rates) * 1.15 if all_rates else 100)

        # Shared legend
        handles = [
            mpatches.Patch(color=CONDITION_COLORS["baseline"], label="Baseline"),
            mpatches.Patch(color=CONDITION_COLORS["lucid_k1"], label="LUCID k=1"),
            mpatches.Patch(color=CONDITION_COLORS["lucid_k3"], label="LUCID k=3"),
        ]
        fig.legend(
            handles=handles, loc="upper center",
            ncol=3, fontsize=11,
            bbox_to_anchor=(0.5, 1.02),
        )

        fig.suptitle(
            "State of AI Code Quality 2026\nAll Platforms, All Tracks",
            fontsize=15, fontweight="bold", y=1.08,
        )

        plt.tight_layout()
        return _save_chart(fig, output_path)
