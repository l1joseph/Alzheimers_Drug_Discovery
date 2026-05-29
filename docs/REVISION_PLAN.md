# Revision Plan — addressing the computational peer review

Scope: this manuscript stays **computational**. In-vitro experimental validation is
deferred to a separate follow-up once this paper is validated, so no review item
requires wet-lab work. Most of the strengthening data **already exists in the repo**
(`results/`, `docs/notes/`) and needs reporting/re-derivation, not new pipeline runs.

Priority key: **M** = claim-critical (Major), **R** = rigor (Recommended), **m** = Minor.
Owner suggestions follow the CRediT split (Leo=pipeline/writing, Yashwin=generation/reward,
Cale=off-target/Vina/multiconf/structure, Ziheng=PyMOL/figures/druglikeness).

---

## Phase 1 — New computational analyses (generate/repair data)

These produce the numbers and figures the manuscript edits depend on. Do first.

### M1. Pose-recovery validation + resolve the K5K failure  *(Cale + Ziheng)*
- **Problem:** `results/pose_recovery.csv` shows centroid recovery 0.29–1.14 Å for ONV/ONS/K58/HMT but **30.8 Å (heavy-atom 31.7 Å) for K5K/6RJ6** — only 105 of ~300 CA pairs aligned, CA-align RMSD 17.9 Å. K5K is the #2 candidate and a Fig 4 panel.
- **Actions:**
  1. Re-run the 6RJ6→apo `cealign` selecting the correct single chain/assembly (6RJ6 likely has multiple chains; the ligand may have mapped to a symmetry/duplicate copy). Recompute K5K centroid + heavy-atom RMSD.
  2. If recovery succeeds → update `pose_recovery.csv` + Fig 4 K5K panel.
  3. If it still fails → label K5K pose "site-level only" and caveat its pose/affinity; keep K58 (recovers at 0.70 Å centroid) as the anchored example.
  4. Note the general result: site recovered (centroid <1.2 Å, 4/5) but pose imprecise (heavy-atom 4.7–6.3 Å).
- **Output:** corrected `pose_recovery.csv`; decision on K5K pose.

### M3. Boltz↔Vina agreement statistic  *(Cale / Leo)*
- **Problem:** `results/orthogonal_rescore/vina_scores.csv` shows rank discordance (e.g., r2b2_285 Boltz −0.56 / Vina −9.12 vs ONS −1.82 / −10.42). "Orthogonal validation" is not yet quantified.
- **Actions:** compute Spearman ρ and Pearson r (Boltz_aff vs vina_local) over all scored ligands; generate a Boltz-vs-Vina scatter (supp figure).
- **Output:** correlation value + `fig_supp_boltz_vina.{png,svg}`.

