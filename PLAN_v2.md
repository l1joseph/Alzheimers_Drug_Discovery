# PLAN v2 — extending the PHGDH pipeline with library screen + RL closed-loop

## Context

Plan v1 (`PLAN.md`) is wrapped: TamGen scaffold-seeded design + Boltz-2 scoring across 887 candidates, iterative loop plateaued at b2_067 (aff −1.59), Round-1 best ≈ Round-2 best (same molecule rediscovered). Plan v2 picks up two open threads:

1. **Library virtual screen** — never executed for v1's "Branch A" because DrugBank free academic download was unavailable. **ChEMBL 34** is the substitute (no signup, fully open, better-curated for bioactives anyway).
2. **A different generation tool** — TamGen's pure pocket-conditional sampling plateaued. **REINVENT closed-loop RL** uses Boltz directly as the reward, giving a gradient signal toward the actual scoring objective, with a composite reward that also enforces drug-likeness (so we don't repeat the b2_067 PAINS-hit failure mode).

Plus three independent validation layers (orthogonal rescore, multi-conformation robustness, selectivity counter-screen) that strengthen confidence in the final top hits regardless of whether new generation breaks the −1.79 ceiling.

## Hard compute budget

- **Up to 4 nodes** (16 MI300A APUs) simultaneously
- **Wall-clock deadline: 08:00 tomorrow** (~12 h available)
- Total budget: ~192 APU-hours

At ~25 s per Boltz call, that's ~27 600 Boltz scorings possible if we keep the GPUs full.

## Composite reward (replaces single-objective Boltz score)

The b2_067 failure mode was Boltz-only optimization: aff −1.59 but logP 7.1, MW 558, PAINS hit. REINVENT will use:

```
hard_reject if:
    Chem.MolFromSmiles(smi) is None        # invalid
    PAINS or Brenk filter hit              # known false-positive pattern
    SA_score > 7                           # unsynthesizable

else reward =
    0.45 * sigmoid(-affinity_C1)           # primary: Boltz binding strength
  + 0.20 * QED                              # composite druglikeness (Bickerton)
  + 0.15 * sigmoid(6 - SA_score)            # synthesizable
  + 0.10 * MW_window(150, 500)              # Lipinski
  + 0.05 * logP_window(-1, 5)               # Lipinski / solubility
  + 0.05 * mechanism_bonus                  # 1 - |Δaff C2 vs C1|, NADH-competitive favored
```

## Timeline within the 12-hour window

Order chosen to maximise expected payoff within the deadline. Items run in parallel where independent.

| Block | Time | What | Compute | Risk if delayed |
|---|---|---|---|---|
| **A** | T+0:00 → 0:30 | ChEMBL: filter chemreps.txt.gz to drug-like (3-5k cpds), build Boltz YAMLs | Login CPU | None |
| **B** | T+0:30 → 2:30 | ChEMBL Boltz screen via 4-node array | 4 nodes × 4 APU | Cluster contention may push out |
| **C** | parallel to B, T+0:30 → 4:30 | REINVENT install + smoke test composite reward (no RL yet) | Login CPU + 1 APU smoke | **Highest install risk** — fall back to gen-engine bake-off if REINVENT won't build on ROCm |
| **D** | T+4:30 → 10:30 | REINVENT RL: 200 steps × 64-batch composite reward, 4-node Boltz array as inner-loop scorer | 4 nodes × 4 APU | If C slips, downgrade to "TamGen B1-Round-2" as fallback novel-gen (NCT-503 sibling of B2-R2) |
| **E** | parallel, anytime CPU-free | Orthogonal MM-GBSA + Vina rescore of top-50 | Login CPU | Low — independent layer |
| **F** | T+10:30 → 11:30 | Multi-conformation robustness: top-20 × {6RJ6, 6PLF, 6RJ3, 2G76} | 1-2 nodes × 4 APU | Skip if cluster jammed |
| **G** | T+11:30 → 12:00 | Selectivity counter-screen: top-10 × {LDH-A, MDH2, GAPDH, IDH1} | 1 node × 4 APU | Skip if no time |
| **H** | final, ≤ 08:00 | Refresh `results/final/top50.csv` with all signals; commit + push | Login CPU | Must happen |

## Block-by-block detail

### A — ChEMBL filter (CPU, 30 min)

- Input: `chembl_34_chemreps.txt.gz` (≈50 MB, downloading now to `/cosmos/vast/scratch/l1joseph/chembl/`)
- Filter pipeline (`scripts/filter_chembl.py`):
  - Canonical SMILES via RDKit
  - Lipinski-passing (MW 150–500, logP < 5, HBD ≤ 5, HBA ≤ 10)
  - No PAINS / Brenk pattern hit
  - SA score < 6
- Optional richer filter (needs SQLite, 6 GB also downloading): restrict to compounds with measured activity against any human oxidoreductase / dehydrogenase. Significantly enriches for relevant chemistry.
- Output: `data/libraries/chembl_druglike.csv` with `id, smiles, source, [activity_data]`
- Expected size: 3–8k compounds depending on activity-data filter

### B — ChEMBL Boltz screen (2 h on 4-node array)

