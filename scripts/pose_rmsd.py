"""Compute ligand pose RMSD between Boltz-2 predictions and crystal structures.

For each case in data/pose_recovery_inputs/manifest.json:
  1. Load crystal CIF (data/structures/<pdb>.cif), extract chain-A protein CA atoms + ligand HETATM
  2. Load predicted CIF from Boltz output, extract chain-A protein CA atoms + ligand atoms
  3. Superpose predicted protein onto crystal protein (CA-only)
  4. Apply transformation to predicted ligand
  5. Compute heavy-atom RMSD between transformed predicted ligand and crystal ligand
     - Atom-name-matched where possible; centroid-only as fallback

Writes results/pose_recovery.csv.

Usage:
    python scripts/pose_rmsd.py --pred-dir <boltz_out_dir>
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
from Bio.PDB import MMCIFParser, Superimposer
from Bio.PDB.Polypeptide import is_aa


PROJECT = Path(__file__).resolve().parent.parent


def chain_ca_atoms(structure, chain_id="A"):
    out = []
    for model in structure:
        for chain in model:
            if chain.id != chain_id:
                continue
            for r in chain:
                if is_aa(r, standard=True) and "CA" in r:
                    out.append((r.id[1], r["CA"]))
        break
    return out


def het_atoms(structure, resname, chain_id="A"):
    atoms = []
    for model in structure:
        for chain in model:
            if chain_id and chain.id != chain_id:
                continue
            for r in chain:
                if r.id[0] != " " and r.resname.strip() == resname:
                    for a in r.get_atoms():
                        if a.element != "H":
                            atoms.append(a)
        break
    return atoms


def superpose_on_overlap(crystal_ca, pred_ca):
    cmap = {n: a for n, a in crystal_ca}
    pairs = [(crystal_ca_atom, pred_ca_atom)
             for (n, pred_ca_atom) in pred_ca if (crystal_ca_atom := cmap.get(n)) is not None]
    if len(pairs) < 30:
        return None, None
    sup = Superimposer()
    sup.set_atoms([c for c, _ in pairs], [p for _, p in pairs])
    return sup, len(pairs)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pred-dir", required=True, help="Boltz output root (e.g. .../boltz_results_*)")
    p.add_argument("--out-csv", default=str(PROJECT / "results" / "pose_recovery.csv"))
    args = p.parse_args()

    pred_dir = Path(args.pred_dir)
    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    with open(PROJECT / "data" / "pose_recovery_manifest.json") as f:
        manifest = json.load(f)

    rows = []
    parser = MMCIFParser(QUIET=True)
    for case in manifest:
        pdb_id = case["pdb"]
        resname = case["ligand_resname"]
        name = case["name"]
        key = f"{pdb_id}_{resname}"

        # Crystal
        crystal_cif = PROJECT / "data" / "structures" / f"{pdb_id}.cif"
        crystal = parser.get_structure(pdb_id, str(crystal_cif))
        crystal_ca = chain_ca_atoms(crystal)
        crystal_het = het_atoms(crystal, resname)
        if not crystal_het:
            rows.append({"case": key, "name": name, "status": "no_crystal_ligand"})
            continue

        # Find Boltz prediction CIF for this case
        # Boltz writes: boltz_results_<input>/predictions/<input>/<input>_model_0.cif
        cands = list(pred_dir.glob(f"**/{key}_model_*.cif"))
        if not cands:
            rows.append({"case": key, "name": name, "status": "no_prediction"})
            continue
        pred_cif = cands[0]
        pred = parser.get_structure("pred", str(pred_cif))
        pred_ca = chain_ca_atoms(pred)
        # In Boltz output, the ligand is a separate chain (typically chain "B" per our YAML)
        pred_het = []
        for model in pred:
            for chain in model:
                for r in chain:
                    if r.id[0] != " ":
                        pred_het.extend(a for a in r.get_atoms() if a.element != "H")
            break
        # If no HETATM, try non-protein residues
        if not pred_het:
            for model in pred:
                for chain in model:
                    if chain.id == "A":
                        continue
                    for r in chain:
                        pred_het.extend(a for a in r.get_atoms() if a.element != "H")
                break

        if not pred_het:
            rows.append({"case": key, "name": name, "status": "no_pred_ligand"})
            continue

        sup, n_pairs = superpose_on_overlap(crystal_ca, pred_ca)
        if sup is None:
            rows.append({"case": key, "name": name, "status": "alignment_failed",
                         "pred_cif": str(pred_cif.name)})
            continue

        # Apply transform to predicted ligand
        sup.apply([a for a in pred_het])
        # Centroid RMSD (lightweight, no atom-name matching required)
        crystal_coords = np.array([a.coord for a in crystal_het])
        pred_coords = np.array([a.coord for a in pred_het])
        centroid_rmsd = float(np.linalg.norm(crystal_coords.mean(0) - pred_coords.mean(0)))

        # Heavy-atom RMSD if counts match (best-effort, no symmetry)
        if len(crystal_het) == len(pred_het):
            # Naive ordering match
            diffs = crystal_coords - pred_coords
            heavy_rmsd = float(np.sqrt((diffs ** 2).sum(1).mean()))
        else:
            heavy_rmsd = None

        rows.append({
            "case": key, "name": name,
            "status": "ok",
            "n_crystal_atoms": len(crystal_het),
            "n_pred_atoms": len(pred_het),
            "ca_align_rmsd": round(sup.rms, 3),
            "n_pairs": n_pairs,
            "centroid_rmsd": round(centroid_rmsd, 3),
            "heavy_atom_rmsd": round(heavy_rmsd, 3) if heavy_rmsd is not None else None,
            "pred_cif": pred_cif.name,
        })

    if not rows:
        print("no cases processed")
        return
    keys = sorted({k for r in rows for k in r})
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

    print(f"\nwrote {out_csv}")
    for r in rows:
        if r["status"] == "ok":
            print(f"  {r['case']:15s} {r['name']:25s} centroid={r['centroid_rmsd']:.2f}Å "
                  f"heavy={r['heavy_atom_rmsd']}")
        else:
            print(f"  {r['case']:15s} {r['name']:25s} STATUS={r['status']}")


if __name__ == "__main__":
    main()
