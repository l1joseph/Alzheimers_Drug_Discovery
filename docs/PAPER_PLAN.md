# Final paper — full plan

**Deadline:** 06/09/2026 (assuming user-supplied "06/09/2025" is a typo; ~14 days out).
**Format:** 5 pages **including figures and references**. Single submission for the team.
**Rubric:** Project Option 1 (Zinnia Ma rubric, updated 4 days ago).

---

## 1. Page budget

| Section | Pages | Word count | Maps to rubric component |
|---|---|---|---|
| Title + Abstract + Authors | 0.4 | 150 | — |
| 1. Introduction | 0.7 | 500 | Biological problem; rationale for target + binding site; disease relevance |
| 2. Methods | 1.0 | 700 | Data used; pipeline description |
| 3. Results | 1.7 | 1100 + 4 figures inline | Designed compounds + evaluation + comparisons with known binders |
| 4. Discussion | 0.5 | 350 | Disease insights; limitations |
| References | 0.4 | 10–12 refs | — |
| Author Contributions | 0.3 | 150 | required by spec |
| **Total** | **5.0** | ≈ **2950** | — |

---

## 2. Section content map

### Title (LOCKED)

> **"To Affinity and Beyond: A Structure-Informed Drug Discovery Pipeline for PHGDH Inhibitors Targeting the Alzheimer's-Relevant DNA-Binding Domain"**

19 words. Hook + concrete claim + scope. "Pipeline" (not "platform") to be honest about scope — we built a specific workflow for PHGDH-AD, not a reusable framework.

### Abstract (≈150 words, sentence outline)
1. PHGDH moonlights as a transcription factor via its C-terminal regulatory domain (Park 2025) and is implicated in AD.
2. Of the published PHGDH inhibitors, only NCT-503 has in-vivo AD evidence; the rest of the chemical matter is plausibly AD-relevant but untested.
3. We computationally screened 4 candidate sets — known binders, scaffold-seeded designs, ChEMBL repurposing, REINVENT RL — for both affinity and selectivity.
4. Methods: Boltz-2 + AutoDock Vina + multi-conformation robustness + 6-off-target counter-screen (4 Rossmann-fold dehydrogenases + 2 kinases).
5. **K58 (BI-cmpd-15)** emerges as the cleanest selective PHGDH binder (combined selectivity index −4.78), followed by K5K (BI-4924), NCT-503, and ONS (NCT-cmpd-15).
6. Three of four novel scaffold-seeded designs fail kinase selectivity despite passing affinity + drug-likeness filters — a failure mode invisible to affinity-only screens.
7. The Tier-1 candidates have published ADME profiles and would be tractable for downstream experimental validation against the Park 2025 DBD-activation axis.

### 1. Introduction (4 paragraphs, ≈500 words)
1. **Biological problem** — PHGDH catalytic vs moonlighting DBD function; Park 2025 + Zhong 2025 AD link.
2. **Drug-discovery context + target/site rationale** — oncology programs (NCT-series allosteric, BI series NAD-competitive); only NCT-503 has AD evidence; two-axis hypothesis (NAD-competitive blocks NADH activation; allosteric perturbs regulatory domain).
3. **Gap and approach** — affinity-only screens don't address repurposing safety; need selectivity-aware ranking.
4. **Paper roadmap** — 3 generation engines × 4 validation layers → combined selectivity index.

### 2. Methods (4 subsections, ≈700 words)
- **2.1 Data sources** — target structures (Table 1: 6CWA / 6RJ6 / 6RJ3 / 6PLF / 2G76); MSA; 10-compound known reference set; ChEMBL 34 (5000-cpd lead-like sample).
- **2.2 Generation engines** — TamGen (B1 NCT-503 seed, B2 BI-4924 seed, B3 PKU drugs); REINVENT4 100-step RL with Boltz-2 reward; ChEMBL 5k library screen.
- **2.3 Scoring + validation** — Boltz-2 (ROCm port); Vina rescore; multi-conformation Boltz (top-21 × 4 backbones); 6-off-target panel.
- **2.4 Compute** — AMD MI300A on SDSC Cosmos; ~30 GPU-hours; `HIP_VISIBLE_DEVICES` fan-out (4 APUs/node × 4 nodes via SLURM array); GitHub link.

