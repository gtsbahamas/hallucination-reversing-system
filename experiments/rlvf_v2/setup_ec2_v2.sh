#!/bin/bash
# EC2 Setup for RLVF v2 Scaling Experiment
# Run on g5.12xlarge (4x A10G, 96GB VRAM, 192GB RAM)
# Deep Learning AMI (PyTorch) on Ubuntu

set -euo pipefail

echo "============================================"
echo "  RLVF v2 EC2 Setup"
echo "============================================"

# 1. Install Python dependencies
echo ""
echo "[1/5] Installing Python dependencies..."
pip install --upgrade pip
pip install \
    transformers>=4.45.0 \
    peft>=0.13.0 \
    trl>=0.12.0 \
    bitsandbytes>=0.44.0 \
    datasets>=3.0.0 \
    accelerate>=1.0.0 \
    scipy \
    numpy \
    matplotlib \
    tqdm \
    anthropic

echo "  Dependencies installed."

# 2. Pre-download models
echo ""
echo "[2/5] Pre-downloading models..."
python3 -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

print('Downloading StarCoder2-3B tokenizer + config...')
AutoTokenizer.from_pretrained('bigcode/starcoder2-3b', trust_remote_code=True)
print('  Done.')

print('Downloading StarCoder2-15B tokenizer + config...')
AutoTokenizer.from_pretrained('bigcode/starcoder2-15b', trust_remote_code=True)
print('  Done.')

print('Downloading StarCoder2-3B model weights (~6GB)...')
AutoModelForCausalLM.from_pretrained(
    'bigcode/starcoder2-3b',
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
    device_map='cpu',
)
print('  Done.')

print('Downloading StarCoder2-15B model weights (~30GB)...')
AutoModelForCausalLM.from_pretrained(
    'bigcode/starcoder2-15b',
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
    device_map='cpu',
)
print('  Done.')
"

echo "  Models cached."

# 3. Pre-download datasets
echo ""
echo "[3/5] Pre-downloading datasets..."
python3 -c "
from datasets import load_dataset
print('Downloading MBPP...')
load_dataset('google-research-datasets/mbpp', split='train')
print('  Done.')
"

echo "  Datasets cached."

# 4. Verify GPU setup
echo ""
echo "[4/5] Verifying GPU setup..."
python3 -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU count: {torch.cuda.device_count()}')
for i in range(torch.cuda.device_count()):
    props = torch.cuda.get_device_properties(i)
    print(f'  GPU {i}: {props.name} ({props.total_mem / 1e9:.1f} GB)')
print(f'PyTorch version: {torch.__version__}')
"

# 5. Create working directories
echo ""
echo "[5/5] Creating working directories..."
mkdir -p ~/rlvf_v2/{models,results,data,logs}

echo ""
echo "============================================"
echo "  Setup complete!"
echo "  Upload training data to ~/rlvf_v2/data/"
echo "  Then run: bash run_phase2_ec2.sh"
echo "============================================"
