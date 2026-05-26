# Final paper plan — 5-page PHGDH-AD drug discovery report

**Target deadline:** 06/09/2026 (assumed; user-supplied date "06/09/2025" is past, treating as typo).
**Page limit:** 5 pages **including** figures and references. Tight.
**Format:** standard scientific paper, single submission for the whole team.

---

## Page budget

| Section | Pages | Word target | Maps to rubric |
|---|---|---|---|
| Title + Abstract + Authors | 0.4 | 150 | — |
| 1. Introduction | 0.7 | 500 | Biological problem; rationale for target + site; AD relevance |
| 2. Data & Methods | 1.0 | 700 | Data used; methods pipeline |
| 3. Results | 1.7 | 1100 | Designed compounds; evaluation; comparisons with known binders |
| 4. Discussion | 0.5 | 350 | Insights into disease; limitations; future work |
| References | 0.4 | (10-12 refs) | — |
| Author Contributions | 0.3 | 150 | required by spec |
| **Total** | **5.0** | **~2950 words + figs** | — |

Figures occupy space in Results section. With 3 figures at ~1/4 page each, Results text shrinks to ~800 words.

---

## Figure plan (3 figures, max)

**Figure 1 — Pipeline overview + target structure** (top of page 2 or 3, half-page)
- LEFT: PHGDH cartoon (gray) with two pockets highlighted: NCT-503 allosteric site (orange) and NADH site (cyan). Annotate NADH cofactor + bound 3PG substrate. Use the existing `docs/figures/phgdh_pymol.png` as a base; may need to add pocket sphere labels.
- RIGHT: Pipeline schematic (Mermaid → exported PNG): three generation engines (TamGen scaffold-seeded / ChEMBL library / REINVENT RL) → Boltz-2 scoring → four-layer validation (Vina, multi-conf, dehydrogenase panel, kinase panel) → final ranking.
- **Caption:** target structure + dual-pocket strategy + methods overview in one figure.

**Figure 2 — Selectivity-validated candidate ranking** (middle of Results, half-page)
- Heatmap or grouped bar chart: Top 11 candidates × 6 off-targets (LDH-A, MDH2, GAPDH, IDH1, GRK5, GRK2) + 1 on-target (PHGDH).
- Color scale: blue = strong PHGDH binding, red = strong off-target binding. White = neutral.
- Annotate the combined selectivity index per compound at the right edge.
- **Caption:** "K58 (BI-cmpd-15) is the cleanest binder across all 6 off-targets. Three novel scaffold-seeded TamGen hits show off-target promiscuity (b1_058/112 prefer GRK kinases; b1_005 non-selective)."

**Figure 3 — Binding-pose comparison: validated vs designed compounds** (Results, quarter-page)
- 4-panel grid: K5K (BI-4924, validated reference) | NCT-503 (AD-tested reference) | r2b2_107 (sole novel-scaffold survivor) | REINVENT step-59 hit (Track 4, failed multi-conf check)
- Use existing PyMOL renders from `docs/figures/interactions/`; need to add renders for r2b2_107 and the REINVENT step-59 compound (re-fold via Boltz and render via existing `scripts/render_top_candidates.py`).
- **Caption:** "Predicted poses of designed candidates vs validated PHGDH inhibitors. Cyan = ligand; gray = PHGDH backbone; wheat = pocket residues; yellow dashes = H-bonds <3.5 Å."

---

## Section-by-section content

### Title (~15 words)

Working title: **"Selectivity-Validated Repurposing Candidates for the Moonlighting DNA-Binding Function of PHGDH in Alzheimer's Disease"**

Alternatives:
- "Computational rescreen of PHGDH inhibitors against the Park 2025 moonlighting-DBD axis for Alzheimer's repurposing"
- (shorter) "Computational selectivity screen identifies BI-cmpd-15 as a candidate PHGDH-DBD inhibitor for Alzheimer's"

### Abstract (~150 words)

One paragraph hitting: (a) biological motivation (Park 2025 moonlighting-DBD discovery + AD link), (b) methods one-liner (three generation engines + four-layer validation pipeline using Boltz-2 on AMD MI300A), (c) headline result (K58/BI-cmpd-15 cleanest selective binder, combined sel_idx −4.78; novel-scaffold hits fail kinase selectivity), (d) recommendation (4-compound Tier 1 head-to-head wet-lab DBD-DNA assay).

