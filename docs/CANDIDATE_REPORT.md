# PHGDH novel hit candidates — assessment report

Generated 2026-05-20 from `results/final/top50.csv` and the v1 pipeline runs.
See also: [PLAN.md](../PLAN.md), [PLAN_v2.md](../PLAN_v2.md), [README.md](../README.md).

---

## TL;DR

From the v1 pipeline (887 candidates across de novo, scaffold-seeded, and PKU-repurposing branches), **4 compounds are both novel and drug-like**. All come from the same scaffold-seeded lineage (B1, NCT-503 family, allosteric pocket).

They are predicted **mid-nM-range leads, not optimized drugs**. Their Boltz-2 affinity scores sit at roughly one third of validated PHGDH inhibitors. They pass Lipinski + PAINS + SA filters cleanly, with Tanimoto similarity ≤ 0.15 to any known PHGDH binder.

**Verdict: leads worth following up on, not finished candidates.** The honest path forward is orthogonal validation (MM-GBSA + Vina rescore, multi-conformation robustness, selectivity counter-screen) and the ChEMBL 5k library screen currently running (`sbatch 85169_[0-3]`).

---

## The 4 novel candidates

| rank in top50 | id | Boltz aff (logKd-like) | ~Kd | MW | logP | SA | HBD/HBA | Tanimoto to nearest known | nearest known | scaffold seed |
|---|---|---|---|---|---|---|---|---|---|---|
| 16 | **b1_058** | −0.65 | ~220 nM | 469.4 | 3.37 | 4.02 | 1 / 6 | 0.14 | BI-cmpd-15 | NCT-503 |
| 29 | **b1_051** | −0.48 | ~330 nM | 310.3 | 4.26 | 3.30 | 1 / 4 | 0.12 | NCT-503 | NCT-503 |
| 32 | **b1_005** | −0.39 | ~400 nM | 309.3 | 3.92 | 3.21 | 1 / 4 | 0.12 | NCT-503 | NCT-503 |
| 35 | **b1_112** | −0.37 | ~430 nM | 489.9 | 4.50 | 3.98 | 1 / 6 | 0.15 | NCT-503 | NCT-503 |

All four:
- Lipinski-passing (MW < 500, logP < 5, HBD ≤ 5, HBA ≤ 10)
- PAINS filter clean (no known reactive/false-positive patterns)
- SA score 3.2–4.0 — well within commercially-synthesizable range
- Tanimoto < 0.16 to **any** validated PHGDH binder → genuine new chemistry, not analog rediscovery

(~Kd estimates are rough conversions of the Boltz `affinity_pred_value` log-units. Treat as order-of-magnitude.)

---

## Context: where these sit vs validated inhibitors

| compound | source | Boltz aff | ~Kd | role |
|---|---|---|---|---|
| **ONS (NCT-cmpd-15)** | round-0 known | −1.82 | ~15 nM | validated PHGDH inhibitor (catalytic) |
| **K5K (BI-4924)** | round-0 known | −1.79 | ~16 nM | validated nM-range inhibitor, co-crystal in 6RJ6 |
| K58 (BI-cmpd-15) | round-0 known | ≤ −1.0 (not top 10) | ~100 nM | validated, 6RJ3 highest-res co-crystal |
| **NCT-503** (parent) | round-0 known | not in top 50 | — | parent of B1 series; allosteric inhibitor |
| ONV (NCT-cmpd-1) | round-0 known | −1.02 | ~95 nM | validated allosteric |
| b1_058 (best novel) | tamgen B1 | −0.65 | ~220 nM | **novel lead** |
| b2_067 (best designed, but not druglike) | tamgen B2 | −1.59 | ~25 nM | **fails druglikeness** (logP 7.1, PAINS hit) |

**Read this honestly**: The strongest *predicted* binder we designed (b2_067 at −1.59) reward-hacks the affinity score — Boltz scored it well but it would fail in vivo (logP 7.1 is far outside the bioavailable window, plus a PAINS hit). The composite-reward RL plan (REINVENT, Block C/D) is designed to prevent exactly that mode going forward.

Among compounds that pass drug-likeness AND have novel chemistry, the B1 series tops out at b1_058's −0.65. That's a ~3× weaker predicted affinity than the validated nM binders. For *fragment-grade* hits in a virtual screen that's good. For *optimized leads* it's not.

---

## Interaction figures

Predicted poses are rendered with PyMOL: cyan = ligand, gray cartoon = PHGDH backbone, wheat sticks = pocket residues within 5 Å, yellow dashes = H-bonds < 3.5 Å.

### The 4 novel candidates

| **b1_058** (Tani 0.14, aff −0.65) | **b1_051** (Tani 0.12, aff −0.48) |
| :---: | :---: |
| ![](figures/interactions/b1_058.png) | ![](figures/interactions/b1_051.png) |
| **b1_005** (Tani 0.12, aff −0.39) | **b1_112** (Tani 0.15, aff −0.37) |
| ![](figures/interactions/b1_005.png) | ![](figures/interactions/b1_112.png) |

### Reference binders (for visual comparison)

