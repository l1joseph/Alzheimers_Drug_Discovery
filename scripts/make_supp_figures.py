"""Supplementary figures for the revision (/fig Nature style).

S2: Boltz-2 vs AutoDock Vina rank agreement (orthogonal-rescore correlation).
S3: Boltz-2 pose recovery — ligand centroid RMSD vs crystal (cealign-corrected).
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, pearsonr

PROJECT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery")
OUT = PROJECT / "docs" / "figures" / "paper"

PALETTE = ['#332288', '#88CCEE', '#44AA99', '#117733', '#999933',
           '#DDCC77', '#CC6677', '#882255', '#AA4499']
NATURE_RC = {
    'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'font.size': 7, 'axes.titlesize': 8, 'axes.labelsize': 7,
    'xtick.labelsize': 6, 'ytick.labelsize': 6, 'legend.fontsize': 6,
    'axes.linewidth': 1.0, 'axes.edgecolor': 'black', 'axes.labelcolor': 'black',
    'text.color': 'black', 'xtick.color': 'black', 'ytick.color': 'black',
    'xtick.major.width': 1.0, 'ytick.major.width': 1.0,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.spines.left': True, 'axes.spines.bottom': True,
    'axes.grid': False, 'figure.facecolor': 'white', 'axes.facecolor': 'white',
    'savefig.dpi': 450, 'pdf.fonttype': 42, 'svg.fonttype': 'none',
}
sns.set_theme(rc=NATURE_RC)
plt.rcParams.update(NATURE_RC)


def _save(fig, name):
    for ext in ("png", "svg"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=450, bbox_inches="tight",
                    pad_inches=0.02, facecolor="white")
        print(f"wrote {OUT / f'{name}.{ext}'}")
    plt.close(fig)


def fig_boltz_vina():
    df = pd.read_csv(PROJECT / "results" / "orthogonal_rescore" / "vina_scores.csv")
    d = df.dropna(subset=["boltz_aff_C1", "vina_local_only"]).copy()
    d["vina_local_only"] = d["vina_local_only"].astype(float)
    rho, p = spearmanr(d["boltz_aff_C1"], d["vina_local_only"])
    r, _ = pearsonr(d["boltz_aff_C1"], d["vina_local_only"])
    fig, ax = plt.subplots(figsize=(3.4, 3.0))
    ax.scatter(d["boltz_aff_C1"], d["vina_local_only"], s=22,
               facecolor=PALETTE[0], edgecolor="white", linewidth=0.4, alpha=0.85)
    for _, row in d.iterrows():
        if row["id"] in ("K58", "K5K", "ONS", "ONV", "NCT503"):
            ax.annotate(row["id"], (row["boltz_aff_C1"], row["vina_local_only"]),
                        fontsize=5, xytext=(2, 2), textcoords="offset points")
    ax.set_xlabel("Boltz-2 affinity (logKd-like)")
    ax.set_ylabel("AutoDock Vina (kcal/mol)")
    ax.set_title("Boltz-2 vs Vina rank agreement", pad=6)
    ax.text(0.04, 0.06, f"Spearman $\\rho$ = {rho:.2f} (p = {p:.2f})\n"
            f"Pearson r = {r:.2f},  n = {len(d)}",
            transform=ax.transAxes, fontsize=6, va="bottom",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", lw=0.5))
    _save(fig, "fig_supp_boltz_vina")
    print(f"  rho={rho:.3f} p={p:.3f} r={r:.3f} n={len(d)}")


def fig_pose_recovery():
    df = pd.read_csv(PROJECT / "results" / "pose_recovery_cealign.csv")
    df["label"] = df["ligand_resname"]
    df = df.sort_values("centroid_rmsd")
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    ax.bar(df["label"], df["centroid_rmsd"], color=PALETTE[2],
           edgecolor="black", linewidth=0.6, width=0.62)
    ax.axhline(2.0, color=PALETTE[6], lw=1.0, ls="--")
    ax.text(len(df) - 0.5, 2.05, "2 Å", color=PALETTE[6], fontsize=6, va="bottom", ha="right")
    ax.set_ylabel("Ligand centroid RMSD\nvs crystal (Å)")
    ax.set_xlabel("")
    ax.set_ylim(0, 2.4)
    ax.set_title("Boltz-2 pose recovery (cealign-corrected)", pad=6)
    _save(fig, "fig_supp_pose_recovery")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig_boltz_vina()
    fig_pose_recovery()
