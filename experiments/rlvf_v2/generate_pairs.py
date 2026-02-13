"""
DPO Pair Generation via MBPP Tasks
Generates candidate solutions using Claude Haiku, verifies with local test execution,
and produces DPO preference pairs (passing=chosen, failing=rejected).

Usage:
    python -m experiments.rlvf_v2.generate_pairs --output data/rlvf_v2/candidates.jsonl
    python -m experiments.rlvf_v2.generate_pairs --output data/rlvf_v2/candidates.jsonl --resume
    python -m experiments.rlvf_v2.generate_pairs --dry-run  # estimate cost only
"""

import argparse
import asyncio
import json
import os
import re
import time
from pathlib import Path

import anthropic

from experiments.rlvf_v2.mbpp_dataset import load_all_for_generation
from experiments.rlvf_v2.mbpp_verifier import verify_solution
from experiments.common.cost_tracker import CostTracker

HAIKU_MODEL = "claude-haiku-4-5-20251001"
CANDIDATES_PER_TASK = 20
MAX_CONCURRENT = 25  # API concurrency limit
COST_PER_MTOK_IN = 0.80   # Haiku input
COST_PER_MTOK_OUT = 4.00  # Haiku output

GENERATE_SYSTEM = """You are an expert Python programmer. Write clean, correct Python code.
Return ONLY the function implementation. No explanations, no markdown fences, no tests.
The function should be complete and self-contained.
IMPORTANT: Use the exact function name specified in the task."""

GENERATE_PROMPT = """Write a Python function named `{fn_name}` to solve the following task:

{task_text}

The function MUST be named `{fn_name}`. Return ONLY the Python code. No markdown, no explanations."""


def extract_function_name(task: dict) -> str:
    """Extract expected function name from MBPP test assertions."""
    for test in task.get("test_list", []):
        match = re.match(r"assert\s+(\w+)\s*\(", test)
        if match:
            return match.group(1)
    # Fallback: try to extract from reference code
    code = task.get("code", "")
    match = re.match(r"def\s+(\w+)\s*\(", code)
    if match:
        return match.group(1)
    return "solve"


def strip_code_fences(text: str) -> str:
    """Remove markdown code fences if present."""
    text = text.strip()
    if text.startswith("```python"):
        text = text[len("```python"):]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


