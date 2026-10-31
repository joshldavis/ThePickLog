# ThePickLog — forward-log report · 2026-10-31

Auto-generated weekly from the immutable pick log (picks.csv / outcomes.csv). No predictions; this is the public record summarized. Not investment advice.

> **Excluded from every figure below: 105 picks across 7 cohorts that were logged at or after their own session's open** and therefore scored against a price that had already printed (`2026-06-15 (13), 2026-07-06 (16), 2026-07-07 (16), 2026-07-09 (16), 2026-07-13 (16), 2026-07-27 (14), 2026-08-03 (14)`). The rows stay in picks.csv; the exclusion re-derives from `published_at`. See AUDIT_LOG.md 2026-08-04.

## 1. Maturation

- **1148 picks** logged across **87 scan days** (2026-06-09 → 2026-10-30); ~20.4 weeks live.
- **1042 graded**, **81 pending**, **14 voided** (phantom/holiday rows — excluded from every stat below) (grading runs at 5 trading days).
- Toward the pre-billing gate (~8 wks of graded record): **~8.0 / 8 weeks**.

## ⚠️ One-stock sensitivity

Some averages below are carried by a single pick. The pick is real and stays in every figure; each such mean is marked with a numbered † and the figure without it is given here. Read the median, which one pick cannot move, as the headline.

- †1 **JAGX 2026-09-22** (+1116%) carries 20 averages marked †1, including all picks, open→close: **-1.8%** with it, **-2.9%** without. Across all 20, the figure without it runs -3.1% to -2.7%.
- †2 **SUGP 2026-06-16** (-56%) carries the H-SI arm average: **-2.2%** with it, **-1.7%** without.
- †3 **one pick** (+1116%) carries 2 averages marked †3, including exit batch #2 arm: **-1.8%** with it, **-2.9%** without. Across all 2, the figure without it runs -3.0% to -2.9%.
- †4 **one pick** (+1099%) carries 2 averages marked †4, including exit batch #2 arm: **-2.9%** with it, **-4.0%** without. Across all 2, the figure without it runs -4.0% to -4.0%.
- †5 **one pick** (+1147%) carries 2 averages marked †5, including exit batch #2 arm: **-4.0%** with it, **-5.1%** without. Across all 2, the figure without it runs -5.1% to -5.1%.
- †6 **one pick** (+1145%) carries 2 averages marked †6, including exit batch #2 arm: **-2.3%** with it, **-3.5%** without. Across all 2, the figure without it runs -3.5% to -3.4%.

## 2. Realized performance (graded picks)

- **Win rate:** 31%  (323/1042 positive net, open→close).
- **Open→close net:** median -2.5%, mean -1.8% †1.
- **5-day net:** median -6.8%, mean -8.0%.
- **Drawdown (MAE 5d):** median -11.6%, worst -84.9%.
- **Catastrophic-rug rate (MAE < -30%):** 13%.

## 3. By momentum tier (forward, out-of-sample)

| tier | n | win% | median net | median MAE |
|---|---|---|---|---|
| A | 50 | 43% | -2.5% | -26.6% |
| B | 64 | 31% | -6.1% | -19.8% |
| C | 448 | 35% | -2.4% | -11.8% |
| D | 505 | 27% | -2.4% | -10.0% |

## 4. Finding A check — does hotter momentum = deeper drawdown? (live log)

- High tier (A+B): n=111, median MAE -23.3%, rug 32%.
- Low tier (C+D): n=931, median MAE -10.7%, rug 11%.
- Backtest said A/B draw down deeper. Live log so far: **HOLDS (A+B deeper)** (small N — directional only).

## 4b. Would following the screen have paid? (personal reality check)

