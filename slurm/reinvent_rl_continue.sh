#!/bin/bash
#SBATCH --job-name=reinvent-rl-boltz-phgdh-continue
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=24:00:00
#
# Continuation of the original Block D RL run. Resumes from
# /cosmos/vast/scratch/l1joseph/reinvent_rl/stage1.chkpt produced when
# the first job hit max_steps. Submit only after the original job exits.

set -euo pipefail

PROJECT=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery
SCRATCH=/cosmos/vast/scratch/l1joseph

# Sanity: refuse to start if the chkpt isn't there yet
CHKPT=$SCRATCH/reinvent_rl/stage1.chkpt
if [ ! -f "$CHKPT" ]; then
    echo "ERROR: stage1 chkpt not found at $CHKPT — original RL run hasn't finished?"
    exit 2
fi

ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"

module load rocm/6.3.0 2>&1 | tail -1 || true
source ~/miniforge3/etc/profile.d/conda.sh
conda activate reinvent-rocm

cd "$PROJECT"

echo "=== REINVENT RL continuation start $(date) ==="
echo "SLURM_JOB_ID=$SLURM_JOB_ID  resuming from $CHKPT"
python -c "import torch; print('cuda:', torch.cuda.is_available(), 'devices:', torch.cuda.device_count())"

# Continue the per-step counter — DO NOT reset
echo
echo "=== invoking reinvent (continuation) ==="
reinvent -l "$PROJECT/logs/reinvent_internal_continue_${SLURM_JOB_ID}.log" \
    "$PROJECT/configs/reinvent_rl_phgdh_continue.toml"

echo "=== REINVENT RL continuation done $(date) ==="
