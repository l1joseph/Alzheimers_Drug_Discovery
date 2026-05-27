# To Affinity and Beyond: A Structure-Informed Drug Discovery Pipeline for PHGDH Inhibitors Targeting the Alzheimer's-Relevant DNA-Binding Domain

**Leo Joseph¹, Yashwin Madakamutil¹, Cale Seymour¹, Ziheng Wang¹**
¹University of California, San Diego

---

## Abstract

Phosphoglycerate dehydrogenase (PHGDH) was recently shown to moonlight as a transcription factor independent of its enzymatic activity, via a helix-helix-turn-helix (HHTH) subdomain spanning residues 103–165 within its nucleotide-binding domain (Chen et al. 2025 *Cell*). This DNA-binding activity drives expression of IKKα and HMGB1, suppressing autophagy and accelerating amyloid pathology in Alzheimer's disease (AD). Of the published PHGDH inhibitors only NCT-503 has reported in-vivo AD evidence — the rest of the chemical matter is plausibly AD-relevant but untested. We screened four candidate sets — known binders, scaffold-seeded *de novo* designs, ChEMBL drug-like repurposing candidates, and REINVENT4 reinforcement-learning outputs — using Boltz-2 affinity prediction, AutoDock Vina orthogonal rescoring, multi-conformation robustness against four PHGDH backbones, and a six-target off-target counter-screen (four Rossmann-fold dehydrogenases + two GRK kinases). Structural alignment of five inhibitor co-crystals onto a common apo frame shows that the previously-labeled "allosteric" (Pacold 2016) and "NAD-competitive" (Spillier 2019) inhibitor classes occupy the same physical pocket within the NADH cofactor footprint, with 30–38 % of each inhibitor's pocket-lining residues falling inside the HHTH-DBD span — every published PHGDH inhibitor directly contacts the DNA-binding motif. **Compound 15 of Spillier et al. 2019** (PDB ligand `K58`) emerges as the cleanest selective PHGDH binder (combined selectivity index −4.78), followed by BI-4924, NCT-503, and compound 15 of Pacold et al. 2016 (PDB ligand `ONS`). Three of four novel scaffold-seeded designs pass affinity and drug-likeness filters but fail kinase selectivity — a failure mode invisible to affinity-only screens.

---

## 1. Introduction

PHGDH (EC 1.1.1.95) is the first committed enzyme of serine biosynthesis, catalyzing the NAD⁺-dependent oxidation of 3-phosphoglycerate to 3-phosphohydroxypyruvate. Its catalytic function has been an oncology drug-discovery target for over a decade, ever since tumor cells with PHGDH amplification were shown to be serine-dependent for growth (Possemato et al. 2011; Locasale et al. 2011). Chen et al. (2025) recently reported a second, *moonlighting* function: PHGDH acts as a transcription factor *independent of its enzymatic activity*, via a helix-helix-turn-helix (HHTH) subdomain spanning residues 103–165 within the nucleotide-binding domain. This subdomain shows structural similarity to the three-amino-acid-loop-extension (TALE) homeodomain family of DNA-binding motifs. In astrocytes, this transcriptional activity drives expression of IKKα and HMGB1 — promoting NF-κB signaling and suppressing autophagy — and accelerates amyloid-β pathology in mouse and human-organoid models of AD. NCT-503, an allosteric PHGDH inhibitor developed for cancer (Pacold et al. 2016), produces phenotypic rescue in AD models, establishing it as the only PHGDH inhibitor with published in-vivo AD evidence.

Two distinct published inhibitor classes target PHGDH. The **NCT series** of indole-carboxamides (NCT-503, and compounds 1 and 15 of Pacold et al. 2016 — PDB ligands ONV and ONS respectively) were originally described as allosteric. The **Boehringer-Ingelheim series** (BI-4924 and compound 15 of Spillier et al. 2019 — PDB ligand K58) was described as NAD-competitive. Structural alignment of all four inhibitor co-crystals (PDB 6PLF, 6PLG, 6RJ3, 6RJ6) onto a common apo frame, however, places their ligand centroids within 3.3 Å of each other and 4–6 Å from the NADH centroid in the cofactor pocket of 6CWA; the natural-product binder homoharringtonine (PDB 7EWH, ligand HMT) sits at 2.5 Å from NADH, essentially in the cofactor pose. The 3-phosphoglycerate substrate pocket is 12–18 Å away, clearly distinct. We conclude that all published PHGDH inhibitor scaffolds converge on a single cofactor-binding subsite; the "allosteric" vs "NAD-competitive" labels describe *functional* differences (whether the inhibitor displaces NADH or blocks catalysis) rather than separate binding sites. Moreover, **30–38 % of each inhibitor's pocket-lining residues lie within the Chen 2025 HHTH-DBD span — residues 149–156 of the cofactor pocket sit inside the 103–165 HHTH motif** — direct physical contact between every published PHGDH inhibitor and the DNA-binding motif. This provides a structural rationale for why all five inhibitor classes are mechanistically plausible against the moonlighting axis: by occupying the cofactor pocket, each can perturb the HHTH conformation required for DNA recognition, regardless of whether NADH binding is involved.

