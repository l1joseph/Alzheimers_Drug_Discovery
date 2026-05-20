# Alzheimer's Drug Discovery — PHGDH NADH-Cleft Targeting Pipeline

## Context

Recent work (Park *et al.*, *Nature* 2025 — PubMed 40273909) showed that **PHGDH has a moonlighting transcriptional role**: NADH binding activates a DNA-binding capability that drives a gene-regulatory program implicated in sporadic Alzheimer's disease. NCT-503 (a known allosteric PHGDH inhibitor from cancer-metabolism work) blocked this activity in mouse models and improved cognition.

**Goal**: identify small-molecule binders to the PHGDH catalytic domain — both novel (de novo design) and modified versions of existing PHGDH-interacting drugs — that compete with or otherwise block the **NADH-driven DBD activation**. Run all compute on the **SDSC Cosmos AMD MI300A / ROCm 6.3** stack.

---

## Biology background (mechanism we are targeting)

PHGDH plays two distinct roles:

**Role 1: enzymatic** (serine biosynthesis pathway).
3-phosphoglycerate (3PG) → 3-phosphohydroxypyruvate via NAD⁺/NADH redox. Standard textbook function; well-characterized.

**Role 2: moonlighting transcriptional regulator** (recently discovered).
A subpopulation of PHGDH binds DNA directly and modulates gene expression. The DBD function is **activated by NADH binding** at the cofactor pocket — i.e., the same Rossmann fold that handles cofactor for enzymatic turnover, in a different conformational mode, controls transcriptional activity. This is the axis Park *et al.* implicate in sporadic AD.

**Why this matters for design**:
- The druggable mechanism is to **block NADH-driven DBD activation**, ideally without disrupting enzymatic serine biosynthesis broadly (selectivity goal).
- A small molecule that occupies or allosterically locks the NADH subsite should block DBD activation. NCT-503 demonstrates the proof-of-concept in vivo.

**Strategic decisions log**:

| Decision | Rationale |
|---|---|
| **Do NOT pursue 3PG-mimetic / substrate-blocking axis** | Zhong *et al.* (Cell, citation TBD) showed 3PG **accumulation is not pathogenic** — blocking substrate flux is not a useful AD therapeutic axis. |
| **Target the NADH subsite (Rossmann pocket) as primary** | This is the activator binding event for the DBD moonlighting function. Direct competition with NADH is the cleanest mechanistic disruption. |
| **Also target the NCT-503 allosteric site (within the catalytic domain)** | NCT-503 binds an allosteric pocket dependent on Cys234 (in the catalytic domain, not the ACT domain). It works *in vivo*, so this site is validated. |
| **Use an ensemble of crystal-state conformations, not one PDB** | Literature does not establish whether 3PG induces a meaningful conformational change. Test empirically by screening across apo / +3PG / independent-crystal conformations. |
| **Side-chain repack of holo-stripped pockets** | 6CWA was crystallized holo (NADH + 3PG). Stripping ligands leaves induced-fit holo backbone with empty pocket — repack relaxes rotamers toward apo-compatible state. |
| **Iterative scaffold-seeded design (closed loop)** | Use known PHGDH binders (NCT-503, BI-4924, HHT) as starting scaffolds in TamGen; score with Boltz-2; feed top hits back as next-round seeds. Directed evolution of small molecules. |

---

## Pipeline overview

