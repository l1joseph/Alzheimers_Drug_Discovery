"""Split a directory of Boltz YAML inputs into N sub-shards.

Used to deterministically partition a screen for a job-array × multi-APU run:
N = (num array tasks) * (APUs per node), so each (task, APU) pair takes one shard.

Files are assigned round-robin by sorted name — keeps the work balanced.

Usage:
    python scripts/split_yamls.py --in data/libraries/chembl_yamls \
                                  --out-base /scratch/chembl_yamls_split \
                                  --n 16
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="src", required=True)
    p.add_argument("--out-base", required=True, help="created if missing; existing shard subdirs WIPED")
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--mode", choices=["symlink", "copy"], default="symlink")
    args = p.parse_args()

    src = Path(args.src).resolve()
    out_base = Path(args.out_base).resolve()
    out_base.mkdir(parents=True, exist_ok=True)

    yamls = sorted(src.glob("*.yaml"))
    if not yamls:
        raise SystemExit(f"no yamls in {src}")

    # wipe existing shard subdirs
    for d in out_base.glob("shard_*"):
        if d.is_dir():
            shutil.rmtree(d)

    shards = [out_base / f"shard_{i:02d}" for i in range(args.n)]
    for d in shards:
        d.mkdir()

    for i, yml in enumerate(yamls):
        dst = shards[i % args.n] / yml.name
        if args.mode == "symlink":
            os.symlink(yml, dst)
        else:
            shutil.copy(yml, dst)

    counts = [len(list(d.glob('*.yaml'))) for d in shards]
    print(f"split {len(yamls)} yamls -> {args.n} shards")
    print(f"  min/max per shard: {min(counts)} / {max(counts)}")
    print(f"  shard dirs in: {out_base}")


if __name__ == "__main__":
    main()