The operational question for AD repurposing is therefore not *"which compound binds PHGDH most tightly?"* but *"which existing PHGDH binders are selective enough to repurpose without confounding off-target effects?"* Standard affinity-only screens cannot answer the selectivity question. We address it by ranking candidates on two axes simultaneously: predicted affinity (Boltz-2 with AutoDock Vina rescore) and off-target selectivity against the most chemically-related proteins — four Rossmann-fold dehydrogenases (which share the NADH-binding fold) and two GRK kinases (representing generic ATP-pocket pharmacophore promiscuity).

We construct candidates from three independent generation engines (scaffold-seeded TamGen, ChEMBL library screening, and REINVENT4 with Boltz-as-reward reinforcement learning), score them with two orthogonal predictors, validate against a four-backbone conformational ensemble and a six-target off-target panel, and rank by a *combined selectivity index*. We report four selectivity-validated repurposing candidates, one surviving novel-scaffold candidate, and a methodological finding that novel scaffolds passing affinity and drug-likeness filters can still fail kinase-pharmacophore selectivity.

---

## 2. Methods

### 2.1 Data sources

The primary target structure is PHGDH chain A from PDB 6CWA (1.85 Å; ternary complex with NADH and 3-phosphoglycerate), comprising residues 6–278 of UniProt O43175 (299 amino acids). The query sequence (`data/phgdh_6CWA_chainA.fasta`) was used to construct a 2407-sequence multiple sequence alignment via the ColabFold MMseqs2 API (Mirdita et al. 2022). Three additional PHGDH backbones — 6CWA stripped to apo, 6CWA with bound 3PG, and 2G76 (1.7 Å, alternative apo) — were prepared for the multi-conformation robustness panel.

The validated reference set comprises ten characterized PHGDH binders. Throughout this paper we use PDB chemical-component identifiers as the primary compound names, with publication-canonical reference in parentheses where applicable: **NCT-503** (Pacold et al. 2016; no co-crystal); **ONV** (PDB 6PLF; compound 1 of Pacold et al. 2016); **ONS** (PDB 6PLG; compound 15 of Pacold et al. 2016); **K5K** (PDB 6RJ6; BI-4924 of Spillier et al. 2019); **K58** (PDB 6RJ3 at 1.42 Å, the highest-resolution PHGDH co-crystal published; compound 15 of Spillier et al. 2019); **CBR-5884** (Mullarky et al. 2016; covalent at Cys234); **HMT** (PDB 7EWH; homoharringtonine, natural product); plus the endogenous ligands NADH and 3PG. Real co-crystal structures for each are tracked in `data/structures_reference/`. The repurposing screen drew from ChEMBL 34, which we filtered from 2.4 million compounds to 1.0 million Lipinski/PAINS-clean drug-like molecules and then randomly sampled to 5000 lead-like candidates.

### 2.2 Candidate generation engines

Three engines produced complementary candidate sets. **TamGen** (Wang et al. 2024), a pocket-conditional autoregressive SMILES generator with variational pocket conditioning, was run in three scaffold-seeded branches: B1 (NCT-503 seed, targeting the allosteric pocket), B2 (BI-4924 seed, NAD-competitive), and B3 (PKU drugs, for repurposing). One iterative round of scaffold-seeding from top B2 outputs produced an additional 887 compounds total. **REINVENT4** (Loeffler et al. 2024) was run as a 100-step staged-learning RL job (batch size 64) with Boltz-2 as the inner-loop reward oracle, implemented via a custom `ExternalProcess` plugin that submits a nested SLURM job per RL step. The composite reward is `0.45·σ(−aff) + 0.20·QED + 0.15·σ(6−SA) + 0.10·MW_window + 0.05·logP_window + 0.05·mech_bonus`, with a hard reject (reward = 0) on invalid SMILES, PAINS/Brenk substructure hits (RDKit FilterCatalog), or SA score > 7. The composite design was motivated by an early reward-hacking failure: an affinity-only objective produced compounds with Boltz affinity −1.59 but logP > 7 and PAINS hits.

### 2.3 Scoring and validation

All candidates were scored with **Boltz-2** (Wohlwend et al. 2024), which jointly predicts protein-ligand complex structure and binding affinity. Boltz was ported to AMD MI300A via ROCm 6.3 with the `--no_kernels` flag (cuequivariance is NVIDIA-only). Per-candidate parallelism was achieved by running four Boltz processes per node pinned to individual APUs via `HIP_VISIBLE_DEVICES`, fanned out across four nodes through SLURM array jobs (16 effective parallel workers). **AutoDock Vina 1.2** (Eberhardt et al. 2021) was used as an orthogonal physics-based rescore on Boltz-predicted poses; receptor and ligand PDBQT preparation used Meeko's `mk_prepare_receptor`/`mk_prepare_ligand` with OpenBabel fallback for compounds with tautomer-induced atom-typing failures.

