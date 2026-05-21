"""Orthogonal Vina rescore of Boltz-predicted top-50 complexes.

For each candidate in results/final/top50.csv:
  1. Load the Boltz-predicted CIF
  2. Split into protein (PDB) + ligand (SDF)
  3. Prepare receptor PDBQT (meeko's mk_prepare_receptor)
  4. Prepare ligand PDBQT (meeko MoleculePreparation)
  5. Run vina --score_only on the Boltz pose
     (no re-search — we're asking Vina to evaluate Boltz's pose)
  6. Also run vina --local_only — let Vina locally optimize the pose
     and report the change

Output:
  results/orthogonal_rescore/vina_scores.csv with columns:
    id, vina_score_only_kcal, vina_local_only_kcal, delta_pose

Vina score interpretation:
  - More negative = stronger predicted binding
  - Typical drug binders: -7 to -11 kcal/mol
  - Decoys / non-binders: -3 to -6 kcal/mol
  - For corroboration with Boltz: rank-correlation matters more than absolute
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem

RDLogger.DisableLog("rdApp.*")

PROJECT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT / "results" / "orthogonal_rescore"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CIF_SOURCES = [
    Path("/cosmos/vast/scratch/l1joseph/round0_85062/boltz_results_round0_yamls/predictions"),
    Path("/cosmos/vast/scratch/l1joseph/b1_score_85100/boltz_results_tamgen_b1_yamls/predictions"),
    Path("/cosmos/vast/scratch/l1joseph/b1_score_85121/boltz_results_tamgen_b1_yamls/predictions"),
]
# Tamgen rounds 1, 2 etc are in /cosmos/vast/scratch/l1joseph/runs/boltz_*  or named
SCRATCH = Path("/cosmos/vast/scratch/l1joseph")
for d in SCRATCH.iterdir():
    if d.is_dir() and "score" in d.name and "boltz_results" not in d.name:
        for sub in d.iterdir():
            if sub.is_dir() and "predictions" in str(sub):
                pass
# Easier: scan all */predictions dirs anywhere in scratch
for cif_dir in SCRATCH.rglob("predictions"):
    if cif_dir.is_dir() and cif_dir not in CIF_SOURCES:
        CIF_SOURCES.append(cif_dir)


def find_cif(cand_id: str) -> Path | None:
    """Locate <cand_id>/<cand_id>_model_0.cif under any known prediction dir."""
    for base in CIF_SOURCES:
        candidate = base / cand_id / f"{cand_id}_model_0.cif"
        if candidate.exists():
            return candidate
    return None


def cif_to_pdb_and_sdf(cif: Path, prot_pdb: Path, lig_sdf: Path, ref_smiles: str | None = None):
    """Split a CIF into protein PDB + ligand SDF, preserving the predicted pose.

    Both via openbabel CLI — preserves the Boltz pose. ref_smiles ignored
    (was experimentally used to fix b2_067's broken kekulization but the
    embed-then-overwrite approach corrupted the pose; meeko + obabel fallback
    handles the kekulization case at the PDBQT stage instead).
    """
    pdb_tmp = lig_sdf.with_suffix(".raw.pdb")
    r = subprocess.run(["obabel", str(cif), "-O", str(pdb_tmp)], capture_output=True, text=True)
    if r.returncode != 0 or not pdb_tmp.exists():
        raise RuntimeError(f"obabel failed: {r.stderr[:200]}")

    prot_lines = []
    lig_lines = []
    with open(pdb_tmp) as f:
        for line in f:
            tag = line[:6].strip()
            if tag in ("ATOM", "HETATM"):
                chain = line[21:22]
                if chain == "A":
                    prot_lines.append(line)
                else:
                    lig_lines.append(line)
    with open(prot_pdb, "w") as f:
        f.writelines(prot_lines)
        f.write("TER\nEND\n")
    lig_pdb = lig_sdf.with_suffix(".lig.pdb")
    with open(lig_pdb, "w") as f:
        f.writelines(lig_lines)
        f.write("END\n")
    r = subprocess.run(["obabel", str(lig_pdb), "-O", str(lig_sdf), "-h"], capture_output=True, text=True)
    if r.returncode != 0 or not lig_sdf.exists():
        raise RuntimeError(f"obabel SDF conversion failed: {r.stderr[:200]}")


def prepare_pdbqt(prot_pdb: Path, lig_sdf: Path, prot_pdbqt: Path, lig_pdbqt: Path):
    # Receptor via meeko's mk_prepare_receptor (correct syntax: no --skip_gpf flag)
    r = subprocess.run(
        ["mk_prepare_receptor.py", "--read_pdb", str(prot_pdb),
         "--write_pdbqt", str(prot_pdbqt)],
        capture_output=True, text=True
    )
    if not prot_pdbqt.exists():
        r2 = subprocess.run(
            ["obabel", str(prot_pdb), "-O", str(prot_pdbqt), "-xr"],
            capture_output=True, text=True
        )
        if not prot_pdbqt.exists():
            raise RuntimeError(f"receptor prep failed: meeko={r.stderr[:120]} obabel={r2.stderr[:120]}")

    # Ligand via meeko first, fallback to openbabel if meeko produces invalid AD types
    r = subprocess.run(
        ["mk_prepare_ligand.py", "-i", str(lig_sdf), "-o", str(lig_pdbqt)],
        capture_output=True, text=True
    )
    if lig_pdbqt.exists():
        # sanity check: vina rejects atom types like CG0
        with open(lig_pdbqt) as f:
            content = f.read()
        bad_types = [t for t in ("CG0", "G0") if f" {t} " in content]
        if bad_types:
            lig_pdbqt.unlink()
    if not lig_pdbqt.exists():
        r2 = subprocess.run(
            ["obabel", str(lig_sdf), "-O", str(lig_pdbqt), "-h"],
            capture_output=True, text=True
        )
        if not lig_pdbqt.exists():
            raise RuntimeError(f"ligand prep failed: meeko={r.stderr[:120]} obabel={r2.stderr[:120]}")


def compute_box(lig_pdbqt: Path, pad: float = 8.0) -> tuple[float, float, float, float, float, float]:
    xs, ys, zs = [], [], []
    with open(lig_pdbqt) as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")):
                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    xs.append(x); ys.append(y); zs.append(z)
                except ValueError:
                    continue
    if not xs:
        raise RuntimeError(f"no atoms in {lig_pdbqt}")
    cx = (max(xs) + min(xs)) / 2
    cy = (max(ys) + min(ys)) / 2
    cz = (max(zs) + min(zs)) / 2
    sx = max(max(xs) - min(xs), 12) + pad
    sy = max(max(ys) - min(ys), 12) + pad
    sz = max(max(zs) - min(zs), 12) + pad
    return cx, cy, cz, sx, sy, sz


def vina_score(prot_pdbqt: Path, lig_pdbqt: Path, mode: str = "score_only") -> float | None:
    cx, cy, cz, sx, sy, sz = compute_box(lig_pdbqt)
    cmd = ["vina",
           "--receptor", str(prot_pdbqt),
           "--ligand", str(lig_pdbqt),
           "--center_x", f"{cx:.3f}", "--center_y", f"{cy:.3f}", "--center_z", f"{cz:.3f}",
           "--size_x",   f"{sx:.3f}", "--size_y",   f"{sy:.3f}", "--size_z",   f"{sz:.3f}"]
    if mode == "score_only":
        cmd.append("--score_only")
    elif mode == "local_only":
        cmd.append("--local_only")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        return None
    # Parse: line "Estimated Free Energy of Binding   : -7.5 kcal/mol"
    for line in r.stdout.splitlines():
        if "Estimated Free Energy" in line:
            parts = line.split()
            for p in parts:
                try:
                    return float(p)
                except ValueError:
                    continue
        # Newer vina format: just "  AFFINITY: -7.5"
        if line.strip().startswith("Affinity:") or line.strip().startswith("AFFINITY:"):
            parts = line.split()
            for p in parts:
                try:
                    return float(p)
                except ValueError:
                    continue
    # Try to find first kcal/mol number
    for line in r.stdout.splitlines():
        if "kcal/mol" in line:
            parts = line.replace(":", " ").split()
            for p in parts:
                try:
                    v = float(p)
                    if -20 < v < 5:
                        return v
                except ValueError:
                    continue
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--top-csv", default=str(PROJECT / "results" / "final" / "top50.csv"))
    p.add_argument("--out-csv", default=str(OUT_DIR / "vina_scores.csv"))
    p.add_argument("--limit", type=int, default=0, help="cap for smoke test")
    args = p.parse_args()

    rows = list(csv.DictReader(open(args.top_csv)))
    if args.limit:
        rows = rows[: args.limit]
    print(f"Vina rescore {len(rows)} candidates")
    print(f"CIF source dirs: {len(CIF_SOURCES)}")

    out_rows = []
    n_ok = 0
    n_fail = 0
    for i, r in enumerate(rows, 1):
        cid = r["id"]
        cif = find_cif(cid)
        if cif is None:
            print(f"[{i:>3}/{len(rows)}] {cid:>12}  -- NO CIF; skipping")
            n_fail += 1
            continue
        print(f"[{i:>3}/{len(rows)}] {cid:>12}  cif={cif.name}", end="  ", flush=True)
        try:
            with TemporaryDirectory(prefix=f"vina_{cid}_") as td:
                td_p = Path(td)
                prot_pdb = td_p / "prot.pdb"
                lig_sdf = td_p / "lig.sdf"
                prot_pdbqt = td_p / "prot.pdbqt"
                lig_pdbqt = td_p / "lig.pdbqt"
                cif_to_pdb_and_sdf(cif, prot_pdb, lig_sdf, ref_smiles=r.get("smiles"))
                prepare_pdbqt(prot_pdb, lig_sdf, prot_pdbqt, lig_pdbqt)
                score = vina_score(prot_pdbqt, lig_pdbqt, mode="score_only")
                local = vina_score(prot_pdbqt, lig_pdbqt, mode="local_only")
                delta = (score - local) if (score is not None and local is not None) else None
                out_rows.append({
                    "id": cid,
                    "boltz_aff_C1": r.get("affinity_C1", ""),
                    "vina_score_only": "" if score is None else f"{score:.2f}",
                    "vina_local_only": "" if local is None else f"{local:.2f}",
                    "delta_score_to_local": "" if delta is None else f"{delta:+.2f}",
                })
                print(f"score_only={score}  local_only={local}")
                n_ok += 1
        except Exception as e:
            print(f"FAIL: {e}")
            out_rows.append({"id": cid, "boltz_aff_C1": r.get("affinity_C1", ""),
                             "vina_score_only": "", "vina_local_only": "", "delta_score_to_local": ""})
            n_fail += 1

    out = Path(args.out_csv)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)
    print(f"\nDONE  ok={n_ok}  fail={n_fail}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
