"""Aggregate Boltz-2 affinity predictions into a single CSV.

Boltz writes per-input results under <pred_dir>/boltz_results_<input>/predictions/<input>/
including affinity_<input>.json with the predicted binding affinity.

Usage:
    python scripts/aggregate_boltz.py --pred-dir <work_out> --out-csv <out.csv>
"""
import argparse
import csv
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pred-dir", required=True, help="Boltz output directory (top-level)")
    p.add_argument("--out-csv", required=True)
    args = p.parse_args()

    pred_dir = Path(args.pred_dir)
    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    # Boltz output structure (v2.x): <pred_dir>/boltz_results_<run>/predictions/<input>/
    # Recursive in case the caller passed a parent containing several
    # task*_apu* output dirs (the boltz_array_screen.sh layout).
    for run_dir in sorted(pred_dir.rglob("boltz_results_*")):
        predictions = run_dir / "predictions"
        if not predictions.is_dir():
            continue
        for inp_dir in sorted(predictions.iterdir()):
            if not inp_dir.is_dir():
                continue
            input_id = inp_dir.name
            aff_file = inp_dir / f"affinity_{input_id}.json"
            conf_file = inp_dir / f"confidence_{input_id}_model_0.json"
            row = {"input_id": input_id}
            if aff_file.exists():
                with open(aff_file) as f:
                    row.update({f"affinity_{k}": v for k, v in json.load(f).items()})
            if conf_file.exists():
                with open(conf_file) as f:
                    row.update({f"confidence_{k}": v for k, v in json.load(f).items()
                                if not isinstance(v, (list, dict))})
            rows.append(row)

    if not rows:
        print(f"WARNING: no predictions found under {pred_dir}")
        return

    all_keys = sorted({k for row in rows for k in row})
    keys = ["input_id"] + [k for k in all_keys if k != "input_id"]
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {out_csv}")


if __name__ == "__main__":
    main()
