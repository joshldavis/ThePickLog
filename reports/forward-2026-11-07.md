# ThePickLog — forward-log report · 2026-11-07

Auto-generated weekly from the immutable pick log (picks.csv / outcomes.csv). No predictions; this is the public record summarized. Not investment advice.

> **Excluded from every figure below: 105 picks across 7 cohorts that were logged at or after their own session's open** and therefore scored against a price that had already printed (`2026-06-15 (13), 2026-07-06 (16), 2026-07-07 (16), 2026-07-09 (16), 2026-07-13 (16), 2026-07-27 (14), 2026-08-03 (14)`). The rows stay in picks.csv; the exclusion re-derives from `published_at`. See AUDIT_LOG.md 2026-08-04.

## 1. Maturation

- **1195 picks** logged across **92 scan days** (2026-06-09 → 2026-11-06); ~21.4 weeks live.
- **1095 graded**, **75 pending**, **14 voided** (phantom/holiday rows — excluded from every stat below) (grading runs at 5 trading days).
- Toward the pre-billing gate (~8 wks of graded record): **~8.0 / 8 weeks**.

## ⚠️ One-stock sensitivity

Some averages below are carried by a single pick. The pick is real and stays in every figure; each such mean is marked with a numbered † and the figure without it is given here. Read the median, which one pick cannot move, as the headline.

- †1 **JAGX 2026-09-22** (+1116%) carries 20 averages marked †1, including all picks, open→close: **-1.8%** with it, **-2.9%** without. Across all 20, the figure without it runs -3.0% to -2.5%.
- †2 **SUGP 2026-06-16** (-56%) carries the H-SI arm average: **-2.2%** with it, **-1.7%** without.
- †3 **one pick** (+1116%) carries 2 averages marked †3, including exit batch #2 arm: **-1.8%** with it, **-2.9%** without. Across all 2, the figure without it runs -2.9% to -2.9%.
- †4 **one pick** (+1099%) carries 2 averages marked †4, including exit batch #2 arm: **-2.9%** with it, **-4.0%** without. Across all 2, the figure without it runs -4.0% to -4.0%.
- †5 **one pick** (+1147%) carries 2 averages marked †5, including exit batch #2 arm: **-4.1%** with it, **-5.2%** without. Across all 2, the figure without it runs -5.2% to -5.2%.
- †6 **one pick** (+1145%) carries 2 averages marked †6, including exit batch #2 arm: **-2.8%** with it, **-3.9%** without. Across all 2, the figure without it runs -4.0% to -3.9%.

## 2. Realized performance (graded picks)

- **Win rate:** 31%  (339/1095 positive net, open→close).
- **Open→close net:** median -2.5%, mean -1.8% †1.
- **5-day net:** median -6.8%, mean -8.4%.
- **Drawdown (MAE 5d):** median -11.8%, worst -84.9%.
- **Catastrophic-rug rate (MAE < -30%):** 13%.

## 3. By momentum tier (forward, out-of-sample)

| tier | n | win% | median net | median MAE |
|---|---|---|---|---|
| A | 50 | 43% | -2.5% | -26.6% |
| B | 66 | 30% | -6.1% | -19.8% |
| C | 479 | 35% | -2.4% | -11.8% |
| D | 525 | 26% | -2.4% | -10.1% |

## 4. Finding A check — does hotter momentum = deeper drawdown? (live log)

- High tier (A+B): n=113, median MAE -23.3%, rug 33%.
- Low tier (C+D): n=982, median MAE -10.7%, rug 11%.
- Backtest said A/B draw down deeper. Live log so far: **HOLDS (A+B deeper)** (small N — directional only).

## 4b. Would following the screen have paid? (personal reality check)

