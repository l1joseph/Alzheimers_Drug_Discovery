"""Composite reward function for REINVENT4 closed-loop RL with Boltz-2 as oracle.

Reward formula (from PLAN_v2 v2 plan, Block D):

    reward = 0.45 * sigmoid(-aff)
           + 0.20 * QED
           + 0.15 * sigmoid(6 - SA)
           + 0.10 * MW_window
           + 0.05 * logP_window
           + 0.05 * mechanism_bonus

    hard_reject if PAINS or Brenk hit, or SA > 7.

Components:
  - aff:           Boltz-2 affinity prediction (lower = stronger; sigmoid(-aff)
                   maps strong binders -> ~1, weak -> ~0). For the smoke test
                   `aff` is mocked via random.uniform(-2, 2). Real integration
                   comes in Block D.
  - QED:           RDKit Quantitative Estimate of Drug-likeness, [0, 1].
  - SA:            Ertl & Schuffenhauer 2009 synthetic accessibility (1=easy,
                   10=hard). Pulled via rdkit.Contrib.SA_Score.sascorer.
  - MW_window:     trapezoidal window centered on 300-500 Da, drops to 0
                   below 200 / above 600.
  - logP_window:   trapezoidal centered on 1-4, drops to 0 below 0 / above 5.
  - mechanism_bonus: domain-specific tag indicating the molecule contains a
                   recognised PHGDH-binding warhead motif (currently a small
                   SMARTS panel; intended as a placeholder that can be swapped
                   for a learned classifier later).

CLI usage (smoke test):
  python composite_reward.py --smiles-file <file> --n 50 --seed 42 --out <csv>

If --smiles-file is omitted, a built-in 50-SMILES test panel pulled from
data/libraries/chembl_druglike.csv (deterministic via seed) is used.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from pathlib import Path
from typing import Iterable

from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, Descriptors, QED
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams

RDLogger.DisableLog("rdApp.*")

# SA score via RDKit Contrib script
import rdkit
_rdkit_root = Path(rdkit.__file__).resolve().parent
sys.path.insert(0, str(_rdkit_root / "Contrib" / "SA_Score"))
import sascorer  # noqa: E402


# ---------- component functions ---------- #

def sigmoid(x: float) -> float:
    """Numerically stable logistic sigmoid."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def trapezoidal_window(value: float, lo_zero: float, lo_one: float,
                       hi_one: float, hi_zero: float) -> float:
    """Trapezoidal membership function.

    Returns 0.0 below lo_zero or above hi_zero, 1.0 between lo_one and hi_one,
    and linearly interpolates on the shoulders.
    """
    if value <= lo_zero or value >= hi_zero:
        return 0.0
    if lo_one <= value <= hi_one:
        return 1.0
    if value < lo_one:
        return (value - lo_zero) / (lo_one - lo_zero)
    return (hi_zero - value) / (hi_zero - hi_one)


def mw_window(mw: float) -> float:
    """MW reward window: 1.0 on [300, 500], 0 outside [200, 600]."""
    return trapezoidal_window(mw, 200.0, 300.0, 500.0, 600.0)


def logp_window(logp: float) -> float:
    """logP reward window: 1.0 on [1, 4], 0 outside [0, 5]."""
    return trapezoidal_window(logp, 0.0, 1.0, 4.0, 5.0)


# Mechanism bonus: SMARTS patterns characteristic of PHGDH NAD-pocket binders.
# These are placeholders pulled from inspecting the known-binder set
# (data/libraries/known_phgdh_binders.csv). Hit -> bonus = 1.0.
_PHGDH_WARHEAD_SMARTS = [
    "[c]1ccc2[nH]ncc2c1",                # indazole core (CBR-5884-like)
    "c1ccc(cc1)C(=O)N[C@H](CO)c2ccc(cc2)S(=O)(=O)",  # BI-4924-style sulfone-amide
    "c1cc2c(cc1)n(C)c(c2)C(=O)N",        # methyl-indole carboxamide
    "c1nn(C)c(c1)C(=O)N",                # pyrazole carboxamide (BI-cmpd-15)
]


def mechanism_bonus(mol: Chem.Mol) -> float:
    """Return 1.0 if mol matches any PHGDH warhead SMARTS, else 0.0."""
    for smarts in _PHGDH_WARHEAD_SMARTS:
        patt = Chem.MolFromSmarts(smarts)
        if patt is not None and mol.HasSubstructMatch(patt):
            return 1.0
    return 0.0


# ---------- filter catalog (singleton) ---------- #

_FILTER_CATALOG: FilterCatalog | None = None


def _get_filter_catalog() -> FilterCatalog:
    global _FILTER_CATALOG
    if _FILTER_CATALOG is None:
        params = FilterCatalogParams()
        params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS)
        params.AddCatalog(FilterCatalogParams.FilterCatalogs.BRENK)
        _FILTER_CATALOG = FilterCatalog(params)
    return _FILTER_CATALOG


# ---------- main scoring ---------- #

