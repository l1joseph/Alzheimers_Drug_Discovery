"""Render Panel A for paper Figure 1: PHGDH structure with two pockets labeled.

Loads phgdh_6CWA_apo.pdb (cartoon, gray). Highlights two pockets using the
project's own pocket-center JSON files (these were computed by aligning the
NCT-503 series allosteric co-crystals to 6CWA and taking centroids):

  - NCT-503 allosteric site center -> orange labeled sphere + nearby pocket residues
    (within 6 A of center). Source: pocket_center_allosteric.json (6PLF ONV).
  - NADH / catalytic Rossmann site -> cyan labeled sphere + nearby pocket residues.
    Source: pocket_center.json (6CWA catalytic).

The two pocket-residue rings are chosen so they don't share atoms (residues
appearing in both are assigned to the closer center to keep distinct patches).

Output: docs/figures/paper/fig1A_phgdh_pockets.png  800x800, ray-traced.

Run with the boltz-rocm env active:
    pymol -cqr scripts/render_fig1_panelA.py
"""
import json
import math
from pathlib import Path

import pymol
from pymol import cmd

PROJECT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery")
APO = PROJECT / "data" / "targets" / "phgdh_6CWA_apo.pdb"
POCKET_CAT = PROJECT / "pocket_center.json"
POCKET_ALLO = PROJECT / "pocket_center_allosteric.json"
OUT_PNG = PROJECT / "docs" / "figures" / "paper" / "fig1A_phgdh_pockets.png"
OUT_PNG.parent.mkdir(parents=True, exist_ok=True)

POCKET_R = 7.5  # A radius used to define pocket-lining residues from each center


def load_center(path: Path) -> tuple[float, float, float]:
    d = json.loads(path.read_text())
    return (d["center_x"], d["center_y"], d["center_z"])


def residues_near_point(target: str, point: tuple[float, float, float],
                        radius: float) -> list[int]:
    """Return CA-residue numbers in `target` whose CA atom is within `radius` of point."""
    px, py, pz = point
    cmd.pseudoatom("__center", pos=[px, py, pz])
    sel = f"byres ({target} and polymer) within {radius} of __center"
    cmd.select("__tmp", sel)
    resis = set()
    cmd.iterate("__tmp and name CA", "resis.add(int(resi))",
                space={"resis": resis})
    cmd.delete("__center")
    cmd.delete("__tmp")
    return sorted(resis)


def dist(a, b):
    return math.dist(a, b)


def main():
    pymol.finish_launching(['pymol', '-qc'])

    cat_center = load_center(POCKET_CAT)
    allo_center = load_center(POCKET_ALLO)
    print(f"catalytic center: {cat_center}")
    print(f"allosteric center: {allo_center}")
    print(f"d(catalytic, allosteric) = {dist(cat_center, allo_center):.2f} A")

    cmd.reinitialize()
    cmd.load(str(APO), "phgdh")
    cmd.remove("solvent")
    cmd.remove("resn SO4+PEG+EDO+CL+NA+ZN+GOL+ACT+MG+CA")

    # First find candidate residues near each center.
    cat_cand = residues_near_point("phgdh", cat_center, POCKET_R)
    allo_cand = residues_near_point("phgdh", allo_center, POCKET_R)
    print(f"catalytic candidates ({len(cat_cand)}): {cat_cand}")
    print(f"allosteric candidates ({len(allo_cand)}): {allo_cand}")

    # For overlap, assign the residue to the closer center (by CA position).
    cat_resi = []
    allo_resi = []
    all_cand = sorted(set(cat_cand) | set(allo_cand))
    for r in all_cand:
        coords = []
        cmd.iterate_state(1, f"phgdh and polymer and resi {r} and name CA",
                          "coords.append((x,y,z))", space={"coords": coords})
        if not coords:
            continue
        ca = coords[0]
        if dist(ca, cat_center) <= dist(ca, allo_center):
            cat_resi.append(r)
        else:
            allo_resi.append(r)
    print(f"final catalytic ({len(cat_resi)}): {cat_resi}")
    print(f"final allosteric ({len(allo_resi)}): {allo_resi}")

    cat_str = "+".join(str(r) for r in cat_resi) or "0"
    allo_str = "+".join(str(r) for r in allo_resi) or "0"
    cmd.select("cat_pocket", f"phgdh and polymer and resi {cat_str}")
    cmd.select("allo_pocket", f"phgdh and polymer and resi {allo_str}")

    # Style: cartoon backbone in light gray
    cmd.hide("everything")
    cmd.show("cartoon", "phgdh and polymer")
    cmd.color("gray80", "phgdh and polymer")
    cmd.set("cartoon_transparency", 0.0)

    # NCT-503 allosteric pocket — orange sticks (sidechains)
    cmd.show("sticks", "allo_pocket and sidechain")
    cmd.color("orange", "allo_pocket and elem C")
    cmd.util.cnc("allo_pocket")
    cmd.set("stick_radius", 0.20, "allo_pocket")

    # NADH catalytic pocket — cyan sticks (sidechains)
    cmd.show("sticks", "cat_pocket and sidechain")
    cmd.color("cyan", "cat_pocket and elem C")
    cmd.util.cnc("cat_pocket")
    cmd.set("stick_radius", 0.20, "cat_pocket")

    # Pocket-center marker spheres (no PyMOL labels — those will be added in
    # post via matplotlib so they don't get occluded by the structure)
    cmd.pseudoatom("allo_marker", pos=list(allo_center), color="orange")
    cmd.show("spheres", "allo_marker")
    cmd.set("sphere_scale", 2.0, "allo_marker")
    cmd.set("sphere_transparency", 0.20, "allo_marker")

    cmd.pseudoatom("cat_marker", pos=list(cat_center), color="cyan")
    cmd.show("spheres", "cat_marker")
    cmd.set("sphere_scale", 2.0, "cat_marker")
    cmd.set("sphere_transparency", 0.20, "cat_marker")

    # Render style
    cmd.bg_color("white")
    cmd.set("ray_shadows", 0)
    cmd.set("ray_trace_mode", 1)
    cmd.set("antialias", 2)
    cmd.set("ambient", 0.35)

    # Orient on the whole polymer, then rotate so pockets face camera
    cmd.orient("polymer")
    cmd.zoom("polymer", 6)
    cmd.rotate("y", 60)
    cmd.rotate("x", -20)

    cmd.png(str(OUT_PNG), width=800, height=800, dpi=300, ray=1)
    print(f"wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
