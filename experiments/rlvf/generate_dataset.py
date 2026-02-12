"""
RLVF Dataset Generator
Generates two training datasets for the LUCID RLVF experiment:
1. Vanilla: Standard code generation (no constraints)
2. LUCID: Reverse LUCID pipeline (spec → constrain → generate → self-verify)

Uses MBPP-like coding tasks as source prompts.
Output: JSONL files with (prompt, completion) pairs for fine-tuning.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

import anthropic

MODEL = "claude-sonnet-4-5-20250929"
MAX_CONCURRENT = 10  # Parallel API calls
OUTPUT_DIR = Path(__file__).parent / "data"

# ---------------------------------------------------------------------------
# Coding tasks — mix of MBPP-style + practical tasks
# ---------------------------------------------------------------------------

CODING_TASKS = [
    # String manipulation
    "Write a function that reverses the words in a sentence while preserving whitespace.",
    "Write a function that checks if a string is a valid palindrome, ignoring non-alphanumeric characters and case.",
    "Write a function that converts a string from camelCase to snake_case.",
    "Write a function that finds the longest common prefix among a list of strings.",
    "Write a function that compresses a string using run-length encoding (e.g., 'aabccc' -> 'a2b1c3').",
    "Write a function that validates an email address format.",
    "Write a function that implements a simple template engine replacing {{variable}} with values from a dictionary.",
    "Write a function that finds all anagrams of a word in a list of words.",
    "Write a function that converts a Roman numeral string to an integer.",
    "Write a function that performs string interpolation with nested object access (e.g., 'Hello {{user.name}}').",

    # Array/List operations
    "Write a function that finds the k-th largest element in an unsorted array without sorting.",
    "Write a function that merges two sorted arrays into one sorted array.",
    "Write a function that rotates an array by k positions to the right.",
    "Write a function that finds all pairs in an array that sum to a target value.",
    "Write a function that removes duplicates from a sorted array in-place.",
    "Write a function that implements binary search on a sorted array.",
    "Write a function that finds the maximum subarray sum (Kadane's algorithm).",
    "Write a function that flattens a nested array to a specified depth.",
    "Write a function that partitions an array around a pivot value.",
    "Write a function that finds the intersection of two arrays.",

    # Math/Number operations
    "Write a function that checks if a number is prime.",
    "Write a function that generates the first n Fibonacci numbers.",
    "Write a function that computes the greatest common divisor of two numbers.",
    "Write a function that converts a decimal number to any base (2-36).",
    "Write a function that checks if a number is a perfect square without using sqrt.",
    "Write a function that computes the power of a number using fast exponentiation.",
    "Write a function that finds all prime factors of a number.",
    "Write a function that computes the nth triangular number.",
    "Write a function that checks if three numbers can form a valid triangle.",
    "Write a function that rounds a floating-point number to n decimal places without floating-point errors.",

    # Data structures
    "Write a function that implements a stack with push, pop, peek, and isEmpty operations.",
    "Write a function that implements a queue using two stacks.",
    "Write a function that checks if parentheses in a string are balanced (supporting (), [], {}).",
    "Write a function that implements a simple LRU cache with get and put operations.",
    "Write a function that converts a nested dictionary to a flat dictionary with dot-notation keys.",
    "Write a function that implements a trie (prefix tree) with insert, search, and startsWith.",
    "Write a function that finds the depth of a nested dictionary.",
    "Write a function that implements a min-heap with insert and extractMin.",
    "Write a function that merges multiple sorted lists into one sorted list.",
    "Write a function that implements a simple hash map with collision handling.",

    # Tree/Graph operations
    "Write a function that performs a breadth-first search on a graph represented as an adjacency list.",
    "Write a function that detects a cycle in a directed graph.",
    "Write a function that finds the shortest path in an unweighted graph.",
    "Write a function that performs topological sort on a directed acyclic graph.",
    "Write a function that serializes and deserializes a binary tree.",
    "Write a function that finds the lowest common ancestor of two nodes in a binary tree.",
    "Write a function that inverts a binary tree.",
    "Write a function that checks if a binary tree is a valid binary search tree.",
    "Write a function that finds all paths from root to leaf in a binary tree.",
    "Write a function that computes the diameter of a binary tree.",

    # Error handling / Robustness
    "Write a function that safely parses JSON with detailed error messages including line numbers.",
    "Write a function that retries an async operation with exponential backoff.",
    "Write a function that validates a credit card number using the Luhn algorithm.",
    "Write a function that parses a date string in multiple formats and returns a standardized format.",
    "Write a function that implements a circuit breaker pattern for API calls.",
    "Write a function that validates and sanitizes HTML input to prevent XSS.",
    "Write a function that rate-limits function calls to n per time window.",
    "Write a function that deep-clones an object handling circular references.",
    "Write a function that compares two version strings (e.g., '1.2.3' vs '1.2.4').",
    "Write a function that implements a timeout wrapper for promises/async functions.",

    # File/Data processing
    "Write a function that parses CSV text into an array of objects using the header row as keys.",
    "Write a function that converts a markdown table to JSON.",
    "Write a function that extracts all URLs from a text string.",
    "Write a function that computes a SHA-256 hash of a string.",
    "Write a function that implements diff between two strings showing additions and deletions.",
    "Write a function that generates a random UUID v4.",
    "Write a function that converts bytes to human-readable format (KB, MB, GB).",
    "Write a function that validates a YAML-like indented structure for correctness.",
    "Write a function that implements a simple key-value store with TTL expiration.",
    "Write a function that batch-processes items with configurable concurrency limits.",

    # Algorithm challenges
    "Write a function that solves the N-Queens problem and returns all valid configurations.",
    "Write a function that implements Dijkstra's shortest path algorithm.",
    "Write a function that finds the longest increasing subsequence in an array.",
    "Write a function that implements the knapsack problem using dynamic programming.",
    "Write a function that generates all valid combinations of n pairs of parentheses.",
    "Write a function that finds the median of two sorted arrays in O(log(m+n)) time.",
    "Write a function that implements the edit distance (Levenshtein distance) between two strings.",
    "Write a function that solves the coin change problem (minimum coins to make a target).",
    "Write a function that implements a simple regex matcher supporting '.' and '*'.",
    "Write a function that finds all permutations of a string.",

    # API/Web patterns
    "Write a function that implements pagination with cursor-based navigation.",
    "Write a function that validates and normalizes URL paths.",
    "Write a function that implements a simple router matching URL patterns with parameters.",
    "Write a function that builds a query string from an object, handling arrays and nested objects.",
    "Write a function that implements JWT token creation and verification.",
    "Write a function that computes HMAC-SHA256 for webhook signature verification.",
    "Write a function that implements a simple middleware pipeline pattern.",
    "Write a function that parses HTTP Accept headers and returns content negotiation results.",
    "Write a function that implements a simple event emitter with on, off, and emit.",
    "Write a function that converts between different data formats (JSON, YAML, TOML).",

    # Concurrency/Async patterns
    "Write a function that implements Promise.allSettled from scratch.",
    "Write a function that creates a debounce wrapper for a function.",
    "Write a function that creates a throttle wrapper for a function.",
    "Write a function that implements a semaphore for limiting concurrent operations.",
    "Write a function that implements a pub/sub message broker.",
    "Write a function that pools and reuses expensive resources (connection pool pattern).",
    "Write a function that implements a task queue with priority ordering.",
    "Write a function that creates a lazy-evaluated infinite sequence generator.",
    "Write a function that implements cooperative multitasking with yield-based coroutines.",
    "Write a function that batches multiple rapid calls into a single execution with combined results.",

    # Additional practical tasks (to reach ~200)
    "Write a function that converts a color from hex to RGB and back.",
    "Write a function that calculates the distance between two GPS coordinates using the Haversine formula.",
    "Write a function that implements a simple state machine with transitions and guards.",
    "Write a function that generates a secure random password with configurable requirements.",
    "Write a function that validates a phone number for multiple international formats.",
    "Write a function that implements a simple expression parser and evaluator.",
    "Write a function that computes moving averages over a sliding window.",
    "Write a function that implements a bloom filter for probabilistic set membership.",
    "Write a function that normalizes unicode text (NFC, NFD, NFKC, NFKD).",
    "Write a function that implements a simple dependency resolver with cycle detection.",
    "Write a function that converts a flat list with parent IDs into a tree structure.",
    "Write a function that implements cron expression parsing and next-run calculation.",
    "Write a function that performs natural language number parsing ('twenty-three' -> 23).",
    "Write a function that implements a simple diff3 merge for version control.",
    "Write a function that validates and formats international bank account numbers (IBAN).",
    "Write a function that implements a trie-based autocomplete system.",
    "Write a function that computes the Jaccard similarity between two sets.",
    "Write a function that implements reservoir sampling for streaming data.",
    "Write a function that performs matrix multiplication with validation.",
    "Write a function that implements the Fisher-Yates shuffle algorithm.",
]

LANGUAGE = "python"

# ---------------------------------------------------------------------------
# Spec synthesis prompt (mirrors Reverse LUCID's spec-synthesizer.ts)
# ---------------------------------------------------------------------------

SPEC_SYSTEM_PROMPT = """You are a formal specification synthesizer. Given a coding task and language, generate 10-20 formal specifications that any correct implementation MUST satisfy.

