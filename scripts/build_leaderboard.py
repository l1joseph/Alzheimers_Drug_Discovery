"""Aggregate Boltz affinity scores from all rounds into a single ranked CSV.

Replaces the three inline heredoc blocks that previously lived in b1/b2/b3_score.sh.
Uses an fcntl flock to avoid the race when concurrent scoring jobs all try to
rewrite results/combined/all_rounds.csv simultaneously.

Usage (default — picks up every known source):
    python scripts/build_leaderboard.py

Outputs results/combined/all_rounds.csv with one row per (input_id, source),
sorted by affinity_pred_value ascending. Sources are auto-detected from the
results/ tree.
"""
from __future__ import annotations

import csv
import fcntl
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
RESULTS = PROJECT / "results"
OUT = RESULTS / "combined" / "all_rounds.csv"

# (source_label, scores_csv) — extend as new branches are added
SOURCES: list[tuple[str, Path]] = [
    ("round0_known",   RESULTS / "round0" / "baseline_scores.csv"),
    ("tamgen_round1",  RESULTS / "tamgen_round1" / "scores.csv"),
    ("tamgen_round2",  RESULTS / "tamgen_round2" / "scores.csv"),
    ("tamgen_b1",      RESULTS / "tamgen_b1" / "scores.csv"),
    ("tamgen_b2",      RESULTS / "tamgen_b2" / "scores.csv"),
    ("tamgen_b3",      RESULTS / "tamgen_b3" / "scores.csv"),
    ("tamgen_b2_round2", RESULTS / "tamgen_b2_round2" / "scores.csv"),
    ("ensemble_c2",    RESULTS / "ensemble_c2" / "scores.csv"),
]


def main() -> None:
    rows: list[dict] = []
    for label, path in SOURCES:
        if not path.exists():
            continue
        for r in csv.DictReader(open(path)):
            try:
                aff = float(r["affinity_affinity_pred_value"])
            except (KeyError, ValueError):
                continue
            rows.append({
                "id": r["input_id"],
                "source": label,
                "affinity_pred_value": aff,
                "prob_binary": float(r.get("affinity_affinity_probability_binary", "nan")),
                "confidence": float(r.get("confidence_confidence_score", 0) or 0),
            })

    rows.sort(key=lambda r: r["affinity_pred_value"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lock_path = OUT.parent / ".all_rounds.lock"
    with open(lock_path, "w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        with open(OUT, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "source", "affinity_pred_value",
                                              "prob_binary", "confidence"])
            w.writeheader()
            w.writerows(rows)

    print(f"merged {len(rows)} rows from {sum(1 for _,p in SOURCES if p.exists())} sources → {OUT}")
    print("\n=== top 20 ===")
    for r in rows[:20]:
        print(f"  {r['id']:10s} {r['source'][:14]:14s}  "
              f"aff={r['affinity_pred_value']:+6.2f}  prob={r['prob_binary']:.2f}  "
              f"conf={r['confidence']:.2f}")


if __name__ == "__main__":
    main()
