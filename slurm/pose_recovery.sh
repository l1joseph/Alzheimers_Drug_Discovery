#!/bin/bash
#SBATCH --job-name=boltz2-pose-recovery
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=02:00:00

# Pose-recovery validation: dock 5 known PHGDH-ligand pairs with Boltz-2, compare to crystal poses.
set -euo pipefail

PROJECT="/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery"
SCRATCH="/cosmos/vast/scratch/l1joseph"
BOLTZ_CACHE="$SCRATCH/boltz_cache"
WORK="$SCRATCH/pose_recovery_$SLURM_JOB_ID"
mkdir -p "$BOLTZ_CACHE" "$WORK"

ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"

module load rocm/6.3.0 2>&1 | tail -3 || true
source ~/miniforge3/etc/profile.d/conda.sh
conda activate boltz-rocm

echo "=== Pose recovery on $(hostname) at $(date) ==="
python -c "import torch; print('cuda:', torch.cuda.is_available(), 'devices:', torch.cuda.device_count())"

cd "$PROJECT/tools/boltz"
boltz predict "$PROJECT/data/pose_recovery_inputs" \
     \
    --no_kernels \
    --cache "$BOLTZ_CACHE" \
    --out_dir "$WORK" \
    --output_format mmcif \
    --accelerator gpu \
    --devices 1 \
    2>&1

echo
echo "=== Computing pose RMSDs ==="
python "$PROJECT/scripts/pose_rmsd.py" --pred-dir "$WORK"

echo
echo "=== Done at $(date) ==="
