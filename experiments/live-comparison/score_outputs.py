#!/usr/bin/env python3
"""Score all 30 outputs across 6 dimensions and generate report."""

import os
import sys
import json
import time
import subprocess

import anthropic

MODEL = "claude-sonnet-4-5-20250929"

TASKS = [
    ("task_01", "Auth middleware", "Write a middleware that validates JWT tokens, checks expiration, handles refresh tokens, and attaches user context to the request"),
    ("task_02", "Rate limiter", "Write a sliding window rate limiter that supports per-user and per-endpoint limits with Redis-compatible storage"),
    ("task_03", "Webhook handler", "Write a webhook receiver that validates HMAC signatures, handles retries/deduplication, and processes events asynchronously"),
    ("task_04", "Database migration", "Write a migration system that supports up/down migrations, tracks applied migrations, and handles failures with rollback"),
    ("task_05", "File upload processor", "Write a file upload handler that validates file types, enforces size limits, scans for malware signatures, and stores to S3-compatible storage"),
    ("task_06", "API pagination", "Write cursor-based pagination for a REST API that handles sorting, filtering, and returns consistent results under concurrent writes"),
    ("task_07", "Config validator", "Write a configuration loader that validates YAML/JSON config against a schema, supports environment variable interpolation, and provides helpful error messages"),
    ("task_08", "Retry with circuit breaker", "Write an HTTP client wrapper with exponential backoff retry, circuit breaker pattern, timeout handling, and request/response logging"),
    ("task_09", "Event sourcing", "Write an event store that appends events, rebuilds aggregate state, supports snapshots, and handles concurrent writes with optimistic locking"),
    ("task_10", "Input sanitizer", "Write an input sanitization library that prevents XSS, SQL injection, and path traversal while preserving legitimate content"),
]

DIMENSIONS = ["Correctness", "Edge Cases", "Error Handling", "Security", "Type Safety", "Documentation"]

SCORE_SYSTEM = """You are a senior software engineering evaluator. You will be given a task description and Python code.

Score the code on these 6 dimensions, each on a 1-5 scale:

1. **Correctness** (1-5): Does it handle the happy path correctly? Is the core logic sound?
   - 1: Fundamentally broken  2: Major logic errors  3: Works for basic cases  4: Mostly correct  5: Completely correct

2. **Edge Cases** (1-5): Does it handle empty inputs, nulls, boundary conditions, unexpected types?
   - 1: No edge case handling  2: Minimal  3: Common cases  4: Thorough  5: Comprehensive

3. **Error Handling** (1-5): Are exceptions caught, logged, and handled gracefully? Does it fail safely?
   - 1: No error handling  2: Basic try/except  3: Reasonable handling  4: Good with custom errors  5: Production-grade

4. **Security** (1-5): Are there injection vulnerabilities, improper validation, data leaks, timing attacks?
   - 1: Critical vulnerabilities  2: Major issues  3: Basic security  4: Good security  5: Security-hardened

5. **Type Safety** (1-5): Are types annotated? Are invariants enforced? Are inputs validated?
   - 1: No type hints  2: Minimal  3: Partial coverage  4: Good coverage  5: Full coverage with runtime validation

6. **Documentation** (1-5): Are docstrings clear? Are complex sections commented? Is the API documented?
   - 1: No docs  2: Minimal  3: Basic docstrings  4: Good docs  5: Comprehensive documentation

Return a JSON object:
{
  "scores": {
    "correctness": N,
    "edge_cases": N,
    "error_handling": N,
    "security": N,
    "type_safety": N,
    "documentation": N
  },
  "total": N,
  "highlights": ["One sentence about what this code does particularly well or poorly"],
  "critical_issues": ["Any show-stopping problems, or empty array if none"]
}

Be calibrated: a 3 means "acceptable production code". Reserve 5 for genuinely excellent implementations.
Score honestly — don't inflate or deflate. Compare against what a senior engineer would write."""


def get_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", "claude-code", "-a", "anthropic-api-key", "-w"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    raise RuntimeError("ANTHROPIC_API_KEY not found")


def score_file(client, task_desc, code):
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SCORE_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Task: {task_desc}\n\nCode:\n```python\n{code}\n```"
        }],
    )
    text = response.content[0].text
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text), response.usage
    except (json.JSONDecodeError, IndexError):
        return {"scores": {}, "total": 0, "highlights": [], "critical_issues": [], "raw": text}, response.usage


