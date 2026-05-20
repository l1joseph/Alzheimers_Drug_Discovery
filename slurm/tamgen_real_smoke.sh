#!/bin/bash
#SBATCH --job-name=tamgen-smoke-realgen
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=00:30:00

# Real TamGen generation smoke test: feed PHGDH 6CWA + pocket center → sample 20 SMILES.

set -euo pipefail

PROJECT="/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery"
SCRATCH="/cosmos/vast/scratch/l1joseph"
WORK="$SCRATCH/tamgen_smoke_$SLURM_JOB_ID"
mkdir -p "$WORK"

ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"

module load rocm/6.3.0 2>&1 | tail -3 || true
source ~/miniforge3/etc/profile.d/conda.sh
conda activate tamgen-rocm

echo "=== Environment ==="
echo "host: $(hostname)"
python -c "import torch; print('torch:', torch.__version__, 'cuda:', torch.cuda.is_available(), 'devices:', torch.cuda.device_count())"
echo

cd "$PROJECT/tools/TamGen"

echo "=== Step 1: Prepare PHGDH pocket data from 6CWA + pocket center ==="
# Copy our input CSV into scratch
cp "$PROJECT/tamgen_input.csv" "$WORK/input.csv"
python scripts/build_data/prepare_pdb_ids_center.py \
    "$WORK/input.csv" gen_6cwa \
    -o "$WORK/data" -t 10 2>&1 | tail -20

echo
echo "=== Step 2: Inspect prepared dataset ==="
ls -la "$WORK/data/" 2>&1
ls -la "$WORK/data/gen_6cwa/" 2>&1 | head -20 || echo "no gen_6cwa dir"

echo
echo "=== Step 3: Run TamGen sampling (20 candidates) ==="
mkdir -p "$WORK/out"
RAW_OUT="$WORK/out/raw_generation.txt"
SMILES_OUT="$PROJECT/results/smoke/tamgen_6cwa_samples.csv"
mkdir -p "$(dirname $SMILES_OUT)"

python generate.py \
    "$WORK/data" \
    -s tg -t m1 \
    --task translation_coord \
    --path checkpoints/crossdocked_model/checkpoint_best.pt \
    --gen-subset gen_6cwa \
    --beam 20 --nbest 20 --max-tokens 1024 \
    --seed 42 --sample-beta 1 \
    --use-src-coord \
    > "$RAW_OUT" 2>&1
echo "(generation done; tail of raw output:)"
tail -30 "$RAW_OUT"

echo
echo "=== Step 4: Format output → SMILES CSV ==="
python scripts/format_output.py "$RAW_OUT" "$SMILES_OUT"
echo "wrote: $SMILES_OUT"
echo "--- top of generated SMILES ---"
head -25 "$SMILES_OUT" 2>&1
echo "--- row count ---"
wc -l "$SMILES_OUT"

echo
echo "=== Done at $(date) ==="
