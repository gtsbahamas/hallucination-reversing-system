#!/bin/bash
# Phase 2: Training + Evaluation (runs on EC2 g5.12xlarge)
# Trains 4 new DPO models and evaluates all conditions
#
# Training conditions:
#   1. Base 3B = 89.6% (existing v1 result)
#   2. DPO 120 on 3B = 91.5% (existing v1 result)
#   3. Base 15B (eval only, no training)
#   4. DPO 500 on 15B (NEW)
#   5. DPO 1K on 15B (NEW)
#   6. DPO 2K on 15B (NEW — full dataset)
#   7. DPO 2K on 3B (NEW — isolate model size vs data)
#
# Usage:
#   cd ~/rlvf_v2/hallucination-reversing-system
#   nohup bash experiments/rlvf_v2/run_phase2_ec2.sh > ~/rlvf_v2/logs/phase2.log 2>&1 &

set -euo pipefail

WORK_DIR="$HOME/rlvf_v2"
MODELS_DIR="$WORK_DIR/models"
RESULTS_DIR="$WORK_DIR/results"
DATA_DIR="$WORK_DIR/hallucination-reversing-system/data/rlvf_v2"
LOGS_DIR="$WORK_DIR/logs"
PROJECT_DIR="$WORK_DIR/hallucination-reversing-system"
VENV="$WORK_DIR/venv/bin/python"

mkdir -p "$MODELS_DIR" "$RESULTS_DIR" "$LOGS_DIR"

echo "============================================"
echo "  RLVF v2 Phase 2: Training + Evaluation"
echo "  Started: $(date)"
echo "============================================"

# Verify data exists
echo ""
echo "[Check] Verifying training data..."
for f in dpo_pairs_full.jsonl dpo_pairs_1k.jsonl dpo_pairs_500.jsonl; do
    if [ ! -f "$DATA_DIR/$f" ]; then
        echo "ERROR: Missing $DATA_DIR/$f"
        exit 1
    fi
    lines=$(wc -l < "$DATA_DIR/$f")
    echo "  $f: $lines pairs"
done

# Verify GPUs
echo ""
echo "[Check] GPU status..."
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader

cd "$PROJECT_DIR"

# ==========================================
# PHASE 2A: TRAINING
# ==========================================

echo ""
echo "========================================"
echo "  Phase 2A: Training (4 models)"
echo "========================================"

# Train 1: DPO 2K on 15B (all GPUs, largest job)
echo ""
echo "[Train 1/4] DPO 2K on 15B (all GPUs)..."
echo "  Started: $(date)"
CUDA_VISIBLE_DEVICES=0,1,2,3 $VENV -m experiments.rlvf_v2.train_v2 \
    --dataset "$DATA_DIR/dpo_pairs_full.jsonl" \
    --output-dir "$MODELS_DIR/dpo_2k_15b" \
    --base-model bigcode/starcoder2-15b \
    --epochs 1 \
    --save-steps 200 \
    2>&1 | tee "$LOGS_DIR/train_dpo_2k_15b.log"
echo "  Done: $(date)"

# Train 2: DPO 1K on 15B
echo ""
echo "[Train 2/4] DPO 1K on 15B..."
echo "  Started: $(date)"
CUDA_VISIBLE_DEVICES=0,1,2,3 $VENV -m experiments.rlvf_v2.train_v2 \
    --dataset "$DATA_DIR/dpo_pairs_1k.jsonl" \
    --output-dir "$MODELS_DIR/dpo_1k_15b" \
    --base-model bigcode/starcoder2-15b \
    --epochs 1 \
    --save-steps 200 \
    2>&1 | tee "$LOGS_DIR/train_dpo_1k_15b.log"
echo "  Done: $(date)"

# Train 3: DPO 500 on 15B
echo ""
echo "[Train 3/4] DPO 500 on 15B..."
echo "  Started: $(date)"
CUDA_VISIBLE_DEVICES=0,1,2,3 $VENV -m experiments.rlvf_v2.train_v2 \
    --dataset "$DATA_DIR/dpo_pairs_500.jsonl" \
    --output-dir "$MODELS_DIR/dpo_500_15b" \
    --base-model bigcode/starcoder2-15b \
    --epochs 1 \
    --save-steps 100 \
    2>&1 | tee "$LOGS_DIR/train_dpo_500_15b.log"
echo "  Done: $(date)"

# Train 4: DPO 2K on 3B (isolate model size vs data)
echo ""
echo "[Train 4/4] DPO 2K on 3B..."
echo "  Started: $(date)"
CUDA_VISIBLE_DEVICES=0,1 $VENV -m experiments.rlvf_v2.train_v2 \
    --dataset "$DATA_DIR/dpo_pairs_full.jsonl" \
    --output-dir "$MODELS_DIR/dpo_2k_3b" \
    --base-model bigcode/starcoder2-3b \
    --epochs 1 \
    --save-steps 200 \
    2>&1 | tee "$LOGS_DIR/train_dpo_2k_3b.log"
echo "  Done: $(date)"

echo ""
echo "  All training complete: $(date)"

# ==========================================
# PHASE 2B: EVALUATION (HumanEval)
# ==========================================

echo ""
echo "========================================"
echo "  Phase 2B: Evaluation (HumanEval)"
echo "========================================"

