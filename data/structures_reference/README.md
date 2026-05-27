# PHGDH co-crystal reference structures

Real PDB co-crystals of PHGDH with each compound in the validated-binder reference set. Sources are the original PDB entries; we use these for paper figures (binding-pose references in Figure 4) and for sanity-checking Boltz-predicted poses against published structures.

| File | PDB ID | Bound ligand | Compound name | Resolution | Source |
|---|---|---|---|---|---|
| `6CWA_PHGDH_NADH_3PG_ternary.cif` | 6CWA | NADH + 3PG | (endogenous ternary) | 1.85 Å | Unni et al. 2018 |
| `6RJ3_K58_BI-cmpd-15.cif` | 6RJ3 | K58 | BI-cmpd-15 (NAD-competitive) | **1.42 Å** (highest-res PHGDH) | Spillier et al. 2019 *J Med Chem* |
| `6RJ6_K5K_BI-4924.cif` | 6RJ6 | K5K | BI-4924 (NAD-competitive) | 1.98 Å | Spillier et al. 2019 *J Med Chem* |
| `6PLF_ONV_NCT-cmpd-1.cif` | 6PLF | ONV | NCT-cmpd-1 (allosteric) | 1.7 Å | Pacold et al. 2016 *Nat Chem Biol* |
| `6PLG_ONS_NCT-cmpd-15.cif` | 6PLG | ONS | NCT-cmpd-15 (allosteric) | 2.0 Å | Pacold et al. 2016 *Nat Chem Biol* |
| `2G76_PHGDH_D-malate.cif` | 2G76 | D-malate | (near-apo) | 1.7 Å | Dey et al. 2008 |
| `7EWH_HMT_homoharringtonine.cif` | 7EWH | HMT | homoharringtonine | 2.5 Å | natural-product binder |

NCT-503 itself does not have a published co-crystal in PDB — the Pacold 2016 series structures (6PLF/6PLG) cover the same allosteric pocket with sibling compounds.

The processed apo / co-bound structures used as Boltz target inputs live in `data/targets/`; these are stripped + chain-A-only versions of the above.
