"""Canonicalise + dedupe a TamGen-output samples CSV.

Input CSV has at least a `smiles` column. Optional columns are preserved.
Writes a CSV with an added `canonical_smiles` column, one row per unique
RDKit-canonical SMILES. Rows with invalid SMILES are dropped. If
--exclude-smiles is given, rows whose canonical SMILES match it are dropped
(useful for excluding the parent scaffold from a seeded generation).

Usage:
    python scripts/dedup_smiles.py --in raw.csv --out unique.csv \\
        [--exclude-smiles "<parent SMILES>"]
"""
import argparse
import csv
import sys
from typing import Optional

from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")  # silence per-row SMILES parse errors


def canonical(smi: Optional[str]) -> Optional[str]:
    if not smi:
        return None
    mol = Chem.MolFromSmiles(smi)
    return Chem.MolToSmiles(mol) if mol is not None else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--exclude-smiles", default=None,
                   help="optional SMILES to exclude (canonicalised) — typically the parent scaffold")
    args = p.parse_args()

    exclude_canon = canonical(args.exclude_smiles) if args.exclude_smiles else None

    with open(args.inp) as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("empty input")

    if "smiles" not in rows[0]:
        sys.exit("input CSV missing 'smiles' column")

    seen: set[str] = set()
    out_rows = []
    for r in rows:
        canon = canonical(r["smiles"])
        if canon is None:
            continue
        if canon == exclude_canon:
            continue
        if canon in seen:
            continue
        seen.add(canon)
        r["canonical_smiles"] = canon
        out_rows.append(r)

    fieldnames = list(rows[0].keys())
    if "canonical_smiles" not in fieldnames:
        fieldnames.append("canonical_smiles")
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)
    print(f"wrote {len(out_rows)} unique canonical SMILES to {args.out} "
          f"(from {len(rows)} input rows)")


if __name__ == "__main__":
    main()
