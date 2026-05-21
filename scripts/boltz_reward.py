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


def score_batch_with_srun(yaml_dir: Path, out_dir: Path, n_apus: int) -> dict:
    """Run boltz predict via srun in the parent allocation.

    We split YAMLs across APUs by creating sub-dirs and launching one Boltz
    process per APU in parallel using srun.
    """
    job_id = os.environ.get("SLURM_JOB_ID")
    if not job_id:
        raise RuntimeError("must run inside sbatch (SLURM_JOB_ID not set)")
    n_apus_per_node = 4
    n_nodes = int(os.environ.get("SLURM_NNODES", "1"))
    total_apus = n_nodes * n_apus_per_node

    yamls = sorted(yaml_dir.glob("*.yaml"))
    if not yamls:
        return {}

    # Round-robin into total_apus shards
    shards = [[] for _ in range(total_apus)]
    for i, y in enumerate(yamls):
        shards[i % total_apus].append(y)

    # Stage shards into per-(node,apu) dirs
    procs = []
    for global_apu_idx, shard in enumerate(shards):
        if not shard:
            continue
        node_idx = global_apu_idx // n_apus_per_node
        local_apu = global_apu_idx % n_apus_per_node
        sd = out_dir / f"shard_{global_apu_idx:02d}"
        sd.mkdir(parents=True, exist_ok=True)
        shard_in = out_dir / f"in_shard_{global_apu_idx:02d}"
        shard_in.mkdir(parents=True, exist_ok=True)
        for y in shard:
            (shard_in / y.name).symlink_to(y) if not (shard_in / y.name).exists() else None
        # Launch boltz via srun pinned to (node, apu)
        cmd = [
            "srun", "--jobid", job_id, "--exclusive",
            "--nodes=1", "--ntasks=1",
            f"--nodelist={os.environ.get('SLURM_JOB_NODELIST').split(',')[node_idx]}" if "," in os.environ.get("SLURM_JOB_NODELIST", "") else "",
            "bash", "-c",
            f"HIP_VISIBLE_DEVICES={local_apu} "
            f"boltz predict {shard_in} --use_msa_server --no_kernels "
            f"--cache {BOLTZ_CACHE} --out_dir {sd} --output_format mmcif "
            f"--accelerator gpu --devices 1",
        ]
        cmd = [c for c in cmd if c]
        log = sd / "boltz.log"
        p = subprocess.Popen(cmd, stdout=open(log, "w"), stderr=subprocess.STDOUT)
        procs.append((p, sd, shard))

    for p, _, _ in procs:
        p.wait()

    # Collect affinity_pred_value from each per-yaml output dir
    scores = {}
    for _, sd, shard in procs:
        # Boltz writes predictions under sd/boltz_results_*/predictions/<id>/affinity_<id>.json
        for pred_root in sd.glob("boltz_results_*/predictions"):
            for cand in pred_root.iterdir():
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
        # Score via srun
        affs = score_batch_with_srun(yaml_dir, out_dir, args.n_apus)

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