- Build YAMLs (same canonical PHGDH MSA we already have cached)
- Submit single `sbatch --array=0-3 slurm/boltz_array_score.sh data/libraries/chembl_yamls chembl` (new script — array-aware version of `boltz_screen.sh`)
- Each task fans 4 APUs via HIP_VISIBLE_DEVICES (proven pattern from `tamgen_b1_scaffold.sh`)
- At 25 s/lig × 5k cpds / 16 APUs = ~2.2 h
- Results merge into `results/combined/all_rounds.csv` automatically (build_leaderboard.py flock-guarded)

### C — REINVENT install + smoke test (parallel to B, on login node)

- `git clone https://github.com/MolecularAI/REINVENT3.0` (or v4 if available)
- New conda env `reinvent-rocm` (Python 3.10, PyTorch ROCm 6.2, RDKit, REINVENT deps)
- Smoke test: composite reward on 100 random SMILES (no RL yet) — verify Boltz array call works as a scorer plugin
- **Failure mode**: if REINVENT install hits a hard CUDA-only dep we can't patch in <2 h, abort and substitute Block D with:
  - `tamgen_b1_round2.sh` — sibling of the B2-R2 we ran; iterate NCT-503 family. Same architecture, no install risk.

### D — REINVENT RL loop (6 h with 4-node array)

- Batch 64 SMILES/step, 200 RL steps = 12 800 Boltz calls
- Inner-loop scoring via `slurm/reinvent_batch_score.sh` (array job)
  - Step writes batch to scratch
  - Submits 4-node array, fans 4 APUs per node
  - 64 SMILES / 16 APUs / 25 s = ~1.7 min wall per step
  - + REINVENT policy update overhead ~30 s/step
  - Total: 200 × 2 min ≈ 6.7 h
- Composite reward applied as above; surrogate not needed because we have the budget
- Final ~50 top-reward SMILES re-scored with real Boltz + posted via build_leaderboard.py

### E — Orthogonal MM-GBSA / Vina (parallel, CPU-only)

- Independent of GPU contention; runs whenever the login node is free
- For each top-50 hit's existing Boltz-predicted complex CIF:
  - AutoDock Vina re-dock (CPU, ~30 s/lig × 50 ≈ 25 min)
  - MM-GBSA single-point on the Vina pose (OpenMM Amber14 + obc2 implicit solvent, ~5 min/lig × 50 ≈ 4 h)
- Output: `results/orthogonal_rescore.csv` — `id, vina_kcal, mmgbsa_dG, agreement_with_boltz`

### F — Multi-conformation robustness (1 h, 1-2 nodes)

- For top-20 by composite reward: build Boltz YAMLs for {6RJ6, 6PLF, 6RJ3, 2G76} backbones (their cached MSAs already exist in `data/msa/`)
- 20 × 4 = 80 predictions @ 25 s on 4 APUs ≈ 8 min wall (with 1 node), 2 min (with 4 nodes)
- Compute robustness metric: stdev(affinity) across conformations
- Robust hits (stdev < 0.5 logKd) get a flag in final report

### G — Selectivity counter-screen (30 min, 1 node)

- UniProt FASTAs for off-targets:
  - LDH-A (P00338)
  - MDH2 (P40926)
  - GAPDH (P04406)
  - IDH1 (O75874)
- Fetch each MSA via `scripts/fetch_msa.py` (parallel)
- Score top-10 PHGDH hits × 4 off-targets = 40 predictions ≈ 4 min wall on 4 APUs
- Selectivity index = aff(PHGDH) − aff(off-target). Generic Rossmann binders flagged.

### H — Final refresh (30 min, CPU)

- Regenerate `results/final/top50.csv`, `.sdf`, `.md` with:
  - Composite reward columns
  - Vina + MM-GBSA scores
  - Multi-conformation stdev
  - Selectivity index
- Commit + push
- Optional: PR comment / Slack ping summarising delta vs v1

## Fallbacks if blocks slip

| Block at risk | Fallback |
|---|---|
| C (REINVENT install) | Drop to D' = TamGen B1 Round-2 — proven pipeline, ~1 GPU-h |
| B (ChEMBL screen) | Reduce filter to clinical-trial subset only (≤ 500 cpds) → 20 min |
| Cluster all 4 nodes unavailable | Run blocks serially on fewer nodes; D shrinks to 100 RL steps |
| All else | At minimum: do A + E + F + G + H — orthogonal/robustness layer of existing top-50 |

## Acceptance criteria for "shipped v2"

By 08:00 tomorrow, `results/final/top50.csv` must include columns for at least:
- `affinity_C1` ✓ (already exists)
- `MM_GBSA_dG` (new)
- `vina_score` (new)
- `selectivity_index` (new)
- `multi_conformation_stdev` (new)
- `chembl_screen_rank` (new) — where the candidate sits relative to ChEMBL hits
- `source` extended to include `reinvent_rl` if Block D succeeded

Anything missing is acceptable as long as it's clearly noted in `results/final/top50.md`.

## Critical paths

1. **Most expected value: Block B** (ChEMBL screen). It's the missing Branch A from v1 and tests whether existing-drug repurposing finds anything competitive with our designed hits. Most likely to surface a real candidate.
2. **Highest variance: Block D** (REINVENT RL). Could break the −1.79 ceiling or could fail at install. Worth the swing if Block B is rolling cleanly.
3. **Floor**: Blocks E + F + G alone harden the v1 hits enough to justify the report even if generation produces nothing new.