def score_smiles(smiles: str, aff: float) -> dict:
    """Compute the composite reward for a single SMILES + affinity pair.

    Returns a dict with the reward, all components, hard_reject flag, and the
    underlying properties (for downstream logging).
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {
            "smiles": smiles, "valid": False, "reward": 0.0, "hard_reject": True,
            "reject_reason": "invalid_smiles",
        }

    try:
        sa = sascorer.calculateScore(mol)
    except Exception:
        sa = None
    qed = QED.qed(mol)
    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)

    catalog = _get_filter_catalog()
    # `HasMatch` is faster than `GetMatches` and we don't care which catalog
    # hit fired — both PAINS and BRENK hits trigger hard reject.
    any_hit = catalog.HasMatch(mol)

    # Components
    aff_term = sigmoid(-aff)
    sa_term = sigmoid(6.0 - sa) if sa is not None else 0.0
    mw_term = mw_window(mw)
    logp_term = logp_window(logp)
    mech_term = mechanism_bonus(mol)

    reward = (
        0.45 * aff_term
        + 0.20 * qed
        + 0.15 * sa_term
        + 0.10 * mw_term
        + 0.05 * logp_term
        + 0.05 * mech_term
    )

    hard_reject = False
    reject_reason = ""
    if any_hit:
        hard_reject = True
        reject_reason = "pains_or_brenk"
    elif sa is not None and sa > 7.0:
        hard_reject = True
        reject_reason = "sa_gt_7"

    if hard_reject:
        reward = 0.0

    return {
        "smiles": smiles,
        "valid": True,
        "aff_input": aff,
        "qed": qed,
        "sa": sa if sa is not None else float("nan"),
        "mw": mw,
        "logp": logp,
        "pains_or_brenk_hit": any_hit,
        "aff_term": aff_term,
        "sa_term": sa_term,
        "mw_term": mw_term,
        "logp_term": logp_term,
        "mech_term": mech_term,
        "qed_term": qed,
        "hard_reject": hard_reject,
        "reject_reason": reject_reason,
        "reward": reward,
    }


def score_batch(smiles_list: Iterable[str], affs: Iterable[float]) -> list[dict]:
    return [score_smiles(s, a) for s, a in zip(smiles_list, affs)]


# ---------- smoke-test driver ---------- #

DEFAULT_TEST_PANEL_CSV = Path(__file__).resolve().parent.parent / \
    "data/libraries/chembl_druglike.csv"


def load_smiles_panel(n: int, seed: int,
                      smiles_file: Path | None = None) -> list[str]:
    """Load a deterministic SMILES test panel for the smoke test."""
    if smiles_file is None:
        smiles_file = DEFAULT_TEST_PANEL_CSV

    smiles: list[str] = []
    with open(smiles_file) as fh:
        reader = csv.DictReader(fh)
        if "smiles" not in reader.fieldnames:
            raise ValueError(
                f"input file {smiles_file} missing 'smiles' column "
                f"(found: {reader.fieldnames})"
            )
        for row in reader:
            s = row.get("smiles", "").strip()
            if s:
                smiles.append(s)

    rng = random.Random(seed)
    rng.shuffle(smiles)
    return smiles[:n]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--smiles-file", type=Path, default=None,
                    help="CSV with a 'smiles' column (default: chembl_druglike.csv)")
    ap.add_argument("--n", type=int, default=50,
                    help="number of SMILES to score (default: 50)")
    ap.add_argument("--seed", type=int, default=42,
                    help="random seed for shuffling + mock affinities")
    ap.add_argument("--out", type=Path, default=None,
                    help="optional CSV path to write per-SMILES scores")
    ap.add_argument("--mock-aff-low", type=float, default=-2.0)
    ap.add_argument("--mock-aff-high", type=float, default=2.0)
    args = ap.parse_args()

    smiles = load_smiles_panel(args.n, args.seed, args.smiles_file)
    rng = random.Random(args.seed)
    affs = [rng.uniform(args.mock_aff_low, args.mock_aff_high) for _ in smiles]
    rows = score_batch(smiles, affs)

    n_valid = sum(1 for r in rows if r.get("valid"))
    n_reject = sum(1 for r in rows if r.get("hard_reject"))
    rewards = [r["reward"] for r in rows]
    print(f"scored {len(rows)} SMILES "
          f"({n_valid} valid, {n_reject} hard-rejected)")
    if rewards:
        print(f"reward stats: min={min(rewards):.3f} "
              f"max={max(rewards):.3f} mean={sum(rewards)/len(rewards):.3f}")

    # Sanity checks (smoke test assertions)
    assert all("reward" in r for r in rows), "missing reward column"
    assert all(0.0 <= r["reward"] <= 1.0 for r in rows), \
        "reward outside [0, 1]"
    assert n_valid >= int(0.8 * args.n), \
        f"too many invalid SMILES ({n_valid}/{args.n}); panel likely corrupt"
    print("smoke-test assertions PASS")

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        # Stabilise column order
        keys = [
            "smiles", "valid", "aff_input", "qed", "sa", "mw", "logp",
            "pains_or_brenk_hit",
            "aff_term", "qed_term", "sa_term", "mw_term", "logp_term",
            "mech_term", "hard_reject", "reject_reason", "reward",
        ]
        with open(args.out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
