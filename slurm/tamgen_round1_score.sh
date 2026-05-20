#!/bin/bash
#SBATCH --job-name=boltz2-tamgen-round1
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=01:00:00

set -euo pipefail
PROJECT=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery
SCRATCH=/cosmos/vast/scratch/l1joseph
BOLTZ_CACHE=$SCRATCH/boltz_cache
WORK=$SCRATCH/tamgen_round1_$SLURM_JOB_ID
mkdir -p $BOLTZ_CACHE $WORK

ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"

module load rocm/6.3.0 2>&1 | tail -1
source ~/miniforge3/etc/profile.d/conda.sh
conda activate boltz-rocm

echo "=== TamGen Round-1 scoring on $(hostname) at $(date) ==="
echo "n yamls: $(ls $PROJECT/data/tamgen_round1_yamls/*.yaml | wc -l)"

cd $PROJECT
boltz predict $PROJECT/data/tamgen_round1_yamls --no_kernels \
  --cache $BOLTZ_CACHE --out_dir $WORK \
  --output_format mmcif --accelerator gpu --devices 1

mkdir -p $PROJECT/results/tamgen_round1
python $PROJECT/scripts/aggregate_boltz.py \
    --pred-dir $WORK \
    --out-csv $PROJECT/results/tamgen_round1/scores.csv
echo
echo "=== Top 5 by affinity_pred_value (lower=better) ==="
python3 -c "
import csv
rows = list(csv.DictReader(open('$PROJECT/results/tamgen_round1/scores.csv')))
rows.sort(key=lambda r: float(r.get('affinity_affinity_pred_value', 999) or 999))
for r in rows[:10]:
    print(f'  {r[\"input_id\"]:10s} aff={r.get(\"affinity_affinity_pred_value\",\"?\"):>8.8s}  prob={r.get(\"affinity_affinity_probability_binary\",\"?\"):>6.6s}  conf={r.get(\"confidence_confidence_score\",\"?\"):>5.5s}')
"
echo "=== Done at $(date) ==="
