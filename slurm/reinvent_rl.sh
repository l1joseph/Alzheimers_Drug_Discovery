#!/bin/bash
#SBATCH --job-name=reinvent-rl-boltz-phgdh
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=24:00:00
#
# REINVENT4 staged-learning RL run with Boltz-2 composite-reward scoring.
# This sbatch reserves only 1 node for REINVENT itself (it's CPU-bound on the
# head node, only needs 1 GPU for the prior model). For each RL step the
# ExternalProcess scorer (scripts/boltz_reward.py) launches a fresh nested
# sbatch via `sbatch --wait` against the cluster pool (1 node × 4 APUs per
# step), waits for it, then continues. Adds ~30s/step queue overhead but
# avoids the srun-in-allocation complexity.
#
# Tuning knobs:
#   batch_size : in configs/reinvent_rl_phgdh.toml ([parameters])
#   max_steps  : in configs/reinvent_rl_phgdh.toml ([[stage]])

set -euo pipefail

PROJECT=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery
SCRATCH=/cosmos/vast/scratch/l1joseph
mkdir -p "$SCRATCH/reinvent_rl"

ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"

module load rocm/6.3.0 2>&1 | tail -1 || true
source ~/miniforge3/etc/profile.d/conda.sh
conda activate reinvent-rocm

cd "$PROJECT"

echo "=== REINVENT RL start $(date) ==="
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
echo "SLURM_NNODES=$SLURM_NNODES"
echo "SLURM_JOB_NODELIST=$SLURM_JOB_NODELIST"
echo

# Sanity check: torch sees the APUs (REINVENT only needs 1 GPU on the head;
# the scorer uses the others)
python -c "import torch; print('cuda:', torch.cuda.is_available(), 'devices:', torch.cuda.device_count())"

# Pre-warm: reset the step counter that boltz_reward.py uses
rm -f "$SCRATCH/reinvent_rl_step.txt"

echo
echo "=== invoking reinvent ==="
reinvent -l "$PROJECT/logs/reinvent_internal_${SLURM_JOB_ID}.log" \
    "$PROJECT/configs/reinvent_rl_phgdh.toml"

echo "=== REINVENT RL done $(date) ==="
