#!/bin/bash
set -e

INPUT="/Users/johnsmith/Desktop/beng_203/PHGDH_affinity/data/boltz_inputs/candidate_000.yaml"
OUTDIR="/Users/johnsmith/Desktop/beng_203/PHGDH_affinity/data/boltz_output"

mkdir -p "$OUTDIR"

mamba run -n boltz-rocm boltz predict "$INPUT" \
    --accelerator cpu \
    --use_msa_server \
    --out_dir "$OUTDIR" \
    --output_format pdb \
    --sampling_steps 50

echo "Done. Output written to: $OUTDIR"