Draft sentence-level outline:
1. PHGDH moonlights as a transcription factor via its C-terminal regulatory domain (Park 2025) and is implicated in AD.
2. Of the published PHGDH inhibitors, only NCT-503 has in-vivo AD evidence.
3. We computationally screened 4 candidate sets — known binders, scaffold-seeded designs, ChEMBL repurposing, and REINVENT RL — for both affinity and selectivity against the PHGDH-DBD pocket.
4. Boltz-2 scoring + AutoDock Vina rescore + multi-conformation robustness + off-target counter-screens (4 Rossmann-fold dehydrogenases + 2 kinases).
5. K58 (BI-cmpd-15) emerges as the cleanest selective binder.
6. Three of four novel scaffold-seeded designs fail kinase selectivity — a result the on-target screen alone wouldn't have caught.
7. Recommendation: 4-compound wet-lab DBD-DNA assay (K58 / K5K / NCT-503 / ONS).

### 1. Introduction (~500 words)

**Paragraph 1 — biological problem** (~120 words):
PHGDH (EC 1.1.1.95) first committed enzyme of serine biosynthesis. Two functions: catalytic (3PG → 3PHP, NAD⁺-dependent) and a recently-discovered moonlighting DNA-binding role via the C-terminal regulatory domain (Park 2025 *Cell Metabolism*). NADH allosterically activates the DBD function. PHGDH is implicated in AD pathology through this moonlighting axis (Park 2025; Zhong 2025 PMC12204802).

**Paragraph 2 — drug-discovery context + target rationale** (~140 words):
PHGDH has been an oncology target for ~15 years (Possemato 2011 *Nature*; Locasale 2011 *Nat Genet*); multiple inhibitor series exist (NCT-503 allosteric from Pacold 2016 *Nat Chem Biol*; BI-4924 / BI-cmpd-15 NAD-competitive from Spillier 2019 *J Med Chem*). However, **only NCT-503 has published in-vivo AD evidence** — making the rest of the chemical matter *plausibly* AD-relevant but untested. Our hypothesis: NAD-competitive inhibitors should silence the DBD function by competing the activating NADH cofactor off the protein; allosteric inhibitors should perturb the regulatory domain. Two axes; both worth testing.

**Paragraph 3 — gap and approach** (~140 words):
Standard *affinity-only* screens would re-prioritize known inhibitors by predicted affinity. But for *AD repurposing* the operational question is "which existing PHGDH binders are selective enough to safely repurpose?" We address this with a two-axis ranking: predicted affinity (Boltz-2 + AutoDock Vina) AND off-target selectivity against the most chemically-related proteins (Rossmann-fold dehydrogenases that share the NADH-pocket fold; kinases that share generic ATP-pocket pharmacophore). We also probe whether novel-scaffold designs (TamGen / REINVENT) can match validated binders on both axes.

**Paragraph 4 — paper roadmap** (~100 words):
We construct candidates from three independent generation engines, score them with two orthogonal predictors, validate against multi-conformation robustness and a 6-off-target selectivity panel, and rank by combined selectivity index. We report 4 selectivity-validated repurposing candidates (Tier 1), 1 surviving novel-scaffold candidate, and a methodological finding that novel scaffolds passing affinity filters can still fail kinase-pharmacophore selectivity.

### 2. Data & Methods (~700 words)

**2.1 Data sources** (~180 words):
- Target structures (Table 1): 6CWA (1.85 Å, ours), 6RJ6 (BI-4924 co-crystal, 1.98 Å), 6RJ3 (BI-cmpd-15, 1.42 Å), 6PLF/6PLG (NCT-cmpd allosteric co-crystals), 2G76 (1.7 Å near-apo), 7EWH (homoharringtonine).
- Sequence: PHGDH chain A residues 6–278, 299 aa.
- MSA: ColabFold MMseqs2 (2407 sequences, query-length-filtered). Required a custom patient poller (`scripts/fetch_msa.py`) due to flaky API.
- Known binder set (10 compounds): NCT-503, NCT-cmpd-1 (ONV), NCT-cmpd-15 (ONS), BI-4924 (K5K), BI-cmpd-15 (K58), homoharringtonine (HMT), CBR-5884, WQ-2101, 3PG (substrate), NADH (cofactor).
- Library: ChEMBL 34 chemreps.txt.gz (2.4M compounds) → 1.0M druglike → random sample 5000 lead-like for screening.

