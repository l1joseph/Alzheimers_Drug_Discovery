# PHGDH-AD candidate report — final v2

Generated 2026-05-21 07:40 PDT. Integrates all v1 + v2 signals (Boltz affinity, Vina rescore, off-target selectivity, ChEMBL screen, REINVENT RL).
See also: [PLAN.md](../PLAN.md), [PLAN_v2.md](../PLAN_v2.md), [README.md](../README.md), [`top_candidates_v2.csv`](../results/final/top_candidates_v2.csv).

---

## TL;DR

The pipeline now has four independent candidate tracks, ordered by experimental friction:

| Track | What | Best candidate | Status |
|---|---|---|---|
| 1 — **AD repurposing** | Validated PHGDH binders with mechanism-of-action precedent for the DBD function (Park 2025) | **K58 (BI-cmpd-15)** — strongest selective binder, sel_idx −2.36 | **Recommended wet-lab next step** |
| 2 — **Novel scaffold-seeded** | TamGen B1/B2 outputs, novel composition-of-matter | **b1_058** at Boltz −0.65 / Vina −7.91 | Pending validation |
| 3 — **ChEMBL repurposing** | 5k drug-like ChEMBL screen | **CHEMBL3093256** (GRK-2/5 hit) | Untested; provenance caveats |
| 4 — **REINVENT de novo** | 51-step RL run with composite reward + Boltz oracle | **step 41**, reward 0.725, MW 326, Tani 0.11 | Computational only |

**Single biggest finding from the v2 work**: **the off-target selectivity screen (Block G) reorders the candidate ranking dramatically.** K58 (BI-cmpd-15) — the highest-resolution PHGDH co-crystal (1.42 Å) — emerges as the strongest selective PHGDH binder in our entire set with sel_idx −2.36 (no off-target binding detected at all). K5K (BI-4924) is second. Both are NAD-competitive — mechanistically the cleanest way to silence the DBD function per Park 2025. The Track 1 wet-lab experiment is now sharply specified.

**A B1 candidate was dropped after selectivity testing**: b1_112 actually prefers GAPDH over PHGDH (sel_idx +0.48). Down to 3 novel druglike B1 hits.

**REINVENT did learn slowly**: max reward edged from 0.714 (step 10) to 0.725 (step 41), and the chemistry diversified considerably across the run (747 unique novel druglike SMILES at reward ≥ 0.55). But the affinity ceiling (~−0.8 logKd) wasn't broken — the validated nM PHGDH inhibitors at affinity −1.79 remain unmatched by anything generated.

---

## Background

### PHGDH's two functions

Phosphoglycerate dehydrogenase (PHGDH; EC 1.1.1.95) is the first committed enzyme of the serine biosynthesis pathway. Its **catalytic function** converts 3-phosphoglycerate (3PG) to 3-phosphohydroxypyruvate using NAD⁺ as a cofactor. This activity has been studied for decades, primarily in oncology:

- **Cancer**: tumor cells that re-amplify PHGDH show serine-dependent growth (Possemato et al. 2011 *Nature*, Locasale et al. 2011 *Nat Genet*).
- **Serine deficiency disorders**: rare germline PHGDH loss-of-function causes Neu-Laxova syndrome.

**Park et al. 2025** (*Cell Metabolism*, Sheng Zhong lab UCSD) reported a **moonlighting function**: in the cytoplasm, PHGDH dimerizes via its substrate-binding domain and **the C-terminal regulatory domain acts as a DNA-binding domain (DBD)**, with **NADH (the reduced cofactor) acting as an allosteric activator**. PHGDH in this mode is a transcription factor implicated in:

- α-synuclein and amyloid-β related gene regulation in neurons
- Alzheimer's pathology in mouse models (the NCT-503 in-vivo work)

The Zhong 2025 paper (PMC12204802) builds on this — NCT-503 administration in AD-model mice produces phenotypic rescue and reduces neuroinflammatory markers. The DBD-blocking activity (not catalytic inhibition) is credited as the mechanism.

### Two axes of drug discovery against PHGDH

| Axis | Goal | Best inhibitor class | Pocket |
|---|---|---|---|
| **Catalytic** (cancer) | Block serine production | NAD-competitive | NADH binding site |
| **Moonlighting DBD** (AD) | Block transcription-factor activity | Allosteric (perturbs DBD) OR NAD-competitive (blocks DBD activator NADH) | NCT-503 allosteric pocket OR NADH pocket |

