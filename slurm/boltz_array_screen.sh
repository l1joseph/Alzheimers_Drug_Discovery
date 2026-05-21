#!/bin/bash
#SBATCH --job-name=boltz2-array-screen
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%A_%a.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%A_%a.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=04:00:00
# Note: submit with --array=0-3 (or fewer) and pass YAML_SPLIT_DIR + RUN_LABEL
#
# Each array task gets one node (4 APUs) and processes 4 pre-split shards
# numbered (TASK*4 .. TASK*4 + 3), running 4 parallel Boltz processes
# (one per APU via HIP_VISIBLE_DEVICES) in the same pattern used by
# tamgen_b1_scaffold.sh.
#
# Usage:
#   1. Pre-split YAMLs:
#        python scripts/split_yamls.py \
#            --in data/libraries/chembl_yamls \
#            --out-base /cosmos/vast/scratch/l1joseph/chembl_yamls_split \
#            --n 16   # = NUM_TASKS * APUS_PER_NODE = 4*4
#   2. Submit array:
#        sbatch --array=0-3 \
#               --export=ALL,YAML_SPLIT_DIR=/cosmos/vast/scratch/l1joseph/chembl_yamls_split,RUN_LABEL=chembl \
#               slurm/boltz_array_screen.sh
#   3. Aggregate (after all tasks done):
#        python scripts/aggregate_boltz.py --pred-dir <scratch>/runs/boltz_chembl_${SLURM_ARRAY_JOB_ID} \
#                                          --out-csv results/chembl/scores.csv

set -euo pipefail

: "${YAML_SPLIT_DIR:?need YAML_SPLIT_DIR env var (output of split_yamls.py)}"
: "${RUN_LABEL:?need RUN_LABEL env var}"

PROJECT=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery
SCRATCH=/cosmos/vast/scratch/l1joseph
APUS_PER_NODE=4
BOLTZ_CACHE=$SCRATCH/boltz_cache
mkdir -p "$BOLTZ_CACHE"

TASK=$SLURM_ARRAY_TASK_ID
JOB=$SLURM_ARRAY_JOB_ID
WORK_BASE=$SCRATCH/runs/boltz_${RUN_LABEL}_${JOB}
mkdir -p "$WORK_BASE"

ts=$(date +%Y%m%d-%H%M%S)
ln -sf "${SLURM_JOB_NAME}_${JOB}_${TASK}.out" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${JOB}_${TASK}.out"
ln -sf "${SLURM_JOB_NAME}_${JOB}_${TASK}.err" "$PROJECT/logs/${ts}_${SLURM_JOB_NAME}_${JOB}_${TASK}.err"

module load rocm/6.3.0 2>&1 | tail -1 || true
source ~/miniforge3/etc/profile.d/conda.sh
conda activate boltz-rocm

echo "=== array task $TASK of job $JOB on $(hostname) at $(date) ==="
python -c "import torch; print('cuda:', torch.cuda.is_available(), 'devices:', torch.cuda.device_count())"

cd "$PROJECT/tools/boltz"

run_apu() {
    local apu=$1
    local shard_idx=$2
    local shard_dir="$YAML_SPLIT_DIR/shard_$(printf %02d $shard_idx)"
    local out_dir="$WORK_BASE/task${TASK}_apu${apu}"
    mkdir -p "$out_dir"
    if [ ! -d "$shard_dir" ]; then
        echo "  APU $apu: shard $shard_idx not found ($shard_dir); skipping"
        return 0
    fi
    local n=$(ls "$shard_dir"/*.yaml 2>/dev/null | wc -l)
    echo "  APU $apu shard $shard_idx ($n yamls) -> $out_dir"
    HIP_VISIBLE_DEVICES=$apu boltz predict "$shard_dir" \
        --use_msa_server \
        --no_kernels \
        --cache "$BOLTZ_CACHE" \
        --out_dir "$out_dir" \
        --output_format mmcif \
        --accelerator gpu \
        --devices 1 \
        > "$out_dir/boltz.log" 2>&1
}

# Each task processes APUS_PER_NODE shards in parallel
for apu in $(seq 0 $((APUS_PER_NODE - 1))); do
    shard_idx=$(( TASK * APUS_PER_NODE + apu ))
    run_apu "$apu" "$shard_idx" &
done
wait

echo
echo "=== task $TASK aggregating its own out dirs ==="
mkdir -p "$PROJECT/results/${RUN_LABEL}"
python "$PROJECT/scripts/aggregate_boltz.py" \
    --pred-dir "$WORK_BASE" \
    --out-csv "$PROJECT/results/${RUN_LABEL}/scores_task${TASK}.csv"

echo
echo "=== task $TASK done at $(date) ==="
