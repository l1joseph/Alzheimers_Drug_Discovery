"""Build Boltz-2 YAML inputs for pose-recovery validation.

For each (PDB, ligand_resname, ligand_smiles) tuple: extract chain-A protein sequence
from the PDB, build a Boltz YAML with the protein + ligand SMILES, and write to disk.
After Boltz prediction, we compare the predicted ligand pose to the crystal HETATM
coordinates to compute RMSD.

Run from project root: python scripts/build_pose_recovery_yamls.py
"""
from pathlib import Path
import json

import yaml
from Bio.PDB import MMCIFParser
from Bio.PDB.Polypeptide import is_aa


PROJECT = Path(__file__).resolve().parent.parent
STRUCTURES = PROJECT / "data" / "structures"
OUT_DIR = PROJECT / "data" / "pose_recovery_inputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)


THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}


# (PDB, ligand resname, name, SMILES)
# SMILES extracted from PDB Chemical Component Dictionary (see plan + positive_controls.csv)
CASES = [
    ("6RJ6", "K5K", "BI-4924",
     "Cc1cc2c(cc(n2C)C(=O)N[C@H](CO)c3ccc(cc3)S(=O)(=O)CC(=O)O)c(c1Cl)Cl"),
    ("6PLF", "ONV", "NCT-series-cmpd-1",
     "C1[C@H](OC(=O)N1)COC2=C(C=C3C=C(NC3=C2)C(=O)N[C@H](CO)C4=CC=C(C=C4)C(=O)O)Cl"),
    ("6PLG", "ONS", "NCT-series-cmpd-15",
     "Cn1c(cc2c(Cl)c(Cl)ccc12)C(=O)NC3(COC3)c4ccc(cc4)[C@H](C(O)=O)c5cccnc5"),
    ("6RJ3", "K58", "BI-cmpd-15",
     "C[C@H](c1ccc(cc1)C(=O)O)NC(=O)c2cc(nn2C)c3ccccc3"),
    ("7EWH", "HMT", "Homoharringtonine",
     "COC(=O)C[C@](O)(CCCC(C)(C)O)C(=O)O[C@H]1[C@H]2c3cc4OCOc4cc3CCN5CCC[C@]25C=C1OC"),
]


def extract_sequence(cif_path: Path, chain_id: str = "A") -> str:
    parser = MMCIFParser(QUIET=True)
    structure = parser.get_structure(cif_path.stem, str(cif_path))
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
    manifest = []
    for pdb_id, lig_resname, name, smiles in CASES:
        cif = STRUCTURES / f"{pdb_id}.cif"
        if not cif.exists():
            print(f"SKIP {pdb_id}: CIF not found")
            continue
        seq = extract_sequence(cif)
        if not seq:
            print(f"SKIP {pdb_id}: no chain-A protein sequence")
            continue
        yaml_path = OUT_DIR / f"{pdb_id}_{lig_resname}.yaml"
        with open(yaml_path, "w") as f:
            yaml.safe_dump({
                "version": 1,
                "sequences": [
                    # Omit msa field so --use_msa_server can fetch MSAs from ColabFold.
                    # Explicit "msa: empty" forces single-sequence mode → very poor pose accuracy.
                    {"protein": {"id": "A", "sequence": seq}},
                    {"ligand": {"id": "B", "smiles": smiles}},
                ],
                "properties": [{"affinity": {"binder": "B"}}],
            }, f, default_flow_style=False, sort_keys=False, width=200)
        manifest.append({
            "pdb": pdb_id, "ligand_resname": lig_resname, "name": name,
            "smiles": smiles, "n_residues": len(seq),
        })
        print(f"  wrote {yaml_path.name} (protein {len(seq)} aa, ligand {name})")

    with open(OUT_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nwrote manifest with {len(manifest)} cases to {OUT_DIR}/manifest.json")


if __name__ == "__main__":
    main()
