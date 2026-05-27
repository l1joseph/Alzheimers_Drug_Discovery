"""Assemble Figure 1: 3-panel composite for the PHGDH-AD paper.

Panel A (top-left): PyMOL render of PHGDH with HHTH-DBD region + inhibitor pocket
                    overlap highlighted. Loaded from
                    docs/figures/paper/fig1A_phgdh_pockets.png

Panel B (top-right): Chen 2025 Cell mechanism schematic — catalytic mode
                     (NAD+ + 3PG -> serine) and the moonlighting transcription-
                     factor mode (HHTH-DBD drives IKKalpha + HMGB1).

Panel C (bottom):    horizontal pipeline flowchart with 4 swim-lanes.

Output:
    docs/figures/paper/fig1_target_pipeline.{png,svg}   300 DPI

Run under boltz-rocm env:
    python scripts/render_fig1_composite.py
"""
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.gridspec import GridSpec

PROJECT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery")
OUT_DIR = PROJECT / "docs" / "figures" / "paper"
PANEL_A_PNG = OUT_DIR / "fig1A_phgdh_pockets.png"
OUT_PNG = OUT_DIR / "fig1_target_pipeline.png"
OUT_SVG = OUT_DIR / "fig1_target_pipeline.svg"

sns.set_theme(style="whitegrid", context="paper")
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "axes.titleweight": "bold",
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})

COLOR_HHTH = "#c53030"       # red — HHTH-DBD region
COLOR_OVERLAP = "#e6c800"    # yellow — pocket residues overlapping HHTH (149-156)
COLOR_POCKET = "#e6932a"     # orange — pocket residues outside HHTH
COLOR_NADH = "#1f9fb4"       # cyan — NADH cofactor
COLOR_INH = "#b53389"        # magenta — K58 inhibitor
COLOR_CAT = "#1f7fb4"        # blue — catalytic dimer
COLOR_TF = "#7a3c8c"         # purple — transcription factor mode dimer
COLOR_DNA1 = "#444444"
COLOR_DNA2 = "#888888"
COLOR_BOX_GEN = "#ecd1ad"
COLOR_BOX_SCORE = "#bcd7ec"
COLOR_BOX_VAL = "#c7e2c4"
COLOR_BOX_RANK = "#e9c2c2"


# --------------------------------------------------------------------------- #
# Panel A: PyMOL PNG + matplotlib legend overlay (no arrows; legend swatches)
# --------------------------------------------------------------------------- #
def draw_panel_a(ax):
    if PANEL_A_PNG.exists():
        img = mpimg.imread(str(PANEL_A_PNG))
        ax.imshow(img)
    else:
        ax.text(0.5, 0.5, "[Panel A PyMOL render missing]",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=12, color="red")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines[:].set_visible(False)
    ax.grid(False)

    ax.set_title("a   PHGDH target: inhibitor pocket overlaps the HHTH-DBD motif",
                 loc="left", fontsize=12, fontweight="bold")

    # Inset legend with color swatches
    legend_items = [
        (COLOR_HHTH,    "HHTH-DBD ribbon (residues 103–165)"),
        (COLOR_OVERLAP, "Pocket residues in HHTH (149–156)"),
        (COLOR_POCKET,  "Pocket residues outside HHTH"),
        (COLOR_NADH,    "NADH cofactor (6CWA)"),
        (COLOR_INH,     "K58 inhibitor (6RJ3)"),
    ]
    legend_x = 0.02
    legend_y_top = 0.97
    line_h = 0.045
    for i, (color, label) in enumerate(legend_items):
        y = legend_y_top - i * line_h
        ax.add_patch(mpatches.Rectangle(
            (legend_x, y - 0.018), 0.030, 0.024,
            transform=ax.transAxes,
            facecolor=color, edgecolor="black", linewidth=0.6,
            zorder=5,
        ))
        ax.text(
            legend_x + 0.040, y, label,
            transform=ax.transAxes,
            fontsize=8.0, color="black", ha="left", va="center",
            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.85),
            zorder=5,
        )


