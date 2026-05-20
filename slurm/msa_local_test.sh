#!/bin/bash
#SBATCH --job-name=boltz2-msa-local
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=00:15:00
set -e
PROJECT=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery
SCRATCH=/cosmos/vast/scratch/l1joseph
module load rocm/6.3.0 2>&1 | tail -1
source ~/miniforge3/etc/profile.d/conda.sh
conda activate boltz-rocm
cd $PROJECT
boltz predict $PROJECT/data/msa_test2 --no_kernels \
  --cache $SCRATCH/boltz_cache --out_dir $SCRATCH/msa_local_$SLURM_JOB_ID \
  --output_format mmcif --accelerator gpu --devices 1
echo "=== Done at $(date) ==="
