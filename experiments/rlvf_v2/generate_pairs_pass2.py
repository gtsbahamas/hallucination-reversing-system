"""
DPO Pair Generation — Second Pass
Targets tasks from pass 1 that had all-pass or all-fail candidates.
For all-pass tasks: generates more candidates at higher temperature to get failures.
For all-fail tasks: generates candidates at lower temperature (greedy) to get passes.

Usage:
    python -m experiments.rlvf_v2.generate_pairs_pass2 \
        --candidates data/rlvf_v2/candidates.jsonl \
        --output data/rlvf_v2/candidates_pass2.jsonl
"""

import argparse
import asyncio
import json
import os
import time
from pathlib import Path

import anthropic

from experiments.rlvf_v2.mbpp_dataset import load_all_for_generation
from experiments.rlvf_v2.mbpp_verifier import verify_solution
from experiments.rlvf_v2.generate_pairs import (
    strip_code_fences, extract_function_name,
    HAIKU_MODEL, GENERATE_SYSTEM, GENERATE_PROMPT,
)
from experiments.common.cost_tracker import CostTracker

MAX_CONCURRENT = 25
EXTRA_CANDIDATES = 30  # Per task in second pass


class SecondPassGenerator:
    def __init__(self, output_path: Path, budget: float = 30.0):
        self.output_path = output_path
        self.tracker = CostTracker(budget_limit=budget)
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            timeout=120,
        )
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    def _generate_sync(self, task_text: str, fn_name: str, temperature: float) -> tuple[str, int, int]:
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

    async def generate_candidate(self, task_text: str, fn_name: str, temperature: float) -> tuple[str, int, int]:
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self._generate_sync, task_text, fn_name, temperature
            )

    async def process_task(self, task: dict, strategy: str) -> dict | None:
        task_id = task["task_id"]
        task_text = task["text"]
        fn_name = extract_function_name(task)

        # Set temperature based on strategy
        if strategy == "need_failures":
            # High temp to introduce errors
            temps = [0.9 + (i / EXTRA_CANDIDATES) * 0.6 for i in range(EXTRA_CANDIDATES)]
            temps = [min(t, 1.5) for t in temps]
        elif strategy == "need_passes":
            # Low temp for best chance of correct code
            temps = [0.0] * 5 + [0.1] * 5 + [0.2] * 5 + [0.3] * 5 + [0.4] * 5 + [0.5] * 5
        else:
            return None

        api_tasks = [
            self.generate_candidate(task_text, fn_name, t)
            for t in temps[:EXTRA_CANDIDATES]
        ]

        results = await asyncio.gather(*api_tasks, return_exceptions=True)

        candidates = []
        total_in = 0
        total_out = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                candidates.append({
                    "index": i, "code": "", "passed": False,
                    "error": str(result), "error_type": "api_error",
                })
                continue

            code, in_tok, out_tok = result
            total_in += in_tok
            total_out += out_tok

            verification = verify_solution(code, task, timeout=30)
            candidates.append({
                "index": i,
                "code": code,
                "passed": verification["all_passed"],
                "error_type": verification.get("error_type"),
            })

        self.tracker.record(
            model=HAIKU_MODEL, role="generate_pass2",
            input_tokens=total_in, output_tokens=total_out,
            task_id=str(task_id), condition="pair_generation_pass2",
            iteration=0, duration_ms=0,
        )

        passing = [c for c in candidates if c["passed"] and c["code"]]
        failing = [c for c in candidates if not c["passed"] and c["code"]]

        record = {
            "task_id": task_id,
            "task_text": task_text,
            "strategy": strategy,
            "num_passing": len(passing),
            "num_failing": len(failing),
            "candidates": candidates,
        }

        with open(self.output_path, "a") as f:
            f.write(json.dumps(record) + "\n")

        return record

    async def run(self, tasks_needing_failures: list[dict], tasks_needing_passes: list[dict]):
        print(f"Second pass:")
        print(f"  Need failures: {len(tasks_needing_failures)} tasks")
        print(f"  Need passes:   {len(tasks_needing_passes)} tasks")
        print(f"  Extra candidates per task: {EXTRA_CANDIDATES}")
        print()

        all_tasks = [
            (t, "need_failures") for t in tasks_needing_failures
        ] + [
            (t, "need_passes") for t in tasks_needing_passes
        ]

        start_time = time.time()
        new_with_both = 0
        batch_size = 30

        for batch_start in range(0, len(all_tasks), batch_size):
            batch = all_tasks[batch_start:batch_start + batch_size]

            results = await asyncio.gather(
                *[self.process_task(t, s) for t, s in batch],
                return_exceptions=True,
            )

            for r in results:
                if isinstance(r, dict) and r.get("num_passing", 0) > 0 and r.get("num_failing", 0) > 0:
                    new_with_both += 1

            elapsed = time.time() - start_time
            done = min(batch_start + batch_size, len(all_tasks))
            print(
                f"  [{done}/{len(all_tasks)}] "
                f"New tasks with both: {new_with_both} | "
                f"Cost: ${self.tracker.total_cost:.2f} | "
                f"Time: {elapsed:.0f}s"
            )

            if self.tracker.is_over_budget():
                print("  Budget exceeded — stopping")
                break

        print(f"\n  Second pass complete. New tasks with both pass+fail: {new_with_both}")
        print(f"  Cost: ${self.tracker.total_cost:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Second pass DPO pair generation")
    parser.add_argument("--candidates", type=str, required=True,
                        help="Path to pass 1 candidates.jsonl")
    parser.add_argument("--output", type=str, required=True,
                        help="Output path for pass 2 candidates")
    parser.add_argument("--budget", type=float, default=30.0)
    args = parser.parse_args()

    # Load pass 1 results
    pass1 = []
    with open(args.candidates) as f:
        for line in f:
            pass1.append(json.loads(line))

    # Identify tasks needing second pass
    all_pass_ids = set()
    all_fail_ids = set()
    for r in pass1:
        if r["num_passing"] > 0 and r["num_failing"] == 0:
            all_pass_ids.add(r["task_id"])
        elif r["num_passing"] == 0 and r["num_failing"] > 0:
            all_fail_ids.add(r["task_id"])

    # Load task data
    all_tasks = {t["task_id"]: t for t in load_all_for_generation()}

    tasks_needing_failures = [all_tasks[tid] for tid in all_pass_ids if tid in all_tasks]
    tasks_needing_passes = [all_tasks[tid] for tid in all_fail_ids if tid in all_tasks]

    print(f"Pass 1 stats:")
    print(f"  Total tasks: {len(pass1)}")
    print(f"  All-pass (need failures): {len(all_pass_ids)}")
    print(f"  All-fail (need passes): {len(all_fail_ids)}")
    print(f"  Already have both: {len(pass1) - len(all_pass_ids) - len(all_fail_ids)}")
    print()

    if not tasks_needing_failures and not tasks_needing_passes:
        print("No tasks need second pass!")
        return

    # Remove existing output if exists
    output_path = Path(args.output)
    if output_path.exists():
        output_path.unlink()

    generator = SecondPassGenerator(output_path, budget=args.budget)
    asyncio.run(generator.run(tasks_needing_failures, tasks_needing_passes))


if __name__ == "__main__":
    main()
