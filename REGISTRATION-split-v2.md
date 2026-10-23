# Pre-registration — filing_lens reverse-split question v2

**Registered:** 2026-09-28, before any filing in the test sample was retrieved, read, or labeled. The git commit that adds this file is the timestamp.
**Model:** `jev-1.13.0` (TypeSafe AI, pinned; never an alias).
**Question block:** `filing_lens.QUESTIONS_V2`, sha256 `394e6c22687a…` (full hash printed by `python3 filing_lens.py --selftest`). Only `reverse_split` differs from v1 (`6be36476189a…`).

## Why a v2 exists

Calibration run 2 (2026-09-25, 543 filings) failed the pre-set bar for `reverse_split = effective`: precision 0.833 at the 0.90 floor against a 0.95 bar. The misses were filings that recite a split completed earlier ("as previously disclosed", a recap of recent developments, adjusted share counts). The v1 question never said such a mention counts as `historical`; the labels assumed it did. v2 puts that definition in the question. A result restricted to 8-Ks from run 2 (36 of 38) was chosen after seeing run 1 and is not evidence; this test exists to replace it with one that is.

## Population and sample (fixed now)

1. **Population.** Every Form 8-K or 8-K/A filed 2024-01-01 through 2024-12-31 that carries Item 5.03 or Item 3.03, filed by a registrant whose ticker appears in `picks.csv` at the commit that adds this file. No 2024 filing was used in any earlier calibration set (all earlier sets are 2025-01-01 or later).
2. **Readable.** The primary document is fetched from EDGAR and passed through `filing_lens.strip_html` and `cap_text`; a document shorter than 200 characters after stripping is excluded and counted.
3. **Draw.** If the population exceeds 200 readable filings, a random sample of 200 with `random.Random(2026)` over the population sorted by accession number; otherwise all of it.
4. **Top-up, only if needed.** If fewer than 30 filings in the draw are labeled `effective`, add filings from EDGAR full-text search (8-K, filed in 2024, Item 5.03 or 3.03, query `"reverse stock split"`, not already in the draw), in `random.Random(2027)` order over accession-sorted results, in batches of 20, until 30 are labeled `effective` or 150 have been added. Top-up rows are reported separately as well as pooled.

## Labels (fixed now; finalized before Jev sees the sample)

- Each filing is labeled on all six questions by a model reader working from the **same text Jev receives** (full text up to the 30,000-token cap), using the v2 definitions verbatim, with a verbatim quote per label.
- Yahoo split history is recorded for each filing as evidence and is **not** used as a label: run 2 showed the Item 5.03 market-truth rule mislabels preferred-stock designation amendments.
- The finished label file's sha256 is committed **before** the first Jev call on the sample.
- After the run, a label may be corrected only with a verbatim quotation from the filing that settles it. Every correction is published with its quote, and results are published both as labeled and as corrected.

## Outcomes and bar (fixed now)

Scope for all split outcomes: 8-Ks carrying Item 5.03 or 3.03 (the only filings the split guard reads).

| Outcome | Measure | Bar |
| --- | --- | --- |
| **Primary** | `reverse_split = effective`, precision at p ≥ 0.90 | ≥ 0.95, with ≥ 30 labeled `effective` |
| Primary, sanity floor | same, on labels **as made** (before any correction) | ≥ 0.90 |
| Secondary | `reverse_split = announced`, precision at p ≥ 0.90 | ≥ 0.95 (reported; underpowered below 30 positives) |
| Secondary | `split_ratio` accuracy given a labeled split | ≥ 0.95 |
| Secondary | Reproducibility: 30 random sample filings re-asked once | 0 changed `reverse_split` answers |

Also reported, not gated: ECE and reliability per question, every question's accuracy on the new sample (a check that the v2 block did not disturb the others), recall at the floor, and the floor that would give 0.95 precision.

**Pass** = the primary bar on corrected labels **and** the sanity floor on the labels as made. Anything else is a fail.

## What each result allows

- **Pass:** `reverse_split = effective` may route `auto` at p ≥ 0.90 for 8-Ks with Item 5.03/3.03 only, with p in [0.80, 0.90) routed to review (run 2 measured up to 0.10 of run-to-run drift in probabilities). "Auto" still means only that the split guard reconciles the filing's ratio and date against the quote series before any row is touched; Jev never voids a row by itself.
- **Fail:** split answers stay review-only (`NO_AUTO`) for as long as v2 is the question. No v3 is tested on this sample, and this sample is not reused to tune anything.

## Reproduce

`FILING_LENS_QUESTIONS=v2 python3 calibration_run.py --cal <sample dir>`; raw responses are cached per filing with the text and question hashes; the logged response, not a re-run, is the record of what the model answered.