### 3. Results (5 subsections, ≈1100 words + 4 inline figures)
- **3.1 Pipeline architecture** (Fig 1) — dual-pocket strategy + 3-generation × 4-validation pipeline
- **3.2 Designed compounds and screening yield** — TamGen 887, ChEMBL 4882, REINVENT 6400 scored. **Reward-hack failure mode** (b2_067) motivates composite reward.
- **3.3 Selectivity-validated candidate ranking** (Figs 2, 3) — Tier-1 K58/K5K/NCT-503/ONS; B1 series collapses after kinase panel
- **3.4 Comparison with known PHGDH binders** (Fig 4) — pose comparison + drug-likeness + affinity (rubric requirement)
- **3.5 Iterative improvement attempts** — TamGen scaffold-seeded rounds; REINVENT RL plateau analysis (rubric "outstanding" component)

### 4. Discussion (3 paragraphs, ≈350 words)
1. **Main finding** — K58 (BI-cmpd-15) and K5K (BI-4924) emerge as the cleanest selective PHGDH binders in our pipeline; both are NAD-competitive and have published industry-grade ADME from the Boehringer oncology program, making them strong mechanism-of-action candidates against the Park 2025 DBD-activation axis.
2. **Methodological insight** — the off-target panel reordered the ranking AND killed three of our top novel-scaffold designs; affinity-only screens would have surfaced compounds that bind GRK kinases more tightly than PHGDH. This is a generalizable cautionary point for ML-based drug-design pipelines.
3. **Limitations + future work** — no experimental validation in this study; Boltz affinity stochasticity (multi-seed averaging would help); LRRK2 excluded due to length limit; scaffold-restricted REINVENT (Mol2Mol / LibInvent on the NCT-503 core) is the natural next iteration. **One sentence on experimental follow-up**: The Park 2025 fluorescence-polarization PHGDH-DNA binding assay would be the most direct downstream test of the Tier 1 candidates' DBD-blocking activity.

### References (10–12, ACS-style numbered)
Park 2025, Zhong 2025, Pacold 2016, Weinstabl 2019, Mullarky 2016, Possemato 2011, Locasale 2011, Wohlwend 2024 (Boltz), Mirdita 2022 (ColabFold), Loeffler 2024 (REINVENT4), Trott & Olson 2010 (Vina), Bickerton 2012 (QED).

### Author Contributions
Template (single-author version):
> Leo Joseph (UCSD; Knight Lab / Alexandrov Lab): conceptualization, pipeline architecture, ROCm porting of Boltz-2 / TamGen / REINVENT4, all computational experiments and data analysis, figure preparation, manuscript writing. SDSC Cosmos cluster access via UCSD.

(Replace with full team list if not solo.)

---

## 3. Figure roster

| # | Figure | Status | Maps to rubric |
|---|---|---|---|
| **1** | Target biology + pipeline overview (3-panel) | **TODO** — needs structure annotation + schematic | Rationale for target/site; data; methods |
| **2** | Top-10 candidate metrics (4-panel) | ✅ generated (`fig2_metrics_top10.png/svg`) | Designed compounds; comparison of drug-likeness; comparison of affinities |
| **3** | Selectivity heatmap (11 lig × 7 targets) | ✅ generated (`fig3_selectivity_heatmap.png/svg`) | Evaluation; comparison with known binders |
| **4** | Binding-pose comparison: top 3 PyMOL panels | **TODO** — need r2b2_107 + K58 renders; K5K already exists | Comparison of binding poses / interactions |
| Supp | REINVENT learning curve | ✅ generated (`fig_supp_reinvent_curve.png/svg`) | Iterative improvement attempts |
| Supp (opt) | 2D chemistry grid (top 6) | optional; ~5 min to generate | Comparison with known binders |
| Supp (opt) | Multi-conformation violin plot | optional; ~10 min | Evaluation depth |

### Figure 1 — what's still needed
- **1A — annotated PHGDH PyMOL render**: extend `scripts/render_top_candidates.py` to mark NCT-503-site residues (allosteric pocket) and NADH-site residues (catalytic pocket) on the apo structure
- **1B — Park 2025 mechanism schematic**: best done in Inkscape / draw.io (cartoon of PHGDH dimer with DBD-DNA contact + NADH allosteric activator)
- **1C — pipeline flowchart**: can render via matplotlib if needed; cleaner in Inkscape

