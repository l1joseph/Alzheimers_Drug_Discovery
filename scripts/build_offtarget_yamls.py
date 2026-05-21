"""Build Boltz YAML inputs for off-target counter-screening.

Each YAML: an off-target protein (from FASTA + cached MSA) + one ligand SMILES.
Used to ask: does this PHGDH hit also bind LDH-A / MDH2 / GAPDH / IDH1?

Usage:
    python scripts/build_offtarget_yamls.py \
        --ligands data/libraries/top10_offtarget.csv \
        --out-dir /cosmos/vast/scratch/l1joseph/offtarget_yamls
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent.parent

OFF_TARGETS = [
    ("LDH-A",  "P00338", "LDH_A_offtarget"),
    ("MDH2",   "P40926", "MDH2_offtarget"),
    ("GAPDH",  "P04406", "GAPDH_offtarget"),
    ("IDH1",   "O75874", "IDH1_offtarget"),
]


def read_fasta(path: Path) -> str:
    seq = []
    with open(path) as f:
        for line in f:
            if line.startswith(">"):
                continue
            seq.append(line.strip())
    return "".join(seq)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ligands", required=True,
                   help="CSV with id,smiles columns (top hits to counter-screen)")
    p.add_argument("--out-dir", required=True)
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # load off-target seqs + verify MSAs exist
    targets = {}
    for name, uniprot, msa_stem in OFF_TARGETS:
        fa = PROJECT / "data" / "off_targets" / f"{name}.fasta"
        msa = PROJECT / "data" / "msa" / f"{msa_stem}.a3m"
        if not fa.exists():
            raise FileNotFoundError(fa)
        if not msa.exists():
            raise FileNotFoundError(f"missing cached MSA: {msa}")
        targets[name] = {
            "uniprot": uniprot,
            "seq": read_fasta(fa),
            "msa": str(msa.resolve()),
        }
        print(f"  {name}: {len(targets[name]['seq'])} aa, MSA at {msa.name}")

    ligands = list(csv.DictReader(open(args.ligands)))
    print(f"counter-screening {len(ligands)} ligands x {len(targets)} off-targets")

    n_written = 0
    for tname, tdata in targets.items():
        for lig in ligands:
            lid = lig["id"]
            yaml_id = f"{tname.replace('-','_')}__{lid}"
            sequences = [
                {"protein": {
                    "id": "A",
                    "sequence": tdata["seq"],
                    "msa": tdata["msa"],
                }},
                {"ligand": {"id": "B", "smiles": lig["smiles"]}},
            ]
            yp = out_dir / f"{yaml_id}.yaml"
            with open(yp, "w") as f:
                yaml.safe_dump({
                    "version": 1,
                    "sequences": sequences,
                    "properties": [{"affinity": {"binder": "B"}}],
                }, f, default_flow_style=False, sort_keys=False, width=200)
            n_written += 1
    print(f"wrote {n_written} YAMLs to {out_dir}")


if __name__ == "__main__":
    main()
