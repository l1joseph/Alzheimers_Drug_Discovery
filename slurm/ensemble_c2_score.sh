#!/bin/bash
#SBATCH --job-name=boltz2-ensemble-c2
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=02:00:00
set -euo pipefail
PROJECT=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery
SCRATCH=/cosmos/vast/scratch/l1joseph
WORK=$SCRATCH/ensemble_c2_$SLURM_JOB_ID
mkdir -p $WORK
ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"
module load rocm/6.3.0 2>&1 | tail -1
source ~/miniforge3/etc/profile.d/conda.sh
conda activate boltz-rocm
echo "=== Ensemble C2 (top-50 druglike + 3PG co-ligand) at $(date) ==="
cd $PROJECT
boltz predict $PROJECT/data/ensemble_c2_yamls --no_kernels \
  --cache $SCRATCH/boltz_cache --out_dir $WORK \
  --output_format mmcif --accelerator gpu --devices 1
mkdir -p $PROJECT/results/ensemble_c2
python $PROJECT/scripts/aggregate_boltz.py --pred-dir $WORK \
    --out-csv $PROJECT/results/ensemble_c2/scores.csv
echo "=== Done at $(date) ==="
