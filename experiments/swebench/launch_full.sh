#!/bin/bash
# Full SWE-bench 300-task run with parallel runners + smart skipping.
#
# Usage:
#   ./experiments/swebench/launch_full.sh          # Default: 4 chunks, $750/chunk budget
#   ./experiments/swebench/launch_full.sh --dry-run # Print commands without executing
#   ./experiments/swebench/launch_full.sh --chunks 2 # Use 2 chunks instead of 4
#
# Monitoring:
#   tail -f /tmp/swebench-chunk-*.log              # Watch all chunks
#   ./experiments/swebench/launch_full.sh --status  # Summary of results so far

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_DIR"

# Configuration
DOCKER_HOST="unix:///Users/tywells/.colima/default/docker.sock"
export DOCKER_HOST
VENV="$PROJECT_DIR/experiments/.venv"
OUTPUT_DIR="results/swebench"
TOTAL_TASKS=300
NUM_CHUNKS=4
BUDGET_PER_CHUNK=750
CONDITIONS="baseline lucid"
ITERATIONS="1 3"
DRY_RUN=false
STATUS_ONLY=false

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --status) STATUS_ONLY=true; shift ;;
        --chunks) NUM_CHUNKS="$2"; shift 2 ;;
        --budget) BUDGET_PER_CHUNK="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

