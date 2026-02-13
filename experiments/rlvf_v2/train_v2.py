"""
RLVF v2 Training Script
DPO fine-tuning of StarCoder2-3B and StarCoder2-15B on MBPP-derived preference pairs.

Key differences from v1 (experiments/rlvf/train.py):
- Supports both 3B and 15B models
- Memory-efficient DPO for 15B (no separate ref_model — uses PEFT reference)
- Configurable batch size per model size
- Learning rate scaling for larger datasets
- Checkpoint saving every N steps
- Training loss logging to file

Usage:
    python -m experiments.rlvf_v2.train_v2 \
        --dataset data/rlvf_v2/dpo_pairs_10k.jsonl \
        --output-dir models/rlvf_v2/dpo_10k_15b \
        --base-model bigcode/starcoder2-15b \
        --epochs 1

    python -m experiments.rlvf_v2.train_v2 \
        --dataset data/rlvf_v2/dpo_pairs_10k.jsonl \
        --output-dir models/rlvf_v2/dpo_10k_3b \
        --base-model bigcode/starcoder2-3b \
        --epochs 1
"""

import argparse
import json
import time
from pathlib import Path

import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig, prepare_model_for_kbit_training
from trl import DPOTrainer, DPOConfig

MODEL_3B = "bigcode/starcoder2-3b"
MODEL_15B = "bigcode/starcoder2-15b"
MAX_SEQ_LENGTH = 2048


def load_dpo_dataset(path: str) -> Dataset:
    """Load JSONL dataset for DPO training."""
    records = []
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            records.append({
                "prompt": f"### Task\n{rec['prompt']}\n\n### Solution\n",
                "chosen": rec["chosen"],
                "rejected": rec["rejected"],
            })
    return Dataset.from_list(records)


def get_quantization_config() -> BitsAndBytesConfig:
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )


def get_lora_config(model_size: str = "3b") -> LoraConfig:
    """LoRA config adjusted for model size."""
    # Same rank for both — QLoRA makes this memory-efficient
    return LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                         "c_fc", "c_proj"],
    )


def get_training_config(
    output_dir: str,
    model_size: str,
    dataset_size: int,
    num_epochs: int,
    save_steps: int,
) -> DPOConfig:
    """Training config adjusted for model and dataset size."""

    # Batch size: smaller for 15B to fit in memory
    if model_size == "15b":
        per_device_batch = 1
        grad_accum = 16  # effective batch = 16
    else:
        per_device_batch = 2
        grad_accum = 8   # effective batch = 16

    # Learning rate: scale down for larger datasets
    if dataset_size >= 5000:
        lr = 2e-5
        warmup = 0.1
    elif dataset_size >= 1000:
        lr = 3e-5
        warmup = 0.1
    else:
        lr = 5e-5
        warmup = 0.1

    return DPOConfig(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=per_device_batch,
        gradient_accumulation_steps=grad_accum,
        learning_rate=lr,
        warmup_ratio=warmup,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_steps=save_steps,
        save_strategy="steps",
        bf16=True,
        max_length=MAX_SEQ_LENGTH,
        max_prompt_length=512,
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
        report_to="none",
        beta=0.1,
        # For 15B: use PEFT reference model (no separate ref_model needed)
        # This is handled by DPOTrainer when peft_config is provided
    )


def train_dpo(
    dataset_path: str,
    output_dir: str,
    base_model: str = MODEL_3B,
    num_epochs: int = 1,
    save_steps: int = 500,
):
    """DPO training with QLoRA — supports both 3B and 15B."""

    # Detect model size
    model_size = "15b" if "15b" in base_model.lower() else "3b"
    print(f"Model: {base_model} (size: {model_size})")

    # Load dataset
    print(f"Loading DPO dataset from {dataset_path}...")
    dataset = load_dpo_dataset(dataset_path)
    dataset_size = len(dataset)
    print(f"  {dataset_size} preference pairs loaded")

    # Load tokenizer
    print(f"Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # Load model with quantization
    print(f"Loading model with 4-bit quantization...")
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=get_quantization_config(),
        device_map="auto",
        trust_remote_code=True,
        dtype=torch.bfloat16,
    )
    model = prepare_model_for_kbit_training(model)

    # For 15B: NO separate ref_model — DPOTrainer with peft_config uses
    # the base model weights as implicit reference (memory efficient)
    # For 3B: same approach works and saves memory
    ref_model = None

    peft_config = get_lora_config(model_size)

    # Print trainable parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Total parameters: {total_params:,}")

    # Training config
    training_args = get_training_config(
        output_dir=output_dir,
        model_size=model_size,
        dataset_size=dataset_size,
        num_epochs=num_epochs,
        save_steps=save_steps,
    )

    print(f"  Batch size: {training_args.per_device_train_batch_size}")
    print(f"  Gradient accumulation: {training_args.gradient_accumulation_steps}")
    print(f"  Effective batch: {training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps}")
    print(f"  Learning rate: {training_args.learning_rate}")
    print(f"  DPO beta: {training_args.beta}")
    print(f"  Save every: {save_steps} steps")

    # Create trainer
    trainer = DPOTrainer(
        model=model,
        ref_model=ref_model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
        peft_config=peft_config,
    )

    # Log training start
    start_time = time.time()
    print(f"\nStarting DPO training ({num_epochs} epoch(s), {dataset_size} pairs)...")
    print(f"  Estimated steps: {dataset_size // (training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps) * num_epochs}")

    # Train
    train_result = trainer.train()

    elapsed = time.time() - start_time
    print(f"\nTraining complete in {elapsed:.0f}s ({elapsed/3600:.1f} hrs)")

    # Save model
    print(f"Saving model to {output_dir}...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Save training metrics
    metrics = {
        "model": base_model,
        "model_size": model_size,
        "dataset": dataset_path,
        "dataset_size": dataset_size,
        "epochs": num_epochs,
        "elapsed_seconds": elapsed,
        "training_loss": train_result.training_loss,
        "global_step": train_result.global_step,
    }
    metrics_path = Path(output_dir) / "training_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2))
    print(f"  Metrics saved to {metrics_path}")

    # Save loss log
    if hasattr(trainer.state, "log_history"):
        log_path = Path(output_dir) / "loss_log.json"
        log_path.write_text(json.dumps(trainer.state.log_history, indent=2))
        print(f"  Loss log saved to {log_path}")

    print(f"\n{'='*60}")
    print(f"  Model: {base_model}")
    print(f"  Dataset: {dataset_size} pairs")
    print(f"  Final loss: {train_result.training_loss:.4f}")
    print(f"  Steps: {train_result.global_step}")
    print(f"  Time: {elapsed:.0f}s")
    print(f"  Saved to: {output_dir}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="RLVF v2 DPO Training")
    parser.add_argument("--dataset", required=True, help="Path to DPO pairs JSONL")
    parser.add_argument("--output-dir", required=True, help="Where to save the model")
    parser.add_argument("--base-model", type=str, default=MODEL_3B,
                        help=f"Base model ({MODEL_3B} or {MODEL_15B})")
    parser.add_argument("--epochs", type=int, default=1,
                        help="Number of training epochs")
    parser.add_argument("--save-steps", type=int, default=500,
                        help="Save checkpoint every N steps")
    args = parser.parse_args()

    train_dpo(
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        base_model=args.base_model,
        num_epochs=args.epochs,
        save_steps=args.save_steps,
    )


if __name__ == "__main__":
    main()