| **K5K (BI-4924)** validated, aff −1.79 | **NCT-503** parent scaffold |
| :---: | :---: |
| ![](figures/interactions/K5K.png) | ![](figures/interactions/NCT503.png) |

(Renders are made directly from each candidate's Boltz-predicted CIF — no manual posing.)

---

## How novel are they?

Tanimoto similarity (Morgan radius-2, 2048-bit) to the nearest of 10 validated PHGDH binders:

| Tanimoto window | Interpretation | Hits in this window |
|---|---|---|
| ≥ 0.85 | analog of known — essentially same molecule | K5K, ONS, ONV, K58 (validated controls) |
| 0.4 – 0.85 | conventionally novel but obviously inspired | (none in our novel druglike set) |
| 0.15 – 0.4 | distinct chemistry, possibly related core | b1_112 (0.15), b1_058 (0.14) |
| < 0.15 | unrelated chemistry by standard cheminformatics | b1_051 (0.12), b1_005 (0.12) |

**All four are conventionally novel** (< 0.4) and two are well below the typical "novel chemotype" cutoff. The catch: all four come from the *same scaffold-seeded TamGen run*, so they share lineage even though pairwise similarity to known binders is low. Treat them as a single chemical series with internal diversity, not four independent discoveries.

---

## Validity caveats — what we know, what we don't

1. **Boltz affinity is a prediction, not an experiment.** The Boltz-2 model was trained on PDBBind-like data and has shown ~0.6 Pearson with measured affinities in published benchmarks. We *validated pose recovery* on 5 known PHGDH-ligand co-crystal structures and got centroid RMSD < 2 Å in 4 of 5 cases — so the geometry is trustworthy, but the affinity *number* should be treated as a ranking, not an absolute. A predicted "220 nM" might be anywhere from 50 nM to 2 μM in vitro.

2. **All 4 hits share a scaffold lineage.** Diversity within the set is real (pairwise Tanimoto between b1_058 and b1_051 ≈ 0.3) but not as broad as 4 independent novel chemotypes would be. A negative result for one might generalize to all.

3. **No multi-conformation cross-check yet.** All scores are against `6CWA_apo` (C1). We have 3 other conformations (`6CWA+3PG` ternary, `2G76 apo`, `6PLF-allosteric`) — robustness across these would significantly tighten confidence. (Block F in PLAN_v2.)

4. **No selectivity data.** PHGDH is a Rossmann-fold dehydrogenase. Compounds that bind its NADH/allosteric pocket could plausibly bind LDH-A, MDH2, GAPDH, IDH1. A counter-screen (Block G) is queued in the plan.

5. **No orthogonal scoring engine.** Vina + MM-GBSA rescore (Block E) would tell us whether Boltz's affinity ranking holds up under an independent physics-based score.

6. **NCT-503 itself didn't make the top 50.** That's striking. It could mean (a) Boltz is noisy on the parent at this conformation (we used apo, but NCT-503's co-crystal is with a slightly different state), or (b) the scaffold-decorated children actually have better predicted affinity than the parent — a real "lead optimization" signal — or (c) the score is noisy at this affinity range and we shouldn't over-interpret. The orthogonal rescore (Block E) is the most direct way to distinguish these.

---

## Are any of these viable drug candidates?

Honest answer: **not yet.** These are virtual hits that have cleared drug-likeness and novelty filters but have not yet been validated by:

- A second, physics-based scoring engine (Vina / MM-GBSA — queued, Block E)
- Multi-conformation Boltz scoring (queued, Block F)
- Selectivity testing against off-target dehydrogenases (queued, Block G)
- **Wet-lab anything** (out of scope — no wet lab in this project)

For a follow-up team to consider these worth synthesizing:
- All 4 should be re-scored with Vina + MM-GBSA. If 2+ agree with Boltz's ranking, that's meaningful corroboration.
- All 4 should be tested across the 4-conformation ensemble. If 2+ remain top-50 across all 4, that's *strong* evidence of a real binding mode.
- All 4 should be counter-screened against LDH-A and MDH2. If selectivity index > 1 log-Kd, that's worth a tox/PK assessment.
- If passing all 3 layers, **b1_058 is the most promising single candidate** (best predicted affinity in the novel-druglike set, MW 469 / logP 3.4 — well within drug space).

---

## What's currently running

| Block | Job | Status | What it adds |
|---|---|---|---|
| **B** | 85169_[0-3] | running (~2h) | ChEMBL 5k drug-like screen — could surface a stronger candidate from existing-drug repurposing |
| E | (queued) | not yet | Vina + MM-GBSA orthogonal rescore — strengthens the predictions above |
| F | (queued) | not yet | Multi-conformation robustness — top-20 across 4 backbones |
| G | (queued) | not yet | Selectivity vs LDH-A / MDH2 / GAPDH / IDH1 |
| C/D | (queued) | not yet | REINVENT closed-loop RL with composite reward — could break the −1.79 affinity ceiling |

By 08:00 tomorrow, the report will be re-issued with whichever of these completed. Acceptance criteria + fallbacks are in `PLAN_v2.md`.
