"""
RLVF Fine-Tuning Script
Fine-tunes StarCoder2-3B using QLoRA on LUCID-verified vs vanilla training data.

Usage:
    python train.py --dataset data/vanilla_train.jsonl --output-dir models/vanilla
    python train.py --dataset data/lucid_train.jsonl --output-dir models/lucid
    python train.py --dataset data/dpo_pairs.jsonl --output-dir models/dpo --mode dpo
"""

import argparse
import json
import os
from pathlib import Path

import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig, DPOTrainer, DPOConfig

DEFAULT_BASE_MODEL = "bigcode/starcoder2-3b"
MAX_SEQ_LENGTH = 2048


def load_sft_dataset(path: str) -> Dataset:
    """Load JSONL dataset for SFT training."""
    records = []
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            # Format as instruction-following
            text = f"### Task\n{rec['instruction']}\n\n### Solution\n{rec['output']}"
            records.append({"text": text})
    return Dataset.from_list(records)


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


def get_lora_config() -> LoraConfig:
    return LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )


def train_sft(dataset_path: str, output_dir: str, num_epochs: int = 3, base_model: str = DEFAULT_BASE_MODEL):
    """Supervised fine-tuning with QLoRA."""
    print(f"Loading dataset from {dataset_path}...")
    dataset = load_sft_dataset(dataset_path)
    print(f"  {len(dataset)} examples loaded")

    print(f"Loading model {base_model} with 4-bit quantization...")
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=get_quantization_config(),
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, get_lora_config())

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"  Trainable: {trainable:,} / {total:,} ({100*trainable/total:.2f}%)")

    training_args = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_strategy="epoch",
        bf16=True,
        max_length=MAX_SEQ_LENGTH,
        dataset_text_field="text",
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    print(f"Starting SFT training ({num_epochs} epochs)...")
    trainer.train()

    print(f"Saving model to {output_dir}...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    print("Training complete.")


def train_dpo(dataset_path: str, output_dir: str, num_epochs: int = 1, base_model: str = DEFAULT_BASE_MODEL):
    """DPO training with LUCID-verified as preferred."""
    print(f"Loading DPO dataset from {dataset_path}...")
    dataset = load_dpo_dataset(dataset_path)
    print(f"  {len(dataset)} preference pairs loaded")

    print(f"Loading model {base_model} with 4-bit quantization...")
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=get_quantization_config(),
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model = prepare_model_for_kbit_training(model)

    # DPO needs a reference model — use the same base
    ref_model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=get_quantization_config(),
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )

    peft_config = get_lora_config()

    training_args = DPOConfig(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        learning_rate=5e-5,
        warmup_ratio=0.1,
        lr_scheduler_type="cosine",
        logging_steps=10,
        save_strategy="epoch",
        bf16=True,
        max_length=MAX_SEQ_LENGTH,
        max_prompt_length=512,
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
        report_to="none",
        beta=0.1,
    )

    trainer = DPOTrainer(
        model=model,
        ref_model=ref_model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
        peft_config=peft_config,
    )

    print(f"Starting DPO training ({num_epochs} epochs)...")
    trainer.train()

    print(f"Saving model to {output_dir}...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    print("Training complete.")


def main():
    parser = argparse.ArgumentParser(description="RLVF Fine-Tuning")
    parser.add_argument("--dataset", required=True, help="Path to training JSONL")
    parser.add_argument("--output-dir", required=True, help="Where to save the model")
    parser.add_argument("--mode", choices=["sft", "dpo"], default="sft",
                        help="Training mode: sft (supervised) or dpo (preference)")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--base-model", type=str, default=DEFAULT_BASE_MODEL, help="Base model to fine-tune")
    args = parser.parse_args()

    if args.mode == "sft":
        train_sft(args.dataset, args.output_dir, args.epochs, base_model=args.base_model)
    elif args.mode == "dpo":
        train_dpo(args.dataset, args.output_dir, args.epochs, base_model=args.base_model)


if __name__ == "__main__":
    main()