Each specification must have:
- id: Sequential "SPEC-001", etc.
- category: correctness | edge-case | error-handling | security | type-safety | performance
- severity: critical | high | medium | low
- description: What the code must do or guarantee
- assertion: A specific, testable assertion (pseudocode or test case)

Return ONLY a JSON array. No markdown fences, no commentary."""

CONSTRAINT_SYSTEM_PROMPT = """You are a constraint generator. Given specifications, produce generation constraints.

Each constraint:
- type: "must" | "must-not" | "prefer"
- description: Clear guidance (1-2 sentences)

Return ONLY a JSON array. No markdown fences."""

GENERATION_SYSTEM_PROMPT_TEMPLATE = """You are an expert {language} programmer. Generate production-quality code.

SPECIFICATIONS — Your code MUST satisfy ALL of these:
{specs}

CONSTRAINTS:
{constraints}

Return ONLY the code. No markdown fences, no explanations. Include type hints and docstrings."""

VANILLA_SYSTEM_PROMPT = """You are an expert {language} programmer. Generate production-quality code.
Return ONLY the code. No markdown fences, no explanations. Include type hints and docstrings."""


@dataclass
class TrainingExample:
    task: str
    language: str
    code: str
    method: str  # "vanilla" or "lucid"
    specs: Optional[list] = None
    constraints: Optional[list] = None
    input_tokens: int = 0
    output_tokens: int = 0


def strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        first_nl = text.index("\n") if "\n" in text else len(text)
        text = text[first_nl + 1:]
    last_fence = text.rfind("```")
    if last_fence != -1:
        text = text[:last_fence]
    return text.strip()


def parse_json_array(text: str) -> list:
    text = strip_code_fences(text)
    if not text.endswith("]"):
        last_brace = text.rfind("}")
        if last_brace != -1:
            text = text[:last_brace + 1] + "\n]"
    return json.loads(text)


class DatasetGenerator:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            timeout=900.0,
        )
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.vanilla_count = 0
        self.lucid_count = 0
        self.errors = 0

    def _call_sync(self, system: str, user: str) -> tuple[str, int, int]:
        resp = self.client.messages.create(
            model=MODEL,
            max_tokens=8000,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        return text, resp.usage.input_tokens, resp.usage.output_tokens

    async def generate_vanilla(self, task: str) -> Optional[TrainingExample]:
        """Generate code without any constraints (baseline)."""
        async with self.semaphore:
            try:
                loop = asyncio.get_event_loop()
                text, inp, out = await loop.run_in_executor(
                    None,
                    self._call_sync,
                    VANILLA_SYSTEM_PROMPT.format(language=LANGUAGE),
                    f"Generate {LANGUAGE} code for: {task}",
                )
                code = strip_code_fences(text)
                self.total_input_tokens += inp
                self.total_output_tokens += out
                self.vanilla_count += 1
                return TrainingExample(
                    task=task, language=LANGUAGE, code=code,
                    method="vanilla", input_tokens=inp, output_tokens=out,
                )
            except Exception as e:
                self.errors += 1
                print(f"  [vanilla ERROR] {task[:50]}... → {e}", file=sys.stderr)
                return None

    async def generate_lucid(self, task: str) -> Optional[TrainingExample]:
        """Generate code using the full Reverse LUCID pipeline."""
        async with self.semaphore:
            try:
                loop = asyncio.get_event_loop()
                total_inp, total_out = 0, 0

                # Phase 1: Synthesize specs
                text, inp, out = await loop.run_in_executor(
                    None, self._call_sync,
                    SPEC_SYSTEM_PROMPT,
                    f"Generate formal specifications for:\nLanguage: {LANGUAGE}\nTask: {task}",
                )
                total_inp += inp
                total_out += out
                specs = parse_json_array(text)

                # Phase 2: Generate constraints
                specs_text = "\n".join(
                    f"[{s.get('id', f'SPEC-{i}')}] ({s.get('category', 'correctness')}) {s.get('description', '')}"
                    for i, s in enumerate(specs)
                )
                text, inp, out = await loop.run_in_executor(
                    None, self._call_sync,
                    CONSTRAINT_SYSTEM_PROMPT,
                    f"Generate constraints for:\nLanguage: {LANGUAGE}\nTask: {task}\n\nSpecs:\n{specs_text}",
                )
                total_inp += inp
                total_out += out
                constraints = parse_json_array(text)

                # Phase 3: Constrained generation
                spec_lines = "\n".join(
                    f"- [{s.get('id', f'SPEC-{i}')}] {s.get('description', '')}\n  Assertion: {s.get('assertion', 'N/A')}"
                    for i, s in enumerate(specs)
                )
                constraint_lines = "\n".join(
                    f"- [{c.get('type', 'must').upper()}] {c.get('description', '')}"
                    for c in constraints
                )
                gen_system = GENERATION_SYSTEM_PROMPT_TEMPLATE.format(
                    language=LANGUAGE, specs=spec_lines, constraints=constraint_lines,
                )
                text, inp, out = await loop.run_in_executor(
                    None, self._call_sync,
                    gen_system,
                    f"Generate {LANGUAGE} code for: {task}",
                )
                total_inp += inp
                total_out += out
                code = strip_code_fences(text)

                self.total_input_tokens += total_inp
                self.total_output_tokens += total_out
                self.lucid_count += 1

                return TrainingExample(
                    task=task, language=LANGUAGE, code=code,
                    method="lucid", specs=specs, constraints=constraints,
                    input_tokens=total_inp, output_tokens=total_out,
                )
            except Exception as e:
                self.errors += 1
                print(f"  [lucid ERROR] {task[:50]}... → {e}", file=sys.stderr)
                return None

    async def generate_all(self, tasks: list[str]) -> tuple[list[TrainingExample], list[TrainingExample]]:
        """Generate both vanilla and LUCID datasets for all tasks."""
        print(f"Generating datasets for {len(tasks)} tasks...", file=sys.stderr)
        print(f"  Vanilla: {len(tasks)} generations", file=sys.stderr)
        print(f"  LUCID: {len(tasks)} generations (3 API calls each)", file=sys.stderr)
        print(f"  Max concurrent: {MAX_CONCURRENT}", file=sys.stderr)
        print(f"  Estimated API calls: {len(tasks) * 4} total", file=sys.stderr)

        start = time.time()

        # Generate vanilla and LUCID in parallel
        all_tasks = []
        for task in tasks:
            all_tasks.append(("vanilla", self.generate_vanilla(task)))
            all_tasks.append(("lucid", self.generate_lucid(task)))

        results = await asyncio.gather(
            *[coro for _, coro in all_tasks],
            return_exceptions=True,
        )

        vanilla_examples = []
        lucid_examples = []

        for i, result in enumerate(results):
            method = all_tasks[i][0]
            if isinstance(result, Exception):
                self.errors += 1
                print(f"  [ERROR] {method}: {result}", file=sys.stderr)
                continue
            if result is None:
                continue
            if method == "vanilla":
                vanilla_examples.append(result)
            else:
                lucid_examples.append(result)

            # Progress
            total_done = len(vanilla_examples) + len(lucid_examples)
            if total_done % 20 == 0:
                elapsed = time.time() - start
                rate = total_done / elapsed if elapsed > 0 else 0
                est_remaining = (len(tasks) * 2 - total_done) / rate if rate > 0 else 0
                print(
                    f"  Progress: {total_done}/{len(tasks)*2} "
                    f"({elapsed:.0f}s elapsed, ~{est_remaining:.0f}s remaining) "
                    f"Tokens: {self.total_input_tokens:,} in / {self.total_output_tokens:,} out",
                    file=sys.stderr,
                )

        elapsed = time.time() - start
        print(f"\nDataset generation complete:", file=sys.stderr)
        print(f"  Vanilla: {len(vanilla_examples)} examples", file=sys.stderr)
        print(f"  LUCID:   {len(lucid_examples)} examples", file=sys.stderr)
        print(f"  Errors:  {self.errors}", file=sys.stderr)
        print(f"  Tokens:  {self.total_input_tokens:,} in / {self.total_output_tokens:,} out", file=sys.stderr)
        print(f"  Time:    {elapsed:.1f}s ({elapsed/60:.1f}m)", file=sys.stderr)

        # Estimate cost (Sonnet 4.5: $3/M in, $15/M out)
        cost = (self.total_input_tokens * 3 + self.total_output_tokens * 15) / 1_000_000
        print(f"  Est cost: ${cost:.2f}", file=sys.stderr)

        return vanilla_examples, lucid_examples


def save_dataset(examples: list[TrainingExample], path: Path):
    """Save as JSONL for fine-tuning."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        for ex in examples:
            # Format as instruction-following for fine-tuning
            record = {
                "instruction": ex.task,
                "output": ex.code,
                "language": ex.language,
                "method": ex.method,
                "input_tokens": ex.input_tokens,
                "output_tokens": ex.output_tokens,
            }
            if ex.specs:
                record["specs"] = ex.specs
            if ex.constraints:
                record["constraints"] = ex.constraints
            f.write(json.dumps(record) + "\n")

    print(f"Saved {len(examples)} examples to {path}", file=sys.stderr)