```
                                ┌──────────────────────┐
PHGDH PDBs ────────────────────▶│ Target prep         │──▶ 4-conformation ensemble
(6CWA, 2G76, 6PLF, 6RJ3, 6RJ6,  │ (strip + repack +    │   (apo×2, +3PG, allosteric)
 6PLG, 7EWH)                    │  align allosteric)   │
                                └──────────┬───────────┘
                                           │
                ┌──────────────────────────┼──────────────────────────────┐
                ▼                          ▼                              ▼
┌────────────────────────┐   ┌────────────────────────┐    ┌────────────────────────┐
│ (A) Library screen     │   │ (B) De novo TamGen     │    │ (C) Scaffold-seeded    │
│ - DrugBank approved    │   │     pocket-conditioned │    │     iterative design   │
│ - ChEMBL drug-like     │   │     no scaffold        │    │     (closed loop)      │
│ - Positive controls    │   │                        │    │  ┌─Round 0: known binders→
│ - Known PHGDH binders  │   │                        │    │  ├─Round 1: TamGen seeded─
│ - PKU drug subset      │   │                        │    │  │  ↓ Boltz-2 score      │
└──────────┬─────────────┘   └──────────┬─────────────┘    │  ├─Round 2: top-K seeds──
           │                            │                  │  │  ↓                    │
           ├── RDKit filter ────────────┤                  │  └─ ...until plateau────┘
           │   (Lipinski, PAINS,        │                  └──────────┬─────────────┘
           │    valid SMILES)           │                             │
           ▼                            ▼                             ▼
         ┌─────────────────────────────────────────────────────────────────┐
         │ Boltz-2 affinity scoring (--no_kernels for ROCm)               │
         │  - binary mode (protein + ligand)        ← C1 (apo)            │
         │  - ternary mode (+ 3PG as co-ligand)     ← C2                  │
         │  scored across all 4 target conformations                      │
         └────────────────────────────┬────────────────────────────────────┘
                                      ▼
         ┌─────────────────────────────────────────────────────────────────┐
         │ Consensus ranking + mechanism classification                   │
         │  - top-K Jaccard across conformations (robust hits)            │
         │  - positive-control rank check (calibration)                   │
         │  - 3PG-tolerant vs 3PG-sensitive (NADH-competitive vs not)     │
         │  - improvement vs round-0 known-binder baseline                │
         └─────────────────────────────────────────────────────────────────┘
```

---

## Targets and conditions

The construct in 6CWA is residues 6–278 (catalytic N-terminal half only; ACT regulatory domain not present). All targeting happens within this construct's two pockets: the **substrate+cofactor cleft** (orthosteric, containing the NADH subsite) and the **NCT-503 allosteric site** (Cys234-adjacent, within the catalytic domain).

| Conformation | PDB | State | Resolution | Purpose |
|---|---|---|---|---|
| **C1** — 6CWA apo | 6CWA | Holo backbone, ligands stripped, side-chain repacked | 1.77 Å | Primary; closest to native NADH-bound geometry |
| **C2** — 6CWA + 3PG | 6CWA | 3PG re-injected, NADH out | 1.77 Å | Tests for 3PG-tolerant (NADH-competitive) binders |
| **C3** — 2G76 apo | 2G76 | Independent crystal, D-malate stripped, repacked, longer construct (res 3–314) | 1.7 Å | Tests for conformation-bias artifacts in C1 |
| **C4** — 6PLF allosteric pocket | 6PLF → aligned to 6CWA frame | NCT-503-style allosteric site within catalytic domain | 1.7 Å | Second druggable site |

**Pocket centers** (6CWA chain-A frame):
- Substrate+cofactor cleft (NADH centroid): **(9.58, 0.40, 29.83) Å**, radius 10 Å — verified by `prep_targets.py` against NADH HETATM centroid.
- Allosteric (NCT-503 site, from 6PLF→6CWA alignment): **(13.40, 5.04, 28.20) Å**, radius 10 Å. NB: alignment RMSD was 3.98 Å over 299 residues — substantial conformational difference between holo and inhibitor-bound states; allosteric pocket may overlap with NADH subsite in 6CWA's frame.

**Consensus rules**:
- **Robust hit** = top-10% in C1 ∩ C3 (substrate cleft, two independent backbones).
- **NADH-competitive** = top-10% in both C1 AND C2 (binds in presence of 3PG → not 3PG-competitive).
- **3PG-competitive** = top-10% in C1 only, loses rank in C2.
- **Allosteric** = top-10% in C4 only.

---

## Iterative scaffold-seeded design loop (new branch)

The closed-loop design that turns TamGen + Boltz-2 into a directed-evolution engine for small molecules.

**Inputs**:
- A target pocket (C1, C4, or both)
- A set of seed scaffolds — Round 0 seeds are known PHGDH binders below

**Round 0 — baseline affinity benchmark**:
Score known PHGDH-interacting drugs with Boltz-2 across all four conformations to establish the affinity-distribution baseline.
- **Round-0 seed set**: NCT-503, BI-4924 (K5K), BI compound 15 (K58), NCT-cmpd-1 (ONV), NCT-cmpd-15 (ONS), homoharringtonine (HMT), CBR-5884, indole-carboxamide series.
- **Output**: `results/round_0_baseline.csv` with affinity scores per (compound, conformation). Sets the bar that later rounds must clear.