# --- Status mode ---
if $STATUS_ONLY; then
    echo "=== SWE-bench Full Run Status ==="
    echo ""

    # Count result files
    TOTAL_FILES=$(ls "$OUTPUT_DIR"/*.json 2>/dev/null | grep -v cost_tracker | wc -l | tr -d ' ')
    BASELINE=$(ls "$OUTPUT_DIR"/*_baseline_k1.json 2>/dev/null | wc -l | tr -d ' ')
    LUCID_K1=$(ls "$OUTPUT_DIR"/*_lucid_k1.json 2>/dev/null | wc -l | tr -d ' ')
    LUCID_K3=$(ls "$OUTPUT_DIR"/*_lucid_k3.json 2>/dev/null | wc -l | tr -d ' ')

    echo "Result files: $TOTAL_FILES"
    echo "  Baseline k=1: $BASELINE / $TOTAL_TASKS"
    echo "  LUCID k=1:    $LUCID_K1 / $TOTAL_TASKS"
    echo "  LUCID k=3:    $LUCID_K3 / $TOTAL_TASKS (minus smart-skipped)"
    echo ""

    # Count pass/fail
    BASELINE_PASS=$(grep -l '"final_passed": true' "$OUTPUT_DIR"/*_baseline_k1.json 2>/dev/null | wc -l | tr -d ' ')
    LUCID_K1_PASS=$(grep -l '"final_passed": true' "$OUTPUT_DIR"/*_lucid_k1.json 2>/dev/null | wc -l | tr -d ' ')
    LUCID_K3_PASS=$(grep -l '"final_passed": true' "$OUTPUT_DIR"/*_lucid_k3.json 2>/dev/null | wc -l | tr -d ' ')

    echo "Pass rates:"
    [ "$BASELINE" -gt 0 ] && echo "  Baseline k=1: $BASELINE_PASS / $BASELINE ($(( BASELINE_PASS * 100 / BASELINE ))%)" || echo "  Baseline k=1: no data"
    [ "$LUCID_K1" -gt 0 ] && echo "  LUCID k=1:    $LUCID_K1_PASS / $LUCID_K1 ($(( LUCID_K1_PASS * 100 / LUCID_K1 ))%)" || echo "  LUCID k=1:    no data"
    [ "$LUCID_K3" -gt 0 ] && echo "  LUCID k=3:    $LUCID_K3_PASS / $LUCID_K3 ($(( LUCID_K3_PASS * 100 / LUCID_K3 ))%)" || echo "  LUCID k=3:    no data"
    echo ""

    # Cost trackers
    echo "Cost per chunk:"
    for f in "$OUTPUT_DIR"/cost_tracker*.json; do
        if [ -f "$f" ]; then
            COST=$(python3 -c "import json; d=json.load(open('$f')); print(f'\${d.get(\"total_cost\", 0):.2f}')" 2>/dev/null || echo "?")
            echo "  $(basename "$f"): $COST"
        fi
    done
    echo ""

    # Running processes
    echo "Running processes:"
    ps aux | grep "experiments.swebench.runner" | grep -v grep || echo "  (none)"
    exit 0
fi

# --- Pre-flight checks ---
echo "=== SWE-bench Full Run Launcher ==="
echo ""
echo "Configuration:"
echo "  Tasks: $TOTAL_TASKS"
echo "  Chunks: $NUM_CHUNKS"
echo "  Budget/chunk: \$$BUDGET_PER_CHUNK"
echo "  Total budget: \$$(( BUDGET_PER_CHUNK * NUM_CHUNKS ))"
echo "  Conditions: $CONDITIONS"
echo "  Iterations: $ITERATIONS"
echo "  Output: $OUTPUT_DIR"
echo "  Smart skip: enabled"
echo ""

# Check API key
API_KEY=$(security find-generic-password -s "claude-code" -a "anthropic-api-key" -w 2>/dev/null || true)
if [ -z "$API_KEY" ]; then
    echo "ERROR: No API key found in keychain"
    exit 1
fi
export ANTHROPIC_API_KEY="$API_KEY"

# Check venv
if [ ! -d "$VENV" ]; then
    echo "ERROR: Venv not found at $VENV"
    exit 1
fi

# Check Colima
if ! colima status &>/dev/null; then
    echo "Colima is not running. Starting with 8 CPU / 16GB..."
    colima start --cpu 8 --memory 16 --disk 60
else
    CPUS=$(colima list -o json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)[0].get('cpus', '?'))" 2>/dev/null || echo "?")
    MEM=$(colima list -o json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)[0].get('memory', '?'))" 2>/dev/null || echo "?")
    echo "Colima running: ${CPUS} CPUs, ${MEM} memory"
    if [ "$CPUS" != "?" ] && [ "$CPUS" -lt 8 ]; then
        echo ""
        echo "WARNING: Colima has only $CPUS CPUs. Recommended: 8"
        echo "To boost: colima stop && colima start --cpu 8 --memory 16 --disk 60"
        echo "Continuing with current resources..."
    fi
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Calculate chunk sizes
CHUNK_SIZE=$(( TOTAL_TASKS / NUM_CHUNKS ))
REMAINDER=$(( TOTAL_TASKS % NUM_CHUNKS ))

echo ""
echo "Chunk breakdown:"
OFFSET=0
for i in $(seq 1 "$NUM_CHUNKS"); do
    SIZE=$CHUNK_SIZE
    if [ "$i" -le "$REMAINDER" ]; then
        SIZE=$(( SIZE + 1 ))
    fi
    echo "  Chunk $i: tasks[$OFFSET:$((OFFSET + SIZE))] ($SIZE tasks)"
    OFFSET=$((OFFSET + SIZE))
done

if $DRY_RUN; then
    echo ""
    echo "=== DRY RUN — Commands that would be executed ==="
    OFFSET=0
    for i in $(seq 1 "$NUM_CHUNKS"); do
        SIZE=$CHUNK_SIZE
        if [ "$i" -le "$REMAINDER" ]; then
            SIZE=$(( SIZE + 1 ))
        fi
        echo ""
        echo "# Chunk $i:"
        echo "nohup $VENV/bin/python -m experiments.swebench.runner \\"
        echo "  --conditions $CONDITIONS \\"
        echo "  --iterations $ITERATIONS \\"
        echo "  --output $OUTPUT_DIR \\"
        echo "  --offset $OFFSET --limit $SIZE \\"
        echo "  --resume --smart-skip \\"
        echo "  --budget $BUDGET_PER_CHUNK \\"
        echo "  --chunk-id chunk$i \\"
        echo "  > /tmp/swebench-chunk-$i.log 2>&1 &"
        OFFSET=$((OFFSET + SIZE))
    done
    echo ""
    echo "Would launch $NUM_CHUNKS processes."
    exit 0
fi

# --- Launch parallel runners ---
echo ""
echo "Launching $NUM_CHUNKS parallel runners..."
PIDS=()
OFFSET=0
for i in $(seq 1 "$NUM_CHUNKS"); do
    SIZE=$CHUNK_SIZE
    if [ "$i" -le "$REMAINDER" ]; then
        SIZE=$(( SIZE + 1 ))
    fi

    LOG="/tmp/swebench-chunk-$i.log"
    echo "  Chunk $i: offset=$OFFSET limit=$SIZE -> $LOG"

    nohup "$VENV/bin/python" -m experiments.swebench.runner \
        --conditions $CONDITIONS \
        --iterations $ITERATIONS \
        --output "$OUTPUT_DIR" \
        --offset "$OFFSET" --limit "$SIZE" \
        --resume --smart-skip \
        --budget "$BUDGET_PER_CHUNK" \
        --chunk-id "chunk$i" \
        > "$LOG" 2>&1 &

    PIDS+=($!)
    OFFSET=$((OFFSET + SIZE))
done

echo ""
echo "All $NUM_CHUNKS runners launched."
echo ""
echo "PIDs: ${PIDS[*]}"
echo ""
echo "=== Monitoring Commands ==="
echo "  tail -f /tmp/swebench-chunk-*.log          # Watch all output"
echo "  tail -1 /tmp/swebench-chunk-{1,2,3,4}.log  # Latest line per chunk"
echo "  $0 --status                                 # Results summary"
echo "  ps aux | grep swebench                      # Running processes"
echo "  kill ${PIDS[*]}                              # Stop all runners"
echo ""
echo "Estimated time: 6-10 hours with 4 chunks + smart skipping"