# Eval 1: Base 15B
echo ""
echo "[Eval 1/6] Base 15B on HumanEval..."
CUDA_VISIBLE_DEVICES=0,1,2,3 $VENV -m experiments.rlvf_v2.evaluate_v2 \
    --model bigcode/starcoder2-15b \
    --output "$RESULTS_DIR/base_15b_humaneval.json" \
    --benchmark humaneval \
    2>&1 | tee "$LOGS_DIR/eval_base_15b.log"
echo "  Done."

# Eval 2: DPO 500 on 15B
echo ""
echo "[Eval 2/6] DPO 500 (15B) on HumanEval..."
CUDA_VISIBLE_DEVICES=0,1,2,3 $VENV -m experiments.rlvf_v2.evaluate_v2 \
    --model "$MODELS_DIR/dpo_500_15b" \
    --output "$RESULTS_DIR/dpo_500_15b_humaneval.json" \
    --benchmark humaneval \
    2>&1 | tee "$LOGS_DIR/eval_dpo_500_15b.log"
echo "  Done."

# Eval 3: DPO 1K on 15B
echo ""
echo "[Eval 3/6] DPO 1K (15B) on HumanEval..."
CUDA_VISIBLE_DEVICES=0,1,2,3 $VENV -m experiments.rlvf_v2.evaluate_v2 \
    --model "$MODELS_DIR/dpo_1k_15b" \
    --output "$RESULTS_DIR/dpo_1k_15b_humaneval.json" \
    --benchmark humaneval \
    2>&1 | tee "$LOGS_DIR/eval_dpo_1k_15b.log"
echo "  Done."

# Eval 4: DPO 2K on 15B
echo ""
echo "[Eval 4/6] DPO 2K (15B) on HumanEval..."
CUDA_VISIBLE_DEVICES=0,1,2,3 $VENV -m experiments.rlvf_v2.evaluate_v2 \
    --model "$MODELS_DIR/dpo_2k_15b" \
    --output "$RESULTS_DIR/dpo_2k_15b_humaneval.json" \
    --benchmark humaneval \
    2>&1 | tee "$LOGS_DIR/eval_dpo_2k_15b.log"
echo "  Done."

# Eval 5: DPO 2K on 3B
echo ""
echo "[Eval 5/6] DPO 2K (3B) on HumanEval..."
CUDA_VISIBLE_DEVICES=0,1 $VENV -m experiments.rlvf_v2.evaluate_v2 \
    --model "$MODELS_DIR/dpo_2k_3b" \
    --output "$RESULTS_DIR/dpo_2k_3b_humaneval.json" \
    --benchmark humaneval \
    2>&1 | tee "$LOGS_DIR/eval_dpo_2k_3b.log"
echo "  Done."

# Eval 6: Base 3B (re-eval for fair comparison)
echo ""
echo "[Eval 6/6] Base 3B on HumanEval (re-eval)..."
CUDA_VISIBLE_DEVICES=0 $VENV -m experiments.rlvf_v2.evaluate_v2 \
    --model bigcode/starcoder2-3b \
    --output "$RESULTS_DIR/base_3b_humaneval.json" \
    --benchmark humaneval \
    2>&1 | tee "$LOGS_DIR/eval_base_3b.log"
echo "  Done."

# ==========================================
# PHASE 2C: MBPP (secondary eval)
# ==========================================

echo ""
echo "========================================"
echo "  Phase 2C: MBPP Evaluation (secondary)"
echo "========================================"

for condition in base_15b dpo_2k_15b dpo_2k_3b base_3b; do
    model_path=""
    case $condition in
        base_15b)    model_path="bigcode/starcoder2-15b" ;;
        dpo_2k_15b)  model_path="$MODELS_DIR/dpo_2k_15b" ;;
        dpo_2k_3b)   model_path="$MODELS_DIR/dpo_2k_3b" ;;
        base_3b)     model_path="bigcode/starcoder2-3b" ;;
    esac

    echo ""
    echo "[MBPP] $condition..."
    CUDA_VISIBLE_DEVICES=0,1,2,3 $VENV -m experiments.rlvf_v2.evaluate_v2 \
        --model "$model_path" \
        --output "$RESULTS_DIR/${condition}_mbpp.json" \
        --benchmark mbpp \
        2>&1 | tee "$LOGS_DIR/eval_${condition}_mbpp.log"
    echo "  Done."
done

# ==========================================
# RESULTS SUMMARY
# ==========================================

echo ""
echo "============================================"
echo "  Phase 2 Complete!"
echo "  Finished: $(date)"
echo "============================================"
echo ""
echo "HumanEval Results:"
for f in "$RESULTS_DIR"/*humaneval*.json; do
    name=$(basename "$f" .json)
    passed=$($VENV -c "
import json
d = json.load(open('$f'))
he = d.get('humaneval', d)
print(f\"{he.get('passed', '?')}/{he.get('total_tasks', '?')} ({he.get('pass_rate_pct', '?')})\")
" 2>/dev/null || echo "parse error")
    echo "  $name: $passed"
done

echo ""
echo "MBPP Results:"
for f in "$RESULTS_DIR"/*mbpp*.json; do
    name=$(basename "$f" .json)
    passed=$($VENV -c "
import json
d = json.load(open('$f'))
mb = d.get('mbpp', d)
print(f\"{mb.get('passed', '?')}/{mb.get('total_tasks', '?')} ({mb.get('pass_rate_pct', '?')})\")
" 2>/dev/null || echo "parse error")
    echo "  $name: $passed"
done

echo ""
echo "Download results:"
echo "  scp -r ubuntu@\$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):~/rlvf_v2/results/ results/rlvf_v2/"
