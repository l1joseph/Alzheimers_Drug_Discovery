# Block G selectivity counter-screen — findings (2026-05-21 00:15)

Top 11 PHGDH candidates × 4 Rossmann-fold dehydrogenase off-targets (LDH-A, MDH2, GAPDH, IDH1).

`selectivity_index` = PHGDH affinity − min(off-target affinity). Negative = more selective for PHGDH (lower is better).

## Results

| Ligand | PHGDH | GAPDH | MDH2 | LDH-A | IDH1 | min_off | sel_idx | Interpretation |
|---|---|---|---|---|---|---|---|---|
| **K58 (BI-cmpd-15)** | −1.00 | +1.36 | +1.62 | +1.76 | +1.54 | +1.36 | **−2.36** | STRONG selectivity ✓ |
| **K5K (BI-4924)** | −1.79 | +0.00 | +0.13 | +0.21 | −0.17 | −0.17 | **−1.62** | STRONG selectivity ✓ |
| **NCT-503** | −0.30 | +1.43 | +1.56 | +1.57 | +1.16 | +1.16 | **−1.46** | STRONG selectivity ✓ |
| **ONV (NCT-cmpd-1)** | −1.02 | +1.09 | +0.56 | +0.75 | +0.11 | +0.11 | **−1.13** | STRONG selectivity ✓ |
| **ONS (NCT-cmpd-15)** | −1.82 | −1.06 | −0.95 | −0.34 | −0.05 | −1.06 | **−0.76** | modest (GAPDH off-target close) |
| r2b2_285 | −0.56 | +0.23 | +1.39 | +0.01 | +0.20 | +0.01 | −0.57 | modest |
| b1_051 | −0.48 | +0.40 | +0.26 | +0.18 | −0.07 | −0.07 | −0.41 | modest |
| b1_005 | −0.39 | +0.71 | −0.09 | +0.31 | −0.07 | −0.09 | −0.30 | modest |
| r2b2_107 | −0.66 | −0.50 | +0.65 | +0.23 | −0.19 | −0.50 | −0.16 | weak |
| b1_058 | −0.65 | −0.60 | +0.13 | −0.43 | +0.39 | −0.60 | −0.05 | barely selective |
| **b1_112** | −0.37 | **−0.85** | −0.45 | −0.28 | −0.40 | −0.85 | **+0.48** | NON-SELECTIVE → drop |

## Headline takeaways

1. **K58 (BI-cmpd-15) is the strongest selective PHGDH binder in the set** — sel_idx −2.36. Combined with its NAD-competitive mechanism (silences DBD activation per Park 2025) and the 1.42 Å co-crystal (highest-resolution PHGDH structure published, PDB 6RJ3), this is the **best AD repurposing candidate** by a substantial margin. K58's PHGDH affinity in our screen is moderate (−1.0) but its near-complete absence of off-target binding (all 4 off-targets predicted to NOT bind, aff ≥ +1.36) is striking.

2. **K5K (BI-4924) is the second-best repurposing candidate** — sel_idx −1.62, with the highest predicted PHGDH affinity (−1.79). NAD-competitive, industry-grade ADME from the Boehringer cancer program. The Track 1 wet-lab experiment we recommended earlier (Park 2025 fluorescence-polarization DBD-DNA assay) just got sharper: **K58 and K5K are the top two candidates.**

3. **NCT-503 is selective** (sel_idx −1.46) — re-validates its use in Park 2025 / Zhong 2025 in-vivo experiments as a clean probe.

4. **ONS / NCT-cmpd-15 reframing**: previously framed as "may beat NCT-503 because higher affinity." Selectivity tells a different story. ONS also binds GAPDH (−1.06) and MDH2 (−0.95) almost as well as PHGDH (−1.82). It's the most affinity-promiscuous of the allosteric series. **Probably not a better AD compound than NCT-503 because the off-target binding could cause confounding effects in cells.** Pull the earlier "ONS may be better than NCT-503" framing back to nuance.

5. **b1_112 is non-selective** — prefers GAPDH over PHGDH (+0.48 sel_idx). Drop it from the candidate list. The "4 novel B1 hits" reduce to **3**.

6. **The remaining B1 hits (b1_005, b1_051, b1_058) have modest-to-poor selectivity.** Adding lipophilic decoration to the NCT-503 scaffold appears to have driven promiscuity. This is a known optimization risk. They're still novel chemistry, but the selectivity loss vs NCT-503 should be flagged.

7. **r2b2_285 is unexpectedly the best of our novel hits by selectivity** (sel_idx −0.57). This is the *novel NAD-competitive* design from Round-2 B2. Worth promoting in the novel hits ranking.

## Implications for the candidate report

Need to update:
- Track 1 repurposing recommendation: **lead with K58 + K5K** (sel_idx ≤ −1.6), not with ONS/ONV (less selective in this screen).
- Drop b1_112 from the 4-novel-druglike list → 3 hits + r2b2_285.
- Add selectivity index column to the top50.csv.
- Note: NCT-503 successor compound ONS is more *affinity*-potent but less *selective* than NCT-503 itself.

## Caveats

- Selectivity index uses min(off-target) — single worst off-target. A more permissive view (mean off-target) would give different rankings.
- The off-targets are Rossmann-fold dehydrogenases. Kinase off-targets (ATP pocket promiscuity that the ChEMBL screen surfaced) are not in this counter-screen.
- All 4 off-target sequences have ColabFold MSAs (~7-21k sequences each); the MSA-fix removed null bytes that initially crashed Boltz.
- Block G v2 ran successfully under job 85181 on a single node × 4 APUs, ~5 min wall.