**Round N (N ≥ 1) — seeded generation**:
For each seed in the round's seed pool:
1. Run TamGen with `prepare_pdb_ids_center_scaffold.py` style — keep the scaffold core, generate periphery variants conditioned on the target pocket.
2. Sample M variants per seed (default M=200).
3. Filter: valid SMILES, Lipinski (mol_wt 150–500, logP < 5, HBD ≤ 5, HBA ≤ 10), no PAINS, Tanimoto distance > 0.3 from the seed (force novelty).
4. Score all survivors with Boltz-2 affinity (target conformations C1 + C4).
5. **Convergence check**: if no variant beats the seed by ≥ Δ (default 0.3 log Kd) AND no variant has confidence_score > seed's, drop that seed.

**Update seed pool**:
- Variants with improvement Δ vs. parent seed become seeds for round N+1.
- Cap seed pool at top-K (default K=20) to control compute.
- **Hard stop**: 5 rounds OR seed pool empty OR cumulative GPU-budget exceeded.

**Output**:
- `results/iterative_loop/round_{N}_ranked.csv` per round.
- `results/iterative_loop/affinity_trajectory.png` — per-lineage improvement curve.
- `results/iterative_loop/final_top.sdf` — top-50 with predicted complexes + lineage to original seed.

**Two parallel sub-branches**:
- **B1 — NCT-503 family optimization**: seed pool = NCT-series (cmpd 1, cmpd 15, NCT-503 itself). Target site = C4 (allosteric). Goal: NCT-503 analogues with better predicted affinity, drug-likeness, or peripheral atoms compatible with BBB delivery.
- **B2 — BI-4924 family optimization**: seed pool = BI-series (K5K, K58). Target site = C1 (substrate cleft / NADH subsite). Goal: NAD-competitive scaffolds with the same backbone but different chemistry.

**Optional B3 — PKU drug repurposing**:
PKU (phenylketonuria) drugs target phenylalanine hydroxylase (PAH), a related cofactor-dependent enzyme. Some PKU drug scaffolds (e.g., sapropterin / BH4 analogues, pegvaliase substrate mimetics) may serve as starting scaffolds for PHGDH NADH-pocket binders due to overlapping cofactor binding geometries. Run B1-style iterative loop seeded from FDA-approved PKU drugs. Lower priority; only if B1/B2 plateau early.

---

## Compound library (Branch A — virtual screen)

| Set | Size | Source | Purpose |
|---|---|---|---|
| **DrugBank approved** | ~2,700 | drugbank.com (academic, free) | Repurposing candidates |
| **ChEMBL drug-like subset** | ~50k (capped) | ChEMBL 34, Lipinski + PAINS filtered | Bioactive space |
| **PHGDH positive controls** | 7+ | Literature + RCSB CCD | Pose-recovery + ranking sanity (committed) |
| **Known PHGDH-binder extended set** | ~30 | Literature SAR series | Round-0 baseline (Sect. above) |
| **PKU drug subset** | ~15 | FDA-approved + investigational PKU therapeutics | Sub-branch B3 seeds |

Canonical format: `data/libraries/{set}.csv` with columns `id,smiles,source[,notes]`.

---

## Compute architecture (Cosmos / MI300A / ROCm 6.3)

