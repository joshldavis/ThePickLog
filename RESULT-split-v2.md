# Result — filing_lens reverse-split question v2

**Verdict: PASS** on the pre-registered bar in `REGISTRATION-split-v2.md` (registered in commit 36a7c0e, 2026-09-28 18:03 ET).
**Run:** 2026-09-28, model `jev-1.13.0` (pinned), question block v2 (`394e6c22687a…`). Cost under $0.10.
**Labels frozen:** commit 945e3ad (2026-09-28 18:14 ET), before the first Jev call on the sample. `calibration_v2/LABELS-split-v2.sha256` holds the hashes.
**Re-derive it:** `FILING_LENS_QUESTIONS=v2 python3 score_split_v2.py --cal calibration_v2`. This uses only committed files, with no network and no key. It writes `calibration_v2/registered_outcomes.json`.

## Sample

The population was every 2024 8-K and 8-K/A carrying Item 5.03 or 3.03 from the 341 tickers in `picks.csv` at the registration commit. That came to 196 readable filings and 0 unreadable. Because the population was under 200, the whole population was used. The model reader labeled 30 filings `effective`, so the registered top-up was not triggered.

Model-reader labels:

| Label | Filings |
| --- | --- |
| none | 135 |
| effective | 30 |
| announced | 29 |
| historical | 2 |

## Registered outcomes

| Outcome | Bar | Result | Pass |
| --- | --- | --- | --- |
| **Primary:** `effective` precision at p ≥ 0.90, corrected labels | ≥ 0.95, with ≥ 30 labeled effective | **24 / 24 = 1.000**, with 30 labeled effective | yes |
| **Primary sanity floor:** same, on labels as made | ≥ 0.90 | 24 / 24 = 1.000 | yes |
| Secondary: `announced` precision at p ≥ 0.90 | ≥ 0.95 | 29 / 29 = 1.000 | yes |
| Secondary: `split_ratio` given a labeled split | ≥ 0.95 | 59 / 59 = 1.000 | yes |
| Secondary: reproducibility, 30 filings re-asked (seed 2028) | 0 changed `reverse_split` answers | 0 changed on any question; largest probability move 0.07 | yes |

No label corrections were made, so "as labeled" and "corrected" are the same file.

## What the numbers do not say

**24 of 24 is a small count.** The 95% Wilson lower bound on that precision is 0.86. The registered bar was a point estimate and the result meets it, but a stranger should read this as "no false positives in 24" and not as "at least 95% guaranteed".

**The run-2 failure mode was barely exercised.** Run 2 failed on filings that recite an earlier split. In this population, only 2 filings were labeled `historical`, because 8-Ks with Item 5.03/3.03 mostly report their own split. So this test shows the question works on the population the split guard actually reads. It does not show that v2 fixed recaps everywhere. That is why the auto route is limited to exactly this scope.

**Recall at 0.90 is 24/30 (0.80).** The six misses are below. Four were answered `effective` with p between 0.60 and 0.89, so they land in review, not auto.

| Filing | Label (reader confidence) | Jev answer | p |
| --- | --- | --- | --- |
| V2-0051 | effective | effective | 0.60 |
| V2-0057 | effective | effective | 0.80 |
| V2-0062 | effective | effective | 0.89 |
| V2-0086 | effective | effective | 0.79 |
| V2-0098 | effective (medium) | announced | 0.54 |
| V2-0166 | effective (low) | historical | 0.44 |

- **V2-0098:** the text says the split "will become effective" at 11:59 p.m. on 2024-10-24, and the filing is dated 10-28. Jev's `announced` is a defensible reading of the future tense.
- **V2-0166:** an 8-K/A filed on the effective day.

These are genuine ambiguities, and none of them touches the primary outcome. They were not corrected.

**Calibration is underconfident, not overconfident.** ECE for `reverse_split` is 0.063, which is not gated. Right answers sit below 0.90 more often than wrong answers sit above it. The floor that would give 0.95 precision is 0.50.

**The labels come from a model reader, not a person.** Each label carries a verbatim quote (`calibration_v2/labels_model_v2.json`). Yahoo split history was recorded as evidence only (`evidence_yahoo.csv`) and never used as a label. It agrees with the labels:

- 27 of 30 `effective` labels have a Yahoo split 0–30 days before the filing, and the other 3 have one 1–3 days after.
- 29 of 29 `announced` labels have a Yahoo split after the filing.

**Other questions on this sample** (not gated; a check that v2 did not disturb them):

| Question | Accuracy |
| --- | --- |
| split_ratio | 0.995 |
| going_concern | 0.985 |
| other_material | 0.964 |
| listing_status | 0.954 |
| dilution_event | 0.888 |

## What this allows (as registered), and what changed in `filing_lens.py`

`reverse_split = effective` may route `auto` at p ≥ 0.90, but only when all three of these hold:

- the question block is v2;
- the form is 8-K or 8-K/A;
- the filing carries Item 5.03 or 3.03.

Routing outside that:

- Effective answers with p in [0.60, 0.90) route to review. The registered [0.80, 0.90) band is inside that range, and a 0.80 floor would have dropped 2 of the 6 missed true splits.
- Every split answer outside the scope routes to review, including anything with no filing context, truncated text, or `announced`.

"Auto" still means only that the split guard reconciles the filing's ratio and date against the quote series before any row is touched. Jev never voids a row by itself.

In the same commit, `listing_status` halt and delisting are marked calibrated from run 2 (2026-09-25), with the auto floor kept at 0.90:

- halt: 20/21 = 0.952 at 0.90, and 0.95 is reached from 0.79 up;
- delisting: 10/10 at 0.90, and 0.95 is reached from 0.56 up.

`deficiency_notice` stays a labeled placeholder, since run 2 measured 0.911 precision at 0.85. Every other threshold is still a placeholder. Gate 3 (shadow mode) only logs routing.

NOT INVESTMENT ADVICE.
