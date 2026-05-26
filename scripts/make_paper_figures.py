"""Generate publication-quality figures for the final paper using seaborn.

Outputs (300 DPI, SVG + PNG):
  docs/figures/paper/fig2_metrics_top10.{png,svg}     — 4-panel: Boltz aff, Vina, drug-likeness grid, sel_idx
  docs/figures/paper/fig3_selectivity_heatmap.{png,svg}  — 11 ligands x 7 targets
  docs/figures/paper/fig_supp_reinvent_curve.{png,svg}   — REINVENT per-step max-reward trajectory

Run from project root with the boltz-rocm conda env active:
    conda activate boltz-rocm
    pip install seaborn   # if not already
    python scripts/make_paper_figures.py
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

PROJECT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery")
OUT_DIR = PROJECT / "docs" / "figures" / "paper"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Seaborn style + paper-style typography
sns.set_theme(style="whitegrid", context="paper", font="DejaVu Sans")
plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "svg.fonttype": "none",
})

# ---------- Top-10 candidate set ---------- #
TOP10 = [
    # (id, label, source_class)
    ("K58",      "K58\n(BI-cmpd-15)",   "validated"),
    ("K5K",      "K5K\n(BI-4924)",      "validated"),
    ("NCT503",   "NCT-503",             "validated"),
    ("ONS",      "ONS\n(NCT-cmpd-15)",  "validated"),
    ("ONV",      "ONV\n(NCT-cmpd-1)",   "validated"),
    ("r2b2_107", "r2b2_107",            "novel-NAD"),
    ("r2b2_285", "r2b2_285",            "novel-NAD"),
    ("b1_115",   "b1_115",              "novel-allo"),
    ("b1_051",   "b1_051",              "novel-allo"),
    ("b1_005",   "b1_005",              "novel-allo"),
]

CLASS_COLORS = {
    "validated":  "#1f77b4",
    "novel-NAD":  "#2ca02c",
    "novel-allo": "#ff7f0e",
}
CLASS_LABELS = {
    "validated":  "Validated (known PHGDH binders)",
    "novel-NAD":  "Novel scaffold-seeded (NAD-competitive)",
    "novel-allo": "Novel scaffold-seeded (allosteric)",
}


def load_csv(path):
    return list(csv.DictReader(open(path))) if Path(path).exists() else []


def _f(x, default=np.nan):
    try:
        return float(x)
    except (ValueError, TypeError):
        return default


def load_top10_dataframe():
    top50 = {r["id"]: r for r in load_csv(PROJECT / "results" / "final" / "top50.csv")}
    vina = {r["id"]: r for r in load_csv(PROJECT / "results" / "orthogonal_rescore" / "vina_scores.csv")}
    sel_dehyd = {r["ligand"]: r for r in load_csv(PROJECT / "results" / "offtarget" / "selectivity_table.csv")}
    sel_kin = {r["ligand"]: r for r in load_csv(PROJECT / "results" / "kinase" / "selectivity_table.csv")}
    multiconf = {r["ligand"]: r for r in load_csv(PROJECT / "results" / "multiconf" / "by_ligand.csv")}
    known = {r["id"]: r for r in load_csv(PROJECT / "data" / "libraries" / "known_phgdh_binders.csv")}

    out = []
    for cid, label, klass in TOP10:
        t = top50.get(cid, {})
        v = vina.get(cid, {})
        sd = sel_dehyd.get(cid, {})
        sk = sel_kin.get(cid, {})
        mc = multiconf.get(cid, {})
        k = known.get(cid, {})

        boltz_aff = _f(mc.get("a6cwa_apo")) if mc.get("a6cwa_apo") else _f(t.get("affinity_C1"))
        vina_kcal = _f(v.get("vina_local_only"))

        mw = _f(t.get("MW"))
        logp = _f(t.get("logP"))
        hbd = _f(t.get("HBD"))
        hba = _f(t.get("HBA"))
        sa = _f(t.get("SA_score"))

        # Validated knowns need property computation from SMILES
        if np.isnan(mw) and k.get("smiles"):
            from rdkit import Chem, RDLogger
            from rdkit.Chem import Descriptors
            RDLogger.DisableLog("rdApp.*")
            mol = Chem.MolFromSmiles(k["smiles"])
            if mol:
                mw = Descriptors.MolWt(mol)
                logp = Descriptors.MolLogP(mol)
                hbd = Descriptors.NumHDonors(mol)
                hba = Descriptors.NumHAcceptors(mol)

        sel_d = _f(sd.get("selectivity_index"))
        sel_k = _f(sk.get("kinase_sel_idx"))
        sel_combined = (0 if np.isnan(sel_d) else sel_d) + (0 if np.isnan(sel_k) else sel_k)

        out.append({
            "id": cid, "label": label, "class": klass,
            "boltz_aff": boltz_aff, "vina_kcal": vina_kcal,
            "MW": mw, "logP": logp, "HBD": hbd, "HBA": hba, "SA": sa,
            "sel_dehyd": sel_d, "sel_kin": sel_k, "sel_combined": sel_combined,
            "tanimoto": _f(t.get("tanimoto_to_nearest")),
            "nearest_known": t.get("nearest_known", k.get("name", "")),
        })
    return pd.DataFrame(out)


# ---------- Figure 2 — top-10 metrics multi-panel ---------- #

def fig2_metrics(df):
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 6.2))

    palette = {c: CLASS_COLORS[c] for c in df["class"].unique()}
    order = df["id"].tolist()

    # A: Boltz affinity
    ax = axes[0, 0]
    sns.barplot(data=df, x="id", y="boltz_aff", hue="class", palette=palette,
                order=order, ax=ax, edgecolor="black", linewidth=0.5, dodge=False)
    ax.invert_yaxis()
    ax.set_ylabel("Boltz-2 affinity (logKd-like)")
    ax.set_xlabel("")
    ax.set_title("A   Predicted affinity vs PHGDH", loc="left")
    ax.set_xticklabels([r["label"] for r in df.to_dict("records")], rotation=45, ha="right", fontsize=7)
    ax.axhline(0, color="black", linewidth=0.4)
    ax.text(0.02, 0.95, "more negative = stronger binding", transform=ax.transAxes,
            fontsize=7, style="italic", verticalalignment="top")
    ax.legend_.remove() if ax.legend_ else None

    # B: Vina rescore
    ax = axes[0, 1]
    sns.barplot(data=df, x="id", y="vina_kcal", hue="class", palette=palette,
                order=order, ax=ax, edgecolor="black", linewidth=0.5, dodge=False)
    ax.invert_yaxis()
    ax.set_ylabel("AutoDock Vina (kcal/mol)")
    ax.set_xlabel("")
    ax.set_title("B   Orthogonal Vina rescore", loc="left")
    ax.set_xticklabels([r["label"] for r in df.to_dict("records")], rotation=45, ha="right", fontsize=7)
    for i, v in enumerate(df["vina_kcal"]):
        if pd.isna(v):
            ax.text(i, 0, "n/a", ha="center", va="center", fontsize=7, color="gray")
    ax.legend_.remove() if ax.legend_ else None

    # C: Drug-likeness — seaborn heatmap of NORMALIZED-to-ideal values
    ax = axes[1, 0]
    metrics = ["MW", "logP", "HBD", "HBA", "SA"]
    ideals = {"MW": (200, 500), "logP": (0, 5), "HBD": (0, 5), "HBA": (0, 10), "SA": (1, 4)}
    raw = df[metrics].values
    norm = np.zeros_like(raw, dtype=float)
    for j, m in enumerate(metrics):
        lo, hi = ideals[m]
        norm[:, j] = np.clip((raw[:, j] - lo) / (hi - lo + 1e-9), 0, 1.2)
    annot = np.empty_like(raw, dtype=object)
    for i in range(raw.shape[0]):
        for j in range(raw.shape[1]):
            v = raw[i, j]
            if np.isnan(v):
                annot[i, j] = "—"
            else:
                annot[i, j] = f"{v:.0f}" if metrics[j] == "MW" else f"{v:.1f}"
    sns.heatmap(norm, annot=annot, fmt="", cmap="RdYlGn_r", vmin=0, vmax=1.2,
                cbar=False, linewidths=0.4, linecolor="white",
                xticklabels=metrics,
                yticklabels=[r["label"].replace("\n", " ") for r in df.to_dict("records")],
                annot_kws={"fontsize": 7}, ax=ax)
    ax.set_title("C   Drug-likeness (green=ideal, red=Lipinski/SA fail)", loc="left")
    ax.set_ylabel("")
    ax.tick_params(axis="y", rotation=0, labelsize=7)

    # D: Combined selectivity index
    ax = axes[1, 1]
    sns.barplot(data=df, x="id", y="sel_combined", hue="class", palette=palette,
                order=order, ax=ax, edgecolor="black", linewidth=0.5, dodge=False)
    ax.set_ylabel("Combined selectivity index\n(dehydrogenase + kinase)")
    ax.set_xlabel("")
    ax.set_title("D   Off-target selectivity (lower = more PHGDH-selective)", loc="left")
    ax.set_xticklabels([r["label"] for r in df.to_dict("records")], rotation=45, ha="right", fontsize=7)
    ax.axhline(0, color="black", linewidth=0.4)
    ax.axhline(-2.0, color="darkgreen", linewidth=0.6, linestyle="--", alpha=0.6)
    ax.text(0.02, 0.04, "dashed line: Tier-1 cutoff (−2.0)", transform=ax.transAxes,
            fontsize=7, style="italic", color="darkgreen")
    ax.legend_.remove() if ax.legend_ else None

    # Single legend for the whole figure
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=CLASS_COLORS[c], edgecolor="black", linewidth=0.5)
               for c in ["validated", "novel-NAD", "novel-allo"]]
    fig.legend(handles, [CLASS_LABELS[c] for c in ["validated", "novel-NAD", "novel-allo"]],
               loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.04), frameon=False)

    plt.tight_layout(rect=(0, 0.03, 1, 1))
    for ext in ("png", "svg"):
        out = OUT_DIR / f"fig2_metrics_top10.{ext}"
        fig.savefig(out, dpi=300)
        print(f"wrote {out}")
    plt.close(fig)


# ---------- Figure 3 — selectivity heatmap ---------- #

def fig3_selectivity():
    sel_dehyd = {r["ligand"]: r for r in load_csv(PROJECT / "results" / "offtarget" / "selectivity_table.csv")}
    sel_kin = {r["ligand"]: r for r in load_csv(PROJECT / "results" / "kinase" / "selectivity_table.csv")}
    ligs = sorted(set(sel_dehyd.keys()) & set(sel_kin.keys()))

    def combined(lig):
        return _f(sel_dehyd[lig].get("selectivity_index"), 0) + _f(sel_kin[lig].get("kinase_sel_idx"), 0)
    ligs.sort(key=combined)

    targets = ["PHGDH", "LDH-A", "MDH2", "GAPDH", "IDH1", "GRK5", "GRK2"]
    M = pd.DataFrame(np.nan, index=ligs, columns=targets)
    for lig in ligs:
        d = sel_dehyd[lig]; k = sel_kin[lig]
        M.loc[lig, "PHGDH"] = _f(d.get("PHGDH"))
        M.loc[lig, "LDH-A"] = _f(d.get("LDH-A"))
        M.loc[lig, "MDH2"] = _f(d.get("MDH2"))
        M.loc[lig, "GAPDH"] = _f(d.get("GAPDH"))
        M.loc[lig, "IDH1"] = _f(d.get("IDH1"))
        M.loc[lig, "GRK5"] = _f(k.get("GRK5"))
        M.loc[lig, "GRK2"] = _f(k.get("GRK2"))

    fig, ax = plt.subplots(figsize=(5.6, 4.4))
    vmax = max(abs(M.min().min()), abs(M.max().max()))
    sns.heatmap(M, cmap="RdBu", center=0, vmin=-vmax, vmax=vmax,
                annot=True, fmt="+.2f", annot_kws={"fontsize": 7},
                linewidths=0.4, linecolor="white",
                cbar_kws={"label": "Boltz-2 affinity (logKd-like)\n(blue = stronger binding)"},
                ax=ax)
    # Vertical separators: PHGDH | dehydrogenases | kinases
    ax.axvline(1.0, color="black", linewidth=1.2)
    ax.axvline(5.0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlabel("")
    ax.set_ylabel("Ligand (sorted by combined sel. index)")
    ax.set_title("Selectivity matrix: PHGDH vs Rossmann-fold dehydrogenases + GRK kinases",
                 fontsize=9, pad=10)

    plt.tight_layout()
    for ext in ("png", "svg"):
        out = OUT_DIR / f"fig3_selectivity_heatmap.{ext}"
        fig.savefig(out, dpi=300)
        print(f"wrote {out}")
    plt.close(fig)


# ---------- Supplementary Figure: REINVENT learning curve ---------- #

def fig_supp_reinvent():
    csv_path = Path("/cosmos/vast/scratch/l1joseph/reinvent_rl/staged_learning_1.csv")
    if not csv_path.exists():
        print(f"skip: {csv_path} not found")
        return
    rows = list(csv.DictReader(open(csv_path)))
    by_step = {}
    for r in rows:
        s = int(r["step"]); sc = float(r["Score"])
        d = by_step.setdefault(s, {"all": [], "nonzero": []})
        d["all"].append(sc)
        if sc > 0: d["nonzero"].append(sc)
    steps = sorted(by_step.keys())
    max_per_step = [max(by_step[s]["all"]) if by_step[s]["all"] else 0 for s in steps]
    mean_nz = [np.mean(by_step[s]["nonzero"]) if by_step[s]["nonzero"] else 0 for s in steps]
    df = pd.DataFrame({"step": steps + steps,
                       "reward": max_per_step + mean_nz,
                       "type": ["max per step"] * len(steps) + ["mean (nonzero)"] * len(steps)})

    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    sns.lineplot(data=df, x="step", y="reward", hue="type",
                 palette=["#1f77b4", "#888888"], marker="o", markersize=3, ax=ax)
    ax.axhline(0.752, linestyle="--", linewidth=0.7, color="red", alpha=0.5)
    ax.text(steps[-1] * 0.55, 0.755, "global max 0.752 (step 59)", fontsize=7, color="red")
    ax.set_xlabel("RL step")
    ax.set_ylabel("Composite reward")
    ax.set_title("REINVENT RL trajectory — agent diversified but did not converge",
                 fontsize=9, loc="left")
    ax.set_ylim(0, 0.85)
    ax.legend(loc="lower right", title="")

    plt.tight_layout()
    for ext in ("png", "svg"):
        out = OUT_DIR / f"fig_supp_reinvent_curve.{ext}"
        fig.savefig(out, dpi=300)
        print(f"wrote {out}")
    plt.close(fig)


def main():
    df = load_top10_dataframe()
    print("=== Top 10 data table ===")
    print(df[["id", "boltz_aff", "vina_kcal", "MW", "logP", "sel_combined"]].to_string(index=False))
    print()
    fig2_metrics(df)
    fig3_selectivity()
    fig_supp_reinvent()
    print("\nAll figures in:", OUT_DIR)


if __name__ == "__main__":
    main()
