"""
DPO Pair Selector
Reads candidate solutions, forms diverse DPO pairs (chosen=pass, rejected=fail),
and produces training datasets at multiple scales (1K, 5K, 10K).

Usage:
    python -m experiments.rlvf_v2.pair_selector \
        --candidates data/rlvf_v2/candidates.jsonl \
        --output-dir data/rlvf_v2/
"""

import argparse
import json
import random
from pathlib import Path


MAX_PAIRS_PER_TASK = 12


def edit_distance(a: str, b: str) -> int:
    """Approximate edit distance using line-level diff (fast heuristic)."""
    lines_a = a.strip().splitlines()
    lines_b = b.strip().splitlines()
    set_a = set(lines_a)
    set_b = set(lines_b)
    # Symmetric difference of lines as a fast proxy
    return len(set_a.symmetric_difference(set_b))


def select_diverse_pairs(
    passing: list[dict],
    failing: list[dict],
    max_pairs: int = MAX_PAIRS_PER_TASK,
) -> list[tuple[dict, dict]]:
    """
    Select diverse DPO pairs from passing and failing candidates.
    Maximizes edit distance between selected pairs for diversity.
    """
    if not passing or not failing:
        return []

    pairs = []
    used_pass = set()
    used_fail = set()

    # Greedy: pick the most diverse pair at each step
    for _ in range(min(max_pairs, len(passing) * len(failing))):
        best_pair = None
        best_distance = -1

        for i, p in enumerate(passing):
            if i in used_pass and len(used_pass) < len(passing):
                continue
            for j, f in enumerate(failing):
                if j in used_fail and len(used_fail) < len(failing):
                    continue
                dist = edit_distance(p["code"], f["code"])
                if dist > best_distance:
                    best_distance = dist
                    best_pair = (i, j)

        if best_pair is None:
            break

        i, j = best_pair
        pairs.append((passing[i], failing[j]))
        used_pass.add(i)
        used_fail.add(j)

        # Reset used sets if exhausted (allow reuse for more pairs)
        if len(used_pass) >= len(passing):
            used_pass.clear()
        if len(used_fail) >= len(failing):
            used_fail.clear()

    return pairs


def format_dpo_pair(task_text: str, chosen_code: str, rejected_code: str) -> dict:
    """Format a DPO pair in standard training format."""
    return {
        "prompt": task_text,
        "chosen": chosen_code,
        "rejected": rejected_code,
    }


def load_candidates(path: Path) -> list[dict]:
    """Load candidate results from JSONL."""
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    return records


def merge_candidates(*candidate_files: list[dict]) -> dict[int, dict]:
    """Merge candidates from multiple passes by task_id.
    Later files add candidates to earlier ones."""
    merged: dict[int, dict] = {}

    for records in candidate_files:
        for record in records:
            task_id = record["task_id"]
            if task_id in merged:
                # Append new candidates to existing
                merged[task_id]["candidates"].extend(record["candidates"])
                merged[task_id]["num_passing"] += record.get("num_passing", 0)
                merged[task_id]["num_failing"] += record.get("num_failing", 0)
            else:
                merged[task_id] = record.copy()

    return merged


def build_pairs(candidates: list[dict] | dict[int, dict]) -> list[dict]:
    """Build all DPO pairs from candidate results."""
    # Accept either list or merged dict
    if isinstance(candidates, dict):
        records = list(candidates.values())
    else:
        records = candidates

    all_pairs = []

    tasks_with_pairs = 0
    tasks_no_passing = 0
    tasks_no_failing = 0

    for record in records:
        task_text = record["task_text"]
        cands = record["candidates"]

        passing = [c for c in cands if c["passed"] and c.get("code")]
        failing = [c for c in cands if not c["passed"] and c.get("code")]

        if not passing:
            tasks_no_passing += 1
            continue
        if not failing:
            tasks_no_failing += 1
            continue

        selected = select_diverse_pairs(passing, failing)
        for chosen, rejected in selected:
            pair = format_dpo_pair(task_text, chosen["code"], rejected["code"])
            pair["task_id"] = record["task_id"]
            all_pairs.append(pair)

        tasks_with_pairs += 1

    print(f"Pair statistics:")
    print(f"  Tasks with pairs: {tasks_with_pairs}")
    print(f"  Tasks without passing: {tasks_no_passing}")
    print(f"  Tasks without failing: {tasks_no_failing}")
    print(f"  Total pairs: {len(all_pairs)}")
    print(f"  Avg pairs/task: {len(all_pairs)/max(1, tasks_with_pairs):.1f}")

    return all_pairs


