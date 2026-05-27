# Boltz-2 predicted poses

Per-compound Boltz-2 predicted structures (protein + ligand) for every compound used in paper figures. These are the inputs that the PyMOL render scripts in `scripts/` consume.

## Files

| File | Compound | Source run | Used in figure |
|---|---|---|---|
| `K58_boltz_pred.cif` | K58 (BI-cmpd-15) | round-0 known-binder set | Fig 4 supp comparison (vs real 6RJ3) |
| `K5K_boltz_pred.cif` | K5K (BI-4924) | round-0 known-binder set | Fig 4 panel B |
| `NCT503_boltz_pred.cif` | NCT-503 | round-0 known-binder set | early interaction figure |
| `ONS_boltz_pred.cif` | ONS (NCT-cmpd-15) | round-0 known-binder set | optional |
| `ONV_boltz_pred.cif` | ONV (NCT-cmpd-1) | round-0 known-binder set | optional |
| `b1_005_boltz_pred.cif` | b1_005 (TamGen B1) | NCT-503-seeded TamGen | early interaction figure |
| `b1_051_boltz_pred.cif` | b1_051 (TamGen B1) | NCT-503-seeded TamGen | early interaction figure |
| `b1_058_boltz_pred.cif` | b1_058 (TamGen B1) | NCT-503-seeded TamGen | early interaction figure |
| `b1_112_boltz_pred.cif` | b1_112 (TamGen B1) | NCT-503-seeded TamGen | early interaction figure (dropped after kinase panel) |
| `r2b2_107_boltz_pred.cif` | r2b2_107 (TamGen B2-Round-2) | BI-4924-seeded iterative TamGen | Fig 4 panel C |

## How to regenerate the PyMOL figures

```bash
conda activate boltz-rocm    # provides PyMOL + RDKit

# Paper Figure 4 (3 panels: K58_real, K5K, r2b2_107)
pymol -cqr scripts/render_paper_fig4.py
# outputs: docs/figures/paper/fig4_*.png

# Earlier interaction figures (b1 series + references)
pymol -cqr scripts/render_top_candidates.py
# outputs: docs/figures/interactions/*.png
```

## How these were predicted

Each CIF is the `model_0` output of running Boltz-2 (`tools/boltz/`) with:
- Protein: PHGDH chain A (residues 6-278, see `data/phgdh_6CWA_chainA.fasta`)
- MSA: ColabFold MMseqs2 result (cached at `data/msa/phgdh_6CWA_chainA.a3m`, not tracked in git)
- Ligand: the canonical SMILES from `data/libraries/known_phgdh_binders.csv` (validated set) or `results/tamgen_*/samples.csv` (designed set)

To re-predict from scratch: see `slurm/boltz_screen.sh` and `slurm/boltz_array_screen.sh`.