def main():
    base_dir = os.path.dirname(__file__)
    conditions = {
        "baseline": os.path.join(base_dir, "baseline"),
        "forward": os.path.join(base_dir, "forward"),
        "reverse": os.path.join(base_dir, "reverse"),
    }

    api_key = get_api_key()
    client = anthropic.Anthropic(api_key=api_key)

    all_scores = {}
    total_tokens = {"input": 0, "output": 0}

    print("\n=== SCORING ALL OUTPUTS ===\n")

    for condition_name, condition_dir in conditions.items():
        all_scores[condition_name] = {}
        for task_id, short_name, task_desc in TASKS:
            filepath = os.path.join(condition_dir, f"{task_id}.py")
            if not os.path.exists(filepath):
                print(f"  MISSING: {condition_name}/{task_id}")
                all_scores[condition_name][task_id] = None
                continue

            with open(filepath) as f:
                code = f.read()

            print(f"  Scoring {condition_name}/{task_id} ({short_name})...", end=" ", flush=True)
            result, usage = score_file(client, task_desc, code)
            total_tokens["input"] += usage.input_tokens
            total_tokens["output"] += usage.output_tokens

            scores = result.get("scores", {})
            total = sum(scores.values()) if scores else 0
            all_scores[condition_name][task_id] = result
            print(f"Total: {total}/30")

    # Save raw scores
    scores_path = os.path.join(base_dir, "scores.json")
    with open(scores_path, "w") as f:
        json.dump(all_scores, f, indent=2)
    print(f"\nScores saved to {scores_path}")

    # Generate report
    generate_report(base_dir, all_scores, total_tokens)


