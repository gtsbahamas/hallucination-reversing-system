#!/bin/bash
# Phase C: Run all 5 LUCID ablation studies sequentially
# Each ablation gets its own subdir to avoid cost tracker conflicts

set -e

cd /Users/tywells/Downloads/projects/hallucination-reversing-system
source experiments/.venv/bin/activate
export ANTHROPIC_API_KEY=$(security find-generic-password -s "claude-code" -a "anthropic-api-key" -w 2>/dev/null)

ABLATIONS="no-extract no-remediate learned-verify no-context random-verify"
BUDGET=175.0

for abl in $ABLATIONS; do
    echo ""
    echo "============================================================"
    echo "Phase C: Running ablation '$abl'"
    echo "============================================================"

    python3 -m experiments.humaneval.runner \
        --conditions lucid \
        --iterations 1 3 5 \
        --ablation "$abl" \
        --output "results/humaneval-c/" \
        --resume \
        --budget $BUDGET
done

echo ""
echo "============================================================"
echo "Phase C COMPLETE: All ablations finished"
echo "============================================================"
