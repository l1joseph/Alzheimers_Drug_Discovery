# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Design a small molecule to target PHGDH's DNA-binding domain (NAD binding site) to inhibit its transcriptional activity in Alzheimer's disease. The target timeline is ~3 weeks for actionable results.

**Biological context**: PHGDH drives amyloid pathology in Alzheimer's disease via DNA binding and transcriptional activation — inhibiting this non-metabolic function (without disrupting its essential enzymatic role) is the therapeutic hypothesis. NCT-503 is a known reference compound that blocks PHGDH's damaging activity.

## Planned Pipeline

The computational workflow follows a generate → score → filter loop:

1. **Structure acquisition** — obtain/predict 3D structure of PHGDH's DNA-binding/NAD-binding domain (PDB or AlphaFold2)
2. **Molecule generation** — use TamGen or LPT to generate SMILES conditioned on the binding pocket
3. **Affinity scoring** — use Boltz-2 to predict small molecule–protein binding affinity
4. **Filtering** — apply drug-likeness filters: QED, Lipinski's Rule of Five, SAS (synthetic accessibility), LogP, PAINS filters, ≤50 heavy atoms
5. **Comparison** — benchmark candidates against NCT-503 as the reference inhibitor

## Key Tools (from Reference Papers)

### Boltz-2
- Foundation model for biomolecular structure prediction **and** binding affinity prediction
- ~1000× faster than FEP; approaches FEP accuracy on benchmarks (CASP16 affinity track)
- Supports: protein-ligand, protein-DNA, antibody-antigen, multi-chain complexes
- Affinity values standardized to log₁₀ scale (µM); input formats: PDB structures + SMILES/SDF
- Code & weights: `github.com/jwohlwend/boltz` (open-source, permissive license)
- Recommended use: score generated candidates and rank by predicted affinity

### TamGen (Nature Communications 2024)
- GPT-like chemical language model; three modules: compound decoder (pretrained on 10M PubChem SMILES), protein encoder (Transformer with geometric self-attention on binding pocket), VAE-based contextual encoder for compound refinement
- Input: protein binding pocket (3D structure) + optional seed compound → Output: SMILES strings
- Generates 100 compounds in ~9 seconds on A6000; Design-Refine-Test loop supports iterative optimization
- Benchmarked on CrossDocked2020; evaluated by: docking score (AutoDock-Vina), QED, SAS, Lipinski RO5, LogP, Tanimoto diversity

### Latent Prompt Transformer / LPT (NeurIPS 2024)
- Three components: (1) learnable latent prior (neural transform of Gaussian noise), (2) causal Transformer molecule generator using latent vector as cross-attention prompt, (3) property predictor MLP
- Trained end-to-end via MLE on molecule–property pairs; online learning algorithm progressively shifts distribution toward desired properties
- **Directly relevant**: LPT paper includes a PHGDH NAD-binding-site task as a benchmark — conditional generation targeting this exact pocket
- Supports single-objective, multi-objective, and structure-constrained optimization
- Project page: `sites.google.com/view/latent-prompt-transformer`

## Molecule Representation

All generative models use **SMILES** strings as the molecular representation. Docking and affinity scoring require 3D coordinates, typically generated from SMILES via RDKit or similar tools. Binding affinity regression values (Kᵢ, K_d, IC₅₀, AC₅₀, EC₅₀) are on a log₁₀ µM scale.

## Hardware Context

NVIDIA RTX A6000 and H100 GPUs are the target compute platform (matching what was used in the Cell paper developing this line of research).

## Evaluation Metrics

When assessing generated candidates, report all of the following:
- **Boltz-2 predicted affinity** (log₁₀ µM, lower = better binder)
- **AutoDock-Vina docking score** (kcal/mol, more negative = better)
- **QED** (drug-likeness, 0–1, higher = better)
- **SAS** (synthetic accessibility, 1–10, lower = easier to synthesize)
- **Lipinski RO5** pass/fail
- **LogP** (0–5 target range for oral bioavailability)
- **Tanimoto similarity** to NCT-503 (reference compound)
- **Heavy atom count** (≤50 filter per Boltz-2 training data constraint)
