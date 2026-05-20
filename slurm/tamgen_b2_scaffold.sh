#!/bin/bash
#SBATCH --job-name=tamgen-b2-bi4924-scaffold
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=00:45:00

# Branch B2: scaffold-seeded TamGen using BI-4924 (K5K) as scaffold seed.
# Reads K5K SMILES from the curated library, augments via random traversal,
# runs scaffold-conditioned TamGen across 5 seeds in parallel (4-way HIP fan-out),
# dedupes against the parent.
set -euo pipefail

PROJECT=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery
SCRATCH=/cosmos/vast/scratch/l1joseph
WORK=$SCRATCH/tamgen_b2_$SLURM_JOB_ID
mkdir -p $WORK

ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"

module load rocm/6.3.0 2>&1 | tail -1
source ~/miniforge3/etc/profile.d/conda.sh
conda activate tamgen-rocm

cd $PROJECT/tools/TamGen

echo "=== Branch B2 scaffold seed: BI-4924 (K5K) ==="
SCAFFOLD_SMILES=$(awk -F, '$1=="K5K"{print $3}' $PROJECT/data/libraries/known_phgdh_binders.csv)
[ -z "$SCAFFOLD_SMILES" ] && { echo "ERROR: K5K row not found in known_phgdh_binders.csv"; exit 1; }
SCAFFOLD_FILE=$WORK/seed_bi4924.txt
python $PROJECT/scripts/augment_smiles.py --smiles "$SCAFFOLD_SMILES" --n 20 --out $SCAFFOLD_FILE
cat $SCAFFOLD_FILE

echo
echo "=== Build scaffold-conditional dataset ==="
python scripts/build_data/prepare_pdb_ids_center_scaffold.py \
    $PROJECT/tamgen_input.csv gen_6cwa_b2 \
    -o $WORK/data -t 10 \
    --scaffold-file $SCAFFOLD_FILE 2>&1 | tail -10

echo
echo "=== Generate scaffold-conditional samples (5 seeds × beam=20, 4-way APU fanout) ==="
ALL=$WORK/all_samples.csv
echo "test_id,seed,smiles,nlogP" > $ALL

run_seed() {
    local seed=$1
    local apu=$2
    local raw=$WORK/raw_seed${seed}.txt
    local csv=$WORK/smiles_seed${seed}.csv
    HIP_VISIBLE_DEVICES=$apu python generate.py \
        $WORK/data \
        -s tg -t m1 \
        --task translation_coord \
        --path checkpoints/crossdocked_model/checkpoint_best.pt \
        --gen-subset gen_6cwa_b2 \
        --beam 20 --nbest 20 --max-tokens 1024 \
        --seed $seed --sample-beta 1 \
        --use-src-coord --gen-vae > $raw 2>&1
    python scripts/format_output.py $raw $csv
    local n=$(tail -n +2 $csv | wc -l)
    echo "  seed $seed (APU $apu): $n SMILES"
    tail -n +2 $csv | awk -F, -v s=$seed '{print $1","s","$2","$3}' >> $ALL
}

SEEDS=(1 7 42 101 1729)
for i in "${!SEEDS[@]}"; do
    run_seed "${SEEDS[$i]}" "$((i % 4))" &
    (( (i + 1) % 4 == 0 )) && wait
done
wait

echo
echo "=== Dedupe + filter (exclude parent) ==="
mkdir -p $PROJECT/results/tamgen_b2
python $PROJECT/scripts/dedup_smiles.py \
    --in $ALL \
    --out $PROJECT/results/tamgen_b2/samples.csv \
    --exclude-smiles "$SCAFFOLD_SMILES"

echo "=== Done at $(date) ==="
