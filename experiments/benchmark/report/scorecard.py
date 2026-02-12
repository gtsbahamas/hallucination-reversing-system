#!/usr/bin/env python3
"""
Platform scorecard generator.

Produces a single-page HTML scorecard for each platform, suitable for
attaching to outreach emails. Includes overall score, rank, track scores,
strengths, weaknesses, and LUCID improvement.

Usage:
    from experiments.benchmark.report.scorecard import ScorecardGenerator
    gen = ScorecardGenerator()
    gen.generate_scorecard("cursor", results, rankings, "output/scorecard_cursor.html")
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Optional

import numpy as np

from .charts import _get_platform_color


TRACK_LABELS = {
    "humaneval": "HumanEval (Function-Level)",
    "swebench": "SWE-bench Lite (Bug Fixing)",
    "app_generation": "App Generation",
    "feature_addition": "Feature Addition",
}


class ScorecardGenerator:
    """Generates HTML platform scorecards."""

    def generate_scorecard(
        self,
        platform: str,
        results: list,
        rankings: list[dict],
        output_path: str | Path,
        report_date: str = "February 2026",
    ) -> str:
        """Generate an HTML scorecard for a single platform.

        Args:
            platform: Platform name.
            results: All TaskResult objects (will be filtered to this platform).
            rankings: Rankings list from Analyzer.compute_rankings().
            output_path: Where to save the HTML file.
            report_date: Date string for the report header.

        Returns:
            Path to generated HTML file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Filter results for this platform
        platform_results = [r for r in results if r.platform == platform]

        # Get rank info
        rank_info = next((r for r in rankings if r["platform"] == platform), None)
        rank = rank_info["rank"] if rank_info else "N/A"
        total_platforms = len(rankings)

        # Compute per-track stats
        track_stats = self._compute_track_stats(platform_results)

        # Compute overall score (weighted average across tracks)
        overall_score = self._compute_overall_score(track_stats)

        # Determine strengths and weaknesses
        strengths, weaknesses = self._determine_strengths_weaknesses(track_stats)

        # Compute LUCID improvement
        lucid_improvement = self._compute_lucid_improvement(platform_results)

        # Generate HTML
        color = _get_platform_color(platform)
        html = self._render_scorecard(
            platform=platform,
            rank=rank,
            total_platforms=total_platforms,
            overall_score=overall_score,
            track_stats=track_stats,
            strengths=strengths,
            weaknesses=weaknesses,
            lucid_improvement=lucid_improvement,
            color=color,
            report_date=report_date,
        )

        output_path.write_text(html)
        return str(output_path)

    def _compute_track_stats(self, results: list) -> dict[str, dict]:
        """Compute per-track baseline and LUCID stats."""
        track_data = defaultdict(lambda: defaultdict(list))
        for r in results:
            track_data[r.track][r.condition].append(1 if r.passed else 0)

        stats = {}
        for track, cond_scores in track_data.items():
            b_scores = cond_scores.get("baseline", [])
            k1_scores = cond_scores.get("lucid_k1", [])
            k3_scores = cond_scores.get("lucid_k3", [])

            b_rate = np.mean(b_scores) * 100 if b_scores else 0
            k1_rate = np.mean(k1_scores) * 100 if k1_scores else 0
            k3_rate = np.mean(k3_scores) * 100 if k3_scores else 0
            best_lucid = max(k1_rate, k3_rate)

            stats[track] = {
                "baseline_rate": b_rate,
                "lucid_k1_rate": k1_rate,
                "lucid_k3_rate": k3_rate,
                "best_lucid_rate": best_lucid,
                "improvement_pp": best_lucid - b_rate,
                "n_tasks": len(b_scores),
                "label": TRACK_LABELS.get(track, track),
            }

        return stats

    def _compute_overall_score(self, track_stats: dict) -> float:
        """Compute weighted overall score (0-100)."""
        if not track_stats:
            return 0.0
        rates = [s["baseline_rate"] for s in track_stats.values()]
        return float(np.mean(rates))

    def _determine_strengths_weaknesses(
        self, track_stats: dict
    ) -> tuple[list[str], list[str]]:
        """Identify strengths (>70%) and weaknesses (<40%)."""
        strengths = []
        weaknesses = []

        for track, stats in sorted(
            track_stats.items(),
            key=lambda x: x[1]["baseline_rate"],
            reverse=True,
        ):
            label = stats["label"]
            rate = stats["baseline_rate"]
            if rate >= 70:
                strengths.append(f"{label}: {rate:.1f}% baseline pass rate")
            elif rate < 40:
                weaknesses.append(f"{label}: {rate:.1f}% baseline pass rate")

        # If no clear strengths/weaknesses from thresholds, use best/worst
        if not strengths and track_stats:
            best = max(track_stats.items(), key=lambda x: x[1]["baseline_rate"])
            strengths.append(f"Best on {best[1]['label']}: {best[1]['baseline_rate']:.1f}%")

        if not weaknesses and track_stats:
            worst = min(track_stats.items(), key=lambda x: x[1]["baseline_rate"])
            if worst[1]["baseline_rate"] < 90:
                weaknesses.append(
                    f"Room to improve on {worst[1]['label']}: {worst[1]['baseline_rate']:.1f}%"
                )

        # Add LUCID improvement as strength if significant
        for track, stats in track_stats.items():
            if stats["improvement_pp"] >= 10:
                strengths.append(
                    f"LUCID improves {stats['label']} by +{stats['improvement_pp']:.1f}pp"
                )

        return strengths[:3], weaknesses[:3]

    def _compute_lucid_improvement(self, results: list) -> dict:
        """Overall LUCID improvement stats."""
        baseline_scores = [1 if r.passed else 0 for r in results if r.condition == "baseline"]
        k1_scores = [1 if r.passed else 0 for r in results if r.condition == "lucid_k1"]
        k3_scores = [1 if r.passed else 0 for r in results if r.condition == "lucid_k3"]

        b_rate = np.mean(baseline_scores) * 100 if baseline_scores else 0
        k1_rate = np.mean(k1_scores) * 100 if k1_scores else 0
        k3_rate = np.mean(k3_scores) * 100 if k3_scores else 0
        best = max(k1_rate, k3_rate)

        return {
            "baseline": b_rate,
            "lucid_k1": k1_rate,
            "lucid_k3": k3_rate,
            "best_lucid": best,
            "absolute_pp": best - b_rate,
            "relative_pct": ((best - b_rate) / b_rate * 100) if b_rate > 0 else 0,
        }

    def _render_scorecard(
        self,
        platform: str,
        rank: int | str,
        total_platforms: int,
        overall_score: float,
        track_stats: dict,
        strengths: list[str],
        weaknesses: list[str],
        lucid_improvement: dict,
        color: str,
        report_date: str,
    ) -> str:
        """Render the scorecard HTML."""
        # Build track rows
        track_rows = ""
        for track, stats in sorted(
            track_stats.items(),
            key=lambda x: x[1]["baseline_rate"],
            reverse=True,
        ):
            improvement_badge = ""
            if stats["improvement_pp"] > 0:
                improvement_badge = (
                    f'<span class="improvement">+{stats["improvement_pp"]:.1f}pp with LUCID</span>'
                )

            bar_width = min(stats["baseline_rate"], 100)
            lucid_bar_width = min(stats["best_lucid_rate"], 100)

            track_rows += f"""
            <div class="track-row">
                <div class="track-label">{stats['label']}</div>
                <div class="track-bars">
                    <div class="bar-container">
                        <div class="bar baseline-bar" style="width: {bar_width}%"></div>
                        <span class="bar-label">{stats['baseline_rate']:.1f}%</span>
                    </div>
                    <div class="bar-container">
                        <div class="bar lucid-bar" style="width: {lucid_bar_width}%"></div>
                        <span class="bar-label">{stats['best_lucid_rate']:.1f}% {improvement_badge}</span>
                    </div>
                </div>
                <div class="track-n">n={stats['n_tasks']}</div>
            </div>"""

        strengths_html = "".join(f"<li>{s}</li>" for s in strengths) if strengths else "<li>-</li>"
        weaknesses_html = "".join(f"<li>{w}</li>" for w in weaknesses) if weaknesses else "<li>-</li>"

        score_color = "#22c55e" if overall_score >= 70 else ("#f59e0b" if overall_score >= 40 else "#ef4444")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{platform.title()} - AI Code Quality Scorecard</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: #f8fafc;
        color: #1e293b;
        padding: 24px;
    }}
    .scorecard {{
        max-width: 800px;
        margin: 0 auto;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        overflow: hidden;
    }}
    .header {{
        background: {color};
        color: white;
        padding: 28px 32px;
    }}
    .header h1 {{
        font-size: 24px;
        margin-bottom: 4px;
    }}
    .header .subtitle {{
        font-size: 14px;
        opacity: 0.85;
    }}
    .score-section {{
        display: flex;
        gap: 32px;
        padding: 24px 32px;
        border-bottom: 1px solid #e2e8f0;
    }}
    .score-box {{
        text-align: center;
        flex: 1;
    }}
    .score-box .value {{
        font-size: 42px;
        font-weight: 800;
        line-height: 1;
    }}
    .score-box .label {{
        font-size: 12px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 6px;
    }}
    .tracks-section {{
        padding: 24px 32px;
        border-bottom: 1px solid #e2e8f0;
    }}
    .tracks-section h2 {{
        font-size: 16px;
        margin-bottom: 16px;
        color: #334155;
    }}
    .track-row {{
        display: flex;
        align-items: center;
        margin-bottom: 16px;
        gap: 12px;
    }}
    .track-label {{
        width: 200px;
        font-size: 13px;
        font-weight: 500;
        flex-shrink: 0;
    }}
    .track-bars {{
        flex: 1;
    }}
    .bar-container {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
    }}
    .bar {{
        height: 18px;
        border-radius: 4px;
        min-width: 4px;
        transition: width 0.3s ease;
    }}
    .baseline-bar {{ background: #cbd5e1; }}
    .lucid-bar {{ background: #22c55e; }}
    .bar-label {{
        font-size: 12px;
        color: #475569;
        white-space: nowrap;
    }}
    .improvement {{
        color: #16a34a;
        font-weight: 600;
        font-size: 11px;
    }}
    .track-n {{
        font-size: 11px;
        color: #94a3b8;
        width: 50px;
        text-align: right;
        flex-shrink: 0;
    }}
    .insights-section {{
        display: flex;
        gap: 24px;
        padding: 24px 32px;
        border-bottom: 1px solid #e2e8f0;
    }}
    .insight-box {{
        flex: 1;
    }}
    .insight-box h3 {{
        font-size: 14px;
        margin-bottom: 8px;
        color: #334155;
    }}
    .insight-box ul {{
        list-style: none;
        padding: 0;
    }}
    .insight-box li {{
        font-size: 13px;
        padding: 4px 0;
        padding-left: 16px;
        position: relative;
        color: #475569;
    }}
    .insight-box.strengths li::before {{
        content: '+';
        position: absolute;
        left: 0;
        color: #22c55e;
        font-weight: bold;
    }}
    .insight-box.weaknesses li::before {{
        content: '-';
        position: absolute;
        left: 0;
        color: #f59e0b;
        font-weight: bold;
    }}
    .lucid-section {{
        padding: 24px 32px;
        background: #f0fdf4;
        border-bottom: 1px solid #bbf7d0;
    }}
    .lucid-section h3 {{
        font-size: 14px;
        color: #166534;
        margin-bottom: 8px;
    }}
    .lucid-stat {{
        display: inline-block;
        background: #dcfce7;
        padding: 6px 14px;
        border-radius: 6px;
        margin-right: 8px;
        margin-bottom: 6px;
        font-size: 13px;
        font-weight: 500;
        color: #166534;
    }}
    .footer {{
        padding: 16px 32px;
        text-align: center;
        font-size: 12px;
        color: #94a3b8;
    }}
    .footer a {{
        color: {color};
        text-decoration: none;
    }}
    @media print {{
        body {{ padding: 0; background: white; }}
        .scorecard {{ box-shadow: none; }}
    }}
</style>
</head>
<body>
<div class="scorecard">
    <div class="header">
        <h1>{platform.title()} &mdash; AI Code Quality Report</h1>
        <div class="subtitle">State of AI Code Quality &middot; {report_date}</div>
    </div>

    <div class="score-section">
        <div class="score-box">
            <div class="value" style="color: {score_color}">{overall_score:.0f}</div>
            <div class="label">Overall Score (of 100)</div>
        </div>
        <div class="score-box">
            <div class="value" style="color: #334155">#{rank}</div>
            <div class="label">Rank (of {total_platforms})</div>
        </div>
        <div class="score-box">
            <div class="value" style="color: #22c55e">+{lucid_improvement['absolute_pp']:.1f}<span style="font-size:20px">pp</span></div>
            <div class="label">LUCID Improvement</div>
        </div>
    </div>

    <div class="tracks-section">
        <h2>Track Scores (Baseline vs LUCID-Enhanced)</h2>
        {track_rows}
    </div>

    <div class="insights-section">
        <div class="insight-box strengths">
            <h3>Strengths</h3>
            <ul>{strengths_html}</ul>
        </div>
        <div class="insight-box weaknesses">
            <h3>Areas for Improvement</h3>
            <ul>{weaknesses_html}</ul>
        </div>
    </div>

    <div class="lucid-section">
        <h3>LUCID Verification Impact</h3>
        <span class="lucid-stat">Baseline: {lucid_improvement['baseline']:.1f}%</span>
        <span class="lucid-stat">LUCID k=1: {lucid_improvement['lucid_k1']:.1f}%</span>
        <span class="lucid-stat">LUCID k=3: {lucid_improvement['lucid_k3']:.1f}%</span>
        <span class="lucid-stat">Relative: +{lucid_improvement['relative_pct']:.1f}%</span>
    </div>

    <div class="footer">
        <a href="https://lucid.dev/benchmark/2026">lucid.dev/benchmark/2026</a> &middot;
        Generated by LUCID Benchmark Suite
    </div>
</div>
</body>
</html>"""

        return html