**2.2 Generation engines** (~150 words):
- **TamGen** (Microsoft) — pocket-conditional SMILES generator with VAE-conditioned beam search. Three branches: B1 (NCT-503 scaffold seed, allosteric site), B2 (BI-4924 seed, NAD site), B3 (PKU drugs, repurposing). 887 compounds generated total across branches + iterative round.
- **REINVENT4** (AstraZeneca) — closed-loop RL with Boltz-2 as inner-loop reward oracle. Composite reward: `0.45·σ(−aff) + 0.20·QED + 0.15·σ(6−SA) + 0.10·MW_window + 0.05·logP_window + 0.05·mech_bonus`; hard-reject on PAINS / Brenk / SA > 7. 100-step run, batch 64 → 6400 scored SMILES.
- **ChEMBL repurposing screen** — 5000 lead-like ChEMBL compounds scored with Boltz-2.

**2.3 Scoring + validation** (~220 words):
- **Boltz-2** (Wohlwend lab) — protein-ligand structure + affinity prediction. Ported to AMD MI300A via ROCm 6.3 (no CUDA). `--no_kernels` flag required (cuequivariance is NVIDIA-only).
- **AutoDock Vina** rescore on Boltz-predicted poses (orthogonal physics-based score).
- **Multi-conformation Boltz** — top-21 candidates scored against 4 PHGDH backbones (6CWA-apo, 6CWA+3PG, 6CWA+3PG+NADH, 2G76-apo); per-ligand stdev = robustness.
- **Off-target selectivity panel** — Boltz scoring of top-11 candidates against 6 off-targets:
  - 4 Rossmann-fold dehydrogenases: LDH-A (P00338), MDH2 (P40926), GAPDH (P04406), IDH1 (O75874)
  - 2 GRK kinases: GRK5 (P34947), GRK2 (P25098) — selected because the top ChEMBL hit (CHEMBL3093256) is a published GRK-2/5 inhibitor (Cho 2013 *BMCL*), flagging pharmacophore promiscuity.
- **Combined selectivity index**: `sel_idx_combined = (PHGDH aff − min(dehydrogenase aff)) + (PHGDH aff − min(kinase aff))`. Lower = more selective.
- **Drug-likeness filter**: RDKit Lipinski (MW≤500, logP≤5, HBD≤5, HBA≤10), Ertl SA score ≤ 4, PAINS + Brenk substructure filters.
- **Novelty**: Tanimoto similarity (Morgan radius-2, 2048-bit) to nearest of 10 known PHGDH binders.

**2.4 Compute** (~150 words):
SDSC Cosmos cluster (AMD MI300A APUs, ROCm 6.3). ~30 GPU-hours total. Boltz parallelism via `HIP_VISIBLE_DEVICES` fan-out (4 APUs per node, 4 nodes via SLURM array; `--devices 1` per Boltz process to avoid a known DDP fork-vs-spawn bug on ROCm). Source: <https://github.com/l1joseph/Alzheimers_Drug_Discovery>.

### 3. Results (~1100 words including 3 figures)

**3.1 Pipeline architecture** (Figure 1, ~150 words)
Describe the dual-pocket targeting strategy + 3-generation × 4-validation pipeline.

**3.2 Designed compounds and screening yield** (~250 words)
- TamGen: 887 compounds; top 50 by Boltz affinity (range −1.82 to −0.27). Best non-known: b2_067 at −1.59 BUT fails drug-likeness (logP 7.1, PAINS hit) — reward-hacking failure mode that motivated the composite-reward design.
- ChEMBL 5k: 4882 scored (98% success); top hit CHEMBL3093256 at −0.85. **7 of top 10 are kinase inhibitors from unrelated programs** — generic nucleotide-pocket pharmacophore promiscuity.
- REINVENT 100 steps: 6400 scored SMILES; 747 unique with composite reward ≥ 0.55; top reward 0.752 (step 59). RL plateaued at affinity ~−0.8 logKd — Boltz ceiling on novel chemistry.

**3.3 Selectivity-validated candidate ranking** (Figure 2, ~300 words)
Walk through Combined sel_idx table.
- **Tier 1 (combined sel_idx < −2.0): K58 −4.78, K5K −3.55, NCT-503 −2.72, ONS −2.58.** All cancer-developed binders. K58 has the 1.42 Å co-crystal (PDB 6RJ3) — chemically the cleanest probe in the set.
- **Tier 2 (−1 to −2)**: ONV −1.66, r2b2_107 −1.27 (sole novel-scaffold survivor).
- **DROP: b1_058 (+0.70) and b1_112 (+1.09)** — actively prefer GRK kinases over PHGDH. The lipophilic decoration TamGen applied to the NCT-503 scaffold produced kinase-like pharmacophore features. **Result the affinity-only screen would have missed.**
- **Multi-conformation robustness**: K5K stdev 0.18, ONS 0.26, b2_067 0.10 (robust but druglike-fail); REINVENT step-59 hit only −0.17 to +0.10 across 4 conformations → confirms that hit was a reward artifact, not a real binder.