class CandidateGenerator:
    def __init__(self, output_dir: Path, budget: float = 50.0):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.candidates_path = output_dir / "candidates.jsonl"
        self.cost_path = output_dir / "generation_costs.json"
        self.tracker = CostTracker(budget_limit=budget)
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            timeout=120,
        )
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        self.completed_tasks: set[int] = set()
        self.stats = {
            "total_tasks": 0,
            "tasks_with_passing": 0,
            "tasks_with_failing": 0,
            "tasks_with_both": 0,
            "total_candidates": 0,
            "total_passing": 0,
            "total_failing": 0,
            "total_errors": 0,
        }

    def load_completed(self):
        """Load already-completed task IDs for resume support."""
        if self.candidates_path.exists():
            with open(self.candidates_path) as f:
                for line in f:
                    rec = json.loads(line)
                    self.completed_tasks.add(rec["task_id"])
            print(f"  Resuming: {len(self.completed_tasks)} tasks already done")

    def _generate_sync(self, task_text: str, fn_name: str, temperature: float = 0.8) -> tuple[str, int, int]:
        """Synchronous API call to generate a candidate solution."""
        response = self.client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=1024,
            temperature=temperature,
            system=GENERATE_SYSTEM,
            messages=[{
                "role": "user",
                "content": GENERATE_PROMPT.format(task_text=task_text, fn_name=fn_name),
            }],
        )
        content = "".join(b.text for b in response.content if b.type == "text")
        return (
            strip_code_fences(content),
            response.usage.input_tokens,
            response.usage.output_tokens,
        )

    async def generate_candidate(self, task_text: str, fn_name: str, temperature: float = 0.8) -> tuple[str, int, int]:
        """Async wrapper for API call with semaphore."""
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self._generate_sync, task_text, fn_name, temperature
            )

    async def process_task(self, task: dict) -> dict | None:
        """Generate candidates for a single task, verify, and return results."""
        task_id = task["task_id"]
        task_text = task["text"]

        if task_id in self.completed_tasks:
            return None

        fn_name = extract_function_name(task)

        # Generate candidates with varying temperatures
        candidates = []
        total_in = 0
        total_out = 0

        tasks = []
        for i in range(CANDIDATES_PER_TASK):
            # Vary temperature slightly for diversity
            temp = 0.6 + (i / CANDIDATES_PER_TASK) * 0.6  # 0.6 to 1.2
            tasks.append(self.generate_candidate(task_text, fn_name, temperature=min(temp, 1.0)))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                candidates.append({
                    "index": i,
                    "code": "",
                    "passed": False,
                    "error": str(result),
                    "error_type": "api_error",
                })
                continue

            code, in_tok, out_tok = result
            total_in += in_tok
            total_out += out_tok

            # Verify against tests
            verification = verify_solution(code, task, timeout=30)

            candidates.append({
                "index": i,
                "code": code,
                "passed": verification["all_passed"],
                "error_type": verification.get("error_type"),
                "stderr": verification.get("stderr", "")[:200] if not verification["all_passed"] else "",
            })

        # Track cost
        self.tracker.record(
            model=HAIKU_MODEL,
            role="generate",
            input_tokens=total_in,
            output_tokens=total_out,
            task_id=str(task_id),
            condition="pair_generation",
            iteration=0,
            duration_ms=0,
        )

        # Compute stats
        passing = [c for c in candidates if c["passed"]]
        failing = [c for c in candidates if not c["passed"] and c["code"]]
        errors = [c for c in candidates if not c["code"]]

        self.stats["total_candidates"] += len(candidates)
        self.stats["total_passing"] += len(passing)
        self.stats["total_failing"] += len(failing)
        self.stats["total_errors"] += len(errors)
        if passing:
            self.stats["tasks_with_passing"] += 1
        if failing:
            self.stats["tasks_with_failing"] += 1
        if passing and failing:
            self.stats["tasks_with_both"] += 1

        record = {
            "task_id": task_id,
            "task_text": task_text,
            "num_passing": len(passing),
            "num_failing": len(failing),
            "num_errors": len(errors),
            "candidates": candidates,
            "input_tokens": total_in,
            "output_tokens": total_out,
        }

        # Append incrementally
        with open(self.candidates_path, "a") as f:
            f.write(json.dumps(record) + "\n")

        self.completed_tasks.add(task_id)
        return record

    async def run(self, tasks: list[dict], batch_size: int = 50):
        """Process all tasks in batches."""
        self.stats["total_tasks"] = len(tasks)
        remaining = [t for t in tasks if t["task_id"] not in self.completed_tasks]

        print(f"Processing {len(remaining)} tasks ({len(self.completed_tasks)} already done)")
        print(f"  {CANDIDATES_PER_TASK} candidates per task")
        print(f"  {MAX_CONCURRENT} concurrent API calls")
        print()

        start_time = time.time()

        for batch_start in range(0, len(remaining), batch_size):
            batch = remaining[batch_start:batch_start + batch_size]
            batch_num = batch_start // batch_size + 1
            total_batches = (len(remaining) + batch_size - 1) // batch_size

            print(f"Batch {batch_num}/{total_batches} ({len(batch)} tasks)...")

            await asyncio.gather(
                *[self.process_task(t) for t in batch],
                return_exceptions=True,
            )

            # Log progress
            done = len(self.completed_tasks)
            elapsed = time.time() - start_time
            rate = done / elapsed if elapsed > 0 else 0

            print(
                f"  Done: {done}/{self.stats['total_tasks']} | "
                f"Cost: ${self.tracker.total_cost:.2f} | "
                f"Rate: {rate:.1f} tasks/s | "
                f"With pairs: {self.stats['tasks_with_both']}"
            )

            # Save cost tracker periodically
            self.tracker.save(self.cost_path)

            # Budget check
            if self.tracker.total_cost > self.tracker.budget_limit * 0.9:
                print(f"WARNING: Approaching budget limit (${self.tracker.total_cost:.2f} / ${self.tracker.budget_limit:.2f})")
            if self.tracker.is_over_budget():
                print("BUDGET EXCEEDED — stopping")
                break

        # Final save
        self.tracker.save(self.cost_path)
        self._print_summary(time.time() - start_time)

    def _print_summary(self, elapsed: float):
        print()
        print("=" * 60)
        print("  CANDIDATE GENERATION COMPLETE")
        print("=" * 60)
        print(f"  Tasks processed: {len(self.completed_tasks)}/{self.stats['total_tasks']}")
        print(f"  Tasks with both pass+fail: {self.stats['tasks_with_both']}")
        print(f"  Total candidates: {self.stats['total_candidates']}")
        print(f"  Passing: {self.stats['total_passing']} ({100*self.stats['total_passing']/max(1,self.stats['total_candidates']):.1f}%)")
        print(f"  Failing: {self.stats['total_failing']} ({100*self.stats['total_failing']/max(1,self.stats['total_candidates']):.1f}%)")
        print(f"  API errors: {self.stats['total_errors']}")
        print(f"  Cost: ${self.tracker.total_cost:.2f}")
        print(f"  Time: {elapsed:.0f}s ({elapsed/60:.1f} min)")
        print(f"  Output: {self.candidates_path}")
        print("=" * 60)


def estimate_cost(num_tasks: int):
    """Dry-run cost estimation."""
    # Average prompt ~400 tokens, response ~200 tokens per candidate
    avg_input = 400
    avg_output = 200
    total_calls = num_tasks * CANDIDATES_PER_TASK
    total_in = total_calls * avg_input
    total_out = total_calls * avg_output
    cost_in = (total_in / 1_000_000) * COST_PER_MTOK_IN
    cost_out = (total_out / 1_000_000) * COST_PER_MTOK_OUT

    print(f"Cost Estimate (dry run):")
    print(f"  Tasks: {num_tasks}")
    print(f"  Candidates per task: {CANDIDATES_PER_TASK}")
    print(f"  Total API calls: {total_calls:,}")
    print(f"  Est. input tokens: {total_in:,}")
    print(f"  Est. output tokens: {total_out:,}")
    print(f"  Input cost: ${cost_in:.2f}")
    print(f"  Output cost: ${cost_out:.2f}")
    print(f"  Total estimated: ${cost_in + cost_out:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Generate DPO candidate pairs from MBPP")
    parser.add_argument("--output", type=str, default="data/rlvf_v2",
                        help="Output directory for candidates")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from previously completed tasks")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only estimate cost, don't generate")
    parser.add_argument("--budget", type=float, default=50.0,
                        help="Maximum budget in dollars")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit number of tasks (0 = all)")
    args = parser.parse_args()

    tasks = load_all_for_generation()
    if args.limit > 0:
        tasks = tasks[:args.limit]

    print(f"MBPP tasks loaded: {len(tasks)}")

    if args.dry_run:
        estimate_cost(len(tasks))
        return

    output_dir = Path(args.output)
    generator = CandidateGenerator(output_dir, budget=args.budget)

    if args.resume:
        generator.load_completed()

    asyncio.run(generator.run(tasks))


if __name__ == "__main__":
    main()
