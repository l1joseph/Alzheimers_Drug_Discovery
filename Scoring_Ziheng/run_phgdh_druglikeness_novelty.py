import os
import sys
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import Descriptors, QED, Crippen, Lipinski, rdMolDescriptors
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams
import rdkit

# RDKit contrib SA score
sa_path = os.path.join(os.path.dirname(rdkit.__file__), "Contrib", "SA_Score")
sys.path.append(sa_path)
import sascorer

compounds = [
    ("K58", "key benchmark", "C[C@H](c1ccc(cc1)C(=O)O)NC(=O)c2cc(nn2C)c3ccccc3"),
    ("K5K", "seed/reference", "Cc1cc2c(cc(n2C)C(=O)N[C@H](CO)c3ccc(cc3)S(=O)(=O)CC(=O)O)c(c1Cl)Cl"),
    ("r2b2_107", "generated candidate", "CC(C)[C@H](NS(=O)(=O)c1ccc(-c2ccccc2)cc1)P(=O)(O)C[C@H](C(=O)O)c1cccc(CN)c1"),
]

# PAINS catalog
pains_params = FilterCatalogParams()
pains_params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_A)
pains_params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_B)
pains_params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_C)
pains_catalog = FilterCatalog(pains_params)

# Brenk medicinal chemistry alerts
brenk_params = FilterCatalogParams()
brenk_params.AddCatalog(FilterCatalogParams.FilterCatalogs.BRENK)
brenk_catalog = FilterCatalog(brenk_params)

mols = {}
fps = {}
for cid, role, smi in compounds:
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        raise ValueError(f"Invalid SMILES for {cid}")
    mols[cid] = mol
    fps[cid] = rdMolDescriptors.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)

rows = []
for cid, role, smi in compounds:
    mol = mols[cid]

    mw = Descriptors.MolWt(mol)
    logp = Crippen.MolLogP(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    tpsa = rdMolDescriptors.CalcTPSA(mol)
    rot = Descriptors.NumRotatableBonds(mol)

    lipinski_violations = int(mw > 500) + int(logp > 5) + int(hbd > 5) + int(hba > 10)

    pains_matches = pains_catalog.GetMatches(mol)
    brenk_matches = brenk_catalog.GetMatches(mol)

    tanimoto_to_k5k = DataStructs.TanimotoSimilarity(fps[cid], fps["K5K"])
    tanimoto_to_k58 = DataStructs.TanimotoSimilarity(fps[cid], fps["K58"])
    max_to_other_known = max(
        DataStructs.TanimotoSimilarity(fps[cid], fps[k])
        for k in ["K5K", "K58"]
        if k != cid
    )

    rows.append({
        "compound_id": cid,
        "role": role,
        "canonical_smiles": Chem.MolToSmiles(mol, canonical=True),
        "MW": mw,
        "logP": logp,
        "HBD": hbd,
        "HBA": hba,
        "TPSA": tpsa,
        "rotatable_bonds": rot,
        "Lipinski_violations": lipinski_violations,
        "Lipinski_pass": lipinski_violations == 0,
        "PAINS_pass": len(pains_matches) == 0,
        "PAINS_alerts": "; ".join(m.GetDescription() for m in pains_matches),
        "Brenk_pass": len(brenk_matches) == 0,
        "Brenk_alerts": "; ".join(m.GetDescription() for m in brenk_matches),
        "SA_score": sascorer.calculateScore(mol),
        "QED": QED.qed(mol),
        "Tanimoto_to_K5K": tanimoto_to_k5k,
        "Tanimoto_to_K58": tanimoto_to_k58,
        "max_Tanimoto_to_K58_or_K5K": max_to_other_known,
        "novelty_score_1_minus_max_Tanimoto": 1 - max_to_other_known,
    })

out = pd.DataFrame(rows)
out.to_csv("phgdh_druglikeness_novelty_scores.csv", index=False)
print(out.to_string(index=False))