**3.4 Comparison with known PHGDH binders** (Figure 3, ~250 words; required by rubric)
- **Affinity comparison** (table): designed compounds top out at b2_067 −1.59 (drug-like fail) and r2b2_107 −0.66 (drug-like pass). Validated K58/K5K/ONS sit at −1.0 to −1.82. Designs are 1-3× weaker than validated.
- **Binding pose comparison** (Figure 3 panels): r2b2_107 occupies the BI-4924 pocket position closely; REINVENT step-59 hit floats near pocket without specific contacts (explains its weak multi-conf affinity).
- **Drug-likeness comparison** (table): Designed compounds have MW 293-558 (some bRo5); validated K58/K5K/NCT-503 MW 308-498. Designed compounds have notable PAINS hits in B2 lineage; B1 lineage is PAINS-clean.

**3.5 Iterative improvement attempts** (~150 words; required for "outstanding")
- v1 B1/B2 → v1 B1-Round-2 / B2-Round-2: iterative scaffold-seeded TamGen using top v1 hits as new seeds. Diminishing returns (r2b2_164 was canonical-SMILES identical to b2_067 — loop converged).
- REINVENT RL: closed-loop with Boltz reward as policy-gradient signal. 51 steps → 100 steps. **Per-step max-reward trajectory flat across the run** (first-third 0.66 ≈ last-third 0.66) — agent diversified chemistry but didn't converge to higher reward. The Boltz affinity ceiling at ~−0.8 logKd for novel chemistry is the bottleneck. Composite-reward design (PAINS/Brenk hard-reject) successfully blocked the v1 b2_067 reward-hack failure mode but couldn't break the affinity plateau.

### 4. Discussion (~350 words)

**Paragraph 1 — main finding** (~120 words):
The most experimentally actionable result is the Tier 1 4-compound set (K58, K5K, NCT-503, ONS) for the Park 2025 fluorescence-polarization PHGDH-DBD assay. All four are commercially available and characterized; the experiment is one week of bench time. Expected best case: K58 or K5K (NAD-competitive) outperforms NCT-503 by silencing DBD via NADH competition — a mechanistically cleaner mode than allosteric perturbation.

**Paragraph 2 — methodological insight** (~120 words):
The off-target selectivity panel reordered the ranking *and* killed three of our top novel-scaffold designs. **An affinity-only screen would have recommended b1_058 as a top candidate**; the kinase panel revealed it binds GRK2 0.75 log-Kd more tightly than PHGDH. This is a generalizable cautionary point for ML-based drug-design pipelines: composite reward in REINVENT (PAINS/Brenk hard-reject) prevented the gross failure mode (logP 7.1, PAINS hit) but couldn't anticipate kinase-pharmacophore similarity.

**Paragraph 3 — limitations + future work** (~110 words):
No wet-lab; all recommendations are predictions. Boltz-2 affinity is a ranking, not an absolute (Pearson ~0.6 with measured affinity in published benchmarks). Multi-seed Boltz averaging would tighten the top-ranking stability (we observed same-backbone same-SMILES Δaff > 0.5 between runs). Selectivity panel excluded LRRK2 (too long for Boltz) — relevant for a Parkinson's-disease-related off-target. Block D RL plateau suggests scaffold-restricted REINVENT (Mol2Mol or LibInvent on the NCT-503 core) is the natural next iteration.

### References (~10-12 entries)

1. Park et al. 2025 *Cell Metabolism* — moonlighting DBD discovery
2. Zhong 2025 PMC12204802 — in-vivo NCT-503 AD model
3. Pacold et al. 2016 *Nat Chem Biol* — NCT-503 series
4. Spillier et al. 2019 *J Med Chem* — BI-4924 / BI-cmpd-15
5. Mullarky et al. 2016 *PNAS* — CBR-5884
6. Possemato et al. 2011 *Nature* — PHGDH cancer link
7. Locasale et al. 2011 *Nat Genet* — PHGDH amplification
8. Wohlwend et al. 2024 — Boltz-1 / Boltz-2 paper
9. Mirdita et al. 2022 *Nature Methods* — ColabFold
10. Loeffler et al. 2024 *J Cheminformatics* — REINVENT4
11. Trott & Olson 2010 *J Comp Chem* — AutoDock Vina
12. Bickerton et al. 2012 — QED

