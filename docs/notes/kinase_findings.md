# Kinase counter-screen findings (2026-05-21 16:04)

Top-11 candidates × 2 GRK kinases (GRK5, GRK2 — the original ChEMBL3093256 targets).
GRK kinase pockets are ATP-binding sites; selected to test the kinase-pharmacophore
promiscuity hypothesis suggested by the ChEMBL screen.

## Results (kinase selectivity index = PHGDH affinity − min(GRK affinity))

| Ligand | PHGDH | GRK5 | GRK2 | min_kinase | sel_idx | Interpretation |
|---|---|---|---|---|---|---|
| **K58 (BI-cmpd-15)** | −1.00 | +1.62 | +1.42 | +1.42 | **−2.42** | STRONG ✓✓ |
| **K5K (BI-4924)** | −1.79 | +0.57 | +0.14 | +0.14 | **−1.93** | STRONG ✓ |
| **ONS (NCT-cmpd-15)** | −1.82 | −0.00 | +0.05 | −0.00 | **−1.82** | STRONG ✓ |
| NCT-503 | −0.30 | +1.22 | +0.96 | +0.96 | −1.26 | STRONG |
| ONV (NCT-cmpd-1) | −1.02 | −0.05 | −0.49 | −0.49 | −0.53 | modest |
| r2b2_107 | −0.66 | +0.57 | +0.45 | +0.45 | −1.11 | STRONG |
| r2b2_285 | −0.56 | +1.00 | +0.33 | +0.33 | −0.89 | modest |
| b1_051 | −0.48 | +0.09 | +0.08 | +0.08 | −0.56 | modest |
| **b1_005** | −0.39 | −0.43 | +0.04 | −0.43 | **+0.04** | NON-SELECTIVE |
| **b1_058** | −0.65 | −1.11 | −1.40 | −1.40 | **+0.75** | **PREFERS GRK2 OFF-TARGET** |
| **b1_112** | −0.37 | −0.98 | −0.90 | −0.98 | **+0.61** | PREFERS GRK5 |

## Combined selectivity (sum of dehydrogenase + kinase sel_idx)

| Ligand | Dehydrogenase sel_idx | Kinase sel_idx | **Combined** | Tier |
|---|---|---|---|---|
| **K58** | **−2.36** | **−2.42** | **−4.78** | **Tier 1 — wins both panels by wide margin** |
| **K5K** | −1.62 | −1.93 | **−3.55** | Tier 1 |
| **NCT-503** | −1.46 | −1.26 | **−2.72** | Tier 1 |
| **ONS** | −0.76 | −1.82 | **−2.58** | Tier 1 |
| ONV | −1.13 | −0.53 | −1.66 | Tier 2 |
| r2b2_107 | −0.16 | −1.11 | −1.27 | Tier 2 |
| b1_051 | −0.41 | −0.56 | −0.97 | Tier 3 — weakly selective |
| b1_005 | −0.30 | +0.04 | −0.26 | Tier 3 |
| **b1_058** | −0.05 | **+0.75** | **+0.70** | **DROP** — prefers off-targets |
| **b1_112** | +0.48 | +0.61 | **+1.09** | DROP |

## Headline implications

1. **K58 (BI-cmpd-15) is the cleanest binder in the entire study** — wins both selectivity panels with sel_idx ≤ −2.36 each. Combined selectivity reservoir −4.78. This was already the Track 1 #1 recommendation; the kinase data only strengthens it.

2. **ONS gets a meaningful upgrade**: previously flagged as "modest selectivity" (vs dehydrogenases). Against kinases it's STRONG (−1.82). Combined −2.58 puts it solidly in Tier 1 alongside K5K and NCT-503. Its earlier framing as "less selective than NCT-503" was based only on the dehydrogenase panel.

3. **The B1 series is now untenable as composition-of-matter candidates**:
   - b1_058 (previously the "best CNS-druggable B1 hit" at MW 469): actually PREFERS GRK2 by 0.75 log-Kd. Drop.
   - b1_112 was already dropped after Block G; the kinase data confirms.
   - b1_005 (the "best surviving B1 hit") is non-selective overall.
   - The lipophilic decoration applied to the NCT-503 scaffold during TamGen B1 generated kinase-like pharmacophore features — exactly the failure mode the ChEMBL screen's kinase enrichment had suggested.

4. **The "Track 2 novel scaffold-seeded" recommendation collapses.** None of the B1 hits survive both selectivity panels. The novelty advantage doesn't compensate for off-target promiscuity.

5. **r2b2_107 (novel NAD-competitive scaffold) survives** with reasonable combined selectivity (−1.27). This was the only TamGen-generated novel druglike candidate with passable selectivity in both panels. Should remain in Track 2 (sole survivor).

## Revised candidate ranking

| Tier | Candidates | Action |
|---|---|---|
| **1 (clean)** | K58, K5K, NCT-503, ONS | **Recommend wet-lab Park 2025 DBD assay** — all 4 head-to-head |
| **2 (modest selectivity)** | ONV, r2b2_107 | Backup compounds for wet-lab if Tier 1 budget allows |
| **3 (weak but PHGDH-preferring)** | b1_051, b1_005 | Computational interest only — not synthesis priority |
| **DROP** | b1_058, b1_112, reinvent_step59 | Off-target promiscuity / reward artifact |
