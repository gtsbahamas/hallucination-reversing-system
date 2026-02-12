#!/bin/bash
# Full RLVF Experiment Orchestrator
# Runs the complete pipeline: dataset generation → training → evaluation
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "  LUCID RLVF EXPERIMENT"
echo "  $(date)"
echo "============================================================"
echo ""

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY not set"
    echo "  export ANTHROPIC_API_KEY=sk-ant-..."
    exit 1
fi

# Check GPU
GPU_COUNT=$(nvidia-smi -L 2>/dev/null | wc -l)
echo "GPUs available: $GPU_COUNT"
echo ""

# ── Phase 1: Dataset Generation ──────────────────────────────
echo "============================================================"
echo "  PHASE 1: Dataset Generation (120 tasks × 2 conditions)"
echo "============================================================"
echo ""

START=$(date +%s)

python generate_dataset.py \
    --tasks 120 \
    --concurrent 10 \
    --output-dir data

PHASE1_TIME=$(($(date +%s) - START))
echo ""
echo "Phase 1 complete in ${PHASE1_TIME}s"
echo ""

# ── Phase 2: SFT Training ────────────────────────────────────
echo "============================================================"
echo "  PHASE 2: Fine-Tuning (3 conditions in sequence)"
echo "============================================================"
echo ""

# 2a: Train on vanilla data
echo "--- Training: Vanilla (baseline fine-tune) ---"
START=$(date +%s)
python train.py \
    --dataset data/vanilla_train.jsonl \
    --output-dir models/vanilla \
    --mode sft \
    --epochs 3
VANILLA_TIME=$(($(date +%s) - START))
echo "Vanilla training: ${VANILLA_TIME}s"
echo ""

# 2b: Train on LUCID-verified data
echo "--- Training: LUCID (verified fine-tune) ---"
START=$(date +%s)
python train.py \
    --dataset data/lucid_train.jsonl \
    --output-dir models/lucid \
    --mode sft \
    --epochs 3
LUCID_TIME=$(($(date +%s) - START))
echo "LUCID training: ${LUCID_TIME}s"
echo ""

# 2c: DPO training (LUCID preferred over vanilla)
echo "--- Training: DPO (preference learning) ---"
START=$(date +%s)
python train.py \
    --dataset data/dpo_pairs.jsonl \
    --output-dir models/dpo \
    --mode dpo \
    --epochs 1
DPO_TIME=$(($(date +%s) - START))
echo "DPO training: ${DPO_TIME}s"
echo ""

# ── Phase 3: Evaluation ──────────────────────────────────────
echo "============================================================"
echo "  PHASE 3: Evaluation on HumanEval (164 tasks × 4 models)"
echo "============================================================"
echo ""

mkdir -p results

# 3a: Base model (no fine-tuning)
echo "--- Evaluating: Base StarCoder2-3B ---"
START=$(date +%s)
python evaluate.py \
    --model bigcode/starcoder2-3b \
    --output results/base_eval.json
BASE_TIME=$(($(date +%s) - START))
echo ""

# 3b: Vanilla fine-tuned
echo "--- Evaluating: Vanilla fine-tuned ---"
START=$(date +%s)
python evaluate.py \
    --model models/vanilla \
    --output results/vanilla_eval.json
echo ""

# 3c: LUCID fine-tuned
echo "--- Evaluating: LUCID fine-tuned ---"
START=$(date +%s)
python evaluate.py \
    --model models/lucid \
    --output results/lucid_eval.json
echo ""

# 3d: DPO trained
echo "--- Evaluating: DPO trained ---"
START=$(date +%s)
python evaluate.py \
    --model models/dpo \
    --output results/dpo_eval.json
echo ""

# ── Summary ──────────────────────────────────────────────────
echo "============================================================"
echo "  RESULTS SUMMARY"
echo "============================================================"
echo ""

python -c "
import json
from pathlib import Path

conditions = [
    ('Base StarCoder2-3B', 'results/base_eval.json'),
    ('Vanilla Fine-tuned', 'results/vanilla_eval.json'),
    ('LUCID Fine-tuned', 'results/lucid_eval.json'),
    ('DPO (LUCID preferred)', 'results/dpo_eval.json'),
]

print(f'{'Condition':<25} {'Passed':>8} {'Total':>8} {'Pass@1':>10}')
print('-' * 55)

base_rate = None
for name, path in conditions:
    try:
        with open(path) as f:
            data = json.load(f)
        rate = data['pass_rate']
        if base_rate is None:
            base_rate = rate
            delta = ''
        else:
            rel = ((rate - base_rate) / base_rate * 100) if base_rate > 0 else 0
            delta = f'  ({rel:+.1f}% rel)'
        print(f'{name:<25} {data[\"passed\"]:>8} {data[\"total_tasks\"]:>8} {data[\"pass_rate_pct\"]:>10}{delta}')
    except FileNotFoundError:
        print(f'{name:<25} {\"N/A\":>8} {\"N/A\":>8} {\"N/A\":>10}')

print()
print('Full results in results/*.json')
"

echo ""
echo "============================================================"
echo "  EXPERIMENT COMPLETE"
echo "  $(date)"
echo "============================================================"