def write_pairs(pairs: list[dict], path: Path):
    """Write DPO pairs to JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for pair in pairs:
            f.write(json.dumps(pair) + "\n")
    print(f"  Wrote {len(pairs)} pairs to {path}")


def spot_check(pairs: list[dict], n: int = 50):
    """Validate a random sample of pairs."""
    from experiments.rlvf_v2.mbpp_dataset import load_all_for_generation
    from experiments.rlvf_v2.mbpp_verifier import verify_solution

    tasks_by_id = {t["task_id"]: t for t in load_all_for_generation()}
    sample = random.sample(pairs, min(n, len(pairs)))

    chosen_pass = 0
    rejected_fail = 0

    for pair in sample:
        task = tasks_by_id.get(pair["task_id"])
        if not task:
            continue

        # Verify chosen passes
        result = verify_solution(pair["chosen"], task, timeout=30)
        if result["all_passed"]:
            chosen_pass += 1

        # Verify rejected fails
        result = verify_solution(pair["rejected"], task, timeout=30)
        if not result["all_passed"]:
            rejected_fail += 1

    total = len(sample)
    print(f"\nSpot check ({total} pairs):")
    print(f"  Chosen passes tests: {chosen_pass}/{total} ({100*chosen_pass/total:.0f}%)")
    print(f"  Rejected fails tests: {rejected_fail}/{total} ({100*rejected_fail/total:.0f}%)")

    if chosen_pass < total * 0.9:
        print("  WARNING: >10% of chosen solutions don't pass — data quality issue!")
    if rejected_fail < total * 0.9:
        print("  WARNING: >10% of rejected solutions actually pass — label noise!")


def main():
    parser = argparse.ArgumentParser(description="Select DPO pairs from candidates")
    parser.add_argument("--candidates", type=str, required=True,
                        help="Path to candidates.jsonl from generate_pairs.py")
    parser.add_argument("--candidates-pass2", type=str, default=None,
                        help="Path to pass 2 candidates (merged with pass 1)")
    parser.add_argument("--output-dir", type=str, required=True,
                        help="Output directory for DPO pair files")
    parser.add_argument("--spot-check", type=int, default=50,
                        help="Number of pairs to spot-check (0 to skip)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    random.seed(args.seed)

    pass1 = load_candidates(Path(args.candidates))
    print(f"Pass 1: {len(pass1)} task records")

    if args.candidates_pass2 and Path(args.candidates_pass2).exists():
        pass2 = load_candidates(Path(args.candidates_pass2))
        print(f"Pass 2: {len(pass2)} task records")
        merged = merge_candidates(pass1, pass2)
        print(f"Merged: {len(merged)} unique tasks")
        all_pairs = build_pairs(merged)
    else:
        all_pairs = build_pairs(pass1)
    output_dir = Path(args.output_dir)

    # Write full dataset
    write_pairs(all_pairs, output_dir / "dpo_pairs_full.jsonl")

    # Create subsampled versions
    shuffled = all_pairs.copy()
    random.shuffle(shuffled)

    sizes = {"10k": 10000, "5k": 5000, "1k": 1000}
    for name, size in sizes.items():
        subset = shuffled[:min(size, len(shuffled))]
        write_pairs(subset, output_dir / f"dpo_pairs_{name}.jsonl")

    # Spot check
    if args.spot_check > 0:
        spot_check(all_pairs, n=args.spot_check)

    # Summary
    print(f"\nDPO pair files written to {output_dir}/")
    print(f"  Full: {len(all_pairs)} pairs")
    for name, size in sizes.items():
        actual = min(size, len(all_pairs))
        print(f"  {name}: {actual} pairs")


if __name__ == "__main__":
    main()
