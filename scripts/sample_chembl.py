"""Sample a tight drug-like subset of ChEMBL for Boltz screening.

Reads data/libraries/chembl_druglike.csv (output of filter_chembl.py),
applies a tighter "lead-like" window (MW 250-450, logP 1-4, SA <= 4,
HBD <= 3, HBA <= 7), then random-samples N compounds.

Output: data/libraries/chembl_sample.csv ready for build_boltz_yamls.py
        (columns: id, smiles)
"""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="src", default=str(PROJECT / "data" / "libraries" / "chembl_druglike.csv"))
    p.add_argument("--out", dest="out", default=str(PROJECT / "data" / "libraries" / "chembl_sample.csv"))
    p.add_argument("--n", type=int, default=5000)
    p.add_argument("--mw-lo", type=float, default=250)
    p.add_argument("--mw-hi", type=float, default=450)
    p.add_argument("--logp-lo", type=float, default=1.0)
    p.add_argument("--logp-hi", type=float, default=4.0)
    p.add_argument("--hbd-hi", type=int, default=3)
    p.add_argument("--hba-hi", type=int, default=7)
    p.add_argument("--sa-hi", type=float, default=4.0)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    src = Path(args.src)
    out = Path(args.out)
    rng = random.Random(args.seed)

    print(f"reading {src}")
    rows = []
    with open(src) as f:
        for r in csv.DictReader(f):
            try:
                mw = float(r["mw"])
                logp = float(r["logp"])
                hbd = int(r["hbd"])
                hba = int(r["hba"])
                sa = float(r["sa"])
            except (ValueError, KeyError):
                continue
            if not (args.mw_lo <= mw <= args.mw_hi):
                continue
            if not (args.logp_lo <= logp <= args.logp_hi):
                continue
            if hbd > args.hbd_hi or hba > args.hba_hi:
                continue
            if sa > args.sa_hi:
                continue
            rows.append((r["id"], r["smiles"]))

    print(f"lead-like population: {len(rows):,}")
    if len(rows) > args.n:
        rows = rng.sample(rows, args.n)
        print(f"random-sampled to {args.n:,}")

    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "smiles"])
        w.writerows(rows)
    print(f"wrote {out} ({len(rows):,} rows)")


if __name__ == "__main__":
    main()