# --------------------------------------------------------------------------- #
# Panel B: Chen 2025 moonlighting mechanism cartoon
# --------------------------------------------------------------------------- #
def _dimer(ax, x, y, color):
    sub_h = 0.55
    sub_w = 0.9
    e1 = mpatches.Ellipse((x, y + sub_h * 0.55), sub_w, sub_h,
                          facecolor=color, edgecolor="black", lw=1.2, alpha=0.92)
    e2 = mpatches.Ellipse((x, y - sub_h * 0.55), sub_w, sub_h,
                          facecolor=color, edgecolor="black", lw=1.2, alpha=0.92)
    ax.add_patch(e1)
    ax.add_patch(e2)


def _arrow(ax, x0, y0, x1, y1, color="black", lw=1.4, style="-|>"):
    arr = FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style,
                          color=color, lw=lw, mutation_scale=14,
                          shrinkA=2, shrinkB=2)
    ax.add_patch(arr)


def _ligand(ax, x, y, label, color, r=0.10):
    c = mpatches.Circle((x, y), r, facecolor=color, edgecolor="black", lw=0.8)
    ax.add_patch(c)
    ax.text(x, y - r - 0.02, label, ha="center", va="top",
            fontsize=8, color="black", fontweight="bold")


def _dna_helix(ax, x0, y0, x1, y1):
    import numpy as np
    n = 60
    t = np.linspace(0, 1, n)
    xs = x0 + (x1 - x0) * t
    base = y0 + (y1 - y0) * t
    amp = 0.06
    freq = 4.5
    y_a = base + amp * np.sin(2 * np.pi * freq * t)
    y_b = base + amp * np.sin(2 * np.pi * freq * t + np.pi)
    ax.plot(xs, y_a, color=COLOR_DNA1, lw=1.8)
    ax.plot(xs, y_b, color=COLOR_DNA2, lw=1.8)
    for i in range(2, n - 2, 4):
        ax.plot([xs[i], xs[i]], [y_a[i], y_b[i]], color="#999999", lw=0.7)


def draw_panel_b(ax):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines[:].set_visible(False)
    ax.grid(False)

    ax.set_title("b   PHGDH moonlights as a transcription factor (Chen et al. 2025)",
                 loc="left", fontsize=12, fontweight="bold")

    ax.plot([5.0, 5.0], [0.4, 5.0], color="gray", lw=0.8,
            linestyle=(0, (4, 3)))

    # ===== LEFT subpanel: catalytic mode =====
    ax.text(2.5, 5.05, "Catalytic mode (canonical)",
            ha="center", va="bottom", fontsize=10.5, fontweight="bold")
    _dimer(ax, 2.5, 2.7, COLOR_CAT)
    _ligand(ax, 1.05, 3.5, "NAD$^+$", "#cfe7f5")
    _ligand(ax, 1.05, 2.0, "3PG", "#cfe7f5")
    _arrow(ax, 1.30, 3.5, 1.95, 3.0, color="gray")
    _arrow(ax, 1.30, 2.0, 1.95, 2.5, color="gray")
    _arrow(ax, 3.1, 2.7, 3.95, 2.7, color="black", lw=1.6)
    _ligand(ax, 4.25, 2.7, "Ser", "#f3e6c3")
    ax.text(2.5, 0.7, "Serine biosynthesis",
            ha="center", va="center", fontsize=8.5,
            style="italic", color="#555555")

    # ===== RIGHT subpanel: moonlighting TF mode =====
    ax.text(7.5, 5.05, "Moonlighting transcription factor",
            ha="center", va="bottom", fontsize=10.5, fontweight="bold")
    _dimer(ax, 6.6, 2.7, "#bda6d4")

    # HHTH-DBD motif highlighted on the dimer as a red wedge
    hhth = FancyBboxPatch((7.15, 2.30), 1.10, 0.80,
                          boxstyle="round,pad=0.02,rounding_size=0.10",
                          linewidth=1.4, edgecolor="black",
                          facecolor=COLOR_HHTH, alpha=0.85)
    ax.add_patch(hhth)
    ax.text(7.70, 2.95, "HHTH",
            ha="center", va="center", fontsize=9,
            fontweight="bold", color="white")
    ax.text(7.70, 2.55, "res 103–165",
            ha="center", va="center", fontsize=7,
            color="white", style="italic")

    # DNA helix
    _dna_helix(ax, 6.55, 1.4, 9.5, 1.4)
    _arrow(ax, 7.70, 2.30, 7.70, 1.55, color=COLOR_HHTH, lw=1.4)

    # Gene targets + downstream
    ax.text(8.05, 0.95,
            "IKK$\\alpha$ + HMGB1\nin astrocytes",
            ha="center", va="top", fontsize=8.5, color=COLOR_HHTH,
            fontweight="bold")
    ax.text(7.5, 0.30,
            "→ NF-κB ↑, autophagy ↓\n→ amyloid pathology",
            ha="center", va="top", fontsize=7.5, color="#555555", style="italic")

    # NADH-independent annotation
    ax.text(7.5, 4.45,
            "(independent of\nenzymatic activity)",
            ha="center", va="top", fontsize=7.5, color="#555555", style="italic")


