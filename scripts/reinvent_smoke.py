"""Smoke test for REINVENT4 installation in the reinvent-rocm conda env.

Checks the minimum surface area we need for v2 closed-loop RL:
  1. torch is the ROCm build (boltz-rocm uses 2.5.1+rocm6.2; REINVENT4 pins
     2.9.1 which means we get 2.9.1+rocm6.3 on this env).
  2. rdkit + RDKit Contrib SA_Score importable.
  3. `reinvent.chemistry.conversions.Conversions().smile_to_mol('CCO')`
     resolves through the backward-compat shim and returns an Mol.
  4. Composite reward (see composite_reward.py) scores a 50-SMILES panel
     end-to-end with mock affinities.

Does NOT exercise the RL loop; that lives in Block D.

Usage:
    conda activate reinvent-rocm
    python scripts/reinvent_smoke.py
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    line = f"  [{mark}] {label}"
    if detail:
        line += f"  ({detail})"
    print(line)
    if not ok:
        sys.exit(1)


def main() -> None:
    print("REINVENT4 smoke test")

    # --- torch ROCm ---
    torch = importlib.import_module("torch")
    is_rocm = hasattr(torch.version, "hip") and torch.version.hip is not None
    check(
        "torch is ROCm build",
        is_rocm,
        detail=f"torch={torch.__version__}, hip={getattr(torch.version, 'hip', None)}",
    )

    # --- rdkit core + Contrib SA_Score ---
    rdkit = importlib.import_module("rdkit")
    Chem = importlib.import_module("rdkit.Chem")
    mol = Chem.MolFromSmiles("CCO")
    check("rdkit MolFromSmiles", mol is not None,
          detail=f"rdkit={rdkit.__version__}")

    rdkit_root = Path(rdkit.__file__).resolve().parent
    sys.path.insert(0, str(rdkit_root / "Contrib" / "SA_Score"))
    sascorer = importlib.import_module("sascorer")
    sa = sascorer.calculateScore(mol)
    check("rdkit Contrib SA_Score", 0.0 < sa < 10.0,
          detail=f"SA(CCO)={sa:.2f}")

    # --- reinvent.chemistry.conversions.Conversions().smile_to_mol ---
    Conversions = importlib.import_module(
        "reinvent.chemistry.conversions"
    ).Conversions
    test_mol = Conversions().smile_to_mol("CCO")
    check("reinvent Conversions().smile_to_mol('CCO')",
          test_mol is not None,
          detail=f"atoms={test_mol.GetNumAtoms() if test_mol else 'NA'}")

    # --- reinvent CLI is on PATH ---
    try:
        out = subprocess.run(["reinvent", "--help"], check=True,
                             capture_output=True, text=True, timeout=30)
        ok = "Reinvent" in out.stdout or "reinvent" in out.stdout.lower()
    except Exception as e:
        ok = False
        out = type("X", (), {"stdout": str(e)})()
    check("reinvent CLI on PATH",
          ok,
          detail=f"first line: {out.stdout.splitlines()[0] if out.stdout else ''}")

    # --- composite reward on 50 SMILES ---
    script = Path(__file__).resolve().parent / "composite_reward.py"
    result = subprocess.run(
        [sys.executable, str(script), "--n", "50", "--seed", "42"],
        capture_output=True, text=True, check=False,
    )
    ok = result.returncode == 0 and "smoke-test assertions PASS" in result.stdout
    check("composite_reward.py on 50 SMILES",
          ok,
          detail=(result.stdout.strip().splitlines()[-1] if result.stdout else
                  result.stderr.strip().splitlines()[-1] if result.stderr else ""))

    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
