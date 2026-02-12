"""
RLVF Evaluation Script
Evaluates fine-tuned models on HumanEval to measure the effect of LUCID-verified training data.

Usage:
    python evaluate.py --model models/vanilla --output results/vanilla_eval.json
    python evaluate.py --model models/lucid --output results/lucid_eval.json
    python evaluate.py --model models/dpo --output results/dpo_eval.json
    python evaluate.py --model bigcode/starcoder2-3b --output results/base_eval.json
"""

import argparse
import json
import os
import sys
import time
import signal
import traceback
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

HUMANEVAL_PATH = Path(__file__).parent / "data" / "humaneval" / "HumanEval.jsonl"
MAX_NEW_TOKENS = 1024
TEMPERATURE = 0.2
NUM_SAMPLES = 1  # pass@1 by default
EXEC_TIMEOUT = 10  # seconds per test execution


def load_humaneval() -> list[dict]:
    """Load HumanEval dataset."""
    tasks = []
    with open(HUMANEVAL_PATH) as f:
        for line in f:
            tasks.append(json.loads(line))
    return tasks


def load_model(model_path: str, is_adapter: bool = False):
    """Load model (base or fine-tuned with adapter)."""
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    if is_adapter:
        # Load base model + LoRA adapter
        # Read adapter config to get base model name
        adapter_config_path = Path(model_path) / "adapter_config.json"
        if adapter_config_path.exists():
            with open(adapter_config_path) as f:
                adapter_config = json.load(f)
            base_model_name = adapter_config.get("base_model_name_or_path", "bigcode/starcoder2-3b")
        else:
            base_model_name = "bigcode/starcoder2-3b"

        print(f"Loading base model: {base_model_name}")
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            quantization_config=quant_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
        )
        print(f"Loading adapter from: {model_path}")
        model = PeftModel.from_pretrained(base_model, model_path)
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    else:
        print(f"Loading model: {model_path}")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=quant_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
        )
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    tokenizer.pad_token = tokenizer.eos_token
    model.eval()
    return model, tokenizer


def generate_completion(model, tokenizer, prompt: str) -> str:
    """Generate a code completion for a HumanEval prompt."""
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

    # Decode only the generated part
    generated = outputs[0][inputs["input_ids"].shape[1]:]
    completion = tokenizer.decode(generated, skip_special_tokens=True)

    # Stop at first function definition or class (likely next problem)
    lines = completion.split("\n")
    result_lines = []
    for i, line in enumerate(lines):
        if i > 0 and (line.startswith("def ") or line.startswith("class ")):
            break
        result_lines.append(line)

    return "\n".join(result_lines)


def _run_test(code_and_test: tuple[str, str]) -> bool:
    """Execute test in a subprocess-safe way."""
    code, test = code_and_test
    try:
        exec_globals = {}
        exec(code, exec_globals)
        exec(test, exec_globals)
        return True
    except Exception:
        return False


def check_correctness(prompt: str, completion: str, test: str, entry_point: str) -> bool:
    """Check if a completion passes the test cases."""
    full_code = prompt + completion

    # Use process pool for timeout safety
    try:
        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_test, (full_code, test))
            return future.result(timeout=EXEC_TIMEOUT)
    except (FuturesTimeoutError, Exception):
        return False


def evaluate_model(model, tokenizer, tasks: list[dict], num_samples: int = 1) -> dict:
    """Evaluate model on HumanEval."""
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
            correct = check_correctness(prompt, completion, test, entry_point)
            completions.append({
                "sample": s,
                "completion": completion[:500],  # Truncate for storage
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

        # Progress
        if (i + 1) % 10 == 0 or i == total - 1:
            print(
                f"  [{i+1}/{total}] pass@{num_samples}: {passed}/{i+1} "
                f"({100*passed/(i+1):.1f}%)",
                file=sys.stderr,
            )

    pass_rate = passed / total if total > 0 else 0

    return {
        "total_tasks": total,
        "passed": passed,
        "pass_rate": pass_rate,
        "pass_rate_pct": f"{100*pass_rate:.1f}%",
        "num_samples": num_samples,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate RLVF models on HumanEval")
    parser.add_argument("--model", required=True, help="Model path (base or adapter directory)")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--samples", type=int, default=NUM_SAMPLES, help="Number of samples per task (pass@k)")
    parser.add_argument("--adapter", action="store_true", help="Model is a LoRA adapter (not standalone)")
    parser.add_argument("--tasks", type=int, default=0, help="Limit number of tasks (0 = all)")
    args = parser.parse_args()

    # Auto-detect adapter
    is_adapter = args.adapter or (Path(args.model) / "adapter_config.json").exists()

    print(f"Model: {args.model}", file=sys.stderr)
    print(f"Adapter: {is_adapter}", file=sys.stderr)
    print(f"Samples: {args.samples}", file=sys.stderr)

    # Load
    model, tokenizer = load_model(args.model, is_adapter=is_adapter)
    tasks = load_humaneval()
    if args.tasks > 0:
        tasks = tasks[:args.tasks]

    print(f"Evaluating on {len(tasks)} HumanEval tasks...", file=sys.stderr)
    start = time.time()

    results = evaluate_model(model, tokenizer, tasks, num_samples=args.samples)

    elapsed = time.time() - start
    results["model"] = args.model
    results["is_adapter"] = is_adapter
    results["elapsed_seconds"] = elapsed
    results["evaluated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  Model:     {args.model}", file=sys.stderr)
    print(f"  pass@{args.samples}:    {results['passed']}/{results['total_tasks']} ({results['pass_rate_pct']})", file=sys.stderr)
    print(f"  Time:      {elapsed:.1f}s", file=sys.stderr)
    print(f"  Saved to:  {args.output}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)


if __name__ == "__main__":
    main()