### Figure 4 — what's still needed
- **K58 (BI-cmpd-15) pose**: not yet rendered; CIF either from PDB 6RJ3 (real co-crystal) or run Boltz on K58 SMILES vs 6CWA
- **r2b2_107 pose**: find the CIF in `/cosmos/vast/scratch/l1joseph/runs/boltz_tamgen_b2_round2_*/predictions/r2b2_107/` and render via existing `scripts/render_top_candidates.py`
- **K5K (BI-4924) pose**: already rendered at `docs/figures/interactions/K5K.png` — reuse

---

## 4. Methods & metrics to mention (paper checklist)

### Tools
- **Boltz-2** — Wohlwend et al. 2024 (preprint); ROCm 6.3 port; `--no_kernels` for AMD
- **AutoDock Vina 1.2** — Trott & Olson 2010; Eberhardt 2021 update
- **TamGen** — pocket-conditional SMILES with VAE beam search (Microsoft, 2024)
- **REINVENT4** — Loeffler et al. 2024 *J Cheminformatics*; staged learning with DAP strategy
- **ColabFold MMseqs2 API** — Mirdita et al. 2022 *Nature Methods*
- **RDKit 2024.03** — fingerprints, drug-likeness, FilterCatalog
- **FPocket 4.0** — Phase 4 druggability pre-screen
- **PyMOL 3.0** — visualization

### Quantitative metrics (with one-line definitions for the methods section)

| Metric | Definition | Range / interpretation |
|---|---|---|
| `affinity_pred_value` | Boltz-2 predicted affinity | logKd-like; more negative = stronger |
| `prob_binary` | Boltz binary binder/non-binder classifier | [0, 1] |
| `confidence_score` | Boltz structural prediction confidence (pLDDT-like) | [0, 1] |
| Vina score | Empirical docking score | kcal/mol; more negative = stronger |
| `selectivity_index` | PHGDH aff − min(off-target aff) | negative = PHGDH-preferring |
| **Combined sel_idx** | sum of dehydrogenase + kinase sel_idx | < −2.0 = Tier 1 |
| Multi-conf stdev | std across 4 PHGDH backbones | lower = robust |
| Tanimoto | Morgan r=2, 2048-bit fingerprint vs reference set | < 0.4 = novel chemotype |
| **Lipinski Ro5** | MW ≤ 500, logP ≤ 5, HBD ≤ 5, HBA ≤ 10 | ≥ 3/4 pass for oral |
| QED | Bickerton 2012 composite druglikeness | [0, 1]; > 0.5 drug-like |
| SA score | Ertl & Schuffenhauer 2009 synthesizability | [1, 10]; ≤ 4 typical drug |
| TPSA | Topological polar surface area | < 90 Å² for CNS-druggable |
| PAINS / Brenk | RDKit FilterCatalog substructure alerts | binary hard-reject |

### Composite reward formula (cite in Results 3.5)
```
hard_reject (r = 0) if invalid OR PAINS OR Brenk OR SA > 7
else r = 0.45·σ(−aff) + 0.20·QED + 0.15·σ(6−SA)
       + 0.10·MW_window + 0.05·logP_window + 0.05·mechanism_bonus
```
Mechanism bonus: SMARTS panel of indazole, BI-4924 sulfone-amide, methyl-indole carboxamide, pyrazole carboxamide. Intentionally weak (5%); soft pull toward known chemistry, not a hard prior.

---

## 5. Timeline (~14 days from now)

| Day | Tasks |
|---|---|
| **D0** (now) | ✅ Figures 2, 3, supp generated. Paper plan finalized. |
| D1 | Generate Figure 1 (PHGDH annotated + pipeline schematic) and Figure 4 (3 PyMOL panels: K58 / K5K / r2b2_107). Decide if K58 uses real 6RJ3 co-crystal or Boltz-predicted CIF. |
| D2 | Optional: 2D chemistry grid as supp. Multi-seed Boltz averaging on top-5 as a sanity-check on the affinity stochasticity claim. |
| D3–D5 | Draft Introduction + Methods (text-heavy, low figure-dependency). |
| D6–D8 | Draft Results + integrate Figures 1–4 + captions. |
| D9 | Draft Discussion + Abstract + Author Contributions. |
| D10 | Internal review pass; trim to 5-page limit. |
| D11–D12 | References formatting + final polish (margins, alignment, captions). |
| D13 | Submit by 06/09 23:59 PDT. |

