"""Aggregate the REINVENT RL run into a top-N report.

For each step in staged_learning_1.csv:
  - Find unique SMILES with reward > threshold
  - Deduplicate by canonical SMILES
  - Sort by composite reward

For each top SMILES, also compute Tanimoto to nearest known PHGDH binder
to flag novelty.

Output:
  results/reinvent/top_reinvent.csv  — top REINVENT-generated hits
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, DataStructs, Descriptors

RDLogger.DisableLog("rdApp.*")

PROJECT = Path(__file__).resolve().parent.parent


def canon_smiles(smi: str) -> str:
    mol = Chem.MolFromSmiles(smi)
    return Chem.MolToSmiles(mol, isomericSmiles=True) if mol else ""


def fingerprint(smi: str):
    mol = Chem.MolFromSmiles(smi)
    return AllChem.GetMorganFingerprintAsBitVect(mol, 2, 2048) if mol else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv",
                   default="/cosmos/vast/scratch/l1joseph/reinvent_rl/staged_learning_1.csv")
    p.add_argument("--out", default=str(PROJECT / "results" / "reinvent" / "top_reinvent.csv"))
    p.add_argument("--top", type=int, default=50)
    p.add_argument("--min-reward", type=float, default=0.55)
    args = p.parse_args()

    src = Path(args.csv)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(open(src)))
    print(f"loaded {len(rows)} REINVENT-step rows from {src.name}")

    # Dedupe by canonical SMILES; keep best reward per molecule
    best: dict[str, dict] = {}
    for r in rows:
        smi_raw = r["SMILES"]
        score = float(r["Score"])
        if score < args.min_reward:
            continue
        smi = canon_smiles(smi_raw)
        if not smi:
            continue
        if smi in best and float(best[smi]["Score"]) >= score:
            continue
        # capture earliest step at which this score was reached
        r2 = dict(r)
        r2["canonical_smiles"] = smi
        best[smi] = r2

    unique = list(best.values())
    unique.sort(key=lambda r: -float(r["Score"]))
    print(f"unique SMILES with reward>={args.min_reward}: {len(unique)}")

    # Add druglikeness + Tanimoto-to-nearest-known
    known = list(csv.DictReader(open(PROJECT / "data" / "libraries" / "known_phgdh_binders.csv")))
    known_fps = []
    for k in known:
        fp = fingerprint(k["smiles"])
        if fp is not None:
            known_fps.append((k["name"], fp))

    out_rows = []
    for r in unique[: args.top]:
        smi = r["canonical_smiles"]
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            continue
        mw = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        hbd = Descriptors.NumHDonors(mol)
        hba = Descriptors.NumHAcceptors(mol)
        # Lipinski (relaxed: at most 1 violation)
        viol = sum([mw > 500, logp > 5, hbd > 5, hba > 10])
        lipinski = viol <= 1
        # Nearest known
        fp = fingerprint(smi)
        nearest_name, nearest_t = "", 0.0
        if fp is not None and known_fps:
            for name, kfp in known_fps:
                t = DataStructs.TanimotoSimilarity(fp, kfp)
                if t > nearest_t:
                    nearest_t = t
                    nearest_name = name
        out_rows.append({
            "rank": len(out_rows) + 1,
            "id": f"reinvent_step{int(r['step']):03d}_{r['canonical_smiles'][:8].replace('/', '_')}",
            "canonical_smiles": smi,
            "boltz_aff": r.get("boltz_phgdh_reward (raw)", ""),
            "reward": r["Score"],
            "step": r["step"],
            "MW": round(mw, 1),
            "logP": round(logp, 2),
            "HBD": hbd,
            "HBA": hba,
            "lipinski_pass": int(lipinski),
            "nearest_known": nearest_name,
            "tanimoto_to_nearest": f"{nearest_t:.2f}",
        })

    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)
    print(f"wrote {len(out_rows)} rows to {out}")

    # Summary
    novel_druglike = [r for r in out_rows
                      if r["lipinski_pass"] == 1 and float(r["tanimoto_to_nearest"]) < 0.4]
    print(f"\nnovel + druglike (Tani<0.4, Lipinski-pass): {len(novel_druglike)}")
    for r in novel_druglike[:5]:
        print(f"  rank {r['rank']:>2} {r['id'][:40]:<42} reward={r['reward'][:6]} MW={r['MW']} Tani={r['tanimoto_to_nearest']}")


if __name__ == "__main__":
    main()
