"""Sanity-check the agent's finding that 6PLF and 6RJ3 ligands occupy near-identical
positions in the monomer frame.

Procedure:
  1. Load 6PLF (NCT-cmpd-1 = ONV at "allosteric" site, Pacold 2016)
  2. Load 6RJ3 (BI-cmpd-15 = K58 at NADH/catalytic site, Spillier 2019)
  3. Align both protein chains A onto our apo target (6CWA-apo)
  4. Compute centroids of each ligand IN THE APO FRAME
  5. Compute centroid-centroid distance
  6. Print pocket residue ranges (numbered) for both ligands
  7. Also compute pairwise atomic distances between the two ligands

If centroids are <2 Å apart, the two pockets are essentially overlapping in 3D.
If 5-15 Å apart, they are distinct but adjacent (typical for moonlighting enzymes).
If >15 Å apart, they are far separated and the agent's finding was an alignment bug.

Run with the boltz-rocm conda env active:
    conda activate boltz-rocm
    pymol -cqr scripts/check_pocket_overlap.py
"""
from pathlib import Path
import json

import pymol
from pymol import cmd

PROJECT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery")
REF = PROJECT / "data" / "structures_reference"
APO = PROJECT / "data" / "targets" / "phgdh_6CWA_apo.pdb"


def centroid(selection):
    """Return (x, y, z) centroid of all atoms in selection (in current model frame)."""
    model = cmd.get_model(selection)
    if not model.atom:
        return None
    xs = [a.coord[0] for a in model.atom]
    ys = [a.coord[1] for a in model.atom]
    zs = [a.coord[2] for a in model.atom]
    return (sum(xs)/len(xs), sum(ys)/len(ys), sum(zs)/len(zs))


def dist(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** 0.5


def get_pocket_residues(selection_within_5):
    """Return sorted list of (chain, resi, resn) tuples for pocket residues."""
    model = cmd.get_model(selection_within_5)
    seen = set()
    for a in model.atom:
        key = (a.chain, int(a.resi), a.resn)
        seen.add(key)
    return sorted(seen, key=lambda x: (x[0], x[1]))


def main():
    pymol.finish_launching(['pymol', '-qc'])

    # 1. Load reference apo as the anchor frame
    cmd.load(str(APO), "apo")
    cmd.select("apo_polymer", "apo and polymer and chain A")

    # 2. Load 6PLF (ONV at allosteric site)
    cmd.load(str(REF / "6PLF_ONV_NCT-cmpd-1.cif"), "plf")
    # Pacold 2016 deposited PHGDH with ligand code ONV
    cmd.select("plf_polymer", "plf and polymer and chain A")
    cmd.select("plf_ligand", "plf and resn ONV")
    nlig_plf = cmd.count_atoms("plf_ligand")
    print(f"6PLF ligand (ONV) atoms: {nlig_plf}")

    # 3. Load 6RJ3 (K58 at NADH site)
    cmd.load(str(REF / "6RJ3_K58_BI-cmpd-15.cif"), "rj3")
    cmd.select("rj3_polymer", "rj3 and polymer and chain A")
    cmd.select("rj3_ligand", "rj3 and resn K58")
    nlig_rj3 = cmd.count_atoms("rj3_ligand")
    print(f"6RJ3 ligand (K58) atoms: {nlig_rj3}")

    # 4. Align both protein chains onto apo. Use cealign for robustness across
    #    different deposition orientations.
    rms_plf = cmd.cealign("apo_polymer", "plf_polymer")
    rms_rj3 = cmd.cealign("apo_polymer", "rj3_polymer")
    print(f"\n6PLF -> 6CWA-apo  RMSD: {rms_plf['RMSD']:.3f} A (aligned residues: {rms_plf['alignment_length']})")
    print(f"6RJ3 -> 6CWA-apo  RMSD: {rms_rj3['RMSD']:.3f} A (aligned residues: {rms_rj3['alignment_length']})")

    # 5. Compute ligand centroids IN APO FRAME (cealign carries the ligand with the protein)
    c_plf = centroid("plf_ligand")
    c_rj3 = centroid("rj3_ligand")
    print(f"\nONV (allosteric) centroid:  ({c_plf[0]:7.2f}, {c_plf[1]:7.2f}, {c_plf[2]:7.2f})")
    print(f"K58 (NADH site)  centroid:  ({c_rj3[0]:7.2f}, {c_rj3[1]:7.2f}, {c_rj3[2]:7.2f})")
    centroid_dist = dist(c_plf, c_rj3)
    print(f"\nCENTROID DISTANCE: {centroid_dist:.2f} A")

    if centroid_dist < 2:
        verdict = "OVERLAPPING — pockets occupy essentially the same volume"
    elif centroid_dist < 5:
        verdict = "ADJACENT — pockets share contact residues"
    elif centroid_dist < 12:
        verdict = "NEARBY — pockets distinct but coupled allosterically plausible"
    else:
        verdict = "DISTANT — pockets clearly separated"
    print(f"Verdict: {verdict}\n")

    # 6. Minimum atomic distance between the two ligand sets
    # Build atom lists in apo frame
    plf_atoms = cmd.get_model("plf_ligand").atom
    rj3_atoms = cmd.get_model("rj3_ligand").atom
    min_d = float("inf")
    for a in plf_atoms:
        for b in rj3_atoms:
            d = ((a.coord[0]-b.coord[0])**2 + (a.coord[1]-b.coord[1])**2 + (a.coord[2]-b.coord[2])**2) ** 0.5
            if d < min_d:
                min_d = d
    print(f"Minimum atom-atom distance between the two ligands: {min_d:.2f} A")
    print(f"(typical bonded distance ~1.5 A; vdW contact ~3-4 A)\n")

    # 7. Pocket residue lists (within 5 A of each ligand)
    cmd.select("plf_pocket", "byres (apo_polymer within 5 of plf_ligand)")
    cmd.select("rj3_pocket", "byres (apo_polymer within 5 of rj3_ligand)")
    plf_res = get_pocket_residues("plf_pocket")
    rj3_res = get_pocket_residues("rj3_pocket")
    print(f"6PLF (ONV) pocket residues on apo backbone ({len(plf_res)}):")
    for r in plf_res:
        print(f"  {r[0]} {r[1]:>3} {r[2]}")
    print(f"\n6RJ3 (K58) pocket residues on apo backbone ({len(rj3_res)}):")
    for r in rj3_res:
        print(f"  {r[0]} {r[1]:>3} {r[2]}")
    shared = set((r[0], r[1]) for r in plf_res) & set((r[0], r[1]) for r in rj3_res)
    print(f"\nSHARED residues (in both pockets): {len(shared)}")
    if shared:
        for r in sorted(shared):
            print(f"  {r[0]} {r[1]}")

    # 8. Also compare to our project's pocket-center JSON files if they exist
    print()
    for name in ["pocket_center.json", "pocket_center_allosteric.json"]:
        p = PROJECT / "data" / name
        if p.exists():
            with open(p) as f:
                d = json.load(f)
            print(f"{name}: {d}")
        else:
            print(f"(no {name} in repo root)")

    cmd.quit()


if __name__ == "__main__":
    main()