def generate_report(base_dir, all_scores, total_tokens):
    """Generate the final comparison report."""
    report_lines = []
    report_lines.append("# LUCID Live Comparison Experiment — Results\n")
    report_lines.append(f"*Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n")
    report_lines.append("---\n")

    # Summary table
    report_lines.append("## Summary Table\n")
    report_lines.append("| Task | Condition | Correct | Edge | Error | Security | Types | Docs | **Total** |")
    report_lines.append("|------|-----------|---------|------|-------|----------|-------|------|-----------|")

    condition_totals = {"baseline": [], "forward": [], "reverse": []}
    dimension_totals = {c: {d: [] for d in ["correctness", "edge_cases", "error_handling", "security", "type_safety", "documentation"]}
                       for c in ["baseline", "forward", "reverse"]}

    for task_id, short_name, _ in TASKS:
        for condition in ["baseline", "forward", "reverse"]:
            result = all_scores.get(condition, {}).get(task_id)
            if result and result.get("scores"):
                s = result["scores"]
                total = sum(s.values())
                condition_totals[condition].append(total)
                for dim in dimension_totals[condition]:
                    dimension_totals[condition][dim].append(s.get(dim, 0))
                report_lines.append(
                    f"| {short_name} | {condition.title()} | "
                    f"{s.get('correctness', '-')} | {s.get('edge_cases', '-')} | "
                    f"{s.get('error_handling', '-')} | {s.get('security', '-')} | "
                    f"{s.get('type_safety', '-')} | {s.get('documentation', '-')} | "
                    f"**{total}** |"
                )
            else:
                report_lines.append(f"| {short_name} | {condition.title()} | - | - | - | - | - | - | **-** |")

    # Averages
    report_lines.append("\n## Average Scores by Condition\n")
    report_lines.append("| Condition | Avg Total (/30) | Correct | Edge | Error | Security | Types | Docs |")
    report_lines.append("|-----------|-----------------|---------|------|-------|----------|-------|------|")

    for condition in ["baseline", "forward", "reverse"]:
        totals = condition_totals[condition]
        avg_total = sum(totals) / len(totals) if totals else 0
        dims = {}
        for dim in dimension_totals[condition]:
            vals = dimension_totals[condition][dim]
            dims[dim] = sum(vals) / len(vals) if vals else 0
        report_lines.append(
            f"| {condition.title()} | **{avg_total:.1f}** | "
            f"{dims['correctness']:.1f} | {dims['edge_cases']:.1f} | "
            f"{dims['error_handling']:.1f} | {dims['security']:.1f} | "
            f"{dims['type_safety']:.1f} | {dims['documentation']:.1f} |"
        )

    # Head-to-head
    report_lines.append("\n## Head-to-Head Comparison\n")
    wins = {"baseline": 0, "forward": 0, "reverse": 0}
    for task_id, short_name, _ in TASKS:
        task_scores = {}
        for condition in ["baseline", "forward", "reverse"]:
            result = all_scores.get(condition, {}).get(task_id)
            if result and result.get("scores"):
                task_scores[condition] = sum(result["scores"].values())
        if task_scores:
            winner = max(task_scores, key=task_scores.get)
            wins[winner] += 1

    report_lines.append("| Condition | Tasks Won |")
    report_lines.append("|-----------|-----------|")
    for condition in ["baseline", "forward", "reverse"]:
        report_lines.append(f"| {condition.title()} | {wins[condition]} |")

    # Qualitative highlights
    report_lines.append("\n## Qualitative Highlights\n")

    # Find tasks with biggest deltas
    deltas = []
    for task_id, short_name, _ in TASKS:
        scores = {}
        for condition in ["baseline", "forward", "reverse"]:
            result = all_scores.get(condition, {}).get(task_id)
            if result and result.get("scores"):
                scores[condition] = sum(result["scores"].values())
        if "baseline" in scores and "reverse" in scores:
            delta = scores["reverse"] - scores["baseline"]
            deltas.append((task_id, short_name, delta, scores))

    deltas.sort(key=lambda x: abs(x[2]), reverse=True)

    for task_id, short_name, delta, scores in deltas[:4]:
        report_lines.append(f"### {short_name} (Delta: {delta:+d})")
        report_lines.append(f"- Baseline: {scores.get('baseline', '-')}/30")
        report_lines.append(f"- Forward: {scores.get('forward', '-')}/30")
        report_lines.append(f"- Reverse: {scores.get('reverse', '-')}/30")

        for condition in ["baseline", "reverse"]:
            result = all_scores.get(condition, {}).get(task_id)
            if result:
                highlights = result.get("highlights", [])
                if highlights:
                    report_lines.append(f"- {condition.title()} highlights: {'; '.join(highlights)}")
                issues = result.get("critical_issues", [])
                if issues:
                    report_lines.append(f"- {condition.title()} issues: {'; '.join(issues)}")
        report_lines.append("")

    # Dimension breakdown
    report_lines.append("## Where LUCID Adds Most Value\n")
    report_lines.append("| Dimension | Baseline Avg | Forward Avg | Reverse Avg | Reverse Delta |")
    report_lines.append("|-----------|-------------|-------------|-------------|---------------|")

    for dim_key, dim_name in [("correctness", "Correctness"), ("edge_cases", "Edge Cases"),
                               ("error_handling", "Error Handling"), ("security", "Security"),
                               ("type_safety", "Type Safety"), ("documentation", "Documentation")]:
        b_vals = dimension_totals["baseline"][dim_key]
        f_vals = dimension_totals["forward"][dim_key]
        r_vals = dimension_totals["reverse"][dim_key]
        b_avg = sum(b_vals) / len(b_vals) if b_vals else 0
        f_avg = sum(f_vals) / len(f_vals) if f_vals else 0
        r_avg = sum(r_vals) / len(r_vals) if r_vals else 0
        delta = r_avg - b_avg
        report_lines.append(f"| {dim_name} | {b_avg:.2f} | {f_avg:.2f} | {r_avg:.2f} | {delta:+.2f} |")

    # Conclusion
    report_lines.append("\n## Conclusion\n")

    b_avg = sum(condition_totals["baseline"]) / len(condition_totals["baseline"]) if condition_totals["baseline"] else 0
    f_avg = sum(condition_totals["forward"]) / len(condition_totals["forward"]) if condition_totals["forward"] else 0
    r_avg = sum(condition_totals["reverse"]) / len(condition_totals["reverse"]) if condition_totals["reverse"] else 0

    report_lines.append(f"- **Baseline** (Raw Claude): Average {b_avg:.1f}/30")
    report_lines.append(f"- **Forward LUCID** (Post-hoc verification): Average {f_avg:.1f}/30 ({f_avg - b_avg:+.1f} vs baseline)")
    report_lines.append(f"- **Reverse LUCID** (Spec-first generation): Average {r_avg:.1f}/30 ({r_avg - b_avg:+.1f} vs baseline)")
    report_lines.append(f"\nReverse LUCID won {wins['reverse']}/10 tasks. "
                       f"Forward LUCID won {wins['forward']}/10. "
                       f"Baseline won {wins['baseline']}/10.")

    report_lines.append(f"\n## Token Usage\n")
    report_lines.append(f"- Scoring tokens: {total_tokens['input']:,} in / {total_tokens['output']:,} out")

    report_path = os.path.join(base_dir, "report.md")
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    print(f"\nReport saved to {report_path}")


if __name__ == "__main__":
    main()
