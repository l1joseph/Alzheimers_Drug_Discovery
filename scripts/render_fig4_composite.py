"""Figure 4 (our composite): four representative candidates side by side.

Row a: 2D structure (RDKit). Row b: predicted/co-crystal 3D binding pose (PyMOL
panels from render_paper_fig4.py). Row c: drug-likeness / selectivity summary
table (computed fresh from SMILES + selectivity tables).

Compounds: compound 15 (K58, validated, 1.42 A co-crystal), BI-4924 (K5K,
validated), NCT-503 (validated AD-anchor; Boltz low-confidence), and the novel
scaffold-seeded design r2b2_107.

Run under boltz-rocm:  python scripts/render_fig4_composite.py
"""
import os
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
from rdkit import Chem, RDLogger, DataStructs
from rdkit.Chem import Draw, Descriptors, RDConfig, QED
from rdkit.Chem import rdMolDescriptors, FilterCatalog
from rdkit.Chem import AllChem
sys.path.append(os.path.join(RDConfig.RDContribDir, "SA_Score"))
import sascorer  # noqa: E402

RDLogger.DisableLog("rdApp.*")
PROJECT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery")
OUT = PROJECT / "docs" / "figures" / "paper"

NATURE_RC = {
    'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'font.size': 7, 'axes.titlesize': 8, 'figure.titlesize': 9,
    'axes.edgecolor': 'black', 'text.color': 'black',
    'figure.facecolor': 'white', 'savefig.dpi': 450,
    'pdf.fonttype': 42, 'svg.fonttype': 'none',
}
sns.set_theme(rc=NATURE_RC)
plt.rcParams.update(NATURE_RC)

# (display name, short, source tag, pose key, SMILES, Boltz aff, combined sel-idx)
COMPOUNDS = [
    ("compound 15 (K58)", "K58", "validated · 6RJ3 co-crystal (1.42 Å)", "fig4_K58_real_6RJ3",
     "C[C@H](c1ccc(cc1)C(=O)O)NC(=O)c2cc(nn2C)c3ccccc3", -1.00, -4.78),
    ("BI-4924 (K5K)", "K5K", "validated · Boltz-predicted", "fig4_K5K_boltz",
     "Cc1cc2c(cc(n2C)C(=O)N[C@H](CO)c3ccc(cc3)S(=O)(=O)CC(=O)O)c(c1Cl)Cl", -1.79, -3.55),
    ("NCT-503", "NCT-503", "AD-anchor · Boltz-predicted (p=0.29)", "fig4_NCT503_boltz",
     "CC1=CC(=NC(=C1)NC(=S)N2CCN(CC2)CC3=CC=C(C=C3)C(F)(F)F)C", -0.30, -2.72),
    ("r2b2_107 (novel)", "r2b2_107", "TamGen design · Boltz-predicted", "fig4_r2b2_107_boltz",
     "CC(C)[C@H](NS(=O)(=O)c1ccc(-c2ccc(CSc3nc(O)c4c(n3)CC=C4)cc2)cc1)C(=O)O", -0.66, -1.28),
]

_pains = FilterCatalog.FilterCatalogParams()
_pains.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS)
PAINS_CAT = FilterCatalog.FilterCatalog(_pains)
_brenk = FilterCatalog.FilterCatalogParams()
_brenk.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.BRENK)
BRENK_CAT = FilterCatalog.FilterCatalog(_brenk)


def metrics(smiles):
    mol = Chem.MolFromSmiles(smiles)
    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = rdMolDescriptors.CalcNumHBD(mol)
    hba = rdMolDescriptors.CalcNumHBA(mol)
    viol = sum([mw > 500, logp > 5, hbd > 5, hba > 10])
    return {
        "mol": mol,
        "lipinski": "pass" if viol <= 1 else f"fail ({viol})",
        "pains": "flag" if PAINS_CAT.HasMatch(mol) else "pass",
        "brenk": "flag" if BRENK_CAT.HasMatch(mol) else "pass",
        "qed": QED.qed(mol),
        "sa": sascorer.calculateScore(mol),
        "fp": AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048),
    }


def main():
    n = len(COMPOUNDS)
    data = [metrics(c[4]) for c in COMPOUNDS]
    k58_fp = data[0]["fp"]
    tani = [DataStructs.TanimotoSimilarity(d["fp"], k58_fp) for d in data]

    fig = plt.figure(figsize=(2.45 * n, 8.4))
    gs = fig.add_gridspec(3, n, height_ratios=[1.0, 1.12, 0.95],
                          hspace=0.30, wspace=0.06)

    for j, (name, short, tag, key, smi, aff, sel) in enumerate(COMPOUNDS):
        ax = fig.add_subplot(gs[0, j])
        ax.imshow(np.asarray(Draw.MolToImage(data[j]["mol"], size=(460, 460))))
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(name, fontsize=8.5, fontweight="bold", pad=3)
        ax.text(0.5, -0.04, tag, transform=ax.transAxes, ha="center", va="top",
                fontsize=6.0, style="italic", color="#555555")

        axp = fig.add_subplot(gs[1, j])
        pose = OUT / f"{key}.png"
        if pose.exists():
            axp.imshow(mpimg.imread(str(pose)))
        axp.set_xticks([]); axp.set_yticks([])
        for s in axp.spines.values():
            s.set_visible(False)
        axp.set_xlabel(f"Boltz {aff:+.2f} · sel-idx {sel:+.2f}", fontsize=6.8, labelpad=3)

    # Panel c: summary table spanning the bottom
    ax_t = fig.add_subplot(gs[2, :])
    ax_t.axis("off")
    row_labels = ["Lipinski", "PAINS", "Brenk", "QED", "SA score",
                  "Tanimoto to K58", "Combined sel-idx"]
    col_labels = [c[1] for c in COMPOUNDS]
    cell = []
    cell.append([d["lipinski"] for d in data])
    cell.append([d["pains"] for d in data])
    cell.append([d["brenk"] for d in data])
    cell.append([f"{d['qed']:.2f}" for d in data])
    cell.append([f"{d['sa']:.1f}" for d in data])
    cell.append([f"{t:.2f}" for t in tani])
    cell.append([f"{c[6]:+.2f}" for c in COMPOUNDS])

    tbl = ax_t.table(cellText=cell, rowLabels=row_labels, colLabels=col_labels,
                     cellLoc="center", rowLoc="left", loc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7.5)
    tbl.scale(1.0, 1.5)
    for (r, c), cellobj in tbl.get_celld().items():
        cellobj.set_edgecolor("#cccccc")
        if r == 0:
            cellobj.set_text_props(fontweight="bold")
            cellobj.set_facecolor("#eef0f4")
        if c == -1:
            cellobj.set_text_props(fontweight="bold", ha="left")
        txt = cellobj.get_text().get_text()
        if txt in ("flag",) or txt.startswith("fail"):
            cellobj.set_text_props(color="#b3202a")

    fig.text(0.085, 0.985, "a", fontsize=12, fontweight="bold", va="top")
    fig.text(0.085, 0.660, "b", fontsize=12, fontweight="bold", va="top")
    fig.text(0.085, 0.350, "c", fontsize=12, fontweight="bold", va="bottom")

    for ext in ("png", "svg"):
        fig.savefig(OUT / f"fig4_composite.{ext}", dpi=450, bbox_inches="tight",
                    pad_inches=0.03, facecolor="white")
        print(f"wrote {OUT / f'fig4_composite.{ext}'}")
    plt.close(fig)


if __name__ == "__main__":
    main()