- **Login node** (`cosmos02`): conda env creation, repo cloning, structure prep, result inspection. No GPU.
- **Compute nodes** (`cluster` partition, exclusive): GPU work via SLURM. Each node = 4× AMD Instinct MI300A APUs, 192 CPUs, 500 GB RAM.
- **ROCm**: `module load rocm/6.3.0`. `PYTORCH_ROCM_ARCH=gfx942` already set.
- **PyTorch ROCm wheels**: pip from `https://download.pytorch.org/whl/rocm6.2` (no conda channel hosts ROCm builds).
- **Scratch**: **`/cosmos/vast/scratch/l1joseph`** (Vast Data, 675 TB, NFS). NOT `/ddn_scratch` (which doesn't exist despite `$SCRATCH` env var). Used for model weights, intermediate predictions, large library files.
- **Home**: `/cosmos/nfs/home/l1joseph` for code + final ranked CSVs.
- **SLURM log discipline**: every job script sets `--job-name=<descriptive>`, `--output=$PROJECT_ROOT/logs/%x_%j.out`, `--error=$PROJECT_ROOT/logs/%x_%j.err`. Chronological symlinks created at job start.

**Observed throughput** (from smoke test #85046, 1 ligand, MI300A):
- Structure prediction: ~27 sec
- Affinity prediction: ~9 sec
- Total per ligand: ~36 sec on 1 APU → ~9 sec effective with 4 APUs in parallel
- **Library projections**: DrugBank (2.7k) ≈ 2 GPU-h; ChEMBL drug-like (50k) ≈ 30 GPU-h; full iterative loop (5 rounds × 20 seeds × 200 variants) ≈ 50 GPU-h.

---

## Installation (validated)

### Boltz-2 → `boltz-rocm` env

```bash
mamba create -y -n boltz-rocm python=3.11 -c conda-forge
mamba activate boltz-rocm
pip install --no-cache-dir torch==2.5.1+rocm6.2 torchvision==0.20.1+rocm6.2 \
    torchaudio==2.5.1+rocm6.2 \
    --index-url https://download.pytorch.org/whl/rocm6.2
cd tools/boltz && pip install -e .   # NO [cuda] extra
```

**Critical runtime flag**: `--no_kernels` on every `boltz predict` call. Without it Boltz tries to import `cuequivariance_torch` (NVIDIA-only). With `--no_kernels`, Boltz falls through to its pure-PyTorch implementation which runs natively on ROCm. Smoke test #85046 confirmed end-to-end correctness with this flag.

### TamGen → `tamgen-rocm` env

```bash
mamba create -y -n tamgen-rocm python=3.9 -c conda-forge
mamba activate tamgen-rocm
mamba install -y -c conda-forge rdkit=2024.03.1 scipy einops tensorboardX ipykernel \
    pandas numpy=1.26.4 networkx dm-tree requests biopython editdistance \
    cffi regex tqdm sacrebleu
pip install --no-cache-dir torch==2.5.1+rocm6.2 \
    --index-url https://download.pytorch.org/whl/rocm6.2
# PyG companions: NO ROCm wheels exist; use CPU wheels (ABI-compatible with our ROCm torch)
pip install --no-cache-dir -f https://data.pyg.org/whl/torch-2.5.0+cpu.html \
    torch_cluster torch_scatter torch_sparse pyg_lib torch_spline_conv torch_geometric
pip install --no-cache-dir fy-common-ext
cd tools/TamGen && pip install --no-deps -e .  # vendored fairseq-0.8.0
```

TamGen setup.py only builds a pure C++ libbleu extension — no CUDA ops to skip. Point-cloud k-NN ops (used in the pocket encoder) run on CPU; pocket sizes are small (~250 residues), negligible.

### TamGen checkpoints (3.3 GB)

```bash
mkdir -p /cosmos/vast/scratch/l1joseph/tamgen_ckpts
cd /cosmos/vast/scratch/l1joseph/tamgen_ckpts
curl -L -O https://zenodo.org/records/13751391/files/checkpoints.zip
curl -L -O https://zenodo.org/records/13751391/files/gpt_model.zip
unzip checkpoints.zip && unzip gpt_model.zip
# Symlink into TamGen/ for relative-path-expecting scripts
ln -sf /cosmos/vast/scratch/l1joseph/tamgen_ckpts/checkpoints tools/TamGen/checkpoints
ln -sf /cosmos/vast/scratch/l1joseph/tamgen_ckpts/gpt_model/checkpoint_best.pt \
    tools/TamGen/gpt_model/checkpoint_best.pt
```

---

## Execution phases

| Phase | What | Compute | Pass criterion |
|---|---|---|---|
| **0. Setup** ✅ | Repos cloned, PDBs downloaded, conda envs built, checkpoints fetched | Login | `torch.cuda.is_available()` True in compute job |
| **1. Smoke tests** ✅ | Boltz-2 minimal example (`--no_kernels`); TamGen import + GPU verification | 1× APU, ~5 min | Both jobs exit 0; Boltz produces affinity JSON; TamGen pointcloud transformer imports |
| **2. Pose-recovery validation** | Boltz-2 dock BI-4924 into 6RJ6, NCT-cmpd-1 into 6PLF, HHT into 7EWH, BI-cmpd-15 into 6RJ3 | 4× APU, ~1 h | ≥ 3/4 cases: predicted ligand RMSD < 2 Å vs crystal HETATM |
| **3. Target prep refinement** | Side-chain repack with PyRosetta `FastRelax` (backbone fixed) on stripped PDBs | Login, ~30 min | 4 conformation PDBs exported, geometry sane |
| **4. Druggability scoring** | Run FPocket on each conformation; compare pocket volumes, druggability score, hydrophobicity at the substrate-cleft vs allosteric pocket | Login, ~10 min | Druggability score per pocket; flag pockets with score < 0.6 |
| **5. Library staging** | Download DrugBank approved, filter ChEMBL drug-like (50k cap), compile known-binder set + PKU drug set | Login | Single canonical CSV per set, all RDKit-valid |
| **6. Round-0 baseline benchmark** | Score known-binder set (Round-0 seed set) with Boltz-2 across all 4 conformations | ~1 GPU-h | All compounds scored; affinity distribution recorded as baseline |
| **7. Library virtual screen (Branch A)** | Score DrugBank + positive controls across all conformations | ~2–4 GPU-h | Positive controls in top-1% on appropriate conformation; if not, recalibrate |
| **8. De novo TamGen (Branch B)** | Generate 1,000 SMILES per conformation, RDKit filter, score with Boltz-2 | ~12 GPU-h | ≥ 80% valid SMILES, scaffold diversity Tanimoto > 0.7, some hits > Round-0 baseline |
| **9. Iterative scaffold-seeded loop (Branch C)** | Run B1 (NCT-503 family) + B2 (BI-4924 family) for up to 5 rounds; closed-loop generate→score→reseed | ~30–50 GPU-h | At least 1 lineage shows monotonic affinity improvement vs round 0 |
| **10. PKU repurposing (optional Branch B3)** | Iterative loop seeded from PKU drugs; only if Phases 8–9 plateau | ~10 GPU-h | Identify whether PKU scaffolds can reach competitive affinity |
| **11. Consensus + reporting** | Merge all branches, ensemble consensus filter, mechanism classification, top-50 + predicted complexes | Login | `results/top_hits.{csv,sdf,pdb}` with provenance per hit |

Phases 2, 4, 5 can run in parallel. Phase 6 gates 7-9 (need baseline before scoring novels). Phase 9 is the most compute-intensive.

---

## Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Boltz `--no_kernels` path slower than CUDA kernels | Medium | Acceptable — already measured at ~9 s/lig effective on MI300A; library + iterative timelines fit |
| Boltz-2 affinity prediction off-scale for new chemistry | Medium | Phase 6 baseline calibrates the scale; relative rank against known binders is what matters |
| Iterative loop overfits to Boltz's biases (Goodhart) | High | Use multi-conformation consensus + require ≥ 2-fold improvement margin to avoid noise-mining; sanity-check top hits with an orthogonal scorer (DiffDock + Vina) before any wet-lab handoff |
| Pose-recovery RMSD > 2 Å | Medium | If failure, drop affinity-scale interpretation; use pose-fit + plddt as filter, rank by confidence; rescue with Vina on the same poses |
| Allosteric pocket (C4) overlaps with NADH subsite | Confirmed (~5 Å apart in 6CWA frame) | Treat C1 and C4 as related rather than fully orthogonal sites; expect some convergence in hits |
| TamGen scaffold-seeded generation produces low-novelty variants | Medium | Hard Tanimoto > 0.3 filter from parent; reject near-duplicates |
| 3PG repack changes substrate-cleft geometry meaningfully | Low | Compare C1 (apo, repacked) and C3 (2G76 apo) — divergent rankings flag this |
| Compute budget overrun on full iterative loop | Medium | Hard 5-round cap; cap variants/round/seed at 200; can shrink Branch B3 first |

---

## Citations

| Ref | Citation | Used for |
|---|---|---|
| Park 2025 | Park *et al.*, *Nature* 2025 (PubMed 40273909) — PHGDH moonlighting / DBD activation / sporadic AD | Mechanism we are targeting |
| Zhong (TBD) | Zhong *et al.*, *Cell*, exact ref TBD — 3PG accumulation not pathogenic | Rules out 3PG-mimetic strategic axis |
| Pacold 2016 | Pacold *et al.*, *Nat Chem Biol*, 2016 — NCT-503 discovery + biochemical characterization | NCT-503 scaffold for Branch B1 |
| Spinelli 2021 | Spinelli *et al.* — BI-4924 series (Boehringer-Ingelheim) | BI-4924 scaffold for Branch B2 |
| Wohlwend 2024 | Wohlwend *et al.* — Boltz / Boltz-2 | Affinity scoring engine |
| Tu 2024 | Tu *et al.*, *Briefings in Bioinformatics*, 2024 (PubMed 39472567) — TamGen | De novo + scaffold-seeded generation |
| Mullarky 2016 | Mullarky *et al.* — CBR-5884 (covalent PHGDH inhibitor at Cys234) | Positive control + Cys234 site reference |
| Rohle 2013 | Rohle *et al.* — PHGDH and serine biosynthesis in cancer | Cancer-context PHGDH literature |

---

## Directory layout

```
Alzheimers_Drug_Discovery/
├── PLAN.md                           # this file
├── 6CWA_chainA_clean.pdb             # original cleaned input (kept)
├── 6CWA.cif
├── pocket_center.json                # substrate cleft / NADH centroid (6CWA frame)
├── pocket_center_allosteric.json     # NCT-503 site center (derived from 6PLF)
├── tamgen_input.csv
├── tools/                            # gitignored
│   ├── boltz/                        # cloned, installed in boltz-rocm env
│   └── TamGen/                       # cloned + checkpoints symlinked from scratch
├── data/
│   ├── structures/                   # 7 PHGDH CIFs (gitignored)
│   ├── targets/                      # prepared PDBs per conformation (gitignored, regen via prep_targets.py)
│   │   ├── phgdh_6CWA_apo.pdb        # C1
│   │   ├── phgdh_6CWA_3pg.pdb        # C2
│   │   ├── phgdh_6CWA_3pg_nadh.pdb   # mechanism rescore
│   │   └── phgdh_2G76_apo.pdb        # C3
│   └── libraries/
│       ├── phgdh_positive_controls.csv  # committed
│       ├── known_phgdh_binders.csv      # Round-0 baseline seed set
│       ├── drugbank_approved.csv
│       ├── chembl_druglike.csv
│       └── pku_drugs.csv
├── scripts/
│   ├── prep_targets.py
│   ├── build_boltz_yamls.py
│   ├── aggregate_boltz.py
│   ├── score_baseline.py             # Phase 6
│   ├── iterative_loop.py             # Phase 9 driver
│   ├── druggability_fpocket.py       # Phase 4
│   └── repack_pyrosetta.py           # Phase 3
├── slurm/
│   ├── boltz_smoke.sh                # ✅ passing
│   ├── tamgen_smoke.sh               # ✅ passing
│   ├── boltz_screen.sh               # generic Boltz batch job
│   ├── tamgen_generate.sh
│   ├── iterative_round.sh
│   └── pose_recovery.sh
├── logs/                             # SLURM logs (gitignored except .gitkeep)
└── results/
    ├── smoke/                        # ✅ smoke outputs
    ├── pose_recovery.csv
    ├── round_0_baseline.csv
    ├── library_screen_<conf>.csv
    ├── iterative_loop/
    │   ├── round_{N}_ranked.csv
    │   ├── affinity_trajectory.png
    │   └── final_top.sdf
    └── top_hits.{csv,sdf,pdb}        # final consensus output
```

---

## Open questions deferred (not blocking execution)

1. **Exact Zhong *et al.* Cell citation** — fill in once user provides DOI/PubMed.
2. **HHT (homoharringtonine) site location** — 7EWH at 2.99 Å has HHT bound. Need to verify it binds the same substrate cleft (likely) or a separate site. If a distinct site, add as C5.
3. **Top-hit MD refinement + MM-GBSA rescore** — for the final top-20 from Phase 11, run short OpenMM MD + MM-GBSA. Out of initial scope; queue if results are promising.
4. **Wet-lab validation handoff** — out of scope. Output format (SDF with predicted poses + affinity) is set up to be directly orderable from Enamine / synthesizable.
5. **Mutational analysis of PHGDH target** — Park 2025 likely identified specific PHGDH residue mutations that block DBD activation. Cross-referencing those residues with our top-hit binding poses would help selectivity arguments. Deferred until top hits are in hand.