### M2. Target-prep druggability disclosure (+ optional repack)  *(Cale)*
- **Problem:** `results/druggability/summary.csv` rates the primary 6CWA-apo (C1) pocket at druggability **0.002** ("side-chain repack needed"); 3PG-retained C2 = 0.119; holo refs 0.2–0.86. Repack (Task #22) is **pending**.
- **Actions:**
  1. Identify which backbone produced the headline primary-pass affinities.
  2. Either run the side-chain repack on the stripped apo pocket and re-score the reference set, **or** disclose the collapsed-pocket limitation and lean on the multi-conformation results (which include better-formed pockets).
- **Output:** druggability table for supp; decision on repack.

### R1. Per-ligand Boltz uncertainty  *(Yashwin / Cale)*
- Extract per-ligand mean ± stdev across the 4 multi-conf backbones from `results/multiconf/by_ligand.csv` (`multiconf_findings.md` already notes b1_058 −0.65→−0.18, step-59 −0.17→+0.10).
- **Output:** error bars / stdev column for the affinity ranking.

---

## Phase 2 — Manuscript edits (`docs/paper/paper_draft.md`)

### M4. Re-scope Claim 1 + ground the mechanism in Chen's NCT-503 data  *(Leo)*
**Update (NCT-503 is experimentally anchored):** Chen et al. 2025 experimentally characterized NCT-503 — it **interacts with residues both outside and within the HHTH DNA-binding domain, reduces PHGDH binding to its target promoters, and alters downstream gene expression** (plus AD mouse-model rescue). So the moonlighting-disruption mechanism is **demonstrated for NCT-503, not merely hypothesized**, and Chen's NCT-503 contact data **corroborates** our computational pocket-overlap finding (residues inside *and* outside the 149–165 motif). This strengthens, rather than weakens, the central thesis.
- **Reframe the logic chain (don't just hedge):** NCT-503 is the experimental bridge — Chen showed a pocket-binding PHGDH inhibitor contacts the HHTH-DBD and blocks DNA binding; our structural-convergence analysis shows the other inhibitors occupy the same subsite and are therefore **predicted** to share that mechanism. Cite Chen's NCT-503 ChIP/expression + HHTH-contact results explicitly (currently the draft only cites "AD phenotype rescue").
- Keep residue-level **pose-precision** caveats for the *de novo* / Boltz-predicted poses (heavy-atom 4.7–6.3 Å) — i.e., qualify our predicted H-bond contacts, but NOT the Chen-validated NCT-503 contact.
- Note NCT-503 still lacks a high-resolution **co-crystal**, so it is absent from our `cealign` set; the BI/Pacold/HMT co-crystals carry the structural convergence, NCT-503 carries the functional validation.
- Temper Claim 4 ("central contribution / invisible to affinity-only") to acknowledge the **2-kinase (GRK5/GRK2)** panel — call it GRK-class promiscuity and flag broader kinases as follow-up.

### Report new analyses in text  *(Leo)*
- Add a **"Pose-recovery validation"** paragraph to Methods §2.3 / Results (from M1): centroid vs heavy-atom RMSD, the K5K outcome, the site-vs-pose distinction.
- Add the **Boltz–Vina correlation** (M3) and reframe Vina as complementary vs corroborating accordingly.
- Add the **druggability/target-prep** disclosure (M2) to Methods §2.1.
- Add **uncertainty** (R1) to the ranking in Results §3.3/§3.4.

### R2. Justify the combined selectivity index  *(Cale / Leo)*
- One or two sentences: why an unweighted **sum** of the two panels, why **min** (worst) off-target vs mean (`selectivity_findings.md` notes mean would reorder), and why these six off-targets. Add a sensitivity note.

### R3. Reproducibility  *(Leo)*
- State the **Boltz-2 model version/commit** (affinity module changed across releases) and confirm the methods description matches Boltz-2 (Passaro 2025), not Boltz-1.

---

## Phase 3 — Figures & supplementary  *(Ziheng + Leo)*

- **Supp Fig (new):** pose-recovery RMSD table/plot from `pose_recovery.csv` (M1).
- **Supp Fig (new):** Boltz-vs-Vina scatter (M3).
- **Supp table (new):** FPocket druggability summary (M2).
- **Fig 4:** update/caveat the K5K panel per M1 outcome.
- **m2:** ✓ RESOLVED — Ziheng confirmed the Fig 1a colour key (cyan = HHTH-DBD 103–165, green = NAD⁺/NADH); legend and caption are final.
- Add error bars to the Fig 2a affinity panel if R1 lands cleanly.

---

## Phase 4 — Finalization

- **m1:** finalize **Author Contributions** — remove the "placeholder … team to refine" line.
- **m4:** Chen 2025 page `3513–3529.e26`; verify supplementary figure numbering.
- **m5:** confirm the two "compound 15" labels (K58 / ONS) read unambiguously at every occurrence.
- Re-check the **5-page limit** after added text (trim Methods if needed; push detail to supp).
- Final consistency pass: numbers in text ↔ tables ↔ figures ↔ `results/` CSVs.
- Commit + push (one revision commit); update `CANDIDATE_REPORT.md` if K5K status changes.

---

## Dependency order
1. Phase 1 (M1, M3, M2, R1) — generate/repair data.
2. Phase 2 (M4 + reporting + R2, R3) — depends on Phase 1 numbers.
3. Phase 3 figures — depends on Phase 1.
4. Phase 4 finalization — last.

## What can start immediately (data already present)
- **M3** (Boltz–Vina Spearman) — pure analysis of an existing CSV.
- **R1** (per-ligand stdev) — pure analysis of `multiconf/by_ligand.csv`.
- **M1 diagnosis** (re-run 6RJ6 alignment) — inputs in `data/structures_reference/`.
- **M4** language edits — no new data needed for the re-scoping itself.