Equal-weight, every graded pick held to the 5-day close, net of the 2% cost haircut (an honest 'if I'd taken them all' proxy — not advice):

| strategy | n | avg net/trade | median | win% |
|---|---|---|---|---|
| Take every pick | 1095 | -8.4% | -6.8% | 27% |
| Skip A/B (Finding-A rule) | 982 | -7.6% | -6.3% | 27% |
| Only A/B (the hot names) | 113 | -15.3% | -18.3% | 22% |

Skipping the hot A/B names changes avg net/trade by **+0.8pp** vs taking everything — Finding A pays as a filter here (small N, directional).

## 4c. Pre-registered filters (tracking vs HYPOTHESES.md)

Each filter **skips** some picks; we want the kept subset to beat baseline on avg net/trade. Registered 2026-06-22 from an in-sample cut — only **post-2026-06-22** picks are the honest test. Both windows shown; judge on the post-registration column as it grows.

| filter | all-time | | | post-reg (out-of-sample) | | |
|---|---|---|---|---|---|---|
| | n | win% | avg net | n | win% | avg net |
| Baseline (all picks) | n=1095 | 31% | -1.8% †1 | n=988 | 31% | -1.7% †1 |
| H-F1 skip <$1 | n=853 | 31% | -1.6% †1 | n=764 | 30% | -1.5% †1 |
| H-F2 skip float≥3M | n=931 | 32% | -1.4% †1 | n=840 | 32% | -1.3% †1 |
| H-F3 skip gap≥+20% | n=1073 | 31% | -1.8% †1 | n=972 | 30% | -1.7% †1 |
| H-F4 skip A/B (Finding A) | n=982 | 30% | -1.6% †1 | n=896 | 30% | -1.5% †1 |
| H-CLEAN (all filters) | n=700 | 32% | -0.9% †1 | n=635 | 31% | -0.9% †1 |

**H-SI — short-interest cut (open question, two-sided):**
- SI ≥ 20%: n=103, win 36%, avg -2.2% †2   ·   SI < 20%: n=940, win 30%, avg -1.8% †1  (graded picks carrying short interest: 1043)

_Exit-rule study: see reports/exit-study-LATEST.md (in-sample, exploratory)._

## 4d. Pre-registered exit rule — H-EX1 (the candidate edge)

Registered 2026-06-23. The screen finds names that **spike then fade**; H-EX1 tests whether a disciplined target monetizes the spike. Rule: rest a **+10% limit** over the 5-day hold — if the 5-day high reaches it, realize **+8% net**, else exit at the 5-day close. Judged on **avg net/trade** vs the current same-day-close exit, on **post-2026-06-23** picks. Median/win% secondary.

| arm | n | win% | avg net | median |
|---|---|---|---|---|
| _all-time (in-sample context, NOT the test)_ |  |  |  |  |
| Same-day close (baseline) | n=1095 | 31% | -1.8% †1 | -2.5% |
| H-EX1 +10% target | n=1095 | 49% | -4.4% | -0.8% |
| _post-registration (the honest test)_ |  |  |  |  |
| Same-day close (baseline) | n=973 | 30% | -1.7% †1 | -2.5% |
| H-EX1 +10% target | n=973 | 48% | -4.4% | -1.6% |

- Post-registration expectancy delta (H-EX1 − baseline): **-2.7pp** on n=973. ⚠️ **One stock drives this:** without JAGX 2026-09-22 (+1116%) the delta is **-1.5pp**.
- ⚠️ Fills assumed exactly at +10%; thin-float gap-through means real fills are worse (see HYPOTHESES.md H-EX1 slippage caveat). `exit_sim.py` walks the daily path as the rigorous cross-check.

## 4e. Pre-registered exit rule — H-EX2 (does a stop add value?)

Registered 2026-06-24. H-EX1 monetizes the spike but ignores the fat left tail (median MAE ≈ −16%, 17% rug rate). H-EX2 pairs the **+10% target with a −20% disaster stop** (first level the daily path touches wins; conservative same-day tie → stop first). Judged on **avg net/trade vs H-EX1 (target alone)** on **post-2026-06-24** path-bearing picks; same-day-close is the secondary baseline.

| arm | n | win% | avg net | median |
|---|---|---|---|---|
| _all-time, path-bearing (in-sample context, NOT the test)_ |  |  |  |  |
| Same-day close (baseline) | n=1043 | 30% | -1.8% †1 | -2.5% |
| H-EX1 +10% target | n=1043 | 48% | -4.7% | -1.6% |
| H-EX2 +10% target / −20% stop | n=1043 | 45% | -4.1% | -2.9% |
| _post-registration, path-bearing (the honest test)_ |  |  |  |  |
| Same-day close (baseline) | n=958 | 30% | -1.7% †1 | -2.5% |
| H-EX1 +10% target | n=958 | 48% | -4.4% | -1.6% |
| H-EX2 +10% target / −20% stop | n=958 | 45% | -4.0% | -2.9% |

- Post-registration expectancy delta (H-EX2 − H-EX1): **+0.4pp** on n=958 path-bearing picks. Positive ⇒ the stop earns its keep; a null/negative keeps H-EX1 stop-less.
- ⚠️ Thin-float names **gap through stops**; the 2% haircut doesn't model gap-through, so realized H-EX2 (esp. the stop arm) would be **worse** than shown (HYPOTHESES.md H-EX2 caveat).

## 4f. Pre-registered exit batch #2 — H-EX3..H-EX9

Registered 2026-07-02 (HYPOTHESES.md, seven hypotheses frozen together). **Family-wise honesty note: with this many arms, one can beat baseline by luck.** The batch is a *ranked screen*, not seven independent claims — a winner must beat its baseline on avg net/trade, hold direction across ≥3 consecutive weekly snapshots, and survive as n grows; prefer the simplest rule among ties. Only **post-2026-07-02** picks are the test; directional until n≥30 per arm. Slippage caveat as H-EX1/H-EX2 (fills assumed at level; thin floats gap through — any edge <~+1pp is noise).

**(i) Arms evaluable from the graded log (target fills read off `mfe_5d`):**

| arm | all-time | | | post-reg (the test) | | |
|---|---|---|---|---|---|---|
| | n | win% | avg net | n | win% | avg net |
| Same-day close (baseline) | n=1095 | 31% | -1.8% †1 | n=869 | 29% | -1.6% †1 |
| 5-day close (baseline) | n=1095 | 27% | -8.4% | n=869 | 26% | -8.9% |
| H-EX1 +10% target (reference) | n=1095 | 49% | -4.4% | n=869 | 47% | -4.7% |
| H-EX3 +5% target | n=1095 | 68% | -3.6% | n=869 | 67% | -3.9% |
| H-EX3 +15% target | n=1095 | 39% | -5.3% | n=869 | 37% | -5.7% |
| H-EX3 +20% target | n=1095 | 35% | -5.6% | n=869 | 33% | -6.1% |
| H-EX6 half at +10%, half to 5d close | n=1095 | 37% | -6.4% | n=869 | 36% | -6.8% |
| H-EX8 tier target (A/B +20%, C/D +10%) | n=1095 | 47% | -4.6% | n=869 | 45% | -5.0% |

**(ii) Arms needing touch order (scored from the committed daily path, `paths.csv`):**

| arm | all-time path-bearing | | | post-reg (the test) | | |
|---|---|---|---|---|---|---|
| | n | win% | avg net | n | win% | avg net |
| Same-day close (baseline) | n=1043 | 30% | -1.8% †3 | n=869 | 29% | -1.6% †3 |
| H-EX1 +10% target (reference) | n=1043 | 48% | -4.7% | n=869 | 47% | -4.7% |
| H-EX2 +10% / −20% stop (reference) | n=1043 | 45% | -4.1% | n=869 | 44% | -4.2% |
| H-EX4 +10% target, day-2 time stop | n=1043 | 41% | -3.4% | n=869 | 40% | -3.4% |
| H-EX5a day-1 close | n=1043 | 28% | -2.9% †4 | n=869 | 28% | -2.7% †4 |
| H-EX5b day-2 close | n=1043 | 28% | -4.1% †5 | n=869 | 28% | -3.9% †5 |
| H-EX7 trail 15% after +10% touch | n=1043 | 30% | -2.8% †6 | n=869 | 30% | -2.6% †6 |
| H-EX9a +10% / −10% stop | n=1043 | 40% | -3.1% | n=869 | 39% | -3.2% |
| H-EX9b +10% / −30% stop | n=1043 | 47% | -4.1% | n=869 | 46% | -4.3% |

_All-time columns are in-sample context, NOT the test. Post-reg columns fill as picks logged after 2026-07-02 reach the 5-day grade (first land ~2026-07-10)._

## 5. Integrity checks (verifiability standard)

- ⚠️ 7 weekday(s) with no VALID scan because the cohort was logged after the open and excluded: 2026-06-15, 2026-07-06, 2026-07-07, 2026-07-09, 2026-07-13, 2026-07-27, 2026-08-03 (see AUDIT_LOG.md 2026-08-04)
- ⚠️ 10 weekday(s) with no scan (may be US market holidays): 2026-07-03, 2026-08-27, 2026-08-28, 2026-08-31, 2026-09-01, 2026-09-02, 2026-09-03, 2026-09-07…

## 6. v0.3 market-wide cohort (H-UNIV1 — registered 2026-07-08)

- **757 picks** across **78 scan days** (2026-07-09 → 2026-11-06); **494 unique tickers** (the H-IND1 effective-N readout the v0.2 cohort lacked).
- Graded: n=686, win 36%, median net -3.6%, mean -1.9%.
- Candidate pool + non-published eligibles: `candidates.csv` (forward-only control pool for H-CTRL).
- Young cohort — directional only; no v0.3 rule is registered yet, so nothing here feeds any verdict.

---
*Generated by weekly_report.py on 2026-11-07T18:29:25.821026Z. Forward log is the canonical record; backtest CSVs are gitignored and exploratory.*
