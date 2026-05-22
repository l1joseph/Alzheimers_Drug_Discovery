"""
Preprocess 6CWA.cif: extract NAI binding pocket center and clean chain A structure.

Outputs:
  data/pocket_center.json      - NAI centroid + radius for TamGen input
  data/tamgen_input.csv        - TamGen-ready CSV (pdb_id, center_x, center_y, center_z)
  data/6CWA_chainA_clean.pdb   - Chain A protein only, no waters/ligands (for Boltz-2)
"""

import json
import csv
import numpy as np
from pathlib import Path
from Bio.PDB import MMCIFParser, PDBIO, Select

DATA_DIR = Path(__file__).parent.parent / "data"
CIF_PATH = DATA_DIR / "6CWA.cif"

# --- Parse structure ---
parser = MMCIFParser(QUIET=True)
structure = parser.get_structure("6CWA", CIF_PATH)
model = structure[0]

# --- Extract NAI atoms from chain A (auth_asym_id == "A") ---
# In 6CWA, NAI has label_asym_id=D but auth_asym_id=A.
# BioPython's MMCIFParser organises residues by auth_asym_id, so NAI sits
# inside chain "A" as a HETATM residue.
nai_coords = []
for residue in model["A"]:
    if residue.resname == "NAI":
        for atom in residue.get_atoms():
            nai_coords.append(atom.coord)

if not nai_coords:
    raise RuntimeError("No NAI residue found — check chain labelling in the CIF file.")

nai_coords = np.array(nai_coords)
centroid = nai_coords.mean(axis=0)
cx, cy, cz = float(centroid[0]), float(centroid[1]), float(centroid[2])

print(f"NAI atoms found : {len(nai_coords)}")
print(f"Pocket centroid : x={cx:.3f}  y={cy:.3f}  z={cz:.3f}")

# --- Write pocket_center.json ---
pocket = {"pdb_id": "6CWA", "center_x": cx, "center_y": cy, "center_z": cz, "radius_angstrom": 10}
with open(DATA_DIR / "pocket_center.json", "w") as f:
    json.dump(pocket, f, indent=2)
print("Written: data/pocket_center.json")

# --- Write tamgen_input.csv ---
with open(DATA_DIR / "tamgen_input.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["pdb_id", "center_x", "center_y", "center_z"])
    writer.writerow(["6CWA", f"{cx:.3f}", f"{cy:.3f}", f"{cz:.3f}"])
print("Written: data/tamgen_input.csv")

# --- Write cleaned chain A PDB (protein ATOM records only, no waters/ligands) ---
EXCLUDE = {"HOH", "NAI", "3PG"}

class ChainAProteinSelect(Select):
    def accept_chain(self, chain):
        return chain.id == "A"

    def accept_residue(self, residue):
        # Keep only standard amino acid ATOM records; drop waters and ligands.
        # BioPython marks hetero residues with an "H_" prefix in the residue id.
        hetflag = residue.id[0]
        return hetflag == " " and residue.resname not in EXCLUDE

io = PDBIO()
io.set_structure(structure)
out_path = DATA_DIR / "6CWA_chainA_clean.pdb"
io.save(str(out_path), ChainAProteinSelect())
print("Written: data/6CWA_chainA_clean.pdb")

# --- Quick sanity check ---
with open(out_path) as f:
    atom_lines = [l for l in f if l.startswith("ATOM")]
print(f"Chain A clean PDB: {len(atom_lines)} ATOM records")
