"""Prep ensemble target PDBs for the PHGDH pipeline.

Builds 4 target variants from raw RCSB CIFs:
  C1: phgdh_6CWA_apo.pdb        - 6CWA chain A, all HETATMs stripped (substrate cleft empty)
  C2: phgdh_6CWA_3pg.pdb        - 6CWA chain A, only 3PG kept (NADH stripped)
  C3: phgdh_2G76_apo.pdb        - 2G76 chain A, all HETATMs stripped (independent apo conformation)
  C4: align 6PLF to 6CWA frame, compute centroid of bound NCT-series ligand → allosteric pocket center

Writes structures to data/targets/ and pocket_centers.json.

Run from project root: python scripts/prep_targets.py
"""
from pathlib import Path
import json

import numpy as np
from Bio.PDB import MMCIFParser, PDBIO, Select, Superimposer
from Bio.PDB.Polypeptide import is_aa


PROJECT = Path(__file__).resolve().parent.parent
STRUCTURES = PROJECT / "data" / "structures"
TARGETS = PROJECT / "data" / "targets"
TARGETS.mkdir(parents=True, exist_ok=True)


class ChainProteinSelect(Select):
    """Keep only protein residues from a single chain, optionally keep specific HETATMs."""

    def __init__(self, chain_id: str, keep_hetatms: set[str] | None = None):
        self.chain_id = chain_id
        self.keep_hetatms = keep_hetatms or set()

    def accept_chain(self, chain):
        return chain.id == self.chain_id

    def accept_residue(self, residue):
        hetflag = residue.id[0]
        if hetflag == " ":
            return is_aa(residue, standard=True)
        # HETATM: keep only if resname is in our keep-set
        resname = residue.resname.strip()
        return resname in self.keep_hetatms


def load_structure(pdb_id: str):
    cif = STRUCTURES / f"{pdb_id}.cif"
    if not cif.exists():
        raise FileNotFoundError(cif)
    parser = MMCIFParser(QUIET=True)
    return parser.get_structure(pdb_id, str(cif))


def write_pdb(structure, out_path: Path, selector: Select):
    io = PDBIO()
    io.set_structure(structure)
    io.save(str(out_path), select=selector)
    print(f"  wrote {out_path.relative_to(PROJECT)}")


def get_chain(structure, chain_id: str):
    for model in structure:
        for chain in model:
            if chain.id == chain_id:
                return chain
    raise KeyError(f"chain {chain_id} not found in {structure.id}")


def centroid_of_hetatms(structure, resname: str, chain_id: str | None = None) -> np.ndarray | None:
    """Return centroid coords of all atoms in any residue with given resname (in chain_id if given)."""
    coords = []
    for model in structure:
        for chain in model:
            if chain_id and chain.id != chain_id:
                continue
            for residue in chain:
                if residue.resname.strip() == resname and residue.id[0] != " ":
                    coords.extend(atom.coord for atom in residue.get_atoms())
        break  # first model only
    if not coords:
        return None
    return np.array(coords).mean(axis=0)


def align_chains(mobile, reference, mobile_chain="A", ref_chain="A"):
    """CA-superposition of mobile chain onto reference chain. Modifies mobile in place; returns RMSD."""
    mobile_ca = [r["CA"] for r in get_chain(mobile, mobile_chain) if is_aa(r, standard=True) and "CA" in r]
    ref_ca = [r["CA"] for r in get_chain(reference, ref_chain) if is_aa(r, standard=True) and "CA" in r]
    # Use overlapping residues by sequence number
    ref_by_num = {a.get_parent().id[1]: a for a in ref_ca}
    pairs = [(m, ref_by_num[m.get_parent().id[1]]) for m in mobile_ca if m.get_parent().id[1] in ref_by_num]
    if len(pairs) < 30:
        raise RuntimeError(f"too few overlapping residues ({len(pairs)}) for alignment")
    mobile_atoms = [m for m, _ in pairs]
    ref_atoms = [r for _, r in pairs]
    sup = Superimposer()
    sup.set_atoms(ref_atoms, mobile_atoms)
    sup.apply(mobile.get_atoms())
    return sup.rms, len(pairs)


# ----------------------------------------------------------------------
# Build C1, C2 from 6CWA
# ----------------------------------------------------------------------
print("=" * 60)
print("Building targets from 6CWA (catalytic domain, res 6-278)")
print("=" * 60)
s6cwa = load_structure("6CWA")
# 6CWA has 3PG and NADH (HETATM code NAI). Choose chain A.
write_pdb(s6cwa, TARGETS / "phgdh_6CWA_apo.pdb", ChainProteinSelect("A"))
write_pdb(s6cwa, TARGETS / "phgdh_6CWA_3pg.pdb", ChainProteinSelect("A", keep_hetatms={"3PG"}))
write_pdb(s6cwa, TARGETS / "phgdh_6CWA_3pg_nadh.pdb", ChainProteinSelect("A", keep_hetatms={"3PG", "NAI"}))

