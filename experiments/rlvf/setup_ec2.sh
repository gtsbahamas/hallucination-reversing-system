#!/bin/bash
# RLVF Experiment Setup for g5.48xlarge (Deep Learning AMI)
# Run this on the EC2 instance after SSH'ing in
set -e

echo "=== LUCID RLVF Experiment Setup ==="
echo "Instance: $(curl -s http://169.254.169.254/latest/meta-data/instance-type)"
echo "GPUs: $(nvidia-smi -L 2>/dev/null | wc -l)"

# Activate PyTorch environment (Deep Learning AMI)
source activate pytorch || conda activate pytorch || true

# Install required packages
echo "Installing Python packages..."
pip install -q --upgrade \
    anthropic \
    transformers \
    datasets \
    accelerate \
    peft \
    trl \
    bitsandbytes \
    scipy \
    sentencepiece \
    protobuf

# Verify GPU access
echo ""
echo "=== GPU Status ==="
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
echo ""

# Verify imports
echo "=== Verifying imports ==="
python -c "
import torch
import transformers
import peft
import trl
import bitsandbytes
import anthropic
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA devices: {torch.cuda.device_count()}')
print(f'Transformers: {transformers.__version__}')
print(f'PEFT: {peft.__version__}')
print(f'TRL: {trl.__version__}')
for i in range(torch.cuda.device_count()):
    print(f'  GPU {i}: {torch.cuda.get_device_name(i)} ({torch.cuda.get_device_properties(i).total_mem / 1e9:.1f}GB)')
"

# Pre-download the base model
echo ""
echo "=== Downloading StarCoder2-3B ==="
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
print('Downloading tokenizer...')
AutoTokenizer.from_pretrained('bigcode/starcoder2-3b', trust_remote_code=True)
print('Downloading model weights (this may take a few minutes)...')
AutoModelForCausalLM.from_pretrained('bigcode/starcoder2-3b', trust_remote_code=True, torch_dtype='auto')
print('Model cached successfully.')
"

echo ""
echo "=== Setup Complete ==="
echo "Ready for RLVF experiment."
echo ""
echo "Next steps:"
echo "  1. Upload experiment files: scp -i key.pem experiments/rlvf/*.py ubuntu@IP:~/rlvf/"
echo "  2. Export API key: export ANTHROPIC_API_KEY=sk-ant-..."
echo "  3. Generate dataset: python generate_dataset.py"
echo "  4. Train: python train.py --dataset data/lucid_train.jsonl --output-dir models/lucid"
echo "  5. Evaluate: python evaluate.py --model models/lucid --output results/lucid_eval.json"
