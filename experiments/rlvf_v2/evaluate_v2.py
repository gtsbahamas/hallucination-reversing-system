"""
RLVF v2 Evaluation Script
Evaluates fine-tuned models on HumanEval (164 tasks) and MBPP test split (500 tasks).

Adapted from experiments/rlvf/evaluate.py with added MBPP support.

Usage:
    # Evaluate on HumanEval
    python -m experiments.rlvf_v2.evaluate_v2 \
        --model models/rlvf_v2/dpo_10k_15b \
        --output results/rlvf_v2/dpo_10k_15b_humaneval.json \
        --benchmark humaneval

    # Evaluate on MBPP
    python -m experiments.rlvf_v2.evaluate_v2 \
        --model models/rlvf_v2/dpo_10k_15b \
        --output results/rlvf_v2/dpo_10k_15b_mbpp.json \
        --benchmark mbpp

    # Evaluate base model
    python -m experiments.rlvf_v2.evaluate_v2 \
        --model bigcode/starcoder2-15b \
        --output results/rlvf_v2/base_15b_humaneval.json
"""

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

from experiments.humaneval.dataset import load_dataset as load_humaneval
from experiments.rlvf_v2.mbpp_dataset import load_mbpp_test_split
from experiments.rlvf_v2.mbpp_verifier import verify_solution

HUMANEVAL_PATH = Path(__file__).parent.parent.parent / "data" / "humaneval" / "HumanEval.jsonl"
MAX_NEW_TOKENS = 1024
TEMPERATURE = 0.2
EXEC_TIMEOUT = 10


def load_model(model_path: str, is_adapter: bool = False):
    """Load model (base or fine-tuned with adapter)."""
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    if is_adapter:
        adapter_config_path = Path(model_path) / "adapter_config.json"
        if adapter_config_path.exists():
            with open(adapter_config_path) as f:
                adapter_config = json.load(f)
            base_model_name = adapter_config.get("base_model_name_or_path", "bigcode/starcoder2-3b")
        else:
            base_model_name = "bigcode/starcoder2-3b"

        print(f"Loading base model: {base_model_name}", file=sys.stderr)
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            quantization_config=quant_config,
            device_map="auto",
            trust_remote_code=True,
            dtype=torch.bfloat16,
        )
        print(f"Loading adapter from: {model_path}", file=sys.stderr)
        model = PeftModel.from_pretrained(base_model, model_path)
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    else:
        print(f"Loading model: {model_path}", file=sys.stderr)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=quant_config,
            device_map="auto",
            trust_remote_code=True,
            dtype=torch.bfloat16,
        )
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    tokenizer.pad_token = tokenizer.eos_token
    model.eval()
    return model, tokenizer


def generate_completion(model, tokenizer, prompt: str) -> str:
    """Generate a code completion."""
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            top_p=0.95,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated = outputs[0][inputs["input_ids"].shape[1]:]
    completion = tokenizer.decode(generated, skip_special_tokens=True)

    # Stop at next function/class definition
    lines = completion.split("\n")
    result_lines = []
    for i, line in enumerate(lines):
        if i > 0 and (line.startswith("def ") or line.startswith("class ")):
            break
        result_lines.append(line)

    return "\n".join(result_lines)


def _run_test(code_and_test: tuple[str, str]) -> bool:
    """Execute test in subprocess-safe way."""
    code, test = code_and_test
    try:
        exec_globals = {}
        exec(code, exec_globals)
        exec(test, exec_globals)
        return True
    except Exception:
        return False


def check_correctness_humaneval(prompt: str, completion: str, test: str, entry_point: str) -> bool:
    """Check if a HumanEval completion passes tests."""
    full_code = prompt + completion
    try:
        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_test, (full_code, test))
            return future.result(timeout=EXEC_TIMEOUT)
    except (FuturesTimeoutError, Exception):
        return False


def evaluate_humaneval(model, tokenizer, num_samples: int = 1) -> dict:
    """Evaluate model on HumanEval benchmark."""
    tasks = load_humaneval()
    results = []
    passed = 0
    total = len(tasks)

    for i, task in enumerate(tasks):
        task_id = task["task_id"]
        prompt = task["prompt"]
        test = task["test"]
        entry_point = task["entry_point"]

        task_passed = False
        completions = []

        for s in range(num_samples):
            completion = generate_completion(model, tokenizer, prompt)
            correct = check_correctness_humaneval(prompt, completion, test, entry_point)
            completions.append({
                "sample": s,
                "completion": completion[:500],
                "correct": correct,
            })
            if correct:
                task_passed = True

        if task_passed:
            passed += 1

        results.append({
            "task_id": task_id,
            "passed": task_passed,
            "completions": completions,
        })

        if (i + 1) % 10 == 0 or i == total - 1:
            print(
                f"  HumanEval [{i+1}/{total}] pass@{num_samples}: "
                f"{passed}/{i+1} ({100*passed/(i+1):.1f}%)",
                file=sys.stderr,
            )

    pass_rate = passed / total if total > 0 else 0
    return {
        "benchmark": "humaneval",
        "total_tasks": total,
        "passed": passed,
        "pass_rate": pass_rate,
        "pass_rate_pct": f"{100*pass_rate:.1f}%",
        "num_samples": num_samples,
        "results": results,
    }


