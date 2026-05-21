"""Build Boltz-2 YAML input files for a screening run.

For each (target_pdb, condition) and a list of ligand SMILES, write a YAML that
boltz-predict can consume. YAMLs include affinity prediction.

Usage:
    python scripts/build_boltz_yamls.py \
        --target data/targets/phgdh_6CWA_apo.pdb \
        --target-id phgdh_apo \
        --ligand-csv data/libraries/phgdh_positive_controls.csv \
        --out-dir data/boltz_inputs/positive_controls_C1 \
        [--co-ligand 3PG_smiles]   # for ternary mode (condition B)
"""
import argparse
import csv
from pathlib import Path

import yaml
from Bio.PDB import PDBParser
from Bio.PDB.Polypeptide import is_aa


THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}


def extract_sequence(pdb_path: Path, chain_id: str = "A") -> str:
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure(pdb_path.stem, str(pdb_path))
    seq = []
    for model in structure:
        for chain in model:
            if chain.id != chain_id:
                continue
            for residue in chain:
                if is_aa(residue, standard=True):
                    resname = residue.resname.strip()
                    seq.append(THREE_TO_ONE.get(resname, "X"))
        break
    return "".join(seq)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--target", required=True, help="path to target PDB")
    p.add_argument("--target-id", required=True, help="short ID for this target conformation")
    p.add_argument("--ligand-csv", required=True, help="CSV with at least id,smiles columns")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--co-ligand-smiles", default=None,
                   help="optional co-ligand SMILES (e.g. 3PG) to include in every YAML (ternary mode)")
    p.add_argument("--co-ligand-id", default="X", help="chain id for co-ligand")
    args = p.parse_args()

    target_pdb = Path(args.target)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sequence = extract_sequence(target_pdb, chain_id="A")
    print(f"Target {args.target_id}: {len(sequence)} residues, chain A")

    n_written = 0
    with open(args.ligand_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            lid = row["id"]
            smiles = row["smiles"]
            sequences = [
                {"protein": {"id": "A", "sequence": sequence, "msa": "empty"}},
                {"ligand": {"id": "B", "smiles": smiles}},
            ]
            if args.co_ligand_smiles:
                sequences.append(
                    {"ligand": {"id": args.co_ligand_id, "smiles": args.co_ligand_smiles}}
                )

            yaml_path = out_dir / f"{lid}.yaml"
            with open(yaml_path, "w") as out:
                yaml.safe_dump({
                    "version": 1,
                    "sequences": sequences,
                    "properties": [{"affinity": {"binder": "B"}}],
                }, out, default_flow_style=False, sort_keys=False, width=200)
            n_written += 1

    print(f"Wrote {n_written} YAML files to {out_dir}")


if __name__ == "__main__":
    main()
