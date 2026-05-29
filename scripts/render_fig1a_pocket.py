"""Render paper Figure 1 panel A: PHGDH cofactor/inhibitor pocket + HHTH-DBD.

Replacement for the previous fig1a.png — same pocket, new orientation and a
colorblind-safe colour scheme drawn from the /fig (Paul Tol) palette so the
structural panel matches the rest of the paper's figures.

Visual encoding (Paul Tol colours):
  - PHGDH cartoon ............ light gray (neutral context)
  - HHTH-DBD (103-165) ....... wine   #882255  ribbon
  - pocket / HHTH overlap .... sand   #DDCC77  sidechain sticks (resi 150-155)
  - pocket / outside HHTH .... lt-blue #88CCEE sidechain sticks
  - NADH cofactor (6CWA) ..... teal   #44AA99  sticks
  - K58 inhibitor (6RJ3) ..... indigo #332288  sticks (representative inhibitor)

Output: docs/figures/paper/fig1a.png (900x900, ray-traced, 300 DPI).

Run with the boltz-rocm env active:
    pymol -cqr scripts/render_fig1a_pocket.py
"""
from pathlib import Path

import pymol
from pymol import cmd

PROJECT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery")
APO = PROJECT / "data" / "targets" / "phgdh_6CWA_apo.pdb"
CWA = PROJECT / "data" / "structures_reference" / "6CWA_PHGDH_NADH_3PG_ternary.cif"
RJ3 = PROJECT / "data" / "structures_reference" / "6RJ3_K58_BI-cmpd-15.cif"
# Alternative Tol-palette render. Fig 1 panel A uses Ziheng's fig1a.png; this
# writes to a separate name so it never clobbers that file.
OUT_PNG = PROJECT / "docs" / "figures" / "paper" / "fig1a_tol_variant.png"
OUT_PNG.parent.mkdir(parents=True, exist_ok=True)

# Paul Tol colorblind-safe palette (matches /fig PALETTE), as 0-1 RGB.
TOL = {
    "tol_indigo":  (0.200, 0.133, 0.533),   # #332288
    "tol_ltblue":  (0.533, 0.800, 0.933),   # #88CCEE
    "tol_teal":    (0.267, 0.667, 0.600),   # #44AA99
    "tol_sand":    (0.867, 0.800, 0.467),   # #DDCC77
    "tol_wine":    (0.533, 0.133, 0.333),   # #882255
}

HHTH_LO, HHTH_HI = 103, 165
POCKET_ALL = [77, 150, 151, 152, 153, 154, 155, 173, 174, 175, 176, 177, 192,
              205, 206, 207, 209, 211, 212, 215]
POCKET_HHTH_OVERLAP = [r for r in POCKET_ALL if HHTH_LO <= r <= HHTH_HI]
POCKET_NONHHTH = [r for r in POCKET_ALL if not (HHTH_LO <= r <= HHTH_HI)]


def main():
    pymol.finish_launching(["pymol", "-qc"])
    cmd.reinitialize()
    for name, rgb in TOL.items():
        cmd.set_color(name, list(rgb))

    cmd.load(str(APO), "apo")
    cmd.remove("solvent")
    cmd.load(str(CWA), "cwa")
    cmd.load(str(RJ3), "rj3")
    cmd.cealign("apo and polymer and chain A", "cwa and polymer and chain A")
    cmd.cealign("apo and polymer and chain A", "rj3 and polymer and chain A")
    cmd.remove("cwa and not resn NAI")
    cmd.remove("rj3 and not resn K58")
    cmd.remove("cwa and not chain A")
    cmd.remove("rj3 and not chain A")

    # === STYLE ===
    cmd.hide("everything")
    cmd.bg_color("white")

    cmd.show("cartoon", "apo and polymer")
    cmd.color("gray85", "apo and polymer")
    cmd.set("cartoon_transparency", 0.10, "apo and polymer")

    # HHTH-DBD ribbon — wine
    cmd.color("tol_wine", f"apo and polymer and resi {HHTH_LO}-{HHTH_HI}")
    cmd.set("cartoon_transparency", 0.0, f"apo and polymer and resi {HHTH_LO}-{HHTH_HI}")

    # Pocket residues OUTSIDE HHTH — light-blue sticks
    sel_non = "+".join(str(r) for r in POCKET_NONHHTH)
    cmd.select("p_non", f"apo and polymer and resi {sel_non} and sidechain")
    cmd.show("sticks", "p_non")
    cmd.color("tol_ltblue", "p_non and elem C")
    cmd.util.cnc("p_non")
    cmd.set("stick_radius", 0.18, "p_non")

    # Pocket residues OVERLAPPING HHTH (149-156) — sand sticks
    sel_ov = "+".join(str(r) for r in POCKET_HHTH_OVERLAP)
    cmd.select("p_ov", f"apo and polymer and resi {sel_ov} and sidechain")
    cmd.show("sticks", "p_ov")
    cmd.color("tol_sand", "p_ov and elem C")
    cmd.util.cnc("p_ov")
    cmd.set("stick_radius", 0.25, "p_ov")

    # NADH cofactor — teal sticks
    cmd.show("sticks", "cwa and resn NAI")
    cmd.color("tol_teal", "cwa and resn NAI and elem C")
    cmd.util.cnc("cwa and resn NAI")
    cmd.set("stick_radius", 0.18, "cwa and resn NAI")

    # K58 inhibitor — indigo sticks
    cmd.show("sticks", "rj3 and resn K58")
    cmd.color("tol_indigo", "rj3 and resn K58 and elem C")
    cmd.util.cnc("rj3 and resn K58")
    cmd.set("stick_radius", 0.22, "rj3 and resn K58")

    # === RENDER ===
    cmd.set("ray_shadows", 0)
    cmd.set("ray_trace_mode", 1)
    cmd.set("antialias", 2)
    cmd.set("ambient", 0.38)
    cmd.set("ray_trace_color", "gray30")

    # New orientation: focus on the pocket + cofactor, distinct from prior view
    cmd.orient("(cwa and resn NAI) or (rj3 and resn K58) or "
               f"(apo and polymer and resi {HHTH_LO}-{HHTH_HI})")
    cmd.zoom("(cwa and resn NAI) or (rj3 and resn K58) or "
             f"(apo and polymer and resi {HHTH_LO}-{HHTH_HI})", 2)
    cmd.rotate("y", -55)
    cmd.rotate("x", 18)

    cmd.png(str(OUT_PNG), width=900, height=900, dpi=300, ray=1)
    print(f"wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