Almost every published PHGDH inhibitor was optimized for catalytic inhibition. Only one class — the **NCT-series allosteric inhibitors** (Pacold et al. 2016) — has been demonstrated to affect the moonlighting function in vivo (NCT-503 specifically).

---

## Track 1: AD repurposing candidates (recommended wet-lab path)

**The Block G selectivity counter-screen makes this the sharpest deliverable from the v2 work.**

| ID | Name | Mechanism | Boltz aff | sel_idx vs LDH-A/MDH2/GAPDH/IDH1 | Vina (kcal/mol) | Source paper |
|---|---|---|---|---|---|---|
| **K58** | **BI-cmpd-15** | NAD-competitive (NADH site) | −1.0 | **−2.36** (strongest selective) | not rescored | Spillier 2019 *J Med Chem* (BI program) |
| **K5K** | **BI-4924** | NAD-competitive (NADH site) | −1.79 | **−1.62** | −9.19 | Spillier 2019 *J Med Chem* (BI program) |
| **NCT-503** | NCT-503 | Allosteric (NCT-503 site) | −0.30 | **−1.46** | not rescored | Pacold 2016 *Nat Chem Biol* |
| **ONV** | NCT-cmpd-1 | Allosteric | −1.02 | −1.13 | −8.00 | Pacold 2016 |
| **ONS** | NCT-cmpd-15 | Allosteric | −1.82 | −0.76 (GAPDH off-target close) | −10.58 | Pacold 2016 |

**Recommendation**: Run a head-to-head test of K58, K5K, ONV, and NCT-503 in the **Park 2025 fluorescence-polarization PHGDH-DNA binding assay**, with NCT-503 as the positive control. Expected outcomes:

- **Best case**: K58 or K5K (NAD-competitive) match or beat NCT-503's DBD inhibition. They block NADH activation directly — mechanistically the cleanest silencing mode. K5K has industry-grade ADME from the Boehringer cancer program; K58 has the 1.42 Å co-crystal (PDB 6RJ3).
- **Mid case**: all 4 work comparably to NCT-503 → useful redundancy with different mechanisms / ADME profiles.
- **Worst case**: none affect DBD function despite mechanism-of-action precedent → narrows the field and re-validates NCT-503 as uniquely positioned.

**Important reframing**: ONS (NCT-cmpd-15) was a successor compound to NCT-503 from the same Pacold paper and ranks #1 in our affinity screen. But the selectivity screen reveals ONS also binds GAPDH (−1.06) and MDH2 (−0.95) — making it the most affinity-promiscuous of the allosteric series. It is likely *not* a cleaner replacement for NCT-503 in AD models because of confounding off-target effects.

Time/cost estimate for Track 1: ~1 week of bench time. Compounds are commercially available (Tocris / MedChemExpress for the NCT series; med-chem suppliers for BI-4924). The assay is exactly Park 2025's setup.

---

## Track 2: Novel scaffold-seeded designs (TamGen B1 family)

After the selectivity drop of b1_112, **3 novel druglike B1 hits** remain, all from the NCT-503-scaffold-seeded TamGen run:

| rank in top50 | id | Boltz aff | Vina | sel_idx | MW | logP | Tani→known | Selectivity verdict |
|---|---|---|---|---|---|---|---|---|
| 32 | **b1_005** | −0.39 | **−8.15** | −0.30 | 309 | 3.92 | 0.12 → NCT-503 | modest selectivity |
| 29 | **b1_051** | −0.48 | **−7.21** | −0.41 | 310 | 4.26 | 0.12 → NCT-503 | modest selectivity |
| 16 | **b1_058** | −0.65 | **−7.91** | −0.05 | 469 | 3.37 | 0.14 → BI-cmpd-15 | barely selective |
| ~~35~~ | ~~b1_112~~ | ~~−0.37~~ | ~~−8.17~~ | **+0.48** | 489 | 4.50 | 0.15 | **dropped — prefers GAPDH** |

**Read this honestly**: all three remaining hits sit at ~3× weaker predicted PHGDH affinity than the validated controls, AND with weaker selectivity than the validated controls. Decorating the NCT-503 scaffold to be more chemistry-novel cost some of the binding mode precision. They're still novel + drug-like + non-PAINS — that's not nothing — but they're not better-than-NCT-503 candidates in the way the initial ranking suggested.

