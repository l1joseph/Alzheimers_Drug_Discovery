"""Render PyMOL interaction figures for top candidate complexes.

For each (id, cif_path) tuple in the candidate list:
  - load the predicted CIF
  - cartoon for the protein (chain A) in gray
  - sticks for the ligand (chain B HETATM), colored by element with cyan carbons
  - thin sticks for protein residues within 5A of the ligand
  - dashed H-bond indicators (PyMOL "find_pairs polar_contacts")
  - camera centered on the ligand, oriented for the allosteric pocket

Outputs:
  docs/figures/interactions/<id>.png  (600x600 ray-traced)
  docs/figures/interactions/grid.png  (2x3 grid of all candidates)

Run via:
  pymol -cq scripts/render_top_candidates.py
"""
import os
import subprocess
import sys
from pathlib import Path

import pymol
from pymol import cmd

PROJECT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery")
OUT_DIR = PROJECT / "docs" / "figures" / "interactions"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PRED = PROJECT / "data" / "predicted_poses"

# (label, cif_path, descriptor)
CANDIDATES = [
    ("b1_058", PRED / "b1_058_boltz_pred.cif",
     "Novel druglike B1: aff -0.65, Tani 0.14 to BI-cmpd-15"),
    ("b1_051", PRED / "b1_051_boltz_pred.cif",
     "Novel druglike B1: aff -0.48, Tani 0.12 to NCT-503"),
    ("b1_005", PRED / "b1_005_boltz_pred.cif",
     "Novel druglike B1: aff -0.39, Tani 0.12 to NCT-503"),
    ("b1_112", PRED / "b1_112_boltz_pred.cif",
     "Novel druglike B1: aff -0.37, Tani 0.15 to NCT-503"),
    ("K5K",    PRED / "K5K_boltz_pred.cif",
     "Validated reference: BI-4924, aff -1.79"),
    ("NCT503", PRED / "NCT503_boltz_pred.cif",
     "Validated reference: NCT-503, parent scaffold"),
]


def render(label, cif_path):
    out_png = OUT_DIR / f"{label}.png"
    cmd.reinitialize()
    cmd.load(cif_path, label)

    # Protein vs ligand: ligand is the non-polymer entity (Boltz YAML 'ligand' -> chain B by spec)
    cmd.select("prot", "polymer")
    cmd.select("lig", "not polymer and not solvent")
    if cmd.count_atoms("lig") == 0:
        # fallback: HETATM
        cmd.select("lig", "hetatm and not solvent")
    if cmd.count_atoms("lig") == 0:
        print(f"  WARN: no ligand atoms found in {cif_path}")
        return

    cmd.hide("everything")
    cmd.show("cartoon", "prot")
    cmd.color("gray80", "prot")
    cmd.show("sticks", "lig")
    cmd.color("cyan", "lig and elem C")
    cmd.util.cnc("lig")  # color non-C by element

    # Pocket residues
    cmd.select("pocket", "byres prot within 5 of lig")
    cmd.show("sticks", "pocket")
    cmd.color("wheat", "pocket and elem C")
    cmd.util.cnc("pocket")
    cmd.set("stick_radius", 0.15, "pocket")
    cmd.set("stick_radius", 0.22, "lig")

    # Polar contacts (H-bonds)
    cmd.distance("hbonds", "lig", "pocket", 3.5, mode=2)
    cmd.color("yellow", "hbonds")
    cmd.hide("labels", "hbonds")

    # Camera: orient on ligand, zoom out a bit
    cmd.orient("lig")
    cmd.zoom("lig", 6)
    cmd.bg_color("white")
    cmd.set("ray_shadows", 0)
    cmd.set("ray_trace_mode", 1)
    cmd.set("antialias", 2)
    cmd.set("ambient", 0.3)
    cmd.set("cartoon_transparency", 0.2)
    cmd.png(str(out_png), width=800, height=800, dpi=150, ray=1)
    print(f"  wrote {out_png}")


def main():
    pymol.finish_launching(['pymol', '-qc'])
    for label, cif_path, desc in CANDIDATES:
        if not Path(cif_path).exists():
            print(f"SKIP {label}: {cif_path} not found")
            continue
        print(f"rendering {label} -- {desc}")
        try:
            render(label, cif_path)
        except Exception as e:
            print(f"  FAIL {label}: {e}")
    print("done.")


if __name__ == "__main__":
    main()