# ----------------------------------------------------------------------
# Build C3 from 2G76
# ----------------------------------------------------------------------
print()
print("=" * 60)
print("Building target from 2G76 (D-malate stripped → independent apo)")
print("=" * 60)
s2g76 = load_structure("2G76")
write_pdb(s2g76, TARGETS / "phgdh_2G76_apo.pdb", ChainProteinSelect("A"))

# ----------------------------------------------------------------------
# Pocket centers
# ----------------------------------------------------------------------
print()
print("=" * 60)
print("Computing pocket centers")
print("=" * 60)

# Substrate cleft: use original pocket_center.json from project root
with open(PROJECT / "pocket_center.json") as f:
    substrate_pocket = json.load(f)
print(f"Substrate cleft (from existing pocket_center.json): "
      f"({substrate_pocket['center_x']:.2f}, {substrate_pocket['center_y']:.2f}, {substrate_pocket['center_z']:.2f}) "
      f"r={substrate_pocket['radius_angstrom']} Å")

# Verify by computing centroid of 3PG + NADH in 6CWA
c_3pg = centroid_of_hetatms(s6cwa, "3PG", chain_id="A")
c_nai = centroid_of_hetatms(s6cwa, "NAI", chain_id="A")
if c_3pg is not None and c_nai is not None:
    c_combined = (c_3pg + c_nai) / 2
    print(f"  cross-check: 3PG centroid = ({c_3pg[0]:.2f}, {c_3pg[1]:.2f}, {c_3pg[2]:.2f})")
    print(f"               NADH centroid = ({c_nai[0]:.2f}, {c_nai[1]:.2f}, {c_nai[2]:.2f})")
    print(f"               midpoint     = ({c_combined[0]:.2f}, {c_combined[1]:.2f}, {c_combined[2]:.2f})")

# Allosteric pocket: align 6PLF to 6CWA, compute centroid of NCT-series ligand
# First need to identify the ligand resname in 6PLF
s6plf = load_structure("6PLF")
ligand_resnames = set()
for model in s6plf:
    for chain in model:
        for residue in chain:
            if residue.id[0] != " " and residue.resname.strip() not in {"HOH", "GOL", "NAI", "NAD", "3PG", "EDO", "PEG", "PG4", "SO4", "CL", "NA", "K", "MG", "ZN", "CA", "MN"}:
                ligand_resnames.add(residue.resname.strip())
    break
print(f"\n6PLF candidate ligand resnames (excluding solvent/cofactor/ions): {ligand_resnames}")

# Pick the most-atom-count ligand (likely the drug)
def ligand_atom_count(structure, resname):
    n = 0
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.id[0] != " " and residue.resname.strip() == resname:
                    n += len([a for a in residue.get_atoms()])
        break
    return n

if ligand_resnames:
    drug_resname = max(ligand_resnames, key=lambda r: ligand_atom_count(s6plf, r))
    print(f"Selected 6PLF drug ligand: {drug_resname} ({ligand_atom_count(s6plf, drug_resname)} atoms)")

    # Align 6PLF chain A onto 6CWA chain A
    rms, n_pairs = align_chains(s6plf, s6cwa, mobile_chain="A", ref_chain="A")
    print(f"6PLF→6CWA chain-A CA alignment: RMSD={rms:.3f} Å over {n_pairs} residues")

    c_drug = centroid_of_hetatms(s6plf, drug_resname, chain_id="A")
    if c_drug is not None:
        print(f"Allosteric pocket center (6PLF drug centroid, in 6CWA frame): "
              f"({c_drug[0]:.2f}, {c_drug[1]:.2f}, {c_drug[2]:.2f})")

        with open(PROJECT / "pocket_center_allosteric.json", "w") as f:
            json.dump({
                "source_pdb": "6PLF",
                "ligand_resname": drug_resname,
                "aligned_frame": "6CWA chain A",
                "alignment_rmsd": float(rms),
                "alignment_residues": int(n_pairs),
                "center_x": float(c_drug[0]),
                "center_y": float(c_drug[1]),
                "center_z": float(c_drug[2]),
                "radius_angstrom": 10,
            }, f, indent=2)
        print(f"  wrote pocket_center_allosteric.json")
else:
    print("No drug-like ligand found in 6PLF; allosteric pocket center deferred")

print()
print("Done.")