**Best single Track 2 candidate**: **b1_005** is the best CNS-druglike (MW 309, logP 3.92) of the three. It has modest selectivity (sel_idx −0.30) and the strongest Vina rescore (−8.15 kcal/mol). Worth synthesizing if Track 1 wet-lab shows allosteric NCT-503-site engagement is the right mechanism class.

---

## Track 3: ChEMBL drug-like screen (5k untested repurposing candidates)

Block B scored 4882 of 5000 sampled drug-like ChEMBL compounds against PHGDH (98% success). Top hits ranked by Boltz `affinity_pred_value`:

| Rank | ChEMBL ID | Boltz aff | prob_binary | confidence | Original target | Therapeutic area | Notes for AD |
|---|---|---|---|---|---|---|---|
| 1 | CHEMBL3093256 | −0.85 | 0.12 | 0.74 | GRK-2 / GRK-5 kinases | cardiovascular | Cho 2013 *BMCL*; kinase ATP-pocket promiscuity flag |
| 2 | CHEMBL1433971 | −0.82 | **0.52** | 0.75 | — | — | (highest prob_binary — most confident binder by Boltz classifier) |
| 3 | CHEMBL3986234 | −0.82 | 0.08 | 0.78 | **LRRK2 kinase** | **Parkinson's disease** | **CNS-tuned!** Worth flagging for AD repurposing |
| 4 | CHEMBL1276764 | −0.73 | **0.63** | 0.79 | — | — | (also high prob_binary) |
| 5 | CHEMBL392031 | −0.70 | 0.41 | 0.80 | — | — | |
| 6 | CHEMBL2062581 | −0.67 | 0.15 | 0.75 | — | — | |
| ... | | | | | | | |
| ~10 | CHEMBL1084018 | −0.44 | 0.44 | 0.73 | PDE10A | **CNS / schizophrenia** | CNS-tuned by design |

**Honest framing**: 7 of the top 10 (by Boltz affinity) are **kinase inhibitors from unrelated drug-discovery programs**. Boltz is recovering scaffolds with generic nucleotide-pocket pharmacophores — kinase ATP pockets and PHGDH's NADH pocket share H-bond donor/acceptor topology. This is real signal (these compounds plausibly do bind PHGDH) but also a strong selectivity flag (binding both kinases and PHGDH is the default expectation, not the exception).

