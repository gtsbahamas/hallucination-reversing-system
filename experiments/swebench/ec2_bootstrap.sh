#!/bin/bash
# EC2 Bootstrap for SWE-bench Re-Run
# Instance: c5.4xlarge, 200GB gp3, Amazon Linux 2023
set -euo pipefail

echo "=== SWE-bench EC2 Bootstrap ==="
echo "Started: $(date)"

# System packages
sudo dnf update -y
sudo dnf install -y docker git python3.11 python3.11-pip

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user
# Apply group immediately for this script
sudo chmod 666 /var/run/docker.sock

# Verify Docker
docker info | head -5
echo "Docker disk: $(df -h /var/lib/docker | tail -1)"

# Python environment
python3.11 -m pip install --user anthropic tqdm numpy matplotlib swebench datasets

# Clone the repo
cd /home/ec2-user
if [ ! -d "lucid" ]; then
    git clone https://github.com/gtsbahamas/hallucination-reversing-system.git lucid
fi
cd lucid

# Create output directory
mkdir -p results/swebench-v2

echo ""
echo "=== Bootstrap Complete ==="
echo "Docker: $(docker --version)"
echo "Python: $(python3.11 --version)"
echo "Disk free: $(df -h / | tail -1)"
echo ""
echo "Next: set ANTHROPIC_API_KEY and run:"
echo "  export ANTHROPIC_API_KEY='sk-...'"
echo "  nohup python3.11 -m experiments.swebench.runner \\"
echo "    --conditions baseline lucid \\"
echo "    --iterations 1 3 \\"
echo "    --output results/swebench-v2/ \\"
echo "    --resume --smart-skip \\"
echo "    > swebench_run.log 2>&1 &"
