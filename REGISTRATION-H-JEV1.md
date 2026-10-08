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

---

## Amendment 1 — 2026-09-30, after Part A ran (reporting only; no rule changed)

1. **NaN.** `outcomes.csv` stores the literal string `nan` in `ret_open_5dclose_net` for 42 rows. `_f()` turned it into a float NaN, so S4 printed NaN. NaN now counts as missing. The primary (`mae_5d`), S1–S3 and both sensitivities have no NaN rows, and re-running the analysis on the same files left every one of them byte-identical. Only S4 changed.
2. **Label.** For Part A, the printed verdict now reads `RETROSPECTIVE: numeric bar …; Part A cannot establish H-JEV1` instead of a bare `PASS`, so the record says what this registration says.

Neither change can make a pass easier. Exposure, strata, estimate, CI, bar, windows and every stored row are unchanged.

## Part A result — 2026-09-30 (retrospective; cannot establish H-JEV1)

756 unique filings read for 1,397 picks. There were 0 unreadable filings, one fetch timeout that was retried and read, and 69 picks excluded for having no CIK (9 tickers, mostly delisted). 1,291 graded picks on 323 tickers entered the analysis. Record: `jev_backfill/` (`events.jsonl` holds every raw response; `result_A.json`). An independent recomputation (separate code, bootstrap seed 7, raw answers re-routed through `route()`: 0 of 756 differed from the logged routing) matched every estimate.

| | flagged (picks / tickers) | clean | D (pp of mae_5d) | 95% CI |
|---|---|---|---|---|
| **Primary** | 900 / 199 | 391 / 135 | **−4.51** | [−7.62, −0.48] |
| S1 within form-code offering/shelf | 755 / 185 | 156 / 59 | −3.16 | [−7.09, +4.53] |
| S2 8-K text only | 214 / 78 | 1077 / 262 | **−6.42** | [−10.94, −2.12] |
| S3 same-day return | | | +0.16 | [−2.59, +2.99] |
| S4 5-day return | | | −4.87 | [−13.39, +1.90] |
| A-sens1 without the 23 seen tickers | 804 / 177 | 390 / 134 | −4.30 | [−7.40, −0.36] |

**Reading.** Part A met the numeric bar. That is consistent with H-JEV1, and it proves nothing, because the outcomes were known. Direction is null, as registered. S1's CI crosses zero, so this record doesn't show that reading the text beats the form-code flag H-DIL2 already uses. The clearest signal is in S2, filings form codes can't see. Part B decides.

---

## Amendment 2 — 2026-10-01, before any Part B outcome exists (tightening only)

H-JEV2 (`REGISTRATION-H-JEV2.md`) was registered today as a second forward test. Two tests mean two chances at a false pass, so H-JEV1 Part B is now judged with H-JEV2 under **Holm's step-down**. A test passes on its 97.5% CI, or on its 95% CI once the other has passed on its 97.5% CI. Before this amendment H-JEV1 needed only its 95% CI, so the bar can only have risen. Exposure, window, estimate, effect bar and ticker floor are unchanged, and Part A's reported numbers are unchanged; `result_A.json` only gains a `ci_level` field on re-run.

For the record, here is the rule applied to Part A's data, which shows the tightening has teeth. H-JEV1's 97.5% CI is [−7.99, +0.37], so it would not pass at step 1. It would pass at step 2 only because the 8-K flag's 97.5% CI is [−11.40, −0.99]. Part A still cannot establish either hypothesis.

---

## Amendment 3 — 2026-10-08, before any Part B outcome exists (procedural guards only)

An automated code review on PR #10 found that the code did not enforce three things the registration already says. `jev_backfill.py` 1.2.0 now enforces them:

1. **One look.** `analyze --part B` refuses to run if `jev_backfill/result_B.json` exists, and writes it in exclusive-create mode. The single look can't be repeated or overwritten.
2. **Complete data.** Part B refuses to run, *before summarizing any outcome*, if any pick in the window is still unselected, if any selected filing has **never been attempted**, or if more than 5% of picks are ungraded. A filing that was tried and failed (logged in `errors.jsonl`) doesn't block the run: as this registration already says, picks whose filings couldn't be read are excluded and counted. `read` now reports every still-unread filing in `remaining`, failures included.
3. **The registered instrument.** `read` refuses unless the model is exactly `jev-1.13.0` and the question block is v2 (`394e6c22687a…`). The analysis refuses if any event it would use came from anything else. All 756 Part A reads and every Part B read so far pass.

None of these changes the exposure, the windows, the estimate, the bar or Holm. Each can only stop a run, never make a pass easier. Part A re-runs byte-identical.