**Of all the ChEMBL hits, two have prior CNS optimization** that would be valuable for AD repurposing:
- **CHEMBL3986234** (LRRK2 inhibitor for Parkinson's): already designed for CNS penetration in a neurodegenerative target
- **CHEMBL1084018** (PDE10A inhibitor for schizophrenia): smallest MW in top 10 (329 Da), best Lipinski profile

Both should be folded into Track 1's wet-lab experiment if Track 1 budgets allow more compounds.

**Caveat**: this Track 3 set was not selectivity-screened (counter-screen was sized for the validated controls only). Treat the affinity numbers as ranking, not absolute.

---

## Track 4: REINVENT de novo (closed-loop RL with composite reward)

A 51-step REINVENT RL run with Boltz-2 as the inner-loop reward oracle (composite reward: affinity + QED + SA + Lipinski + mechanism bonus, hard reject on PAINS/Brenk).

**Statistics:**
- 3264 SMILES scored (64 per step × 51 steps)
- 63% had nonzero reward (37% PAINS/Brenk/SA-rejected → composite reward working as designed; no `b2_067`-style reward hacks)
- 747 unique novel druglike SMILES at reward ≥ 0.55
- Max reward: 0.725 (step 41); slow improvement from 0.714 at step 10
- Mean reward of nonzero: 0.524

**Top 5 REINVENT compounds (canonical SMILES, novel + druglike, ranked by composite reward):**

| Rank | Step | Reward | Boltz aff | MW | Tani→known | SMILES preview |
|---|---|---|---|---|---|---|
| 1 | 41 | 0.725 | 0.72 | 326 | **0.11** | `COc1cncc(-c2cc(OC(F)(F)F)cc3[nH][nH]c(=O)c23)n1` |
| 2 | 10 | 0.714 | 0.71 | 462 | 0.29 | `COc1cc(N2CCC(CNC(=O)c3cc(-c4ccc(C#N)cc4)nn3C)CC2)nc(OC)n1` |
| 3 | 28 | 0.709 | 0.71 | 362 | 0.20 | `CC1(C)CC2C(C#N)=CCC1(O)C2NC(=O)c1cccc(-c2ccco2)c1` |
| 4 | 51 | 0.705 | 0.70 | 334 | 0.15 | `OCCN=c1c...` (pyrimidinone) |
| 5 | 30 | 0.703 | 0.70 | 531 | 0.22 | `CC1(S(=O)(=O)NCC(O)CC(CC(=O)O)c2cccc(Cl)c2)CCN(c2ccc(F)c(F)c2)CC1` |

**Best Track 4 candidate**: the **step-41 hit** — pyrazolopyrimidone with methoxy-pyridine and trifluoromethoxy aryl. MW 326 (excellent CNS range), Tanimoto 0.11 (most novel of any candidate in the entire pipeline), passes Lipinski + PAINS + SA. This is the **purest "composition-of-matter" output** of the project.

**Honest framing**: REINVENT did learn slowly, but the Boltz affinity ceiling (~−0.8 logKd for novel chemistry) was the bottleneck. The agent diversified chemistry but couldn't break through to nM-range affinity within the 51-step budget. With longer training and tighter selectivity-aware reward, this could improve.

---

## Validity caveats — what we know, what we don't

1. **Boltz + Vina agree on top hits** (4/5 cross-validated). Vina re-promotes a few mid-Boltz compounds (b1_122, r2b2_107) into the high-affinity zone — orthogonal scoring is meaningful.

2. **Pose-recovery passed**: 4/5 known PHGDH co-crystals reproduced within 2 Å. Geometry trustworthy.

3. **Selectivity screen is the most novel signal of v2**: Block G's 4-Rossmann-fold counter-screen reorders the candidate ranking. K58 dominates by selectivity, ONS by raw affinity, NCT-503 by AD evidence — they're three different rankings of the same molecules.

4. **No multi-conformation cross-check** (Block F not run — out of time budget). All scores against `6CWA_apo` (C1). Top candidates *should* be robust across conformations but not verified.

5. **No kinase counter-screen.** The ChEMBL screen surfaced kinase pharmacophore promiscuity; a follow-up against GRK-5, LRRK2, JAK1, MK2, MAPK9/10 would be informative.

6. **No wet-lab anything**. This is a computational project. All recommendations assume access to standard wet-lab tools (Park 2025 FP assay, in-vitro PHGDH activity, cellular DBD readouts).

---

## Single-line recommendations per audience

- **For an AD biology group with a Park 2025 FP assay**: test K58 (BI-cmpd-15) and K5K (BI-4924) first, alongside NCT-503 as positive control. ~1 week.

- **For a med-chem group considering composition-of-matter**: synthesize and test the step-41 REINVENT output and b1_005 first. Both are CNS-druglike with novel chemistry; the REINVENT compound is the more chemically novel.

- **For an in-silico repurposing group**: pursue CHEMBL3986234 (LRRK2, already CNS-tuned) and CHEMBL1084018 (PDE10A, also CNS) — flag for off-target counter-screening.

- **For a structural biology group**: the 1.42 Å K58 co-crystal (6RJ3) makes K58 the cleanest starting point for fragment-extension SAR if any of the wet-lab signals come back positive.

---

## Reading list

Primary AD biology:
- **Park et al. 2025** *Cell Metabolism* — moonlighting DBD function, NADH-mediated activation
- **Zhong 2025** (PMC12204802) — in-vivo NCT-503 in AD mouse models

Chemistry / inhibitor design:
- **Pacold et al. 2016** *Nat Chem Biol* — NCT-503, NCT-cmpd-1, NCT-cmpd-15 allosteric series
- **Mullarky et al. 2016** *PNAS* — CBR-5884 covalent Cys234 inhibitor
- **Spillier et al. 2019** *J Med Chem* — BI-4924 / BI-cmpd-15 NAD-competitive series (Boehringer)

Cancer context (why the field cares about PHGDH):
- **Possemato et al. 2011** *Nature*
- **Locasale et al. 2011** *Nat Genet*

Methods:
- **Boltz-2** (Wohlwend lab) — protein-ligand structure + affinity prediction
- **TamGen** (Microsoft) — pocket-conditional SMILES generator (scaffold-seeded mode)
- **REINVENT4** (AstraZeneca) — SMILES + RL with composite reward
- **AutoDock Vina** — orthogonal scoring engine for the rescore validation
- **FPocket** — druggability scoring (Phase 4 pre-screen)
- **ColabFold MMseqs2** — MSA fetcher (with patient-poller to bypass tight retry budget)

Pipeline source: <https://github.com/l1joseph/Alzheimers_Drug_Discovery>
