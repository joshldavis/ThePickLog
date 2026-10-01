# Pre-registration — H-JEV2: do risk events in 8-K text flag deeper drawdowns?

**Registered:** 2026-10-01, after that day's open and before the 2026-10-02 open. The git commit that adds this file is the timestamp. **Forward window: picks traded 2026-10-02 through 2026-12-31.** The 2026-10-01 picks are excluded because this registration came after that day's open.
**Same instrument as H-JEV1:** `jev-1.13.0`, `QUESTIONS_V2` (sha256 `394e6c22687a…`), `filing_lens.THRESHOLDS`, `jev_backfill.py` (the H-JEV2 block in `analyze()`, `JEV2_WINDOW`, `holm()`).

## Where this came from — read before the result

H-JEV2 was chosen **after seeing H-JEV1 Part A** (2026-09-30). There, the 8-K-only flag (secondary S2) gave the clearest separation: D = −6.42pp [−10.94, −2.12] on 78 flagged tickers. Over offering and shelf documents, Jev's reading did not separate from the form-code flag already in use (S1 crossed zero). Part A is the reason for this test, so it is not evidence for it. Only the forward window counts.

## Claim

A pick is *8-K-flagged* when any **Form 8-K or 8-K/A** among its pre-open filings (same selection as H-JEV1: accepted before 09:30 ET, `select_filings()`, 30-day window, items 1.01/3.01/3.02/3.03/5.03/8.01) has any question other than `split_ratio` routed `auto` or `review`. The claim is that 8-K-flagged picks have a deeper `mae_5d` than other picks in the same cohort × score tercile.

**Binding framing:** this is the same as H-JEV1. A pass supports a risk label naming the 8-K and Jev's answer, linked to EDGAR. It is not a direction signal and does not change selection.

## Analysis and bar

The estimate D, the strata, the ticker-clustered bootstrap (2,000 resamples, seed 2026), the effect bar (**D ≤ −3.0pp**) and the floor (**≥ 25 distinct tickers per arm**) are identical to H-JEV1's.

**Family of two, Holm.** H-JEV1 Part B and H-JEV2 are judged together. A test passes if its **97.5%** CI upper bound is below 0. Once one test has passed that way, the other passes if its **95%** CI upper bound is below 0. Both must also meet the effect bar and the ticker floor. This controls the chance of any false pass across the two at 5%.

**One look,** on or after 2027-01-11, through `python3 jev_backfill.py analyze --part B`, which reports H-JEV1 and H-JEV2 together and refuses to run earlier.

## What each result allows

- **PASS:** the 8-K risk label may ship on pick cards with the framing above.
- **FAIL or INSUFFICIENT:** no 8-K risk label, and this flag is not re-tested on 2026 Q4 data.