# --------------------------------------------------------------------------- #
# Panel C: pipeline flowchart (unchanged)
# --------------------------------------------------------------------------- #
def _flow_stage(ax, x, y, w, h, title, sub_items, color):
    outer = FancyBboxPatch((x, y), w, h,
                           boxstyle="round,pad=0.04,rounding_size=0.12",
                           linewidth=1.5, edgecolor="black",
                           facecolor=color, alpha=0.55)
    ax.add_patch(outer)
    ax.text(x + w / 2, y + h - 0.18, title,
            ha="center", va="top", fontsize=10.5, fontweight="bold",
            color="black")
    n = len(sub_items)
    inner_top = y + h - 0.40
    inner_bot = y + 0.18
    sub_h = (inner_top - inner_bot) / max(n, 1) - 0.05
    for i, label in enumerate(sub_items):
        sy = inner_top - (i + 1) * (sub_h + 0.05) + 0.05
        sub = FancyBboxPatch((x + 0.10, sy), w - 0.20, sub_h,
                             boxstyle="round,pad=0.02,rounding_size=0.06",
                             linewidth=0.9, edgecolor="black",
                             facecolor="white", alpha=0.95)
        ax.add_patch(sub)
        ax.text(x + w / 2, sy + sub_h / 2, label,
                ha="center", va="center", fontsize=8.5)


def draw_panel_c(ax):
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 5)
    ax.set_aspect("auto")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines[:].set_visible(False)
    ax.grid(False)
    ax.set_title("c   Pipeline: candidate generation → scoring "
                 "→ validation → ranking",
                 loc="left", fontsize=12, fontweight="bold")

    stages = [
        (0.4, 0.4, 4.4, 4.2, "Candidate generation",
         ["TamGen\n(scaffold-seeded)",
          "ChEMBL 5k library",
          "REINVENT RL\n(composite reward)"],
         COLOR_BOX_GEN),
        (5.4, 0.4, 4.0, 4.2, "Scoring",
         ["Boltz-2\n(affinity + structure)",
          "AutoDock Vina\n(orthogonal rescore)"],
         COLOR_BOX_SCORE),
        (10.0, 0.4, 6.0, 4.2, "Validation",
         ["Multi-conformation robustness\n(4 PHGDH backbones)",
          "Off-target: 4 Rossmann-fold\ndehydrogenases",
          "Off-target: 2 GRK kinases"],
         COLOR_BOX_VAL),
        (16.6, 0.4, 3.2, 4.2, "Ranking",
         ["Combined selectivity\nindex"],
         COLOR_BOX_RANK),
    ]
    for s in stages:
        _flow_stage(ax, *s)
    arrow_y = 2.5
    for i in range(len(stages) - 1):
        x0 = stages[i][0] + stages[i][2] + 0.05
        x1 = stages[i + 1][0] - 0.05
        arr = FancyArrowPatch((x0, arrow_y), (x1, arrow_y),
                              arrowstyle="-|>", color="black",
                              lw=2.0, mutation_scale=18,
                              shrinkA=0, shrinkB=0)
        ax.add_patch(arr)


# --------------------------------------------------------------------------- #
def main():
    fig = plt.figure(figsize=(14, 11))
    gs = GridSpec(
        nrows=2, ncols=2,
        figure=fig,
        height_ratios=[2.0, 1.0],
        width_ratios=[1.0, 1.0],
        hspace=0.18, wspace=0.08,
    )
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, :])
    draw_panel_a(ax_a)
    draw_panel_b(ax_b)
    draw_panel_c(ax_c)
    fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT_SVG, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {OUT_PNG}")
    print(f"wrote {OUT_SVG}")


if __name__ == "__main__":
    main()
