#!/bin/bash
# Phase 1: Data Generation (runs locally)
# Generates DPO pairs from MBPP tasks using Claude Haiku + local test verification
#
# Prerequisites:
#   - ANTHROPIC_API_KEY set in environment
#   - Python venv at experiments/.venv activated
#
# Usage:
#   cd /path/to/hallucination-reversing-system
#   source experiments/.venv/bin/activate
#   bash experiments/rlvf_v2/run_phase1_local.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

DATA_DIR="data/rlvf_v2"
mkdir -p "$DATA_DIR"

echo "============================================"
echo "  RLVF v2 Phase 1: Data Generation"
echo "============================================"
echo "  Project root: $PROJECT_ROOT"
echo "  Output: $DATA_DIR/"
echo ""

# Step 1: Download and verify MBPP dataset
echo "[Step 1] Downloading MBPP dataset..."
python3 -m experiments.rlvf_v2.mbpp_dataset
echo ""

# Step 2: Dry run for cost estimate
echo "[Step 2] Cost estimate..."
python3 -m experiments.rlvf_v2.generate_pairs --dry-run
echo ""

read -p "Proceed with generation? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Step 3: Generate candidates (with resume support)
echo "[Step 3] Generating candidates..."
python3 -m experiments.rlvf_v2.generate_pairs \
    --output "$DATA_DIR" \
    --resume \
    --budget 50.0

echo ""

# Step 4: Select DPO pairs
echo "[Step 4] Selecting DPO pairs..."
python3 -m experiments.rlvf_v2.pair_selector \
    --candidates "$DATA_DIR/candidates.jsonl" \
    --output-dir "$DATA_DIR" \
    --spot-check 50

echo ""
echo "============================================"
echo "  Phase 1 Complete!"
echo "  Files in $DATA_DIR/:"
ls -lh "$DATA_DIR"/*.jsonl 2>/dev/null || echo "  (no files yet)"
echo ""
echo "  Next: Upload data to EC2 and run Phase 2"
echo "  scp $DATA_DIR/dpo_pairs_*.jsonl ec2-user@<IP>:~/rlvf_v2/data/"
echo "============================================"
