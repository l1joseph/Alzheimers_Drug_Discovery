"""Build the final top-N candidate hits report.

For each top candidate:
  - canonical SMILES
  - Boltz affinity (C1, the primary apo target)
  - Boltz affinity (C2, +3PG ternary)  if scored — mechanism flag
  - drug-likeness fields (SA, MW, logP, HBD, HBA, PAINS)
  - source / lineage
  - Tanimoto to nearest known PHGDH binder

Outputs:
  - results/final/top50.csv     full table
  - results/final/top50.sdf     RDKit-built SDF for chemistry-tool import
  - results/final/top50.md      human-readable markdown summary

Mechanism classification:
  - 'NADH-competitive'   : strong C1 affinity AND retained in C2 (Δ < 0.3 logKd)
  - '3PG-competitive'    : strong C1, much weaker in C2 (Δ ≥ 0.3 logKd)
  - 'C1 only'            : strong C1, no C2 score available
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, DataStructs, Descriptors, SDWriter

RDLogger.DisableLog("rdApp.*")

PROJECT = Path(__file__).resolve().parent.parent
FINAL = PROJECT / "results" / "final"
FINAL.mkdir(parents=True, exist_ok=True)
TOP_N = 50
MECH_THRESHOLD = 0.3  # logKd shift considered 3PG-sensitive


def load_csv(path: Path, key: str = "id") -> dict:
    if not path.exists():
        return {}
    return {r[key]: r for r in csv.DictReader(open(path))}


def fingerprint(smi: str):
    mol = Chem.MolFromSmiles(smi)
    return AllChem.GetMorganFingerprintAsBitVect(mol, 2, 2048) if mol else None


def nearest_known_binder(smi: str, known_fps: list[tuple[str, "Fp"]]) -> tuple[str, float]:
    fp = fingerprint(smi)
    if fp is None or not known_fps:
        return ("", 0.0)
    best_name, best_t = "", 0.0
    for name, kfp in known_fps:
        t = DataStructs.TanimotoSimilarity(fp, kfp)
        if t > best_t:
            best_t = t
            best_name = name
    return (best_name, best_t)


def main():
    # Sources
    leaderboard_with_filters = load_csv(PROJECT / "results" / "combined" / "leaderboard_with_filters.csv")
    if not leaderboard_with_filters:
        raise SystemExit("missing results/combined/leaderboard_with_filters.csv; run score_synthesizability.py first")

    # C2 ensemble (3PG-co-bound) scores, keyed by C1 id (strip "c2_" prefix)
    c2_by_c1id: dict[str, dict] = {}
    c2_path = PROJECT / "results" / "ensemble_c2" / "scores.csv"
    if c2_path.exists():
        for r in csv.DictReader(open(c2_path)):
            c1id = r["input_id"].replace("c2_", "", 1)
            c2_by_c1id[c1id] = r

    # Known binders for fingerprint comparison
    known = list(csv.DictReader(open(PROJECT / "data" / "libraries" / "known_phgdh_binders.csv")))
    known_fps = [(r["name"], fingerprint(r["smiles"])) for r in known]
    known_fps = [(n, fp) for n, fp in known_fps if fp is not None]

    # Rank ALL non-c2_-prefixed rows (those are duplicates of base candidates) by C1 affinity
    base_rows = [r for r in leaderboard_with_filters.values() if not r["id"].startswith("c2_")]
    base_rows.sort(key=lambda r: float(r["affinity_pred_value"]))

    out_rows = []
    for r in base_rows[:TOP_N]:
        smi = r["smiles"]
        if not smi:
            continue
        c1_aff = float(r["affinity_pred_value"])
        c2_r = c2_by_c1id.get(r["id"])
        c2_aff = float(c2_r["affinity_affinity_pred_value"]) if c2_r else None

        if c2_aff is None:
            mech = "C1 only"
            delta = ""
        else:
            delta = c2_aff - c1_aff
            mech = "NADH-competitive" if abs(delta) < MECH_THRESHOLD else "3PG-competitive"
            delta = f"{delta:+.2f}"

        nearest_name, nearest_tan = nearest_known_binder(smi, known_fps)

        out_rows.append({
            "rank": len(out_rows) + 1,
            "id": r["id"],
            "source": r["source"],
            "smiles": smi,
            "affinity_C1": f"{c1_aff:+.2f}",
            "prob_binary": r["prob_binary"],
            "confidence": r["confidence"],
            "affinity_C2": f"{c2_aff:+.2f}" if c2_aff is not None else "",
            "delta_C2_minus_C1": delta,
            "mechanism": mech,
            "drug_like_pass": r["drug_like_pass"],
            "SA_score": r["sa_score"],
            "MW": r["mw"],
            "logP": r["logp"],
            "HBD": r["hbd"],
            "HBA": r["hba"],
            "PAINS": r["pains"],
            "nearest_known_binder": nearest_name,
            "tanimoto_to_nearest": f"{nearest_tan:.2f}",
        })

    csv_path = FINAL / "top50.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)
    print(f"wrote {csv_path} ({len(out_rows)} rows)")

    sdf_path = FINAL / "top50.sdf"
    writer = SDWriter(str(sdf_path))
    for r in out_rows:
        mol = Chem.MolFromSmiles(r["smiles"])
        if mol is None:
            continue
        mol.SetProp("_Name", r["id"])
        for k, v in r.items():
            mol.SetProp(k, str(v))
        writer.write(mol)
    writer.close()
    print(f"wrote {sdf_path} ({len(out_rows)} molecules)")

    md_path = FINAL / "top50.md"
    with open(md_path, "w") as f:
        f.write(f"# PHGDH top-{TOP_N} candidate hits\n\n")
        f.write(f"Across all 887 scored candidates from Round-0 known, R1+R2 de novo, B1+B2+B3 scaffold-seeded "
                f"and B2 Round-2 iterative branches. Top-{TOP_N} ranked by Boltz-2 affinity (lower = stronger).\n\n")
        f.write(f"Mechanism classification: |Δ| affinity vs +3PG state < {MECH_THRESHOLD} log Kd = NADH-competitive "
                f"(doesn't disrupt substrate binding); ≥ {MECH_THRESHOLD} = 3PG-competitive.\n\n")
        f.write("| # | id | source | aff_C1 | aff_C2 | mech | druglike | MW | SA | nearest known (Tani) |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        for r in out_rows:
            dl = "✓" if r["drug_like_pass"] == "1" else "✗"
            mech = r["mechanism"] if r["mechanism"] != "C1 only" else "—"
            c2 = r["affinity_C2"] or "—"
            f.write(f"| {r['rank']} | `{r['id']}` | {r['source']} | {r['affinity_C1']} | {c2} | {mech} | {dl} | "
                    f"{r['MW']} | {r['SA_score']} | {r['nearest_known_binder']} ({r['tanimoto_to_nearest']}) |\n")
    print(f"wrote {md_path}")


if __name__ == "__main__":
    main()
