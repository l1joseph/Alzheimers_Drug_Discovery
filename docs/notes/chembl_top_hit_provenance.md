# ChEMBL top-hit provenance notes (saved 2026-05-20 ~22:30)

**Status**: partial Block B aggregation (tasks 0,1 only — 2449 of 5000 sample scored). Tasks 2,3 still running. Full ranking will shift when complete; treat this as a snapshot.

## Top 10 from partial Block B aggregation, by Boltz `affinity_pred_value`

| Rank | ChEMBL ID | Boltz aff | Boltz prob_binary | Boltz confidence | MW | logP | SA | Tanimoto (nearest known PHGDH binder) | **Original drug-discovery target** | Therapeutic area | Source paper |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CHEMBL3093256 | −0.85 | 0.12 | 0.74 | 404 | 3.5 | 3.0 | 0.14 → NADH | **GRK-2 / GRK-5 kinases** | cardiovascular | Cho et al. 2013 *BMCL* 23, 6711 |
| 2 | CHEMBL3986234 | −0.82 | 0.08 | 0.78 | 402 | 3.3 | 3.2 | 0.12 → NCT-cmpd-15 | **LRRK2 kinase** | **Parkinson's disease** (CNS!) | CHEMBL3886204 |
| 3 | CHEMBL3220496 | −0.66 | 0.14 | 0.67 | 443 | 3.7 | 2.4 | 0.18 → NCT-cmpd-15 | JNK / MAPK9-10 | inflammation/cancer | CHEMBL3217652 |
| 4 | CHEMBL1939761 | −0.64 | 0.46 | 0.74 | 440 | 2.5 | 3.3 | 0.16 → BI-4924 | B1 bradykinin receptor | pain | CHEMBL1938332 |
| 5 | CHEMBL1801281 | −0.60 | 0.42 | 0.79 | 359 | 3.8 | 3.4 | 0.11 → BI-cmpd-15 | **MK2 kinase** | inflammation | CHEMBL1799987 |
| 6 | CHEMBL3663284 | −0.53 | 0.55 | 0.76 | 449 | 3.8 | 3.5 | — | P2X7 receptor | neuropathic pain | CHEMBL3638702 |
| 7 | CHEMBL3889509 | −0.51 | 0.17 | 0.79 | 449 | 3.8 | 2.9 | — | **JAK1 / JAK2 kinases** | autoimmune | CHEMBL3886705 |
| 8 | CHEMBL3937129 | −0.47 | 0.55 | 0.75 | 430 | 3.7 | 3.0 | — | Cathepsin S protease | autoimmune | CHEMBL3886685 |
| 9 | CHEMBL1852304 | −0.44 | 0.42 | 0.74 | 366 | 3.2 | 3.0 | — | (no public assay data) | — | — |
| 10 | CHEMBL1084018 | −0.44 | 0.44 | 0.73 | 329 | 2.7 | 2.8 | — | **PDE10A** | **CNS / schizophrenia** | CHEMBL1155487 |

## Pattern

**7 of 10 are kinase or kinase-adjacent inhibitors from unrelated drug-discovery programs.** Boltz appears to be recovering scaffolds with generic nucleotide-pocket-binding pharmacophores (ATP-mimetic heterocyclic warheads that share H-bond donor/acceptor topology with NADH).

This is a *real signal* — these compounds likely do bind PHGDH at the NADH site — but it's also a **strong selectivity flag** (binding *both* kinases and PHGDH is the default expectation, not the exception). The Block G counter-screen (vs LDH-A / MDH2 / GAPDH / IDH1) was sized for Rossmann-fold dehydrogenase off-targets; adding GRK / LRRK2 / JAK / MK2 counter-screens would be valuable but out of the current 9-hour window.

## CNS-tuned candidates of opportunity

Two stand out as worth promoting *if Vina rescore + Block G selectivity + multi-conformation robustness all pass*:

- **CHEMBL3986234** — originally an LRRK2 inhibitor for Parkinson's disease. **Already CNS-optimized** for a neurodegeneration target. If it cross-binds PHGDH, this is a high-quality repurposing candidate because the brain-penetrance and ADME work is already done for a related indication.
- **CHEMBL1084018** — PDE10A inhibitor for schizophrenia. **CNS-tuned by design** (PDE10A is striatum-localized). Smallest MW in the top-10 (329 Da), best Lipinski profile (logP 2.7).

## When to escalate to the main report

Only fold these into `docs/CANDIDATE_REPORT.md` if both:
1. Vina rescore corroborates the Boltz ranking (Vina score < −7.5 kcal/mol)
2. Selectivity counter-screen (Block G) shows > 1 log-Kd preference for PHGDH over at least 2 of {LDH-A, MDH2, GAPDH, IDH1}

If only criterion 1 holds: keep them as "second tier with selectivity caveat". If neither: drop from candidate list, flag as Boltz nucleotide-pocket false positives.

## TODO

- After Block B completes (tasks 2,3): re-aggregate; ranking may shift
- After Block G: cross-reference selectivity index per compound; promote CNS-tuned hits if selective
- After Block D: see whether REINVENT-generated compounds escape the kinase-pharmacophore mode that the ChEMBL screen is exposing
- Consider an LRRK2 / GRK-5 counter-screen as a follow-up (out of current window)

**Source for the cross-reference**: ChEMBL REST API queries on 2026-05-20:
- `/data/molecule/<CHEMBLID>.json`
- `/data/activity.json?molecule_chembl_id=<CHEMBLID>`
- `/data/document/<DOCID>.json`
