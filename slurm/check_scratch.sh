#!/bin/bash
#SBATCH --job-name=check-scratch
#SBATCH --output=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.out
#SBATCH --error=/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/logs/%x_%j.err
#SBATCH --partition=cluster
#SBATCH --nodes=1
#SBATCH --time=00:02:00
set -e
echo "hostname: $(hostname)"
echo "SCRATCH=$SCRATCH"
echo "TMPDIR=$TMPDIR"
echo "HOME=$HOME"
echo "---candidate scratch paths---"
for p in /ddn_scratch /scratch /lus/scratch /local/scratch /tmp/$USER $TMPDIR $SCRATCH; do
  if [ -n "$p" ] && [ -d "$p" ]; then
    echo "  EXISTS: $p ($(ls -ld $p))"
    if [ -w "$p" ]; then
      echo "    writable"
    fi
  else
    echo "  missing or empty: $p"
  fi
done
echo "---env vars containing scratch/tmp---"
env | grep -iE "scratch|tmp" | head -20
