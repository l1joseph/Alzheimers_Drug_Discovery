# Alzheimer's Drug Discovery — PHGDH NADH-Cleft Targeting Pipeline

## Context

Recent work (Park et al., *Nature* 2025) showed that **PHGDH** has a moonlighting transcriptional role: NADH binding triggers DNA-binding activity that drives a gene-regulatory program implicated in sporadic Alzheimer's disease. NCT-503 (a known allosteric PHGDH inhibitor from cancer-metabolism work) blocked this activity in mice. **Goal**: identify additional small-molecule binders to the PHGDH catalytic domain — both novel (de novo design) and from existing compound libraries (repurposing) — that compete with or otherwise block the NADH-driven activation.

**Strategy**: dual-mode in silico screen on the **AMD MI300A** nodes of SDSC Cosmos.
- **TamGen** (Microsoft, target-aware chemical LM) → de novo SMILES generation conditioned on the PHGDH pocket
- **Boltz-2** (Wohlwend lab) → complex prediction + affinity scoring for both de novo candidates and existing libraries

**Why ROCm matters here**: Cosmos has no NVIDIA hardware. Both tools default to CUDA; install plan addresses that.

---

## Pipeline overview

```
                ┌──────────────────────┐
PHGDH PDBs ────▶│ Target prep          │──▶ 4-conformation ensemble (apo×2, +3PG, allosteric)
(6CWA, 2G76,   │ (strip ligs, repack) │
 6PLF, 6RJ3,   └──────────┬───────────┘
 6RJ6)                    │
                          ├─────────────────┐
                          ▼                 ▼
                  ┌───────────────┐  ┌────────────────────────┐
                  │ TamGen        │  │ Compound libraries     │
                  │ pocket-cond.  │  │ DrugBank approved      │
                  │ generation    │  │ ChEMBL drug-like       │
                  │ N=1000/site   │  │ PHGDH pos. controls    │
                  └──────┬────────┘  └──────────┬─────────────┘
                         │                      │
                         ├──── RDKit ───────────┤  (validity, Lipinski, PAINS)
                         ▼                      ▼
                       ┌──────────────────────────┐
                       │ Boltz-2 affinity scoring │
                       │  - binary (apo target)   │
                       │  - ternary (+3PG)        │
                       │ across all conformations │
                       └────────────┬─────────────┘
                                    ▼
                       ┌──────────────────────────┐
                       │ Consensus ranking        │
                       │ • top-K across ensemble  │
                       │ • pos-control sanity     │
                       │ • mechanism class        │
                       └──────────────────────────┘
```

---

## Targets and conditions

### Why 4 conformations, not 1

The literature does **not** establish whether 3PG induces a meaningful conformational change in PHGDH. Rather than assume, we screen against an ensemble of crystal-state conformations and treat consensus as the strongest signal.

| Conformation | PDB | State | Resolution | Purpose |
|---|---|---|---|---|
| C1 — 6CWA apo | 6CWA | Holo backbone, ligands stripped, side-chain repacked | 1.77 Å | Primary; closest to native substrate-bound geometry, empty cleft |
| C2 — 6CWA + 3PG | 6CWA | 3PG re-injected from CIF, NADH still out | 1.77 Å | Tests for 3PG-tolerant (NADH-competitive) binders |
| C3 — 2G76 apo | 2G76 | Independent crystal, D-malate stripped, repacked, longer construct (res 3–314) | 1.7 Å | Tests for conformation-bias artifacts in C1 |
| C4 — 6PLF allosteric pocket | 6PLF → aligned to 6CWA frame | NCT-503-style allosteric site, separate from substrate cleft | 1.7 Å | Second druggable site within the catalytic domain |

Consensus hit = scores top-10% in **C1 ∩ C3** (substrate cleft, robust across two independent backbones).
Mechanism-classified hit = scores top-10% in **C1 but not C2** → likely 3PG-competitive; top-10% in **both C1 and C2** → likely NADH-competitive or peripheral.

### Pocket center

From `pocket_center.json`: (x, y, z) = (9.584, 0.395, 29.832) Å, radius 10 Å in the 6CWA frame. This is the substrate+cofactor cleft (verified: 3PG centroid ≈ (−1, −4, 32), NADH P-A ≈ (12, −1, 33) — both within 10 Å of the center).

Allosteric pocket center: to be derived in Task #14 by aligning 6PLF to 6CWA and computing the centroid of the bound NCT-series ligand atoms.

---

## Compound library (virtual-screen branch)

