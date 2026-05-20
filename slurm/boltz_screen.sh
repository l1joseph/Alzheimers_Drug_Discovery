#!/bin/bash
#SBATCH --job-name=boltz2-screen
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=06:00:00

# Run Boltz-2 affinity scoring over a directory of YAML inputs.
# Usage: sbatch --job-name=<custom> slurm/boltz_screen.sh <yaml_dir> <run_label>
#   yaml_dir:  directory of *.yaml input files (one per ligand)
#   run_label: short label, used in scratch path and `results/<label>/scores.csv`
#
# After scoring, calls scripts/build_leaderboard.py to merge with all other
# completed branches (with flock to avoid race when concurrent jobs finish).

set -euo pipefail

YAML_DIR="${1:?need yaml_dir as arg 1}"
RUN_LABEL="${2:?need run_label as arg 2}"

PROJECT="/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery"
SCRATCH="/cosmos/vast/scratch/l1joseph"
BOLTZ_CACHE="$SCRATCH/boltz_cache"
WORK_OUT="$SCRATCH/runs/boltz_${RUN_LABEL}_${SLURM_JOB_ID}"
mkdir -p "$BOLTZ_CACHE" "$WORK_OUT"

ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"

module load rocm/6.3.0 2>&1 | tail -3 || true
source ~/miniforge3/etc/profile.d/conda.sh
conda activate boltz-rocm

echo "=== $(date) start: $RUN_LABEL ==="
echo "yaml_dir: $YAML_DIR"
echo "n yamls : $(ls $YAML_DIR/*.yaml 2>/dev/null | wc -l)"
python -c "import torch; print('cuda:', torch.cuda.is_available(), 'devices:', torch.cuda.device_count())"
echo

cd "$PROJECT/tools/boltz"
boltz predict "$YAML_DIR" \
    --use_msa_server \
    --no_kernels \
    --cache "$BOLTZ_CACHE" \
    --out_dir "$WORK_OUT" \
    --output_format mmcif \
    --accelerator gpu \
    --devices 1 \
    2>&1

echo
echo "=== Aggregating affinity scores ==="
mkdir -p "$PROJECT/results/$RUN_LABEL"
python "$PROJECT/scripts/aggregate_boltz.py" \
    --pred-dir "$WORK_OUT" \
    --out-csv "$PROJECT/results/$RUN_LABEL/scores.csv"

echo
echo "=== Rebuilding combined leaderboard (flock-guarded) ==="
python "$PROJECT/scripts/build_leaderboard.py"

echo "=== Done at $(date) ==="
