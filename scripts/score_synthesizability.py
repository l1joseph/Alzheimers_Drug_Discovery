"""Apply synthetic accessibility + drug-likeness filters to ranked candidates.

For each row in the combined leaderboard:
  - SA score (Ertl & Schuffenhauer 2009, via RDKit Contrib sascorer)
  - MW, logP, HBD, HBA, rotatable bonds (Lipinski/Veber)
  - PAINS / Brenk hits via RDKit's FilterCatalog

Outputs results/combined/leaderboard_with_filters.csv ranked by affinity, with
boolean pass/fail columns. Sources: round-0, round-1, round-2, B1, B2.

Top-50 by Boltz affinity is the typical use case, but the script processes all.
"""
import argparse
import csv
import sys
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, AllChem
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams

RDLogger.DisableLog("rdApp.*")

# SA score via the RDKit Contrib script — package layout puts it under rdkit/Contrib
import rdkit
_rdkit_root = Path(rdkit.__file__).resolve().parent
sys.path.insert(0, str(_rdkit_root / "Contrib" / "SA_Score"))
import sascorer  # noqa: E402


def lookup_smiles_from_yamls(input_id: str) -> str:
    """Find the SMILES given a leaderboard input_id by checking all YAML dirs."""
    import yaml as yaml_lib
    PROJECT = Path(__file__).resolve().parent.parent
    yaml_dirs = [
        PROJECT / "data" / "round0_yamls",
        PROJECT / "data" / "tamgen_round1_yamls",
        PROJECT / "data" / "tamgen_round2_yamls",
        PROJECT / "data" / "tamgen_b1_yamls",
        PROJECT / "data" / "tamgen_b2_yamls",
    ]
    for d in yaml_dirs:
        p = d / f"{input_id}.yaml"
        if p.exists():
            y = yaml_lib.safe_load(open(p))
            for s in y["sequences"]:
                if "ligand" in s:
                    return s["ligand"]["smiles"]
    return ""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", default="results/combined/all_rounds.csv")
    p.add_argument("--out", default="results/combined/leaderboard_with_filters.csv")
    args = p.parse_args()

    # Build PAINS + Brenk catalog
    params = FilterCatalogParams()
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS)
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.BRENK)
    catalog = FilterCatalog(params)

    rows = list(csv.DictReader(open(args.inp)))
    out_rows = []
    for r in rows:
        input_id = r["id"]
        smi = lookup_smiles_from_yamls(input_id)
        mol = Chem.MolFromSmiles(smi) if smi else None
        if mol is None:
            r.update({"smiles": smi, "sa_score": "", "mw": "", "logp": "", "hbd": "", "hba": "",
                      "rotbonds": "", "pains": "", "brenk": "",
                      "lipinski_pass": "", "veber_pass": "", "drug_like_pass": ""})
            out_rows.append(r)
            continue

        try:
            sa = sascorer.calculateScore(mol)
        except Exception:
            sa = None
        mw = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        hbd = Descriptors.NumHDonors(mol)
        hba = Descriptors.NumHAcceptors(mol)
        rot = Descriptors.NumRotatableBonds(mol)

        pains_match = catalog.HasMatch(mol)
        # Lipinski (rule of 5): MW <= 500, logP <= 5, HBD <= 5, HBA <= 10
        lipinski = (mw <= 500) and (logp <= 5) and (hbd <= 5) and (hba <= 10)
        # Veber: rotbonds <= 10, TPSA <= 140
        tpsa = Descriptors.TPSA(mol)
        veber = (rot <= 10) and (tpsa <= 140)
        # Composite drug-like pass: Lipinski + Veber + no PAINS + SA < 6 (synthesizable)
        drug_like = lipinski and veber and (not pains_match) and (sa is not None) and (sa < 6.0)

        r.update({
            "smiles": smi,
            "sa_score": f"{sa:.2f}" if sa is not None else "",
            "mw": f"{mw:.1f}", "logp": f"{logp:.2f}",
            "hbd": hbd, "hba": hba, "rotbonds": rot,
            "tpsa": f"{tpsa:.1f}",
            "pains": "1" if pains_match else "0",
            "lipinski_pass": "1" if lipinski else "0",
            "veber_pass": "1" if veber else "0",
            "drug_like_pass": "1" if drug_like else "0",
        })
        out_rows.append(r)

    fieldnames = list(out_rows[0].keys())
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    n_pass = sum(1 for r in out_rows if r["drug_like_pass"] == "1")
    print(f"wrote {len(out_rows)} rows to {args.out}; {n_pass} pass drug-like filter")
    print(f"\n=== Top-25 by affinity, drug-like filter applied ===")
    out_rows.sort(key=lambda r: float(r["affinity_pred_value"]) if r["affinity_pred_value"] else 999)
    n_shown = 0
    for r in out_rows:
        if n_shown >= 25: break
        pass_str = "✓" if r["drug_like_pass"] == "1" else "✗"
        sa = r["sa_score"] or "?"
        print(f"  {pass_str}  {r['id']:10s} {r['source'][:14]:14s} aff={r['affinity_pred_value']:>+7.7s} "
              f"SA={sa:>5s} MW={r['mw']:>6s} logP={r['logp']:>5s} PAINS={r['pains']}")
        n_shown += 1


if __name__ == "__main__":
    main()
