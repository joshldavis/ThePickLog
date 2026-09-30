# Pre-registration — H-JEV1: does Jev's reading of a pick's filings flag deeper drawdowns?

**Registered:** 2026-09-30, before Jev has read any filing selected for any pick in `picks.csv`. The git commit that adds this file is the timestamp. It also adds `jev_backfill.py`, whose `analyze()` is the registered analysis. Changing that function after this commit is an amendment and must be recorded as one.
**Model:** `jev-1.13.0` (pinned). **Question block:** `QUESTIONS_V2`, sha256 `394e6c22687a…`. **Thresholds:** `filing_lens.THRESHOLDS` as of this commit.

## What is claimed, and what is not

**Claim.** A pick counts as *Jev-flagged* when any filing it had on file before the open contains an answer that `filing_lens.route()` sends to `auto` or `review`. The claim is that flagged picks have a **deeper 5-day drawdown** (`mae_5d`) than unflagged picks in the same cohort and score band. The comparison holds the score band fixed because H-RISK1 already shows the score predicts drawdown depth, and this test has to show something the score doesn't.

**Binding framing, not to be dropped if the test passes.** A pass supports a *risk label*: "this name has a filing on record that we read as a risk event". It is not a buy or avoid signal, it does not change which tickers are picked, and it does not reopen Gate 1. The 2026-07-29 sweep found nothing that predicts direction, so S3 and S4 below are expected to be null. A result that also predicted direction would get its own dated registration and its own forward window.

## Why this is registered now, and what was already seen

On 2026-09-28 Josh asked how performance looked "now with Jev". Jev had not touched a live pick yet, so the question was answered by replaying calibration run 2 (a stratified sample of 543 filings, not the picks' own filings) against the ledger. Only 69 picks on 23 tickers had a sampled filing in the 60 days before the pick. Excluding them moved the same-day mean from −2.34% to −2.48%. Deficiency notices and reverse splits hinted at deeper drawdowns, but on 4–6 picks each. **That hint is where this hypothesis came from, so it is not evidence for it.** Those 23 tickers are listed in `jev_backfill.SEEN_TICKERS`, and Part A is also reported without them.

## Exposure (fixed now)

1. **Which filings.** For each pick, the SEC submissions block is filtered to filings **accepted before 09:30 ET on the trading date**. A filing with no acceptance time is kept only if its filing date is strictly earlier. The production prefilter `filing_lens.select_filings()` then runs unchanged: 8-Ks carrying Item 1.01/3.01/3.02/3.03/5.03/8.01 within 30 days, plus 424B/FWP/S-1/S-3/F-1/F-3 within 180 days, capped at 6 per pick.
2. **One read per filing.** Each unique accession is fetched once and read once. The first logged response is the record, and a filing is never re-asked (run 2 measured up to 0.10 run-to-run drift).
3. **Flag.** `flag_any` is true when any read filing has any question other than `split_ratio` routed `auto` or `review`. A pick with no qualifying filing is unflagged: in production, Jev would have had nothing to read.
4. **Excluded and counted:** picks with no CIK (current SEC ticker map), SEC fetch errors, and picks whose selected filings could not be read at all. A pick with some filings read is kept (`partial`) and dropped in sensitivity A-sens2.

## Analysis (fixed now; `jev_backfill.analyze`)

- **Rows:** graded picks with a `mae_5d` value in the part's window.
- **Strata:** cohort (`model_version`) × score tercile, with cut points taken within cohort from the analysis rows' scores (these don't depend on outcomes).
- **Estimate D:** the stratum-size-weighted mean of (mean `mae_5d` flagged − mean `mae_5d` unflagged), over strata that contain both arms. Negative D means flagged picks drew down further.
- **CI:** ticker-clustered bootstrap, 2,000 resamples, seed 2026, percentile 95%.
- **Verdict (primary):** **PASS** requires at least 25 distinct tickers in each arm, **D ≤ −3.0 percentage points**, and the CI's upper bound below 0. Anything else is FAIL, or INSUFFICIENT when the ticker floor isn't met.

| | Measure | Status |
|---|---|---|
| **Primary** | D on `mae_5d`, any flag | verdict as above |
| S1 | same, only picks whose form-code `dilution_flag` is offering/shelf (does reading the text add anything to the form code H-DIL2 already uses?) | reported |
| S2 | same, flag from **8-K text only** (what form codes cannot see) | reported |
| S3 / S4 | D on same-day and 5-day signed return | reported, expected null |

The secondaries are descriptive, and none of them can turn a failed primary into a pass.

## Two parts

- **Part A: retrospective.** Picks traded 2026-06-01 through 2026-09-30. The outcomes are already known, and 23 tickers were seen in the replay. Part A is run and published in full, but it **cannot establish the claim**. It is reported with sensitivities A-sens1 (without the seen tickers) and A-sens2 (without partial reads).
- **Part B: forward, confirmatory.** Picks traded 2026-10-01 through 2026-12-31, read by the same code (`select` and `read` over that window). There is **one look**, on or after 2027-01-11, once 5-day grading is complete; `analyze --part B` refuses to run earlier. Only Part B can produce a PASS for H-JEV1.

## What each result allows

- **Part B PASS:** the pick card may show a filing-risk label naming the filing and the answer, linked to the EDGAR document. It must carry the framing above. Selection is unchanged.
- **Part B FAIL or INSUFFICIENT:** Jev stays a data-integrity tool (split guard, halt confirmation) and nothing about risk is shown. The same exposure isn't re-tested on 2026 Q4 data.
- **Part A, whatever it shows:** published as a field note and changes nothing on the site.

## Reproduce

```
python3 jev_backfill.py --selftest
python3 jev_backfill.py select --from 2026-06-01 --to 2026-09-30
JEV_MODEL=jev-1.13.0 JEV_API_KEY=… python3 jev_backfill.py read
python3 jev_backfill.py analyze --part A
```
`jev_backfill/events.jsonl` holds every raw response with its text sha256, question sha256 and model. The analysis re-runs from these files without a key or network.
