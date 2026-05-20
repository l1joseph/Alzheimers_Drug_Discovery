"""Generate N non-canonical traversal-variants of one or more SMILES.

Used by scaffold-seeded TamGen branches (B1, B2, B3 and iterative rounds) to
expand a seed into multiple representations, increasing generation diversity.

Usage:
    # single SMILES (original use case)
    python scripts/augment_smiles.py --smiles "<SMILES>" --n 20 --out seed.txt

    # multiple seeds from a file (one SMILES per line)
    python scripts/augment_smiles.py --in seeds.txt --n 5 --out seed.txt
"""
import argparse
import sys
from typing import Optional

from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")


def augment(smi: str, n: int, max_attempts: int) -> set:
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return set()
    out: set[str] = {Chem.MolToSmiles(mol, canonical=True)}
    attempts = 0
    while len(out) < n + 1 and attempts < max_attempts:
        out.add(Chem.MolToSmiles(mol, doRandom=True, canonical=False))
        attempts += 1
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--smiles", help="single SMILES string")
    p.add_argument("--in", dest="inp", help="file with one SMILES per line")
    p.add_argument("--n", type=int, default=20, help="augmented variants per seed")
    p.add_argument("--out", required=True)
    p.add_argument("--max-attempts", type=int, default=200)
    args = p.parse_args()

    if not args.smiles and not args.inp:
        sys.exit("need either --smiles or --in")

    seeds: list[str] = ([args.smiles] if args.smiles
                        else [s.strip() for s in open(args.inp) if s.strip()])

    total: set[str] = set()
    for smi in seeds:
        variants = augment(smi, args.n, args.max_attempts)
        if not variants:
            print(f"  skipping invalid SMILES: {smi[:60]}", file=sys.stderr)
            continue
        total.update(variants)

    with open(args.out, "w") as f:
        for s in total:
            f.write(s + "\n")
    print(f"wrote {len(total)} augmented SMILES from {len(seeds)} seed(s) to {args.out}")


if __name__ == "__main__":
    main()