### Author Contributions

Template based on CRediT taxonomy:

> Conceptualization: [name]. Methodology + pipeline architecture: [name]. Boltz-2/TamGen ROCm port: [name]. ChEMBL + REINVENT integration: [name]. Off-target counter-screen design + analysis: [name]. PyMOL figures + structural analysis: [name]. Writing — original draft: [name]. Writing — review & editing: [all team]. Compute resource access (SDSC Cosmos): [name].

Note: Solo project? The user is Leo Joseph. If solo, the section is shorter:
> Leo Joseph (UCSD, Knight Lab / Alexandrov Lab): conceptualization, pipeline architecture, ROCm porting of Boltz-2 and TamGen, all computational experiments, data analysis, figure preparation, and manuscript writing.

(Check with user about team composition.)

---

## Asset audit — what's ready vs what needs producing

### Already in repo (reusable as-is)
- `docs/CANDIDATE_REPORT.md` — full narrative, ~3500 words. Most paper text can be derived from here.
- `docs/figures/phgdh_pymol.png` — Figure 1 target structure (needs pocket-sphere annotations added)
- `docs/figures/interactions/{K5K,NCT503,b1_005,b1_051,b1_058,b1_112}.png` — Figure 3 panel sources (4 of 6 needed)
- `results/final/top_candidates_v2.csv` — primary data table
- `results/offtarget/selectivity_table.csv` + `results/kinase/selectivity_table.csv` — Figure 2 data
- `results/multiconf/by_ligand.csv` — multi-conf robustness numbers
- All `docs/notes/*.md` — narrative scaffolding

### Needs producing (1-3 hours)
- **r2b2_107 PyMOL render** — for Figure 3 panel. Find the CIF under `/cosmos/vast/scratch/l1joseph/runs/boltz_tamgen_b2_round2_*/predictions/r2b2_107/r2b2_107_model_0.cif` and run `scripts/render_top_candidates.py` (modify list).
- **REINVENT step-59 PyMOL render** — need to re-fold via Boltz (no cached CIF), then render.
- **Figure 1 panel B (pipeline schematic)** — Mermaid or Inkscape; ~30 min.
- **Figure 2 selectivity heatmap** — matplotlib + seaborn; data already present; ~45 min.
- **Reference list with proper formatting** — pull DOIs and format ACS / Nature style (~30 min).

---

## Timeline to deadline

Assuming 06/09/2026 = 14 days out (Tue 06/09).

| Day | Task |
|---|---|
| **D0–D2** (now): | Finalize asset audit; render r2b2_107 + step-59 PyMOL panels; produce Figure 2 heatmap script |
| D3–D5: | Draft Introduction + Methods sections (text-heavy, low-figure-dependency) |
| D6–D8: | Draft Results section + integrate Figures 1–3 |
| D9: | Draft Discussion + Abstract; write Author Contributions |
| D10: | Internal review pass; trim to 5-page limit (this will be hard) |
| D11–D12: | References formatting + final formatting pass (margins, captions, etc.) |
| D13: | Submit by 06/09 23:59 |

**Page-count risk**: The current `CANDIDATE_REPORT.md` is ~3500 words; the paper target is ~2950 + 3 figures occupying ~1 page total. Will need aggressive trimming — likely cut detailed selectivity tier 3 discussion, REINVENT learning-curve detail, much of methods data-source enumeration. Consider supplementary materials if format allows.

---

## Decisions needed from team / user

1. **Team composition** — solo, or coauthors? Affects Author Contributions and the "team" framing in conclusions.
2. **Title preference** — three options listed; pick one.
3. **Wet-lab claim strength** — recommend Track 1 wet-lab? Or describe candidates and note experimental validation is out of scope? The current `CANDIDATE_REPORT.md` recommends the experiment; the paper should match that framing or moderate it.
4. **Figures vs supplementary** — does the submission allow a supplementary file? If yes, push detailed selectivity tables there and reclaim space.
5. **Citation style** — Gradescope-default or specific journal style? Default to ACS-like (numbered, in order of citation).

Once these are answered I can start drafting individual sections. The pipeline is fully documented in `CANDIDATE_REPORT.md` and `docs/notes/`; the paper is primarily a compression + structural rearrangement, not a new investigation.
