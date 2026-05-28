#!/bin/bash
#SBATCH --job-name=tamgen-b4-k58-scaffold
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=00:45:00

# Branch B4: scaffold-seeded TamGen using K58 (compound 15 of Spillier et al. 2019)
# as the scaffold seed. K58 is the combined-selectivity-index winner from the
# off-target panels; this branch closes the gap where the original de novo
# design (B1 NCT-503, B2 BI-4924) never seeded from the eventual best compound.
# K58 is NAD-competitive, so it targets the same cofactor subsite as B2 (uses
# tamgen_input.csv, the catalytic/NAD pocket center).
set -euo pipefail

PROJECT=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery
SCRATCH=/cosmos/vast/scratch/l1joseph
WORK=$SCRATCH/tamgen_b4_$SLURM_JOB_ID
mkdir -p $WORK

ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"

module load rocm/6.3.0 2>&1 | tail -1
source ~/miniforge3/etc/profile.d/conda.sh
conda activate tamgen-rocm

cd $PROJECT/tools/TamGen

echo "=== Branch B4 scaffold seed: K58 (Spillier compound 15, BI-cmpd-15) ==="
SCAFFOLD_SMILES=$(awk -F, '$1=="K58"{print $3}' $PROJECT/data/libraries/known_phgdh_binders.csv)
[ -z "$SCAFFOLD_SMILES" ] && { echo "ERROR: K58 row not found in known_phgdh_binders.csv"; exit 1; }
SCAFFOLD_FILE=$WORK/seed_k58.txt
python $PROJECT/scripts/augment_smiles.py --smiles "$SCAFFOLD_SMILES" --n 20 --out $SCAFFOLD_FILE
cat $SCAFFOLD_FILE

echo
echo "=== Build scaffold-conditional dataset (NAD/catalytic pocket center) ==="
python scripts/build_data/prepare_pdb_ids_center_scaffold.py \
    $PROJECT/tamgen_input.csv gen_6cwa_b4 \
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
        --gen-subset gen_6cwa_b4 \
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
echo "=== Dedupe + filter (exclude parent K58) ==="
mkdir -p $PROJECT/results/tamgen_b4
python $PROJECT/scripts/dedup_smiles.py \
    --in $ALL \
    --out $PROJECT/results/tamgen_b4/samples.csv \
    --exclude-smiles "$SCAFFOLD_SMILES"

echo "=== Done at $(date) ==="
