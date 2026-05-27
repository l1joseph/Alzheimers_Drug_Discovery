"""Render Panel A for paper Figure 1: PHGDH structure with HHTH-DBD + inhibitor pocket.

Updated mechanistic framing (per Chen et al. 2025 Cell 188(13), 3513-3529):

  - The HHTH (helix-helix-turn-helix) DNA-binding motif spans residues 103-165
    (within the nucleotide-binding domain).
  - All published PHGDH inhibitor co-crystals converge on a single cofactor-
    adjacent pocket; 30-38% of each inhibitor's pocket-lining residues fall
    inside the HHTH-DBD span (residues 149-156 are in both).
  - The NADH cofactor pose from 6CWA shows the spatial reference.

Visual encoding:
  - PHGDH cartoon: light gray
  - HHTH-DBD region (103-165): RED ribbon segment (cartoon color)
  - Inhibitor pocket overlap with HHTH (149-156): YELLOW sidechain sticks
  - Inhibitor pocket OUTSIDE HHTH (77, 173-177, 192, 205-215): ORANGE sidechain sticks
  - NADH cofactor (from 6CWA aligned): CYAN sticks
  - K58 ligand (from 6RJ3 aligned): MAGENTA sticks - one representative inhibitor

Output: docs/figures/paper/fig1A_phgdh_pockets.png at 300 DPI ray-traced.

Run with the boltz-rocm env active:
    pymol -cqr scripts/render_fig1_panelA.py
"""
from pathlib import Path

import pymol
from pymol import cmd

PROJECT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery")
APO = PROJECT / "data" / "targets" / "phgdh_6CWA_apo.pdb"
CWA = PROJECT / "data" / "structures_reference" / "6CWA_PHGDH_NADH_3PG_ternary.cif"
RJ3 = PROJECT / "data" / "structures_reference" / "6RJ3_K58_BI-cmpd-15.cif"
OUT_PNG = PROJECT / "docs" / "figures" / "paper" / "fig1A_phgdh_pockets.png"
OUT_PNG.parent.mkdir(parents=True, exist_ok=True)

# Chen 2025 HHTH-DBD residue span
HHTH_LO, HHTH_HI = 103, 165

# Inhibitor pocket residues from scripts/check_pocket_overlap.py
# Union of pocket residues across all four inhibitor co-crystals (ONV, ONS, K58, K5K)
POCKET_ALL = [77, 150, 151, 152, 153, 154, 155, 173, 174, 175, 176, 177, 192,
              205, 206, 207, 209, 211, 212, 215]
# The 149-156 subset is the overlap with the HHTH-DBD span
POCKET_HHTH_OVERLAP = [r for r in POCKET_ALL if HHTH_LO <= r <= HHTH_HI]
POCKET_NONHHTH = [r for r in POCKET_ALL if not (HHTH_LO <= r <= HHTH_HI)]


def main():
    pymol.finish_launching(['pymol', '-qc'])
    cmd.reinitialize()

    # Load apo target as anchor
    cmd.load(str(APO), "apo")
    cmd.remove("solvent")

    # Load NADH-containing reference + K58 co-crystal, align both to apo
    cmd.load(str(CWA), "cwa")
    cmd.load(str(RJ3), "rj3")
    cmd.cealign("apo and polymer and chain A", "cwa and polymer and chain A")
    cmd.cealign("apo and polymer and chain A", "rj3 and polymer and chain A")

    # Strip non-cofactor heteroatoms from references (keep only NADH and K58 ligands)
    cmd.remove("cwa and not resn NAI")
    cmd.remove("rj3 and not resn K58")
    # Keep only chain A copies of the ligands
    cmd.remove("cwa and not chain A")
    cmd.remove("rj3 and not chain A")

    # === STYLE ===
    cmd.hide("everything")
    cmd.bg_color("white")

    # 1) PHGDH cartoon — light gray
    cmd.show("cartoon", "apo and polymer")
    cmd.color("gray80", "apo and polymer")

    # 2) HHTH-DBD region (103-165) — RED ribbon
    cmd.color("firebrick", f"apo and polymer and resi {HHTH_LO}-{HHTH_HI}")

    # 3) Inhibitor pocket OUTSIDE HHTH — ORANGE sticks (sidechain)
    sel_str_non = "+".join(str(r) for r in POCKET_NONHHTH)
    cmd.select("pocket_nonhhth", f"apo and polymer and resi {sel_str_non} and sidechain")
    cmd.show("sticks", "pocket_nonhhth")
    cmd.color("orange", "pocket_nonhhth and elem C")
    cmd.util.cnc("pocket_nonhhth")
    cmd.set("stick_radius", 0.20, "pocket_nonhhth")

    # 4) Inhibitor pocket OVERLAP with HHTH — YELLOW sticks (the key residues, 149-156)
    sel_str_overlap = "+".join(str(r) for r in POCKET_HHTH_OVERLAP)
    cmd.select("pocket_hhth_overlap", f"apo and polymer and resi {sel_str_overlap} and sidechain")
    cmd.show("sticks", "pocket_hhth_overlap")
    cmd.color("yellow", "pocket_hhth_overlap and elem C")
    cmd.util.cnc("pocket_hhth_overlap")
    cmd.set("stick_radius", 0.25, "pocket_hhth_overlap")

    # 5) NADH cofactor from 6CWA (aligned) — CYAN sticks
    cmd.show("sticks", "cwa and resn NAI")
    cmd.color("cyan", "cwa and resn NAI and elem C")
    cmd.util.cnc("cwa and resn NAI")
    cmd.set("stick_radius", 0.18, "cwa and resn NAI")

    # 6) K58 inhibitor from 6RJ3 (aligned) — MAGENTA sticks (representative inhibitor)
    cmd.show("sticks", "rj3 and resn K58")
    cmd.color("magenta", "rj3 and resn K58 and elem C")
    cmd.util.cnc("rj3 and resn K58")
    cmd.set("stick_radius", 0.20, "rj3 and resn K58")

    # === RENDER ===
    cmd.set("ray_shadows", 0)
    cmd.set("ray_trace_mode", 1)
    cmd.set("antialias", 2)
    cmd.set("ambient", 0.35)
    cmd.set("cartoon_transparency", 0.0)

    # Orient: focus on the pocket region, both pocket residues and HHTH visible
    cmd.orient("apo and polymer")
    cmd.zoom("(apo and polymer and resi 100-220) or (cwa and resn NAI) or (rj3 and resn K58)", 4)
    cmd.rotate("y", 30)
    cmd.rotate("x", -15)

    cmd.png(str(OUT_PNG), width=900, height=900, dpi=300, ray=1)
    print(f"wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