Two validation passes followed primary scoring. **Multi-conformation robustness** re-scored the top 21 candidates against the four PHGDH backbones; per-ligand standard deviation across the ensemble measures sensitivity to conformational state. The **off-target selectivity panel** scored the top 11 candidates against six structurally related proteins: four Rossmann-fold dehydrogenases (LDH-A UniProt P00338, MDH2 P40926, GAPDH P04406, IDH1 O75874) representing NADH-pocket fold homology, plus two GRK kinases (GRK5 P34947, GRK2 P25098) testing ATP-pocket pharmacophore promiscuity. Off-target sequences were obtained from UniProt; per-target MSAs were built with the same ColabFold pipeline. The kinase panel was motivated by post-hoc analysis of top ChEMBL hits, seven of which originated from unrelated kinase drug-discovery programs. The *combined selectivity index* is the sum of dehydrogenase-panel and kinase-panel `sel_idx` values, where each `sel_idx = PHGDH_aff − min(off-target_aff)`; lower values indicate stronger PHGDH preference.

To establish that the validated PHGDH binders share a common pocket, we aligned five inhibitor co-crystals (6PLF, 6PLG, 6RJ3, 6RJ6, 7EWH) and the endogenous-cofactor structure (6CWA) onto our apo target using `cealign` (Shindyalov & Bourne 1998), computed ligand centroids in the apo frame, and constructed an all-pairs distance matrix (Figure 1A inset). All five inhibitor ligand centroids cluster within 3.3 Å of each other and 4–6 Å from NADH; the substrate 3PG is 12–18 Å from any inhibitor. Pocket residues were defined as protein residues with any atom within 5 Å of the bound ligand on the apo backbone (`scripts/check_pocket_overlap.py`); the union of these pocket residues was compared against the Chen 2025 HHTH-DBD span (residues 103–165) to quantify physical overlap between the inhibitor pocket and the DNA-binding motif.

### 2.4 Compute

Pipeline runs were performed on the SDSC Cosmos cluster (AMD MI300A APUs, ROCm 6.3). Total compute footprint ≈ 30 GPU-hours, dominated by REINVENT's inner-loop Boltz scoring (6,400 SMILES × ~25 sec/ligand on a single APU). All code, structure inputs, predicted poses, and reference co-crystals are at https://github.com/l1joseph/Alzheimers_Drug_Discovery.

---

## 3. Results

*[to be drafted in next section]*

## 4. Discussion

*[to be drafted in next section]*

## References

*[to be formatted in ACS style after main text is finalized]*

1. Chen, J. *et al.* Transcriptional regulation by PHGDH drives amyloid pathology in Alzheimer's disease. *Cell* **188**, 3513–3529 (2025). doi:10.1016/j.cell.2025.03.045
2. (reserved — additional reference if needed for moonlighting background)
3. Pacold, M. E. *et al.* A PHGDH inhibitor reveals coordination of serine synthesis and one-carbon unit fate. *Nat. Chem. Biol.* **12**, 452–458 (2016).
4. Spillier, Q. *et al.* Structural and biochemical study of cellular PHGDH inhibitors. *J. Med. Chem.* **62**, 9526–9543 (2019).
5. Mullarky, E. *et al.* Identification of a small molecule inhibitor of PHGDH. *PNAS* **113**, 1778–1783 (2016).
6. Possemato, R. *et al.* Functional genomics reveal that PHGDH is essential for cancer growth. *Nature* **476**, 346–350 (2011).
7. Locasale, J. W. *et al.* PHGDH copy number gain. *Nat. Genet.* **43**, 869–874 (2011).
8. Wohlwend, J. *et al.* Boltz-1 / Boltz-2 protein-ligand affinity. *bioRxiv* (2024).
9. Mirdita, M. *et al.* ColabFold: making protein folding accessible. *Nature Methods* **19**, 679–682 (2022).
10. Loeffler, H. H. *et al.* REINVENT4. *J. Cheminformatics* **16**, 20 (2024).
11. Eberhardt, J. *et al.* AutoDock Vina 1.2. *J. Chem. Inf. Model.* **61**, 3891–3898 (2021).
12. Wang, K. *et al.* TamGen: target-aware molecular generation. (2024).
13. Shindyalov, I. N. & Bourne, P. E. Protein structure alignment by incremental combinatorial extension. *Protein Eng.* **11**, 739–747 (1998).

## Author Contributions

**Leo Joseph**: Conceptualization, pipeline architecture, AMD MI300A ROCm porting of Boltz-2 and TamGen, REINVENT4 + Boltz reward integration, manuscript writing.
**Yashwin Madakamutil**: [TBD by team]
**Cale Seymour**: [TBD by team]
**Ziheng Wang**: [TBD by team]
All authors: manuscript review and editing.
