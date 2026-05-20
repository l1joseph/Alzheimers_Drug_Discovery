#!/bin/bash
#SBATCH --job-name=boltz2-smoke-affinity
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=01:00:00

set -euo pipefail

PROJECT="/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery"
SCRATCH="/cosmos/vast/scratch/l1joseph"
BOLTZ_CACHE="$SCRATCH/boltz_cache"
WORK_OUT="$SCRATCH/boltz_smoke_$SLURM_JOB_ID"
mkdir -p "$BOLTZ_CACHE" "$WORK_OUT"

# Symlink for chronological log searchability (per CLAUDE.md log discipline)
ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"

module load rocm/6.3.0 2>&1 | tail -3 || true

source ~/miniforge3/etc/profile.d/conda.sh
conda activate boltz-rocm

echo "=== Environment ==="
echo "hostname: $(hostname)"
echo "date: $(date)"
echo "rocm: $(ls -d /opt/rocm-* 2>/dev/null | head -1)"
echo "python: $(python --version)"
echo "PYTORCH_ROCM_ARCH=$PYTORCH_ROCM_ARCH"
echo
echo "=== GPU visibility ==="
rocm-smi --showproductname 2>&1 | head -20 || echo "rocm-smi unavailable"
python -c "
import torch
print('torch:', torch.__version__, 'hip:', torch.version.hip)
print('cuda_available:', torch.cuda.is_available())
print('device_count:', torch.cuda.device_count())
for i in range(torch.cuda.device_count()):
    print(f'  device {i}: {torch.cuda.get_device_name(i)}')
"
echo

echo "=== Boltz-2 affinity prediction on example ==="
cd "$PROJECT/tools/boltz"
# Use the example affinity.yaml from the repo. Outputs to scratch.
boltz predict examples/affinity.yaml \
    --use_msa_server \
    --cache "$BOLTZ_CACHE" \
    --out_dir "$WORK_OUT" \
    --output_format mmcif \
    --accelerator gpu \
    --devices 1 \
    2>&1 | tail -100

echo
echo "=== Outputs ==="
find "$WORK_OUT" -type f 2>/dev/null | head -20

# Copy small outputs to project results dir for inspection
mkdir -p "$PROJECT/results/smoke"
find "$WORK_OUT" -type f \( -name "*.json" -o -name "*.cif" -o -name "*.pdb" \) -size -10M -exec cp {} "$PROJECT/results/smoke/" \;
echo "copied outputs to $PROJECT/results/smoke/"
echo
echo "=== Done at $(date) ==="