def save_dpo_dataset(vanilla: list[TrainingExample], lucid: list[TrainingExample], path: Path):
    """Save as DPO pairs: LUCID = chosen, vanilla = rejected."""
    path.parent.mkdir(parents=True, exist_ok=True)

    # Match by task
    vanilla_by_task = {ex.task: ex for ex in vanilla}
    pairs = []

    for lucid_ex in lucid:
        vanilla_ex = vanilla_by_task.get(lucid_ex.task)
        if vanilla_ex is None:
            continue
        pairs.append({
            "prompt": lucid_ex.task,
            "chosen": lucid_ex.code,
            "rejected": vanilla_ex.code,
            "language": lucid_ex.language,
        })

    with open(path, "w") as f:
        for pair in pairs:
            f.write(json.dumps(pair) + "\n")

    print(f"Saved {len(pairs)} DPO pairs to {path}", file=sys.stderr)


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate RLVF training dataset")
    parser.add_argument("--tasks", type=int, default=len(CODING_TASKS),
                        help=f"Number of tasks (max {len(CODING_TASKS)})")
    parser.add_argument("--concurrent", type=int, default=MAX_CONCURRENT,
                        help="Max concurrent API calls")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR))
    args = parser.parse_args()

    tasks = CODING_TASKS[:args.tasks]
    output_dir = Path(args.output_dir)

    gen = DatasetGenerator()
    gen.semaphore = asyncio.Semaphore(args.concurrent)

    vanilla, lucid = await gen.generate_all(tasks)

    # Save individual datasets (for SFT)
    save_dataset(vanilla, output_dir / "vanilla_train.jsonl")
    save_dataset(lucid, output_dir / "lucid_train.jsonl")

    # Save DPO pairs (for preference learning)
    save_dpo_dataset(vanilla, lucid, output_dir / "dpo_pairs.jsonl")

    # Save metadata
    meta = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": MODEL,
        "language": LANGUAGE,
        "total_tasks": len(tasks),
        "vanilla_count": len(vanilla),
        "lucid_count": len(lucid),
        "dpo_pairs": min(len(vanilla), len(lucid)),
        "errors": gen.errors,
        "total_input_tokens": gen.total_input_tokens,
        "total_output_tokens": gen.total_output_tokens,
        "estimated_cost_usd": (gen.total_input_tokens * 3 + gen.total_output_tokens * 15) / 1_000_000,
    }
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\nAll files written to {output_dir}/", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
