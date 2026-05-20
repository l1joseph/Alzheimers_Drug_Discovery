#!/bin/bash
#SBATCH --job-name=tamgen-b2-round2
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=00:45:00

# Iterative Round-2: top-10 B2 hits + their 5-augmented variants as scaffold seeds.
set -euo pipefail
PROJECT=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery
SCRATCH=/cosmos/vast/scratch/l1joseph
WORK=$SCRATCH/tamgen_b2_round2_$SLURM_JOB_ID
mkdir -p $WORK
ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.out"
ln -sf "${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${SLURM_JOB_ID}.err"
module load rocm/6.3.0 2>&1 | tail -1
source ~/miniforge3/etc/profile.d/conda.sh
conda activate tamgen-rocm
cd $PROJECT/tools/TamGen
SCAFFOLD_FILE=$WORK/seeds.txt
# Augment each seed 5x for diversity (unquoted heredoc → $PROJECT/$SCAFFOLD_FILE expand)
python3 << PYEOF2
from rdkit import Chem
seeds = open("$PROJECT/data/round2_b2_seeds.txt").read().splitlines()
out = set()
for smi in seeds:
    m = Chem.MolFromSmiles(smi)
    if m is None: continue
    out.add(Chem.MolToSmiles(m, canonical=True))
    for _ in range(5):
        out.add(Chem.MolToSmiles(m, doRandom=True, canonical=False))
with open("$SCAFFOLD_FILE", "w") as f:
    for s in out: f.write(s + "\n")
print(f"wrote {len(out)} augmented seeds")
PYEOF2
python scripts/build_data/prepare_pdb_ids_center_scaffold.py \
    $PROJECT/tamgen_input.csv gen_6cwa_r2b2 \
    -o $WORK/data -t 10 --scaffold-file $SCAFFOLD_FILE 2>&1 | tail -5
ALL=$WORK/all_samples.csv
echo "test_id,seed,smiles,nlogP" > $ALL
run_seed() {
    local seed=$1 apu=$2
    local raw=$WORK/raw_seed${seed}.txt csv=$WORK/smiles_seed${seed}.csv
    HIP_VISIBLE_DEVICES=$apu python generate.py $WORK/data \
        -s tg -t m1 --task translation_coord \
        --path checkpoints/crossdocked_model/checkpoint_best.pt \
        --gen-subset gen_6cwa_r2b2 \
        --beam 20 --nbest 20 --max-tokens 1024 \
        --seed $seed --sample-beta 1 \
        --use-src-coord --gen-vae > $raw 2>&1
    python scripts/format_output.py $raw $csv
    echo "  seed $seed (APU $apu): $(tail -n +2 $csv | wc -l) SMILES"
    tail -n +2 $csv | awk -F, -v s=$seed '{print $1","s","$2","$3}' >> $ALL
}
SEEDS=(1 7 42 101 1729)
for i in "${!SEEDS[@]}"; do
    run_seed "${SEEDS[$i]}" "$((i % 4))" &
    (( (i + 1) % 4 == 0 )) && wait
done
wait
mkdir -p $PROJECT/results/tamgen_b2_round2
# Exclude all 10 round-1 b2 parents from the new round's output
python $PROJECT/scripts/dedup_smiles.py --in $ALL --out $PROJECT/results/tamgen_b2_round2/samples.csv
echo "=== Done at $(date) ==="