**Page-count risk**: current `CANDIDATE_REPORT.md` is ~3500 words; paper target ~2950 + 4 figures occupying ~1.5 pages total. Will need aggressive trimming — likely cut Tier-3 candidate discussion, REINVENT learning-curve detail (relegate to supp), and some methods enumeration.

---

## 6. Resolved decisions

| # | Decision | Resolution |
|---|---|---|
| 1 | Team composition | **4 authors: Leo Joseph, Yashwin Madakamutil, Cale Seymour, Ziheng Wang** (CRediT contributions to be drafted in §3.5 below) |
| 2 | Title | **LOCKED**: *"To Affinity and Beyond: A Structure-Informed Drug Discovery Pipeline for PHGDH Inhibitors Targeting the Alzheimer's-Relevant DNA-Binding Domain"* |
| 3 | Wet-lab claim strength | **No wet-lab framing in the body.** A brief 1–2 sentence "experimental follow-up" mention in the Discussion (next steps) is acceptable. |
| 4 | Supplementary file | **Yes, allowed.** Park REINVENT learning curve + 2D chemistry grid + larger selectivity tables there. |
| 5 | Citation style | **ACS-numbered** (default) |
| 6 | Figure 1 panels B + C tool | **matplotlib** auto-generated (no Inkscape) |
| 7 | K58 pose source for Fig 4 | **Real 6RJ3 co-crystal** (1.42 Å). Render at `docs/figures/paper/fig4_K58_real_6RJ3.png`. Boltz-predicted version retained as `fig4_K58_boltz_pred.png` for supplementary comparison. |

### Author Contributions (draft, to refine with team)

> **Leo Joseph**: Conceptualization, pipeline architecture, AMD MI300A ROCm porting of Boltz-2 and TamGen, ChEMBL screen design, manuscript writing.
> **Yashwin Madakamutil**: [TBD — typical contributions: TamGen scaffold-seeded branch design, REINVENT4 integration + composite reward formulation, data analysis].
> **Cale Seymour**: [TBD — typical contributions: off-target selectivity panel design, AutoDock Vina rescore, multi-conformation Boltz analysis].
> **Ziheng Wang**: [TBD — typical contributions: structural analysis, PyMOL figure preparation, drug-likeness filtering, manuscript review].
> All authors: writing — review and editing.

(Refine per actual team division of labor before submission.)

---

## 7. Asset audit

### Ready to use (already in repo)
- **Narrative source**: `docs/CANDIDATE_REPORT.md` (~3500 words; most paper text can be derived)
- **Supporting analysis**: `docs/notes/{selectivity_findings,multiconf_findings,kinase_findings,chembl_top_hit_provenance}.md`
- **Figure 2/3/supp**: `docs/figures/paper/*.{png,svg}` ✅
- **PyMOL renders (some)**: `docs/figures/interactions/{K5K,NCT503,b1_005,b1_051,b1_058,b1_112}.png`
- **Tabular data**: `results/final/top_candidates_v2.csv`, `results/offtarget/selectivity_table.csv`, `results/kinase/selectivity_table.csv`, `results/multiconf/by_ligand.csv`, `results/orthogonal_rescore/vina_scores.csv`

### Need to produce (next session, ~2–3 hours)
- Figure 1 — PHGDH-annotated render + Park 2025 schematic + pipeline flowchart
- Figure 4 — K58 pose (download 6RJ3 from PDB), r2b2_107 pose (find CIF in scratch + render)
- Optional 2D chem grid (5 min, RDKit `Draw.MolsToGridImage`)
- Optional multi-conf violin (10 min)

---

## 8. Submission package checklist

By 06/09 23:59:
- [ ] Final PDF (5 pages max)
- [ ] All 4 main figures embedded at 300 DPI
- [ ] References numbered + formatted (ACS style)
- [ ] Author Contributions block
- [ ] (optional) Supplementary file with REINVENT curve + 2D chem grid + larger selectivity tables
- [ ] Gradescope submission