Equal-weight, every graded pick held to the 5-day close, net of the 2% cost haircut (an honest 'if I'd taken them all' proxy — not advice):

| strategy | n | avg net/trade | median | win% |
|---|---|---|---|---|
| Take every pick | 1042 | -8.0% | -6.8% | 27% |
| Skip A/B (Finding-A rule) | 931 | -7.2% | -6.3% | 27% |
| Only A/B (the hot names) | 111 | -14.8% | -18.3% | 23% |

Skipping the hot A/B names changes avg net/trade by **+0.8pp** vs taking everything — Finding A pays as a filter here (small N, directional).

## 4c. Pre-registered filters (tracking vs HYPOTHESES.md)

Each filter **skips** some picks; we want the kept subset to beat baseline on avg net/trade. Registered 2026-06-22 from an in-sample cut — only **post-2026-06-22** picks are the honest test. Both windows shown; judge on the post-registration column as it grows.

| filter | all-time | | | post-reg (out-of-sample) | | |
|---|---|---|---|---|---|---|
| | n | win% | avg net | n | win% | avg net |
| Baseline (all picks) | n=1042 | 31% | -1.8% †1 | n=935 | 31% | -1.7% †1 |
| H-F1 skip <$1 | n=813 | 30% | -1.6% †1 | n=724 | 29% | -1.6% †1 |
| H-F2 skip float≥3M | n=886 | 32% | -1.5% †1 | n=795 | 32% | -1.4% †1 |
| H-F3 skip gap≥+20% | n=1020 | 31% | -1.8% †1 | n=919 | 30% | -1.7% †1 |
| H-F4 skip A/B (Finding A) | n=931 | 30% | -1.6% †1 | n=845 | 30% | -1.4% †1 |
| H-CLEAN (all filters) | n=662 | 31% | -1.0% †1 | n=597 | 30% | -0.9% †1 |

**H-SI — short-interest cut (open question, two-sided):**
- SI ≥ 20%: n=98, win 38%, avg -2.2% †2   ·   SI < 20%: n=892, win 29%, avg -1.8% †1  (graded picks carrying short interest: 990)

_Exit-rule study: see reports/exit-study-LATEST.md (in-sample, exploratory)._

## 4d. Pre-registered exit rule — H-EX1 (the candidate edge)

Registered 2026-06-23. The screen finds names that **spike then fade**; H-EX1 tests whether a disciplined target monetizes the spike. Rule: rest a **+10% limit** over the 5-day hold — if the 5-day high reaches it, realize **+8% net**, else exit at the 5-day close. Judged on **avg net/trade** vs the current same-day-close exit, on **post-2026-06-23** picks. Median/win% secondary.

| arm | n | win% | avg net | median |
|---|---|---|---|---|
| _all-time (in-sample context, NOT the test)_ |  |  |  |  |
| Same-day close (baseline) | n=1042 | 31% | -1.8% †1 | -2.5% |
| H-EX1 +10% target | n=1042 | 49% | -4.1% | -0.4% |
| _post-registration (the honest test)_ |  |  |  |  |
| Same-day close (baseline) | n=920 | 30% | -1.7% †1 | -2.6% |
| H-EX1 +10% target | n=920 | 48% | -4.1% | -1.4% |

- Post-registration expectancy delta (H-EX1 − baseline): **-2.3pp** on n=920. ⚠️ **One stock drives this:** without JAGX 2026-09-22 (+1116%) the delta is **-1.1pp**.
- ⚠️ Fills assumed exactly at +10%; thin-float gap-through means real fills are worse (see HYPOTHESES.md H-EX1 slippage caveat). `exit_sim.py` walks the daily path as the rigorous cross-check.

## 4e. Pre-registered exit rule — H-EX2 (does a stop add value?)

Registered 2026-06-24. H-EX1 monetizes the spike but ignores the fat left tail (median MAE ≈ −16%, 17% rug rate). H-EX2 pairs the **+10% target with a −20% disaster stop** (first level the daily path touches wins; conservative same-day tie → stop first). Judged on **avg net/trade vs H-EX1 (target alone)** on **post-2026-06-24** path-bearing picks; same-day-close is the secondary baseline.

| arm | n | win% | avg net | median |
|---|---|---|---|---|
| _all-time, path-bearing (in-sample context, NOT the test)_ |  |  |  |  |
| Same-day close (baseline) | n=990 | 30% | -1.8% †1 | -2.5% |
| H-EX1 +10% target | n=990 | 48% | -4.4% | -1.5% |
| H-EX2 +10% target / −20% stop | n=990 | 46% | -3.9% | -2.7% |
| _post-registration, path-bearing (the honest test)_ |  |  |  |  |
| Same-day close (baseline) | n=905 | 30% | -1.7% †1 | -2.6% |
| H-EX1 +10% target | n=905 | 48% | -4.1% | -1.5% |
| H-EX2 +10% target / −20% stop | n=905 | 46% | -3.8% | -2.7% |

- Post-registration expectancy delta (H-EX2 − H-EX1): **+0.3pp** on n=905 path-bearing picks. Positive ⇒ the stop earns its keep; a null/negative keeps H-EX1 stop-less.
- ⚠️ Thin-float names **gap through stops**; the 2% haircut doesn't model gap-through, so realized H-EX2 (esp. the stop arm) would be **worse** than shown (HYPOTHESES.md H-EX2 caveat).

## 4f. Pre-registered exit batch #2 — H-EX3..H-EX9

Registered 2026-07-02 (HYPOTHESES.md, seven hypotheses frozen together). **Family-wise honesty note: with this many arms, one can beat baseline by luck.** The batch is a *ranked screen*, not seven independent claims — a winner must beat its baseline on avg net/trade, hold direction across ≥3 consecutive weekly snapshots, and survive as n grows; prefer the simplest rule among ties. Only **post-2026-07-02** picks are the test; directional until n≥30 per arm. Slippage caveat as H-EX1/H-EX2 (fills assumed at level; thin floats gap through — any edge <~+1pp is noise).

**(i) Arms evaluable from the graded log (target fills read off `mfe_5d`):**

| arm | all-time | | | post-reg (the test) | | |
|---|---|---|---|---|---|---|
| | n | win% | avg net | n | win% | avg net |
| Same-day close (baseline) | n=1042 | 31% | -1.8% †1 | n=816 | 29% | -1.6% †1 |
| 5-day close (baseline) | n=1042 | 27% | -8.0% | n=816 | 26% | -8.4% |
| H-EX1 +10% target (reference) | n=1042 | 49% | -4.1% | n=816 | 47% | -4.3% |
| H-EX3 +5% target | n=1042 | 68% | -3.4% | n=816 | 67% | -3.5% |
| H-EX3 +15% target | n=1042 | 39% | -5.0% | n=816 | 37% | -5.3% |
| H-EX3 +20% target | n=1042 | 35% | -5.3% | n=816 | 33% | -5.8% |
| H-EX6 half at +10%, half to 5d close | n=1042 | 37% | -6.0% | n=816 | 36% | -6.4% |
| H-EX8 tier target (A/B +20%, C/D +10%) | n=1042 | 48% | -4.3% | n=816 | 45% | -4.6% |

**(ii) Arms needing touch order (scored from the committed daily path, `paths.csv`):**

| arm | all-time path-bearing | | | post-reg (the test) | | |
|---|---|---|---|---|---|---|
| | n | win% | avg net | n | win% | avg net |
| Same-day close (baseline) | n=990 | 30% | -1.8% †3 | n=816 | 29% | -1.6% †3 |
| H-EX1 +10% target (reference) | n=990 | 48% | -4.4% | n=816 | 47% | -4.4% |
| H-EX2 +10% / −20% stop (reference) | n=990 | 46% | -3.9% | n=816 | 45% | -4.0% |
| H-EX4 +10% target, day-2 time stop | n=990 | 41% | -3.2% | n=816 | 40% | -3.2% |
| H-EX5a day-1 close | n=990 | 28% | -2.9% †4 | n=816 | 28% | -2.7% †4 |
| H-EX5b day-2 close | n=990 | 28% | -4.0% †5 | n=816 | 28% | -3.7% †5 |
| H-EX7 trail 15% after +10% touch | n=990 | 30% | -2.3% †6 | n=816 | 29% | -2.0% †6 |
| H-EX9a +10% / −10% stop | n=990 | 40% | -3.0% | n=816 | 39% | -3.1% |
| H-EX9b +10% / −30% stop | n=990 | 48% | -4.0% | n=816 | 46% | -4.1% |

_All-time columns are in-sample context, NOT the test. Post-reg columns fill as picks logged after 2026-07-02 reach the 5-day grade (first land ~2026-07-10)._

## 5. Integrity checks (verifiability standard)

- ⚠️ 7 weekday(s) with no VALID scan because the cohort was logged after the open and excluded: 2026-06-15, 2026-07-06, 2026-07-07, 2026-07-09, 2026-07-13, 2026-07-27, 2026-08-03 (see AUDIT_LOG.md 2026-08-04)
- ⚠️ 10 weekday(s) with no scan (may be US market holidays): 2026-07-03, 2026-08-27, 2026-08-28, 2026-08-31, 2026-09-01, 2026-09-02, 2026-09-03, 2026-09-07…

## 6. v0.3 market-wide cohort (H-UNIV1 — registered 2026-07-08)

- **707 picks** across **73 scan days** (2026-07-09 → 2026-10-30); **463 unique tickers** (the H-IND1 effective-N readout the v0.2 cohort lacked).
- Graded: n=636, win 36%, median net -3.6%, mean -1.8%.
- Candidate pool + non-published eligibles: `candidates.csv` (forward-only control pool for H-CTRL).
- Young cohort — directional only; no v0.3 rule is registered yet, so nothing here feeds any verdict.

---
*Generated by weekly_report.py on 2026-10-31T18:15:11.628901Z. Forward log is the canonical record; backtest CSVs are gitignored and exploratory.*
