"""
Read TamGen output.csv and produce one Boltz-2 affinity YAML per candidate.

Inputs:
  data/tamgen_output/output.csv     - TamGen SMILES + scores
  data/6CWA_chainA_clean.pdb        - chain A structure (for sequence extraction)

Output:
  data/boltz_inputs/candidate_000.yaml, candidate_001.yaml, ...
"""

import csv
from pathlib import Path
from Bio.PDB import PDBParser
from Bio.SeqUtils import seq1

DATA_DIR = Path(__file__).parent.parent / "data"
SMILES_CSV = DATA_DIR / "tamgen_output" / "output.csv"
PDB_PATH = DATA_DIR / "6CWA_chainA_clean.pdb"
OUT_DIR = DATA_DIR / "boltz_inputs"

# --- Extract chain A sequence from cleaned PDB ---
parser = PDBParser(QUIET=True)
structure = parser.get_structure("6CWA", PDB_PATH)
residues = [r for r in structure[0]["A"] if r.id[0] == " "]
sequence = "".join(seq1(r.resname) for r in residues)
print(f"Chain A sequence: {len(sequence)} residues")

# --- Read SMILES ---
candidates = []
with open(SMILES_CSV) as f:
    for row in csv.DictReader(f):
        candidates.append({"smiles": row["smiles"], "nlogP": row["nlogP"]})
print(f"Candidates loaded: {len(candidates)}")

# --- Write one YAML per candidate ---
OUT_DIR.mkdir(parents=True, exist_ok=True)

yaml_template = """\
version: 1
sequences:
  - protein:
      id: A
      sequence: {sequence}
  - ligand:
      id: B
      smiles: '{smiles}'
properties:
  - affinity:
      binder: B
"""

for i, c in enumerate(candidates):
    content = yaml_template.format(sequence=sequence, smiles=c["smiles"])
    out_path = OUT_DIR / f"candidate_{i:03d}.yaml"
    out_path.write_text(content)

print(f"Written {len(candidates)} YAML files to {OUT_DIR}/")
