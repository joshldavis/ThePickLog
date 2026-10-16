# Correction — expected calibration error (ECE), 2026-10-08

**What was wrong.** `calibration_run.py` computed ECE by comparing each probability bin's accuracy with the bin's **midpoint** (0.95 for the 0.90–1.00 bin), not with the **mean probability Jev actually gave** in that bin. Standard ECE uses the mean. Jev's top-bin probabilities sit near 0.99, not 0.95, so the midpoint version mis-stated every question's ECE. Found by an automated code review on PR #10 and confirmed by re-scoring both runs from the committed responses, with no new Jev calls.

**Fix.** `calibration_run.py` now uses the mean predicted probability per bin, and each reliability row gains a `mean_p` column. The original result files are kept unchanged; the corrected ones sit beside them as `*_ece-corrected.*`.

## Calibration run 2 (2026-09-25, 543 filings, question block v1) — ECE gated at ≤ 0.05

| Question | Reported (midpoint) | Corrected | Verdict |
|---|---|---|---|
| reverse_split | 0.0441 | **0.0520** | FAIL, unchanged. It now also fails the ECE bar, on top of the precision miss it already failed on |
| split_ratio | 0.0244 | 0.0402 | PASS, unchanged |
| listing_status | 0.0366 | 0.0317 | PASS, unchanged |
| dilution_event | 0.0408 | 0.0396 | PASS, unchanged |
| going_concern | 0.0459 | 0.0238 | PASS, unchanged |
| other_material | 0.0384 | 0.0218 | PASS, unchanged |

## Split-v2 test (2026-09-28, 196 filings, question block v2) — ECE reported, not gated

| Question | Reported (midpoint) | Corrected |
|---|---|---|
| reverse_split | 0.0633 | **0.0212** |
| split_ratio | 0.0546 | 0.0064 |
| listing_status | 0.0434 | 0.0267 |
| dilution_event | 0.0357 | **0.0631** |
| going_concern | 0.0582 | 0.0292 |
| other_material | 0.0694 | 0.0304 |

**What changes.** No verdict changes. The split-v2 PASS rests on precision at p ≥ 0.90, which this bug never touched. Two readings do change:
- `reverse_split` under v2 is well calibrated (0.021), not "underconfident at 0.063". `RESULT-split-v2.md` is corrected to match.
- `dilution_event` on the 2024 sample is **over** 0.05 (0.063). ECE is not gated there, and the dilution thresholds are still marked placeholders in `filing_lens.THRESHOLDS`, so nothing routes on it. It is the first thing to recalibrate before any dilution answer is allowed to route `auto`.

The run-2 field-note drafts (`calibration_run2/FIELD-NOTE-DRAFT*.md`) still show the midpoint values. They are drafts and are superseded by this note.
