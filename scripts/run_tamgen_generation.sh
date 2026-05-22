#!/bin/bash
set -e

TAMGEN_DIR="/Users/johnsmith/Desktop/beng_203/PHGDH_affinity/TamGen"
DATADIR="/Users/johnsmith/Desktop/beng_203/PHGDH_affinity/data/tamgen_prepared"
CKPT="$TAMGEN_DIR/checkpoints/crossdocked_model/checkpoint_best.pt"
OUTDIR="/Users/johnsmith/Desktop/beng_203/PHGDH_affinity/data/tamgen_output_100"
DATASET="PHGDH_pocket"

mkdir -p "$OUTDIR"
tmpfile=$(mktemp "$OUTDIR/tmpout.XXXXXX")

cd "$TAMGEN_DIR"

python generate.py \
    "$DATADIR" \
    -s tg -t m1 \
    --task translation_coord \
    --path "$CKPT" \
    --gen-subset "$DATASET" \
    --beam 100 --nbest 100 --max-tokens 1024 \
    --seed 42 --sample-beta 1.0 \
    --use-src-coord \
    --cpu > "$tmpfile"

python scripts/format_output.py "$tmpfile" "$OUTDIR/output.csv"
rm "$tmpfile"

echo "Done. Output written to: $OUTDIR/output.csv"
