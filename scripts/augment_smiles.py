"""Generate N non-canonical traversal-variants of a SMILES string for scaffold seeding.

Used by scaffold-seeded TamGen branches (B1, B2, B3) to expand a single seed
into multiple representations, increasing the diversity of the generated set.

Usage:
    python scripts/augment_smiles.py --smiles "<SMILES>" --n 20 --out path/to/seed.txt
"""
import argparse
import sys

from rdkit import Chem


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--smiles", required=True)
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--out", required=True)
    p.add_argument("--max-attempts", type=int, default=200,
                   help="give up after this many tries if uniqueness stalls")
    args = p.parse_args()

    mol = Chem.MolFromSmiles(args.smiles)
    if mol is None:
        sys.exit(f"invalid SMILES: {args.smiles}")

    seen: set[str] = set()
    attempts = 0
    while len(seen) < args.n and attempts < args.max_attempts:
        seen.add(Chem.MolToSmiles(mol, doRandom=True, canonical=False))
        attempts += 1

    with open(args.out, "w") as f:
        for s in seen:
            f.write(s + "\n")
    print(f"wrote {len(seen)} augmented SMILES to {args.out} (attempts: {attempts})")


if __name__ == "__main__":
    main()
