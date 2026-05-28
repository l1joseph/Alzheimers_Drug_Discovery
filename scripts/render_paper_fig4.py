"""Render PyMOL panels for paper Figure 4 + K58 source comparison.

Outputs to docs/figures/paper/:
  fig4_K58_real_6RJ3.png      — real co-crystal, the most defensible scientific reference
  fig4_K58_boltz_pred.png     — Boltz-predicted K58 vs 6CWA-apo (apples-to-apples with the rest of the pipeline)
  fig4_K5K_boltz.png          — Boltz-predicted (already exists; this re-renders consistently)
  fig4_r2b2_107_boltz.png     — Boltz-predicted; sole novel-scaffold Tier-2 survivor

All consistent style: cyan-C ligand sticks, gray cartoon, wheat pocket sticks
within 5 Å, yellow H-bond dashes <3.5 Å. 800x800 ray-traced PNG at 300 DPI.

Run with the boltz-rocm env active:
    pymol -cqr scripts/render_paper_fig4.py
"""
from pathlib import Path

import pymol
from pymol import cmd

OUT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery/docs/figures/paper")
OUT.mkdir(parents=True, exist_ok=True)

PROJECT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery")
REF_DIR = PROJECT / "data" / "structures_reference"
PRED_DIR = PROJECT / "data" / "predicted_poses"

PANELS = [
    # (label, structure_path, ligand_selection)
    (
        "fig4_K58_real_6RJ3",
        REF_DIR / "6RJ3_K58_BI-cmpd-15.cif",
        "resn K58",
    ),
    (
        "fig4_K58_boltz_pred",
        PRED_DIR / "K58_boltz_pred.cif",
        "not polymer and not solvent",
    ),
    (
        "fig4_K5K_boltz",
        PRED_DIR / "K5K_boltz_pred.cif",
        "not polymer and not solvent",
    ),
    (
        "fig4_r2b2_107_boltz",
        PRED_DIR / "r2b2_107_boltz_pred.cif",
        "not polymer and not solvent",
    ),
    (
        "fig4_b4_112_boltz",
        PRED_DIR / "b4_112_boltz_pred.cif",
        "not polymer and not solvent",
    ),
]


def render(label, cif_path, lig_sel, orient_sel=None):
    orient_sel = orient_sel or lig_sel
    cmd.reinitialize()
    cmd.load(cif_path, label)

    # In real PDB co-crystals, also strip solvent / sulfate / common buffer hits
    cmd.remove("solvent")
    cmd.remove("resn SO4 or resn PEG or resn EDO or resn CL or resn NA or resn ZN")

    cmd.select("prot", "polymer")
    cmd.select("lig", lig_sel)
    if cmd.count_atoms("lig") == 0:
        print(f"  WARN: no ligand atoms in {cif_path} for selection '{lig_sel}'")
        return

    cmd.hide("everything")
    cmd.show("cartoon", "prot")
    cmd.color("gray80", "prot")
    cmd.show("sticks", "lig")
    cmd.color("cyan", "lig and elem C")
    cmd.util.cnc("lig")
    cmd.set("stick_radius", 0.22, "lig")

    # Pocket residues within 5 Å of the ligand
    cmd.select("pocket", "byres prot within 5 of lig")
    cmd.show("sticks", "pocket")
    cmd.color("wheat", "pocket and elem C")
    cmd.util.cnc("pocket")
    cmd.set("stick_radius", 0.13, "pocket")

    # Polar contacts (H-bonds)
    cmd.distance("hbonds", "lig", "pocket", 3.5, mode=2)
    cmd.color("yellow", "hbonds")
    cmd.hide("labels", "hbonds")

    # Render style
    cmd.bg_color("white")
    cmd.set("ray_shadows", 0)
    cmd.set("ray_trace_mode", 1)
    cmd.set("antialias", 2)
    cmd.set("ambient", 0.3)
    cmd.set("cartoon_transparency", 0.15)

    # View
    cmd.orient(orient_sel)
    cmd.zoom(orient_sel, 6)

    out_png = OUT / f"{label}.png"
    cmd.png(str(out_png), width=800, height=800, dpi=300, ray=1)
    print(f"  wrote {out_png}")


def main():
    pymol.finish_launching(['pymol', '-qc'])
    for label, cif_path, lig_sel in PANELS:
        cif_path = Path(cif_path)
        if not cif_path.exists():
            print(f"  SKIP {label}: {cif_path} does not exist")
            continue
        print(f"rendering {label}  <-  {cif_path}")
        try:
            render(label, str(cif_path), lig_sel)
        except Exception as e:
            print(f"  FAIL {label}: {e}")
    print("done.")


if __name__ == "__main__":
    main()