def evaluate_mbpp(model, tokenizer, num_samples: int = 1) -> dict:
    """Evaluate model on MBPP test split."""
    tasks = load_mbpp_test_split()
    results = []
    passed = 0
    total = len(tasks)

    for i, task in enumerate(tasks):
        task_id = task["task_id"]
        task_text = task["text"]

        # Format prompt same as training
        prompt = f"### Task\n{task_text}\n\n### Solution\n"

        task_passed = False
        completions = []

        for s in range(num_samples):
            completion = generate_completion(model, tokenizer, prompt)

            # Verify against MBPP tests
            result = verify_solution(completion, task, timeout=30)
            correct = result["all_passed"]

            completions.append({
                "sample": s,
                "completion": completion[:500],
                "correct": correct,
                "error_type": result.get("error_type"),
            })
            if correct:
                task_passed = True

        if task_passed:
            passed += 1

        results.append({
            "task_id": task_id,
            "passed": task_passed,
            "completions": completions,
        })

        if (i + 1) % 20 == 0 or i == total - 1:
            print(
                f"  MBPP [{i+1}/{total}] pass@{num_samples}: "
                f"{passed}/{i+1} ({100*passed/(i+1):.1f}%)",
                file=sys.stderr,
            )

    pass_rate = passed / total if total > 0 else 0
    return {
        "benchmark": "mbpp",
        "total_tasks": total,
        "passed": passed,
        "pass_rate": pass_rate,
        "pass_rate_pct": f"{100*pass_rate:.1f}%",
        "num_samples": num_samples,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="RLVF v2 Model Evaluation")
    parser.add_argument("--model", required=True, help="Model path (base or adapter)")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--benchmark", choices=["humaneval", "mbpp", "both"],
                        default="humaneval", help="Which benchmark to evaluate on")
    parser.add_argument("--samples", type=int, default=1, help="Samples per task (pass@k)")
    parser.add_argument("--adapter", action="store_true", help="Model is a LoRA adapter")
    parser.add_argument("--tasks", type=int, default=0, help="Limit tasks (0 = all)")
    args = parser.parse_args()

    # Auto-detect adapter
    is_adapter = args.adapter or (Path(args.model) / "adapter_config.json").exists()

    print(f"Model: {args.model}", file=sys.stderr)
    print(f"Adapter: {is_adapter}", file=sys.stderr)
    print(f"Benchmark: {args.benchmark}", file=sys.stderr)
    print(f"Samples: {args.samples}", file=sys.stderr)

    model, tokenizer = load_model(args.model, is_adapter=is_adapter)

    start = time.time()
    all_results = {}

    if args.benchmark in ("humaneval", "both"):
        print(f"\nEvaluating on HumanEval...", file=sys.stderr)
        humaneval_results = evaluate_humaneval(model, tokenizer, num_samples=args.samples)
        all_results["humaneval"] = humaneval_results

    if args.benchmark in ("mbpp", "both"):
        print(f"\nEvaluating on MBPP test split...", file=sys.stderr)
        mbpp_results = evaluate_mbpp(model, tokenizer, num_samples=args.samples)
        all_results["mbpp"] = mbpp_results

    elapsed = time.time() - start

    # Build output
    output = {
        "model": args.model,
        "is_adapter": is_adapter,
        "elapsed_seconds": elapsed,
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    output.update(all_results)

    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    # Print summary
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  Model: {args.model}", file=sys.stderr)
    for bench_name, bench_results in all_results.items():
        print(
            f"  {bench_name} pass@{args.samples}: "
            f"{bench_results['passed']}/{bench_results['total_tasks']} "
            f"({bench_results['pass_rate_pct']})",
            file=sys.stderr,
        )
    print(f"  Time: {elapsed:.1f}s", file=sys.stderr)
    print(f"  Saved to: {args.output}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)


if __name__ == "__main__":
    main()
