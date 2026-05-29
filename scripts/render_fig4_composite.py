"""Figure 4 (our composite): four representative candidates side by side.

Row a: 2D structure (RDKit). Row b: predicted/co-crystal 3D binding pose (PyMOL
panels from render_paper_fig4.py). A metrics line sits under each column.

Compounds: compound 15 (K58, validated, 1.42 A co-crystal), BI-4924 (K5K,
validated), NCT-503 (validated, AD-anchor; Boltz low-confidence), and the novel
scaffold-seeded design r2b2_107.

Run under boltz-rocm:  python scripts/render_fig4_composite.py
"""
import os
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
from rdkit import Chem, RDLogger
from rdkit.Chem import Draw, Descriptors, RDConfig
import sys
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

# (display name, source tag, pose PNG key, SMILES, Boltz aff, combined sel_idx, extra)
COMPOUNDS = [
    ("compound 15 (K58)", "validated · 6RJ3 co-crystal (1.42 Å)", "fig4_K58_real_6RJ3",
     "C[C@H](c1ccc(cc1)C(=O)O)NC(=O)c2cc(nn2C)c3ccccc3", -1.00, -4.78, ""),
    ("BI-4924 (K5K)", "validated · Boltz-predicted", "fig4_K5K_boltz",
     "Cc1cc2c(cc(n2C)C(=O)N[C@H](CO)c3ccc(cc3)S(=O)(=O)CC(=O)O)c(c1Cl)Cl", -1.79, -3.55, ""),
    ("NCT-503", "AD-anchor · Boltz-predicted (p=0.29)", "fig4_NCT503_boltz",
     "CC1=CC(=NC(=C1)NC(=S)N2CCN(CC2)CC3=CC=C(C=C3)C(F)(F)F)C", -0.30, -2.72, ""),
    ("r2b2_107 (novel)", "TamGen design · Boltz-predicted", "fig4_r2b2_107_boltz",
     "CC(C)[C@H](NS(=O)(=O)c1ccc(-c2ccc(CSc3nc(O)c4c(n3)CC=C4)cc2)cc1)C(=O)O", -0.66, -1.28,
     "Tanimoto 0.16"),
]


def mol_image(smiles, size=460):
    mol = Chem.MolFromSmiles(smiles)
    img = Draw.MolToImage(mol, size=(size, size))
    return np.asarray(img), Descriptors.MolWt(mol), sascorer.calculateScore(mol)


def main():
    n = len(COMPOUNDS)
    fig, axes = plt.subplots(2, n, figsize=(2.35 * n, 5.7),
                             gridspec_kw={"height_ratios": [1.0, 1.12],
                                          "hspace": 0.28, "wspace": 0.06})
    for j, (name, tag, key, smi, aff, sel, extra) in enumerate(COMPOUNDS):
        img2d, mw, sa = mol_image(smi)
        # Row a: 2D structure
        ax = axes[0, j]
        ax.imshow(img2d)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(name, fontsize=8.5, fontweight="bold", pad=3)
        ax.text(0.5, -0.04, tag, transform=ax.transAxes, ha="center", va="top",
                fontsize=6.0, style="italic", color="#555555")
        # Row b: 3D pose
        axp = axes[1, j]
        pose = OUT / f"{key}.png"
        if pose.exists():
            axp.imshow(mpimg.imread(str(pose)))
        else:
            axp.text(0.5, 0.5, "[pose missing]", ha="center", va="center",
                     transform=axp.transAxes, color="red")
        axp.set_xticks([]); axp.set_yticks([])
        for s in axp.spines.values():
            s.set_visible(False)
        metric = f"Boltz {aff:+.2f} · sel-idx {sel:+.2f}\nMW {mw:.0f} · SA {sa:.1f}"
        if extra:
            metric += f" · {extra}"
        axp.set_xlabel(metric, fontsize=6.6, labelpad=4)

    axes[0, 0].text(-0.10, 1.10, "a", transform=axes[0, 0].transAxes,
                    fontsize=11, fontweight="bold", va="bottom", ha="right")
    axes[1, 0].text(-0.10, 1.04, "b", transform=axes[1, 0].transAxes,
                    fontsize=11, fontweight="bold", va="bottom", ha="right")
    fig.suptitle("Representative candidates: 2D structure (a) and predicted binding pose (b)",
                 fontsize=9, y=0.98)
    for ext in ("png", "svg"):
        fig.savefig(OUT / f"fig4_composite.{ext}", dpi=450, bbox_inches="tight",
                    pad_inches=0.03, facecolor="white")
        print(f"wrote {OUT / f'fig4_composite.{ext}'}")
    plt.close(fig)


if __name__ == "__main__":
    main()
