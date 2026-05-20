#!/bin/bash
#SBATCH --job-name=boltz2-round0-baseline
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=01:00:00

set -euo pipefail

PROJECT=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery
SCRATCH=/cosmos/vast/scratch/l1joseph
BOLTZ_CACHE=$SCRATCH/boltz_cache
WORK=$SCRATCH/round0_$SLURM_JOB_ID
mkdir -p $BOLTZ_CACHE $WORK

ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"

module load rocm/6.3.0 2>&1 | tail -1
source ~/miniforge3/etc/profile.d/conda.sh
conda activate boltz-rocm

echo "=== Round-0 baseline on $(hostname) at $(date) ==="
python -c "import torch; print('cuda:', torch.cuda.is_available(), 'devices:', torch.cuda.device_count())"
echo "yaml count: $(ls $PROJECT/data/round0_yamls/*.yaml | wc -l)"

cd $PROJECT
boltz predict $PROJECT/data/round0_yamls --no_kernels \
  --cache $BOLTZ_CACHE --out_dir $WORK \
  --output_format mmcif --accelerator gpu --devices 1

echo
echo "=== Aggregating affinity ==="
mkdir -p $PROJECT/results/round0
python $PROJECT/scripts/aggregate_boltz.py \
    --pred-dir $WORK \
    --out-csv $PROJECT/results/round0/baseline_scores.csv
echo
echo "=== Top results ==="
head -20 $PROJECT/results/round0/baseline_scores.csv
echo "=== Done at $(date) ==="