| Set | Size | Source | Purpose |
|---|---|---|---|
| **DrugBank approved** | ~2,700 | drugbank.com (free academic) | Repurposing candidates |
| **ChEMBL drug-like subset** | ~200k after Lipinski + PAINS filter | ChEMBL 34 SQLite dump | Broader bioactive space |
| **PHGDH positive controls** | ~10 | Literature (NCT-503, BI-4924, CBR-5884, WQ-2101, homoharringtonine, indole-carboxamides) | Sanity-check rankings |
| **TamGen de novo** | ~4,000 (1,000/conformation × 4) | Generated this run | Novel chemistry |

Canonical input format: `data/libraries/{set}.csv` with columns `id,smiles,source`.

---

## Compute architecture (Cosmos / MI300A / ROCm)

- **Login node** (`cosmos02`): conda env creation, repo cloning, structure prep (CPU-only Python work), result inspection. No GPU access.
- **Compute nodes** (cluster partition): all model inference (Boltz-2, TamGen) via SLURM jobs.
- **ROCm**: `/opt/rocm-6.3.0`, `module load rocm/6.3.0`. `PYTORCH_ROCM_ARCH=gfx942` already set.
- **PyTorch ROCm wheels**: follow `evo2-rocm` pattern (`torch 2.5.1+rocm6.2`, `pytorch-triton-rocm 3.1.0`, `flash-attn 2.7.4` — all from PyPI ROCm index).
- **Scratch**: `/ddn_scratch/l1joseph` (only mounted on compute nodes) — use for model weights, intermediate predictions, and large library files. Home directory holds code + final ranked CSVs only.
- **SLURM log discipline** (per global CLAUDE.md): every job script sets `--job-name=<descriptive>`, `--output=$PROJECT_ROOT/logs/%x_%j.out`, `--error=$PROJECT_ROOT/logs/%x_%j.err`, with absolute paths.

---

## Installation

### Boltz-2 (`boltz-rocm` env)

```bash
mamba create -y -n boltz-rocm python=3.11 -c conda-forge
mamba activate boltz-rocm

# PyTorch ROCm wheels (matches evo2-rocm working pattern)
pip install torch==2.5.1+rocm6.2 torchvision==0.20.1+rocm6.2 torchaudio==2.5.1+rocm6.2 \
    --index-url https://download.pytorch.org/whl/rocm6.2

# Boltz from local clone, NO [cuda] extra (cuequivariance is NVIDIA-only)
cd tools/boltz && pip install -e .
```

Verify on a compute node: `torch.cuda.is_available()` returns True (PyTorch-ROCm reuses the `cuda` namespace), `torch.cuda.device_count() == 4` (MI300A APUs).

### TamGen (`tamgen-rocm` env)

Patches required vs. upstream `setup_env.sh`:

```bash
mamba create -y -n tamgen-rocm python=3.9 -c conda-forge
mamba activate tamgen-rocm

# Replace: conda install pytorch==2.3.0 pytorch-cuda=12.1 -c pytorch -c nvidia
# With: PyTorch ROCm wheel (pin to torch 2.3.x for fairseq-0.8.0 compatibility)
pip install torch==2.3.0+rocm6.0 --index-url https://download.pytorch.org/whl/rocm6.0
pip install torch_geometric scipy

# Replace PyG CUDA wheel index with ROCm:
pip install --no-index pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv \
    -f https://data.pyg.org/whl/torch-2.3.0+rocm6.0.html

pip install rdkit==2024.03.1 tensorboardX einops ipykernel

# Vendored fairseq-0.8.0 from repo. Custom CUDA ops (lightconv_cuda, dynamicconv_cuda)
# will fail to build on ROCm — skip by setting NO_CUDA_EXT=1 or by editing setup.py
# to drop the cuda_extensions list. The TamGen transformer LM path does NOT require
# these ops at inference time (verify in smoke test).
cd tools/TamGen && NO_CUDA_EXT=1 python -m pip install -e .[chem]

pip uninstall -y numpy && pip install numpy==1.26.4 pandas
```

Risk: fairseq-0.8.0's custom CUDA ops may have hard-coded `nvcc` invocations. If `setup.py` build_ext can't be bypassed cleanly, fork the build to skip the `cuda_extensions` block. TamGen inference itself uses standard PyTorch ops (transformer + cross-attention), so runtime should work.

---

## Execution phases

Phases gate the next: each must pass success criteria before proceeding.

