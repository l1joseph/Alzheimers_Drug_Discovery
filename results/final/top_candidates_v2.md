# PHGDH-AD candidate v2 summary

Bands: 1 = validated (AD repurposing track), 2 = novel scaffold-seeded, 3 = ChEMBL repurposing candidates (untested), 4 = REINVENT RL outputs.

## Band 1: AD repurposing candidates (validated PHGDH binders + selectivity data)

| # | id | source | Boltz aff | Vina | sel_idx | sel_interp | MW | logP | Tani→known | AD relevance |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `BI-cmpd-15` | validated_known | -1.0 |  | -2.3647472858428955 | STRONG selectivity for PHGDH |  |  | 1.00 | AD repurposing candidate (mechanism precedent) |
| 2 | `BI-4924` | validated_known | -1.79 | -9.19 | -1.6233436995744706 | STRONG selectivity for PHGDH |  |  | 1.00 | AD repurposing candidate (mechanism precedent) |
| 3 | `NCT-503` | validated_known | -0.3 |  | -1.4637468338012696 | STRONG selectivity for PHGDH |  |  | 1.00 | AD-tested |
| 4 | `NCT-cmpd-1` | validated_known | -1.02 | -8.00 | -1.1311651957035065 | STRONG selectivity for PHGDH |  |  | 1.00 | AD repurposing candidate (mechanism precedent) |
| 5 | `NCT-cmpd-15` | validated_known | -1.82 | -10.58 | -0.7634875249862672 | modest selectivity for PHGDH |  |  | 1.00 | AD repurposing candidate (mechanism precedent) |

## Band 2: Novel scaffold-seeded design (TamGen branches)

| # | id | source | Boltz aff | Vina | sel_idx | sel_interp | MW | logP | Tani→known | AD relevance |
|---|---|---|---|---|---|---|---|---|---|---|
| 6 | `b1_058` | tamgen_b1 | -0.65 | -7.91 | -0.046248459815979026 | weak preference for PHGDH | 469.4 | 3.37 | 0.14 | novel composition (NCT-503 scaffold lineage) |
| 7 | `b1_051` | tamgen_b1 | -0.48 | -7.21 | -0.406112562417984 | modest selectivity for PHGDH | 310.3 | 4.26 | 0.12 | novel composition (NCT-503 scaffold lineage) |
| 8 | `b1_005` | tamgen_b1 | -0.39 | -8.15 | -0.3019030758738518 | modest selectivity for PHGDH | 309.3 | 3.92 | 0.12 | novel composition (NCT-503 scaffold lineage) |

## Band 3: ChEMBL drug-like screen (untested repurposing candidates)

| # | id | source | Boltz aff | Vina | sel_idx | sel_interp | MW | logP | Tani→known | AD relevance |
|---|---|---|---|---|---|---|---|---|---|---|
| 9 | `CHEMBL1433971` | chembl_repurposing | -0.82 |  |  | not screened (off-target panel pending) |  |  |  | untested; mechanism-of-action precedent inferred from original-target |
| 10 | `CHEMBL1276764` | chembl_repurposing | -0.73 |  |  | not screened (off-target panel pending) |  |  |  | untested; mechanism-of-action precedent inferred from original-target |
| 11 | `CHEMBL392031` | chembl_repurposing | -0.70 |  |  | not screened (off-target panel pending) |  |  |  | untested; mechanism-of-action precedent inferred from original-target |
| 12 | `CHEMBL1939761` | chembl_repurposing | -0.64 |  |  | not screened (off-target panel pending) |  |  |  | untested; mechanism-of-action precedent inferred from original-target |
| 13 | `CHEMBL1801281` | chembl_repurposing | -0.60 |  |  | not screened (off-target panel pending) |  |  |  | untested; mechanism-of-action precedent inferred from original-target |
| 14 | `CHEMBL3663284` | chembl_repurposing | -0.53 |  |  | not screened (off-target panel pending) |  |  |  | untested; mechanism-of-action precedent inferred from original-target |
| 15 | `CHEMBL3937129` | chembl_repurposing | -0.47 |  |  | not screened (off-target panel pending) |  |  |  | untested; mechanism-of-action precedent inferred from original-target |
| 16 | `CHEMBL1852304` | chembl_repurposing | -0.44 |  |  | not screened (off-target panel pending) |  |  |  | untested; mechanism-of-action precedent inferred from original-target |
| 17 | `CHEMBL1084018` | chembl_repurposing | -0.44 |  |  | not screened (off-target panel pending) |  |  |  | untested; mechanism-of-action precedent inferred from original-target |
| 18 | `CHEMBL3962595` | chembl_repurposing | -0.42 |  |  | not screened (off-target panel pending) |  |  |  | untested; mechanism-of-action precedent inferred from original-target |

## Band 4: REINVENT RL with composite reward (novel composition-of-matter)

| # | id | source | Boltz aff | Vina | sel_idx | sel_interp | MW | logP | Tani→known | AD relevance |
|---|---|---|---|---|---|---|---|---|---|---|
| 19 | `reinvent_step010_COc1cc(N` | reinvent_rl | 0.7143 |  |  | not screened | 461.5 | 2.41 | 0.29 | novel composition (REINVENT RL with composite reward) |
| 20 | `reinvent_step028_CC1(C)CC` | reinvent_rl | 0.7092 |  |  | not screened | 362.4 | 3.68 | 0.20 | novel composition (REINVENT RL with composite reward) |
| 21 | `reinvent_step030_CC1(S(=O` | reinvent_rl | 0.7030 |  |  | not screened | 531.0 | 3.91 | 0.22 | novel composition (REINVENT RL with composite reward) |
| 22 | `reinvent_step033_N#CCn1cn` | reinvent_rl | 0.6961 |  |  | not screened | 328.3 | 2.91 | 0.21 | novel composition (REINVENT RL with composite reward) |
| 23 | `reinvent_step036_CCc1cccc` | reinvent_rl | 0.6942 |  |  | not screened | 329.4 | 2.41 | 0.20 | novel composition (REINVENT RL with composite reward) |
| 24 | `reinvent_step033_O=C(Nc1c` | reinvent_rl | 0.6932 |  |  | not screened | 354.2 | 3.21 | 0.15 | novel composition (REINVENT RL with composite reward) |
| 25 | `reinvent_step014_COc1ccc(` | reinvent_rl | 0.6895 |  |  | not screened | 311.4 | 3.75 | 0.16 | novel composition (REINVENT RL with composite reward) |
| 26 | `reinvent_step017_COc1ccc(` | reinvent_rl | 0.6883 |  |  | not screened | 328.3 | 3.19 | 0.12 | novel composition (REINVENT RL with composite reward) |
| 27 | `reinvent_step006_COc1c(Br` | reinvent_rl | 0.6860 |  |  | not screened | 324.1 | 3.85 | 0.16 | novel composition (REINVENT RL with composite reward) |
| 28 | `reinvent_step034_O=C1CN(C` | reinvent_rl | 0.6843 |  |  | not screened | 459.9 | 2.71 | 0.13 | novel composition (REINVENT RL with composite reward) |

