"""All-pairs ligand centroid distance matrix in the apo PHGDH frame.

Each inhibitor co-crystal (6PLF/ONV, 6PLG/ONS, 6RJ3/K58, 6RJ6/K5K, 7EWH/HMT) plus
the endogenous NADH and 3PG (6CWA) is superposed onto the 6CWA-apo backbone by
chain-A cealign; the bound-ligand centroid is read in the apo frame and an
all-pairs centroid distance matrix is computed.

Writes results/pocket_centroid_distances.csv.
Run:  pymol -cqr scripts/pocket_distance_matrix.py
"""
from pathlib import Path
import csv
import numpy as np
import pymol
from pymol import cmd

PROJECT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery")
APO = PROJECT / "data" / "targets" / "phgdh_6CWA_apo.pdb"
XT = PROJECT / "data" / "structures"

# (label, pdb, ligand resname)
LIGANDS = [
    ("compound 1 (ONV)", "6PLF", "ONV"),
    ("compound 15 (ONS)", "6PLG", "ONS"),
    ("compound 15 (K58)", "6RJ3", "K58"),
    ("BI-4924 (K5K)", "6RJ6", "K5K"),
    ("homoharringtonine (HMT)", "7EWH", "HMT"),
    ("NADH", "6CWA", "NAI"),
    ("3PG", "6CWA", "3PG"),
]


def main():
    pymol.finish_launching(["pymol", "-qc"])
    centroids = {}
    for label, pdb, resn in LIGANDS:
        cmd.reinitialize()
        cmd.load(str(APO), "apo")
        cmd.load(str(XT / f"{pdb}.cif"), "xt")
        cmd.remove("solvent")
        cmd.cealign("apo and polymer and chain A", "xt and polymer and chain A")
        sel = f"xt and resn {resn}"
        if cmd.count_atoms(f"{sel} and chain A"):
            sel = f"{sel} and chain A"
        if cmd.count_atoms(sel) == 0:
            print(f"WARN no atoms for {label} ({resn} in {pdb})")
            continue
        centroids[label] = np.array(cmd.centerofmass(sel))

    labels = [l for l, _, _ in LIGANDS if l in centroids]
    n = len(labels)
    M = np.zeros((n, n))
    for i, a in enumerate(labels):
        for j, b in enumerate(labels):
            M[i, j] = np.linalg.norm(centroids[a] - centroids[b])

    out = PROJECT / "results" / "pocket_centroid_distances.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([""] + labels)
        for i, a in enumerate(labels):
            w.writerow([a] + [f"{M[i, j]:.2f}" for j in range(n)])
    print(f"wrote {out}")
    print("       " + " ".join(f"{l.split('(')[0].strip()[:6]:>7}" for l in labels))
    for i, a in enumerate(labels):
        print(f"{a.split('(')[0].strip()[:6]:>7} " + " ".join(f"{M[i, j]:7.2f}" for j in range(n)))


if __name__ == "__main__":
    main()
