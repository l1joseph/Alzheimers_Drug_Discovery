#!/bin/bash
#SBATCH --job-name=tamgen-round2-multiseed
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=00:30:00

# TamGen Round-2: multi-seed generation against PHGDH pocket for more diversity.
set -euo pipefail
PROJECT=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery
SCRATCH=/cosmos/vast/scratch/l1joseph
WORK=$SCRATCH/tamgen_round2_$SLURM_JOB_ID
mkdir -p $WORK

ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"

module load rocm/6.3.0 2>&1 | tail -1
source ~/miniforge3/etc/profile.d/conda.sh
conda activate tamgen-rocm

cd $PROJECT/tools/TamGen

# Reuse Round-1 prepared dataset (already binarised for PHGDH 6CWA pocket)
DATAPATH=$SCRATCH/tamgen_smoke_85052/data   # same pocket center, reusing
[ ! -d $DATAPATH ] && {
  echo "preparing dataset (previous binarised data missing)"
  cp $PROJECT/tamgen_input.csv $WORK/input.csv
  python scripts/build_data/prepare_pdb_ids_center.py $WORK/input.csv gen_6cwa -o $WORK/data -t 10
  DATAPATH=$WORK/data
}

mkdir -p $WORK/out
ALL=$WORK/out/all_samples.csv
echo "test_id,seed,smiles,nlogP" > $ALL

# Generate with 5 different seeds, beam=20 each → up to 100 SMILES (dedup later)
for SEED in 1 7 42 101 1729; do
  RAW=$WORK/out/raw_seed${SEED}.txt
  CSV=$WORK/out/smiles_seed${SEED}.csv
  echo "=== seed $SEED ==="
  python generate.py \
    $DATAPATH \
    -s tg -t m1 \
    --task translation_coord \
    --path checkpoints/crossdocked_model/checkpoint_best.pt \
    --gen-subset gen_6cwa \
    --beam 20 --nbest 20 --max-tokens 1024 \
    --seed $SEED --sample-beta 1 \
    --use-src-coord > $RAW 2>&1
  python scripts/format_output.py $RAW $CSV
  # Append rows (skip header), prefix with seed
  tail -n +2 $CSV | awk -F, -v s=$SEED '{print $1","s","$2","$3}' >> $ALL
  echo "  seed $SEED: $(tail -n +2 $CSV | wc -l) SMILES"
done

# Final dedup by canonical SMILES
python3 << EOF
import csv
from rdkit import Chem
rows = list(csv.DictReader(open("$ALL")))
print(f"\\n=== total samples: {len(rows)} ===")
seen = set()
out = []
for r in rows:
    mol = Chem.MolFromSmiles(r['smiles'])
    if mol is None: continue
    canon = Chem.MolToSmiles(mol)
    if canon in seen: continue
    seen.add(canon)
    r['canonical_smiles'] = canon
    out.append(r)
print(f"unique canonical: {len(out)}")

import os
os.makedirs("$PROJECT/results/tamgen_round2", exist_ok=True)
with open("$PROJECT/results/tamgen_round2/samples.csv", "w") as f:
    w = csv.DictWriter(f, fieldnames=['test_id','seed','smiles','canonical_smiles','nlogP'])
    w.writeheader(); w.writerows(out)
print(f"wrote $PROJECT/results/tamgen_round2/samples.csv")
EOF
echo "=== Done at $(date) ==="
