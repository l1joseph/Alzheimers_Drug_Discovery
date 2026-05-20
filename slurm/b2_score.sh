#!/bin/bash
#SBATCH --job-name=boltz2-b2-score
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=03:00:00

set -euo pipefail
PROJECT=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery
SCRATCH=/cosmos/vast/scratch/l1joseph
BOLTZ_CACHE=$SCRATCH/boltz_cache
WORK=$SCRATCH/b2_score_$SLURM_JOB_ID
mkdir -p $BOLTZ_CACHE $WORK

ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"

module load rocm/6.3.0 2>&1 | tail -1
source ~/miniforge3/etc/profile.d/conda.sh
conda activate boltz-rocm

echo "=== B2 scoring (169 BI-4924 analogues) at $(date) ==="

cd $PROJECT
boltz predict $PROJECT/data/tamgen_b2_yamls --no_kernels \
  --cache $BOLTZ_CACHE --out_dir $WORK \
  --output_format mmcif --accelerator gpu --devices 1

mkdir -p $PROJECT/results/tamgen_b2
python $PROJECT/scripts/aggregate_boltz.py \
    --pred-dir $WORK \
    --out-csv $PROJECT/results/tamgen_b2/scores.csv

echo
echo "=== Combined top-20 (Round-0 known + R1 + R2 + B2) ==="
python3 << 'PY'
import csv
all_rows = []
def addrows(path, source):
    try:
        for r in csv.DictReader(open(path)):
            try: aff = float(r['affinity_affinity_pred_value'])
            except: continue
            all_rows.append({'id': r['input_id'], 'source': source,
                             'affinity_pred_value': aff,
                             'prob_binary': float(r['affinity_affinity_probability_binary']),
                             'confidence': float(r.get('confidence_confidence_score', 0))})
    except FileNotFoundError: pass
P = '/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery'
addrows(f'{P}/results/round0/baseline_scores.csv', 'round0_known')
addrows(f'{P}/results/tamgen_round1/scores.csv', 'tamgen_round1')
addrows(f'{P}/results/tamgen_round2/scores.csv', 'tamgen_round2')
addrows(f'{P}/results/tamgen_b2/scores.csv', 'tamgen_b2')
all_rows.sort(key=lambda r: r['affinity_pred_value'])
import os
os.makedirs(f'{P}/results/combined', exist_ok=True)
with open(f'{P}/results/combined/all_rounds.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['id','source','affinity_pred_value','prob_binary','confidence'])
    w.writeheader(); w.writerows(all_rows)
print(f"Total scored: {len(all_rows)}")
for r in all_rows[:25]:
    print(f"  {r['id']:10s} {r['source'][:14]:14s}  aff={r['affinity_pred_value']:+6.2f}  prob={r['prob_binary']:.2f}  conf={r['confidence']:.2f}")
PY
echo "=== Done at $(date) ==="
