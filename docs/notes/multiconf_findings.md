# Block F (multi-conformation robustness) — findings (2026-05-21 ~15:35)

Top-21 candidates × 4 PHGDH backbones (6CWA-apo, 6CWA+3PG, 6CWA+3PG+NADH, 2G76-apo).

## Headline findings

1. **ONS / K5K dominate by affinity across ALL conformations**:
   - ONS: -1.36 to -1.87 (mean ~-1.65, stdev 0.26)
   - K5K: -1.31 to -1.72 (mean ~-1.55, stdev 0.18)
   - Validates the Track 1 AD-repurposing prioritization.

2. **b1_115 emerges as a strong, previously-overlooked candidate**:
   - Affinity range: -1.73 to -1.08 across 4 conformations
   - In v1 top50 was only -0.56 — multi-conf shows it's much stronger.

3. **b2_067 is robustly strong** (-0.96 to -0.73, stdev 0.10) but still drug-like-fail (logP 7.1, PAINS).

4. **REINVENT step-59 hit doesn't hold up**: only -0.17 to +0.10. The 0.752 reward was driven by druglikeness, not affinity. **Drop from headline.**

5. **b1_058 weakened from v1**: -0.65 (v1) -> -0.02 to -0.18 (multi-conf). Boltz stochasticity or MSA variance.

## Verdict

- K5K + ONS Track 1 prioritization reinforced (low stdev for K5K = 0.18).
- Add b1_115 to Track 2 (previously overlooked).
- Drop reinvent step-59 from headline Track 4 recommendation.
- Disclose Boltz affinity-prediction stochasticity as a methodological caveat.
