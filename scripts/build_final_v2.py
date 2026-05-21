"""Build the final v2 candidates report.

Combines:
  - results/final/top50.csv          (v1 top 50, Boltz aff + drug-likeness + Tani)
  - results/orthogonal_rescore/vina_scores.csv  (Vina rescore on v1 top 50)
  - results/offtarget/selectivity_table.csv     (Block G selectivity indices)
  - results/chembl/scores.csv        (ChEMBL 5k screen)
  - results/reinvent/top_reinvent.csv (REINVENT RL outputs)

Output:
  results/final/top_candidates_v2.csv
  results/final/top_candidates_v2.md (short table for the report)

Unified ranking: ordered by source-specific priority within bands:
  Band 1: validated PHGDH inhibitors (NCT-503 family, BI series)
  Band 2: novel scaffold-seeded (TamGen B1/B2 + R2)
  Band 3: ChEMBL repurposing candidates (top by Boltz prob_binary)
  Band 4: REINVENT RL outputs (top by composite reward, novel + druglike)
"""
from __future__ import annotations

import csv
from pathlib import Path

PROJECT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery")

def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return list(csv.DictReader(open(path)))


def main():
    top50_v1 = load(PROJECT / "results" / "final" / "top50.csv")
    vina = {r["id"]: r for r in load(PROJECT / "results" / "orthogonal_rescore" / "vina_scores.csv")}
    sel = {r["ligand"]: r for r in load(PROJECT / "results" / "offtarget" / "selectivity_table.csv")}
    chembl_all = load(PROJECT / "results" / "chembl" / "scores.csv")
    reinvent = load(PROJECT / "results" / "reinvent" / "top_reinvent.csv")

    # Top ChEMBL by composite signal: rank by affinity_pred_value but filter
    # for prob_binary > 0.4 (more confident classifier predictions)
    chembl_ranked = []
    for r in chembl_all:
        if not r.get("affinity_affinity_pred_value"): continue
        try:
            aff = float(r["affinity_affinity_pred_value"])
            prob = float(r.get("affinity_affinity_probability_binary", "0") or 0)
            conf = float(r.get("confidence_confidence_score", "0") or 0)
        except ValueError:
            continue
        if prob < 0.4: continue
        chembl_ranked.append({"id": r["input_id"], "aff": aff, "prob": prob, "conf": conf})
    chembl_ranked.sort(key=lambda r: r["aff"])
    chembl_top = chembl_ranked[:15]

    # Final unified candidates
    out_rows = []

    # Band 1: validated PHGDH inhibitors that have selectivity data
    band1_ids = ["K58", "K5K", "NCT503", "ONV", "ONS"]
    for cid in band1_ids:
        s = sel.get(cid)
        if not s: continue
        out_rows.append({
            "rank": 0,
            "band": 1,
            "id": cid,
            "label": {"K58": "BI-cmpd-15", "K5K": "BI-4924", "NCT503": "NCT-503", "ONV": "NCT-cmpd-1", "ONS": "NCT-cmpd-15"}.get(cid, cid),
            "source": "validated_known",
            "boltz_aff_C1": s["PHGDH"],
            "vina_kcal": (vina.get(cid, {}) or {}).get("vina_local_only", ""),
            "selectivity_index": s["selectivity_index"],
            "selectivity_interpretation": s["interpretation"],
            "smiles": "",  # filled below
            "MW": "",
            "logP": "",
            "Tanimoto_to_known": "1.00" if cid in band1_ids else "",
            "ad_relevance": "AD-tested" if cid == "NCT503" else "AD repurposing candidate (mechanism precedent)",
        })

    # Band 2: novel scaffold-seeded (top from v1 top50 minus the known controls minus the dropped b1_112)
    drops = {"b1_112"}  # dropped by selectivity (prefers GAPDH)
    band2_candidates = []
    for r in top50_v1:
        if r["id"] in band1_ids: continue
        if r["id"] in drops: continue
        if r["source"] in {"round0_known"}: continue
        if r["drug_like_pass"] != "1": continue
        if float(r["tanimoto_to_nearest"]) > 0.4: continue
        band2_candidates.append(r)
    band2_candidates.sort(key=lambda r: float(r["affinity_C1"]))
    for r in band2_candidates[:10]:
        cid = r["id"]
        s = sel.get(cid, {})
        out_rows.append({
            "rank": 0,
            "band": 2,
            "id": cid,
            "label": cid,
            "source": r["source"],
            "boltz_aff_C1": r["affinity_C1"],
            "vina_kcal": (vina.get(cid, {}) or {}).get("vina_local_only", ""),
            "selectivity_index": s.get("selectivity_index", ""),
            "selectivity_interpretation": s.get("interpretation", "—"),
            "smiles": r["smiles"],
            "MW": r["MW"],
            "logP": r["logP"],
            "Tanimoto_to_known": r["tanimoto_to_nearest"],
            "ad_relevance": "novel composition (NCT-503 scaffold lineage)" if r["source"].startswith("tamgen_b1") else "novel composition (BI-4924 scaffold lineage)",
        })

    # Band 3: ChEMBL repurposing top hits
    for r in chembl_top[:10]:
        out_rows.append({
            "rank": 0,
            "band": 3,
            "id": r["id"],
            "label": r["id"],
            "source": "chembl_repurposing",
            "boltz_aff_C1": f"{r['aff']:.2f}",
            "vina_kcal": "",
            "selectivity_index": "",
            "selectivity_interpretation": "not screened (off-target panel pending)",
            "smiles": "",
            "MW": "",
            "logP": "",
            "Tanimoto_to_known": "",
            "ad_relevance": "untested; mechanism-of-action precedent inferred from original-target",
        })

    # Band 4: REINVENT RL top novel druglike
    for r in reinvent[:10]:
        out_rows.append({
            "rank": 0,
            "band": 4,
            "id": r["id"],
            "label": r["id"][:25],
            "source": "reinvent_rl",
            "boltz_aff_C1": r["boltz_aff"],
            "vina_kcal": "",
            "selectivity_index": "",
            "selectivity_interpretation": "not screened",
            "smiles": r["canonical_smiles"],
            "MW": r["MW"],
            "logP": r["logP"],
            "Tanimoto_to_known": r["tanimoto_to_nearest"],
            "ad_relevance": "novel composition (REINVENT RL with composite reward)",
        })

    # Re-number
    for i, r in enumerate(out_rows, 1):
        r["rank"] = i

    out = PROJECT / "results" / "final" / "top_candidates_v2.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)
    print(f"wrote {len(out_rows)} rows to {out}")

    # Compact markdown summary
    md_out = PROJECT / "results" / "final" / "top_candidates_v2.md"
    with open(md_out, "w") as f:
        f.write("# PHGDH-AD candidate v2 summary\n\n")
        f.write("Bands: 1 = validated (AD repurposing track), 2 = novel scaffold-seeded, "
                "3 = ChEMBL repurposing candidates (untested), 4 = REINVENT RL outputs.\n\n")
        for band, name in [
            (1, "AD repurposing candidates (validated PHGDH binders + selectivity data)"),
            (2, "Novel scaffold-seeded design (TamGen branches)"),
            (3, "ChEMBL drug-like screen (untested repurposing candidates)"),
            (4, "REINVENT RL with composite reward (novel composition-of-matter)"),
        ]:
            band_rows = [r for r in out_rows if r["band"] == band]
            if not band_rows:
                continue
            f.write(f"## Band {band}: {name}\n\n")
            f.write("| # | id | source | Boltz aff | Vina | sel_idx | sel_interp | MW | logP | Tani→known | AD relevance |\n")
            f.write("|---|---|---|---|---|---|---|---|---|---|---|\n")
            for r in band_rows:
                f.write(f"| {r['rank']} | `{r['label']}` | {r['source']} | "
                        f"{r['boltz_aff_C1']} | {r['vina_kcal']} | {r['selectivity_index']} | "
                        f"{r['selectivity_interpretation']} | {r['MW']} | {r['logP']} | "
                        f"{r['Tanimoto_to_known']} | {r['ad_relevance']} |\n")
            f.write("\n")
    print(f"wrote {md_out}")


if __name__ == "__main__":
    main()