| Phase | What | Compute | Pass criterion |
|---|---|---|---|
| **0. Setup** | Repos cloned, PDBs downloaded, conda envs built | Login node | Both envs report `torch.cuda.is_available()=True` in a SLURM smoke job |
| **1. Smoke tests** | Boltz-2 minimal example + TamGen pretrained inference on a known input | 1× MI300A APU, ~30 min | Boltz produces valid output structure; TamGen emits parseable SMILES |
| **2. Pose-recovery validation** | Boltz-2 dock BI-4924 into 6RJ6, NCT-cmpd-1 into 6PLF, homoharringtonine into 7EWH | 1× APU, ~1 h | ≥ 3/4 cases: predicted pose RMSD < 2 Å vs crystal |
| **3. Target prep** | Strip ligands, repack side chains (PyRosetta `FastRelax` backbone-fixed OR OpenMM minimize), align 6PLF → 6CWA frame, derive allosteric pocket center | Login node, ~30 min | 4 conformations exported as cleaned PDB; pocket centers in JSON |
| **4. Library staging** | Download DrugBank, filter ChEMBL drug-like, compile positive-control SMILES | Login node | One canonical CSV with ~3k DrugBank entries + 10 positive controls, all RDKit-valid |
| **5. Library screen (Boltz-2)** | Score DrugBank + positive controls vs all 4 conformations | ~1–2 GPU-days on MI300A | Positive controls (BI-4924, NCT-503) in top-1% on the appropriate conformation |
| **6. De novo (TamGen)** | Generate 1,000 SMILES per conformation, RDKit-filter | ~4× 30 min APU | ≥80% valid SMILES, scaffold diversity > 0.7 (Tanimoto) |
| **7. De novo scoring (Boltz-2)** | Score TamGen output across all 4 conformations | ~12 GPU-h | Outputs ranked CSV |
| **8. Consensus + reporting** | Merge rankings, consensus filter (top-10% in C1 ∩ C3), mechanism classification (C1 vs C2), top-50 candidates with predicted complexes | Login node | Ranked report `results/top_hits.{csv,sdf,pdb}` |

Phases 5 and 6 can run in parallel; 7 depends on 6; 2, 5, 7 all depend on 1.

---

## Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| fairseq-0.8.0 CUDA ops block ROCm install | High | Skip via `NO_CUDA_EXT=1` or fork setup.py; verify inference doesn't need them |
| Boltz-2 weights gated / require HuggingFace auth | Medium | Pre-download via login-node `huggingface-cli`; cache to `$SCRATCH` |
| Side-chain repack changes pocket geometry too much | Low | Run dual: with-repack and without-repack as additional sub-condition; compare top hits |
| Boltz-2 affinity calibration unreliable on AMD | Low–medium | Pose-recovery validation (Phase 2) gates further trust; if RMSD bad, drop affinity, keep pose-fit + Vina rescore |
| Compute budget overrun on full ChEMBL drug-like | Medium | Cap at 50k for first pass; expand only if positive controls behave |
| MI300A flash-attn / triton-rocm kernel mismatch with Boltz's attention modules | Medium | Boltz's attention is standard SDPA; should fall through to PyTorch built-in. Confirm in smoke test. |

---

## Directory layout

```
Alzheimers_Drug_Discovery/
├── PLAN.md                      # this file
├── 6CWA_chainA_clean.pdb        # original cleaned input (kept)
├── 6CWA.cif
├── pocket_center.json           # substrate cleft center, 6CWA frame
├── pocket_center_allosteric.json  # NCT-503 site center, derived
├── tamgen_input.csv
├── tools/
│   ├── boltz/                   # cloned, installed in boltz-rocm
│   └── TamGen/                  # cloned, installed in tamgen-rocm
├── data/
│   ├── structures/              # 7 PHGDH CIFs (downloaded)
│   ├── targets/                 # prepared PDBs per conformation
│   │   ├── phgdh_6CWA_apo.pdb
│   │   ├── phgdh_6CWA_3pg.pdb
│   │   ├── phgdh_2G76_apo.pdb
│   │   └── pocket_centers.json
│   └── libraries/
│       ├── drugbank_approved.csv
│       ├── chembl_druglike.csv
│       └── phgdh_positive_controls.csv
├── slurm/                       # SLURM job scripts
│   ├── boltz_smoke.sh
│   ├── tamgen_smoke.sh
│   ├── pose_recovery.sh
│   ├── library_screen.sh
│   └── tamgen_generate.sh
├── logs/                        # SLURM logs (gitignored except .gitkeep)
└── results/
    ├── pose_recovery.csv
    ├── library_screen_<conf>.csv
    ├── tamgen_<conf>.csv
    └── top_hits.{csv,sdf,pdb}   # final consensus output
```

---

## Open questions deferred (not blocking execution)

1. **Allosteric site definition**: NCT-503 isn't directly co-crystallized in our PDB set; we use the related 6PLF compound 1 as proxy. If the allosteric branch produces no good hits, revisit by finding a true NCT-503 co-crystal or running mutation-based pocket prediction.
2. **Top-hit MD refinement**: After consensus ranking, the top-20 may warrant short OpenMM MD + MM-GBSA rescoring. Not in initial scope; queue for follow-up if results are promising.
3. **Wet-lab validation handoff**: Out of scope for this pipeline. Output format (SDF with predicted poses + affinity) is set up to be directly orderable from Enamine / synthesizable.
