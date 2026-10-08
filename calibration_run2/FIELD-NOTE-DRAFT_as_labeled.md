# Calibration result — filing_lens × jev-1.13.0

Run 2026-09-25 · 543 filings scored (0 skipped) · questions sha `6be36476189a` · lens `0.1.0-gate1` · seed 7

This is the calibration test the spec requires before any answer from the model appears on the site. The bar was fixed before the run; the numbers below are the run.

| Question | n | Accuracy | ECE | Top bin (p≥0.90) | Verdict |
| --- | --- | --- | --- | --- | --- |
| `reverse_split` | 543 | 0.9153 | 0.0367 | 0.9601 (n=501) | **FAIL** |
| `split_ratio` | 543 | 0.9429 | 0.017 | 0.9584 (n=529) | **PASS** |
| `listing_status` | 543 | 0.919 | 0.0366 | 0.9736 (n=455) | **PASS** |
| `dilution_event` | 543 | 0.8877 | 0.0408 | 0.9698 (n=431) | **PASS** |
| `going_concern` | 543 | 0.9705 | 0.0294 | 0.9754 (n=528) | **PASS** |
| `other_material` | 543 | 0.9355 | 0.0384 | 0.979 (n=477) | **PASS** |

## Per-value, at the proposed auto floor

| Question · value | Positives | Floor | Precision | Recall | Predicted | Floor for 0.95 precision |
| --- | --- | --- | --- | --- | --- | --- |
| `reverse_split` · effective | 61 | 0.9 | 0.8333 | 0.6557 | 48 | None |
| `reverse_split` · announced | 49 | 0.9 | 1.0 | 0.898 | 44 | 0.79 |
| `listing_status` · halt | 43 | 0.9 | 0.9524 | 0.4651 | 21 | 0.79 |
| `listing_status` · delisting_determination | 39 | 0.9 | 1.0 | 0.2564 | 10 | 0.56 |
| `listing_status` · deficiency_notice | 81 | 0.85 | 0.9114 | 0.8889 | 79 | 0.94 |
| `dilution_event` · priced_offering | 32 | 0.85 | 0.8966 | 0.8125 | 29 | None |
| `dilution_event` · private_placement | 51 | 0.85 | 0.9545 | 0.4118 | 22 | 0.85 |
| `dilution_event` · atm_or_equity_line | 35 | 0.85 | 0.96 | 0.6857 | 25 | 0.75 |
| `dilution_event` · convertible_or_warrants | 74 | 0.85 | 0.8429 | 0.7973 | 70 | 0.95 |
| `going_concern` · yes | 11 | 0.85 | 0.44 | 1.0 | 25 | None |
| `other_material` · bankruptcy | 4 | 0.9 | 1.0 | 0.5 | 2 | None |
| `other_material` · restatement | 1 | 0.85 | 0.0 | 0.0 | 1 | None |
| `other_material` · auditor_change | 3 | 0.85 | 0.5 | 0.6667 | 4 | None |

## Verdict reasons

- `reverse_split`: effective: precision 0.8333 at floor 0.9 < 0.95

## How the labels were made

Market truth (Yahoo split history, cross-checked against float drops in candidates.csv) decided `reverse_split`/`split_ratio` where it could; 8-K item codes decided bankruptcy/auditor/restatement/M&A; a model reader labeled the rest with a verbatim quote per label; a human audited every disagreement plus a seeded sample. Precedence and rules: `calibration_truth.py`, `calibration_merge.py`. Documented label corrections applied: 0 (calibration/label_corrections.csv, each with the filing's own words as evidence; `--no-corrections` scores the original labels). Audit overrides applied: 0.

## Reproduce

Every request is the stored text (hash in candidates.csv) plus the question block in `filing_lens.QUESTIONS`, sent to `jev-1.13.0`; raw responses are cached under `responses/`. Re-running against the same pinned version must reproduce `result.json`.
