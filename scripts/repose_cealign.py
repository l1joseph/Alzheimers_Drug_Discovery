"""Robust re-computation of Boltz-2 pose recovery using structure-based cealign.

The original scripts/pose_rmsd.py superposed on ALL chain-A CA atoms matched by
residue NUMBER. For multi-domain PHGDH (and especially 6RJ6, a partial 99-303
construct) this global, numbering-dependent fit is unreliable and inflated the
K5K ligand RMSD to ~31 A. Here we use PyMOL cealign (sequence-independent,
structure-based, with outlier rejection) to superpose the predicted complex onto
the crystal, then measure ligand centroid distance + heavy-atom RMSD in the
crystal frame.

Run:  pymol -cqr scripts/repose_cealign.py
"""
from pathlib import Path
import numpy as np
import pymol
from pymol import cmd

PROJECT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery")
XTAL = PROJECT / "data" / "structures"
PRED = Path("/cosmos/vast/scratch/l1joseph/pose_recovery_85124/"
            "boltz_results_pose_recovery_inputs/predictions")

CASES = [
    ("6RJ6_K5K", "K5K"),
    ("6PLF_ONV", "ONV"),
    ("6PLG_ONS", "ONS"),
    ("6RJ3_K58", "K58"),
    ("7EWH_HMT", "HMT"),
]


def lig_coords(sel):
    model = cmd.get_model(sel)
    return np.array([a.coord for a in model.atom if a.symbol != "H"])


def main():
    pymol.finish_launching(["pymol", "-qc"])
    out_csv = PROJECT / "results" / "pose_recovery_cealign.csv"
    rows = []
    print(f"{'case':12s} {'cealign_rmsd':>12s} {'n_aln':>6s} "
          f"{'centroid':>9s} {'heavy_rmsd':>10s}")
    for key, resn in CASES:
        pdb = key.split("_")[0]
        cmd.reinitialize()
        cmd.load(str(XTAL / f"{pdb}.cif"), "xtal")
        cmd.load(str(PRED / key / f"{key}_model_0.cif"), "pred")
        cmd.remove("solvent")

        # crystal ligand: chain A copy preferred, else any
        cmd.select("xlig", f"xtal and resn {resn}")
        if cmd.count_atoms("xlig and chain A"):
            cmd.select("xlig", f"xtal and resn {resn} and chain A")
        # predicted ligand: the non-polymer heteromolecule
        cmd.select("plig", "pred and not polymer and not solvent")

        # structure-based superposition: crystal chain A vs predicted chain A only
        # (these crystals are homodimers; aligning whole polymer mis-pairs chains)
        try:
            res = cmd.cealign("xtal and polymer and chain A",
                              "pred and polymer and chain A")
            cerms, naln = res["RMSD"], res["alignment_length"]
        except Exception as e:
            print(f"{key:12s} cealign FAILED: {e}")
            continue

        xc = lig_coords("xlig")
        pc = lig_coords("plig")
        if len(xc) == 0 or len(pc) == 0:
            print(f"{key:12s} missing ligand atoms (x={len(xc)} p={len(pc)})")
            continue
        centroid = float(np.linalg.norm(xc.mean(0) - pc.mean(0)))
        heavy = (float(np.sqrt(((xc - pc) ** 2).sum(1).mean()))
                 if len(xc) == len(pc) else None)
        hs = f"{heavy:10.2f}" if heavy is not None else f"{'n/a':>10s}"
        print(f"{key:12s} {cerms:12.2f} {naln:6d} {centroid:9.2f} {hs}")
        rows.append({
            "case": key, "ligand_resname": resn,
            "cealign_protein_rmsd": round(cerms, 3),
            "n_aligned_residues": naln,
            "centroid_rmsd": round(centroid, 3),
            "heavy_atom_rmsd_naive": round(heavy, 3) if heavy is not None else "",
        })

    import csv
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\nwrote {out_csv}")
    print("NOTE: centroid_rmsd is the reliable metric (order-independent). "
          "heavy_atom_rmsd_naive uses file atom order without identity/symmetry "
          "matching and overestimates pose error.")


if __name__ == "__main__":
    main()
