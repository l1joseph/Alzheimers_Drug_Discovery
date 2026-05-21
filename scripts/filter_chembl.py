"""Filter ChEMBL 34 chemreps.txt.gz to a drug-like subset for Boltz screening.

Multi-stage funnel — cheapest filters first, expensive ones last:
  1. SMILES length <= 120 chars (drops peptides / large natural products)
  2. RDKit parse + canonical SMILES
  3. Lipinski: MW 150-500, logP <= 5, HBD <= 5, HBA <= 10
  4. PAINS + Brenk substructure filter (RDKit FilterCatalog)
  5. SA score <= 6 (Ertl 2009 synthetic accessibility)

Output:
  data/libraries/chembl_druglike.csv with columns: id, smiles, mw, logp, hbd, hba, sa

Runs in parallel across login-node CPUs (uses multiprocessing.Pool).
Login-node-safe: only RDKit + Python stdlib; no GPU; ~5-15 min wall.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import multiprocessing as mp
import os
import sys
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, Descriptors, FilterCatalog

# SA score via RDKit Contrib (Ertl 2009 — same approach as score_synthesizability.py)
import rdkit
_rdkit_root = Path(rdkit.__file__).resolve().parent
sys.path.insert(0, str(_rdkit_root / "Contrib" / "SA_Score"))
try:
    import sascorer
    sa_calc = sascorer.calculateScore
except Exception:
    sa_calc = None

RDLogger.DisableLog("rdApp.*")

PROJECT = Path(__file__).resolve().parent.parent
OUT_PATH = PROJECT / "data" / "libraries" / "chembl_druglike.csv"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

MAX_SMILES_LEN = 120
MW_LO, MW_HI = 150.0, 500.0
LOGP_HI = 5.0
HBD_HI = 5
HBA_HI = 10
SA_HI = 6.0


# Built once per worker
_FCAT = None


def _ensure_filter_catalog():
    global _FCAT
    if _FCAT is None:
        params = FilterCatalog.FilterCatalogParams()
        params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS)
        params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.BRENK)
        _FCAT = FilterCatalog.FilterCatalog(params)
    return _FCAT


def filter_row(record):
    """Return (id, smiles, mw, logp, hbd, hba, sa) if pass, else None."""
    chembl_id, raw_smi = record
    if len(raw_smi) > MAX_SMILES_LEN:
        return None
    mol = Chem.MolFromSmiles(raw_smi)
    if mol is None:
        return None
    mw = Descriptors.MolWt(mol)
    if not (MW_LO <= mw <= MW_HI):
        return None
    logp = Descriptors.MolLogP(mol)
    if logp > LOGP_HI:
        return None
    hbd = Descriptors.NumHDonors(mol)
    if hbd > HBD_HI:
        return None
    hba = Descriptors.NumHAcceptors(mol)
    if hba > HBA_HI:
        return None
    cat = _ensure_filter_catalog()
    if cat.HasMatch(mol):
        return None  # PAINS or Brenk hit
    if sa_calc is not None:
        try:
            sa = sa_calc(mol)
        except Exception:
            return None
        if sa > SA_HI:
            return None
    else:
        sa = -1.0
    canon = Chem.MolToSmiles(mol, isomericSmiles=True)
    return (chembl_id, canon, round(mw, 1), round(logp, 2), hbd, hba, round(sa, 2))


def stream_chemreps(path: Path):
    with gzip.open(path, "rt") as f:
        header = f.readline()
        assert header.startswith("chembl_id"), f"unexpected header: {header[:80]}"
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            chembl_id, smi = parts[0], parts[1]
            if not smi:
                continue
            yield (chembl_id, smi)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="src", default="/cosmos/vast/scratch/l1joseph/chembl/chembl_34_chemreps.txt.gz")
    p.add_argument("--out", dest="out", default=str(OUT_PATH))
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    p.add_argument("--chunk", type=int, default=2000, help="rows per pool chunk")
    p.add_argument("--limit", type=int, default=0, help="optional sample cap for smoke tests")
    args = p.parse_args()

    src = Path(args.src)
    out = Path(args.out)
    print(f"reading {src}  ({src.stat().st_size / 1e6:.1f} MB)")
    print(f"writing {out}")
    print(f"workers: {args.workers}, chunk: {args.chunk}")

    src_iter = stream_chemreps(src)
    if args.limit:
        from itertools import islice
        src_iter = islice(src_iter, args.limit)

    n_in = 0
    n_pass = 0
    with mp.Pool(args.workers) as pool, open(out, "w", newline="") as fout:
        w = csv.writer(fout)
        w.writerow(["id", "smiles", "mw", "logp", "hbd", "hba", "sa"])
        for result in pool.imap_unordered(filter_row, src_iter, chunksize=args.chunk):
            n_in += 1
            if result is not None:
                n_pass += 1
                w.writerow(result)
            if n_in % 100000 == 0:
                print(f"  scanned {n_in:>9,d}   passed {n_pass:>7,d}   yield {n_pass / n_in:.2%}", flush=True)

    print(f"DONE  scanned {n_in:,}  passed {n_pass:,}  yield {n_pass / n_in if n_in else 0:.2%}")
    print(f"output: {out}")


if __name__ == "__main__":
    main()
