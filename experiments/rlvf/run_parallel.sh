#!/bin/bash
# RLVF Experiment — PARALLELIZED
# Uses all 8 GPUs by running training/eval conditions simultaneously
set -e
source /opt/pytorch/bin/activate
export ANTHROPIC_API_KEY="$(cat ~/rlvf/.env_key)"
cd ~/rlvf

echo "============================================================"
echo "  LUCID RLVF EXPERIMENT — PARALLEL MODE"
echo "  $(date)"
echo "  8x NVIDIA A10G (g5.48xlarge)"
echo "============================================================"

# Phase 1: Generate dataset (skip if already exists)
if [ -f "data/vanilla_train.jsonl" ] && [ -f "data/lucid_train.jsonl" ] && [ -f "data/dpo_pairs.jsonl" ]; then
    echo ""
    echo "▸ PHASE 1: SKIPPED — training data already exists"
    echo "  $(wc -l data/*.jsonl)"
    PHASE1_TIME=0
else
    echo ""
    echo "▸ PHASE 1: Generating training data (120 tasks × 2 conditions)..."
    echo "  Using 25 concurrent API calls"
    START=$(date +%s)
    python generate_dataset.py --tasks 120 --concurrent 25 --output-dir data
    PHASE1_TIME=$(($(date +%s) - START))
    echo "Phase 1 complete in ${PHASE1_TIME}s"
fi

# Phase 2: Train 3 conditions IN PARALLEL on separate GPUs
echo ""
echo "▸ PHASE 2: Training 3 conditions IN PARALLEL..."
echo "  Vanilla SFT  → GPUs 0,1"
echo "  LUCID SFT    → GPUs 2,3"
echo "  DPO          → GPUs 4,5,6,7"
START=$(date +%s)

# Launch all 3 training jobs simultaneously
CUDA_VISIBLE_DEVICES=0,1 python train.py \
    --dataset data/vanilla_train.jsonl \
    --output-dir models/vanilla \
    --mode sft --epochs 3 \
    > logs/train_vanilla.log 2>&1 &
PID_VANILLA=$!

CUDA_VISIBLE_DEVICES=2,3 python train.py \
    --dataset data/lucid_train.jsonl \
    --output-dir models/lucid \
    --mode sft --epochs 3 \
    > logs/train_lucid.log 2>&1 &
PID_LUCID=$!

CUDA_VISIBLE_DEVICES=4,5,6,7 python train.py \
    --dataset data/dpo_pairs.jsonl \
    --output-dir models/dpo \
    --mode dpo --epochs 1 \
    > logs/train_dpo.log 2>&1 &
PID_DPO=$!

echo "  PIDs: vanilla=$PID_VANILLA lucid=$PID_LUCID dpo=$PID_DPO"

# Wait for all training jobs
FAIL=0
wait $PID_VANILLA || { echo "  ERROR: Vanilla training failed!"; FAIL=1; }
echo "  Vanilla training done ($(tail -1 logs/train_vanilla.log))"
wait $PID_LUCID || { echo "  ERROR: LUCID training failed!"; FAIL=1; }
echo "  LUCID training done ($(tail -1 logs/train_lucid.log))"
wait $PID_DPO || { echo "  ERROR: DPO training failed!"; FAIL=1; }
echo "  DPO training done ($(tail -1 logs/train_dpo.log))"

PHASE2_TIME=$(($(date +%s) - START))
echo "Phase 2 complete in ${PHASE2_TIME}s"

if [ $FAIL -ne 0 ]; then
    echo "WARNING: Some training jobs failed. Check logs/train_*.log"
fi

# Phase 3: Evaluate 4 models IN PARALLEL on separate GPUs
echo ""
echo "▸ PHASE 3: Evaluating 4 models IN PARALLEL..."
echo "  Base       → GPU 0,1"
echo "  Vanilla    → GPU 2,3"
echo "  LUCID      → GPU 4,5"
echo "  DPO        → GPU 6,7"
START=$(date +%s)

mkdir -p results

CUDA_VISIBLE_DEVICES=0,1 python evaluate.py \
    --model bigcode/starcoder2-3b \
    --output results/base_eval.json \
    > logs/eval_base.log 2>&1 &
PID_BASE=$!

CUDA_VISIBLE_DEVICES=2,3 python evaluate.py \
    --model models/vanilla \
    --output results/vanilla_eval.json \
    > logs/eval_vanilla.log 2>&1 &
PID_EVAL_V=$!

CUDA_VISIBLE_DEVICES=4,5 python evaluate.py \
    --model models/lucid \
    --output results/lucid_eval.json \
    > logs/eval_lucid.log 2>&1 &
PID_EVAL_L=$!

CUDA_VISIBLE_DEVICES=6,7 python evaluate.py \
    --model models/dpo \
    --output results/dpo_eval.json \
    > logs/eval_dpo.log 2>&1 &
PID_EVAL_D=$!

echo "  PIDs: base=$PID_BASE vanilla=$PID_EVAL_V lucid=$PID_EVAL_L dpo=$PID_EVAL_D"

# Wait for all evaluations
wait $PID_BASE || echo "  ERROR: Base eval failed!"
echo "  Base eval done"
wait $PID_EVAL_V || echo "  ERROR: Vanilla eval failed!"
echo "  Vanilla eval done"
wait $PID_EVAL_L || echo "  ERROR: LUCID eval failed!"
echo "  LUCID eval done"
wait $PID_EVAL_D || echo "  ERROR: DPO eval failed!"
echo "  DPO eval done"

PHASE3_TIME=$(($(date +%s) - START))
echo "Phase 3 complete in ${PHASE3_TIME}s"

# Summary
echo ""
echo "============================================================"
echo "  RESULTS"
echo "============================================================"
python -c "
import json
conditions = [
    ('Base StarCoder2-3B', 'results/base_eval.json'),
    ('Vanilla Fine-tuned', 'results/vanilla_eval.json'),
    ('LUCID Fine-tuned', 'results/lucid_eval.json'),
    ('DPO (LUCID pref)', 'results/dpo_eval.json'),
]
base_rate = None
for name, path in conditions:
    try:
        with open(path) as f:
            d = json.load(f)
        rate = d['pass_rate']
        if base_rate is None:
            base_rate = rate
            delta = ''
        else:
            rel = ((rate - base_rate) / base_rate * 100) if base_rate > 0 else 0
            delta = f'  ({rel:+.1f}% rel)'
        print(f'{name:<25} {d[\"passed\"]:>4}/{d[\"total_tasks\"]} ({d[\"pass_rate_pct\"]}){delta}')
    except:
        print(f'{name:<25} N/A')
"

echo ""
echo "============================================================"
echo "  TIMING"
echo "============================================================"
echo "  Phase 1 (data gen):  ${PHASE1_TIME}s"
echo "  Phase 2 (training):  ${PHASE2_TIME}s"
echo "  Phase 3 (eval):      ${PHASE3_TIME}s"
TOTAL=$((PHASE1_TIME + PHASE2_TIME + PHASE3_TIME))
echo "  TOTAL:               ${TOTAL}s ($((TOTAL/60))m)"
echo ""
echo "EXPERIMENT COMPLETE — $(date)"
