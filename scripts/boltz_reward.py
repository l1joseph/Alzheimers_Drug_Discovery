"""Boltz-2 reward function for REINVENT (ExternalProcess scoring component).

Architecture:
  REINVENT pipes SMILES via stdin (one per line)
  -> we build Boltz YAMLs per SMILES
  -> we dispatch Boltz scoring across the parent SLURM allocation via srun
     (NB: this script MUST be invoked from inside an sbatch job that owns
      $SLURM_JOB_ID with multiple nodes + APUs)
  -> we parse affinity_pred_value from per-prediction JSON
  -> we apply the composite reward (see scripts/composite_reward.py)
  -> we emit JSON to stdout: [score_0, score_1, ..., score_n-1]

Reward composition (from composite_reward.py):
  hard_reject (reward=0) if invalid SMILES, PAINS/Brenk hit, or SA>7
  else reward = 0.45*sigmoid(-aff_C1) + 0.20*QED + 0.15*sigmoid(6-SA)
              + 0.10*MW_window + 0.05*logP_window + 0.05*mech_bonus

Usage (REINVENT TOML):
  [[stage.scoring.component]]
  [stage.scoring.component.ExternalProcess]
  endpoint = [{ name="boltz_reward", weight=1.0 }]
  params = [{ executable="/path/to/conda", args="run -n reinvent-rocm python /path/boltz_reward.py", property="reward" }]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

PROJECT = Path("/cosmos/nfs/home/l1joseph/Alzheimers_Drug_Discovery")
sys.path.insert(0, str(PROJECT / "scripts"))
from composite_reward import score_smiles as _score_one  # noqa: E402

SCRATCH = Path("/cosmos/vast/scratch/l1joseph")
TARGET_PDB = PROJECT / "data" / "targets" / "phgdh_6CWA_apo.pdb"
TARGET_FASTA = PROJECT / "data" / "phgdh_6CWA_chainA.fasta"
TARGET_MSA = PROJECT / "data" / "msa" / "phgdh_6CWA_chainA.a3m"
BOLTZ_CACHE = SCRATCH / "boltz_cache"

# Step counter persisted in scratch (so each RL step gets a unique dir)
STEP_FILE = SCRATCH / "reinvent_rl_step.txt"


def next_step() -> int:
    if STEP_FILE.exists():
        n = int(STEP_FILE.read_text().strip()) + 1
    else:
        n = 0
    STEP_FILE.write_text(str(n))
    return n


def read_fasta(p: Path) -> str:
    seq = []
    for line in p.read_text().splitlines():
        if not line.startswith(">"):
            seq.append(line.strip())
    return "".join(seq)


def build_yaml(smi: str, lid: str, out_path: Path, seq: str, msa_path: Path):
    """Write a single Boltz YAML for one SMILES."""
    import yaml as _yaml
    body = {
        "version": 1,
        "sequences": [
            {"protein": {"id": "A", "sequence": seq, "msa": str(msa_path)}},
            {"ligand": {"id": "B", "smiles": smi}},
        ],
        "properties": [{"affinity": {"binder": "B"}}],
    }
    with open(out_path, "w") as f:
        _yaml.safe_dump(body, f, default_flow_style=False, sort_keys=False, width=200)


def score_batch_with_sbatch(yaml_dir: Path, out_dir: Path) -> dict:
    """Submit a 1-node sbatch (4 APUs, ~5 min for batch=64) and wait for completion.

    Uses sbatch --wait so this call blocks until the scoring job finishes.
    Re-uses the existing boltz_array_screen.sh infrastructure (a single
    array task = 1 node = 4-APU fan-out via HIP_VISIBLE_DEVICES).
    """
    # Pre-split the YAMLs into 4 shards (one per APU)
    project = PROJECT
    n_shards = 4
    split_dir = yaml_dir.parent / "split"
    split_dir.mkdir(exist_ok=True)
    # Wipe existing shards
    for d in split_dir.glob("shard_*"):
        for f in d.glob("*"):
            f.unlink()
        d.rmdir()
    for i in range(n_shards):
        (split_dir / f"shard_{i:02d}").mkdir()

    yamls = sorted(yaml_dir.glob("*.yaml"))
    for i, y in enumerate(yamls):
        link = split_dir / f"shard_{i % n_shards:02d}" / y.name
        if not link.exists():
            link.symlink_to(y)

    # Run sbatch --wait
    label = out_dir.name
    cmd = [
        "sbatch", "--wait",
        "--job-name", f"reinvent-step-{label}",
        "--array=0-0",
        f"--export=ALL,YAML_SPLIT_DIR={split_dir},RUN_LABEL=rl_{label}",
        str(project / "slurm" / "boltz_array_screen.sh"),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    print(f"[step] sbatch exit={res.returncode}; stdout={res.stdout.strip()}", file=sys.stderr)
    if res.returncode != 0:
        print(f"[step] sbatch stderr: {res.stderr[:500]}", file=sys.stderr)

    # Look for outputs under SCRATCH/runs/boltz_rl_<label>_*
    scores = {}
    for run_root in sorted(SCRATCH.glob(f"runs/boltz_rl_{label}_*")):
        for pred_dir in run_root.rglob("predictions"):
            for cand in pred_dir.iterdir():
                if not cand.is_dir():
                    continue
                aff_json = cand / f"affinity_{cand.name}.json"
                if aff_json.exists():
                    try:
                        d = json.loads(aff_json.read_text())
                        scores[cand.name] = float(d.get("affinity_pred_value", 0.0))
                    except (json.JSONDecodeError, ValueError):
                        scores[cand.name] = None
    return scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-apus", type=int, default=16,
                    help="parallel APU budget; only used if running outside SLURM (smoke test mode)")
    ap.add_argument("--mock", action="store_true",
                    help="skip Boltz entirely; use random affinity for testing the wrapper")
    args, smiles_args = ap.parse_known_args()

    # REINVENT ExternalProcess passes SMILES via stdin (one per line)
    smiles = [line.strip() for line in sys.stdin if line.strip()]
    # Some REINVENT variants pass via argv instead — handle both
    if not smiles and smiles_args:
        smiles = [s for s in smiles_args if s]

    if not smiles:
        print(json.dumps({"version": 1, "payload": {"reward": []}}))
        return

    step = next_step()
    step_dir = SCRATCH / "reinvent_rl" / f"step_{step:04d}_{uuid.uuid4().hex[:6]}"
    yaml_dir = step_dir / "yamls"
    out_dir = step_dir / "out"
    yaml_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mock:
        # For smoke testing: skip Boltz, use random affinities
        import random
        affs = {f"lig_{i:03d}": random.uniform(-2.0, 1.0) for i in range(len(smiles))}
    else:
        # Build YAMLs
        seq = read_fasta(TARGET_FASTA)
        for i, smi in enumerate(smiles):
            lid = f"lig_{i:03d}"
            build_yaml(smi, lid, yaml_dir / f"{lid}.yaml", seq, TARGET_MSA)
        # Score via sbatch --wait
        affs = score_batch_with_sbatch(yaml_dir, out_dir)

    # Compute composite reward per SMILES
    rewards = []
    for i, smi in enumerate(smiles):
        lid = f"lig_{i:03d}"
        aff = affs.get(lid)
        if aff is None:
            rewards.append(0.0)  # missing -> hard reject
            continue
        rewards.append(_score_one(smi, aff)["reward"])

    # Emit REINVENT-compatible JSON
    payload = {"version": 1, "payload": {"reward": rewards}}
    print(json.dumps(payload))

    # Persist a per-step CSV for post-hoc analysis
    import csv
    csv_path = step_dir / "scores.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["smiles", "boltz_aff", "reward"])
        for smi, r in zip(smiles, rewards):
            aff_i = affs.get(f"lig_{smiles.index(smi):03d}")
            w.writerow([smi, aff_i, r])


if __name__ == "__main__":
    main()
