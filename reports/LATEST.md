# ThePickLog — forward-log report · 2026-11-21

Auto-generated weekly from the immutable pick log (picks.csv / outcomes.csv). No predictions; this is the public record summarized. Not investment advice.

> **Excluded from every figure below: 105 picks across 7 cohorts that were logged at or after their own session's open** and therefore scored against a price that had already printed (`2026-06-15 (13), 2026-07-06 (16), 2026-07-07 (16), 2026-07-09 (16), 2026-07-13 (16), 2026-07-27 (14), 2026-08-03 (14)`). The rows stay in picks.csv; the exclusion re-derives from `published_at`. See AUDIT_LOG.md 2026-08-04.

## 1. Maturation

- **1280 picks** logged across **102 scan days** (2026-06-09 → 2026-11-20); ~23.4 weeks live.
- **1184 graded**, **71 pending**, **14 voided** (phantom/holiday rows — excluded from every stat below) (grading runs at 5 trading days).
- Toward the pre-billing gate (~8 wks of graded record): **~8.0 / 8 weeks**.

## ⚠️ One-stock sensitivity

Some averages below are carried by a single pick. The pick is real and stays in every figure; each such mean is marked with a numbered † and the figure without it is given here. Read the median, which one pick cannot move, as the headline.

- †1 **JAGX 2026-09-22** (+1116%) carries 20 averages marked †1, including all picks, open→close: **-1.9%** with it, **-2.9%** without. Across all 20, the figure without it runs -3.0% to -2.5%.
- †2 **NCT 2026-11-12** (+687%) carries the Only A/B (the hot names) average: **-9.2%** with it, **-15.0%** without.
- †3 **one pick** (+1116%) carries 2 averages marked †3, including exit batch #2 arm: **-1.9%** with it, **-2.9%** without. Across all 2, the figure without it runs -2.9% to -2.9%.
- †4 **one pick** (+1099%) carries 2 averages marked †4, including exit batch #2 arm: **-3.1%** with it, **-4.1%** without. Across all 2, the figure without it runs -4.1% to -4.1%.
- †5 **one pick** (+1145%) carries 2 averages marked †5, including exit batch #2 arm: **-3.5%** with it, **-4.5%** without. Across all 2, the figure without it runs -4.6% to -4.5%.

## 2. Realized performance (graded picks)

- **Win rate:** 31%  (369/1184 positive net, open→close).
- **Open→close net:** median -2.4%, mean -1.9% †1.
- **5-day net:** median -6.9%, mean -7.1%.
- **Drawdown (MAE 5d):** median -12.0%, worst -84.9%.
- **Catastrophic-rug rate (MAE < -30%):** 14%.

## 3. By momentum tier (forward, out-of-sample)

| tier | n | win% | median net | median MAE |
|---|---|---|---|---|
| A | 52 | 45% | -2.0% | -26.1% |
| B | 72 | 29% | -6.4% | -19.8% |
| C | 518 | 35% | -2.3% | -12.1% |
| D | 567 | 27% | -2.4% | -10.2% |

## 4. Finding A check — does hotter momentum = deeper drawdown? (live log)

- High tier (A+B): n=121, median MAE -23.3%, rug 33%.
- Low tier (C+D): n=1063, median MAE -10.9%, rug 12%.
- Backtest said A/B draw down deeper. Live log so far: **HOLDS (A+B deeper)** (small N — directional only).

## 4b. Would following the screen have paid? (personal reality check)

Equal-weight, every graded pick held to the 5-day close, net of the 2% cost haircut (an honest 'if I'd taken them all' proxy — not advice):

| strategy | n | avg net/trade | median | win% |
|---|---|---|---|---|
| Take every pick | 1184 | -7.1% | -6.9% | 26% |
| Skip A/B (Finding-A rule) | 1063 | -6.9% | -6.4% | 27% |
| Only A/B (the hot names) | 121 | -9.2% †2 | -16.2% | 23% |

Skipping the hot A/B names changes avg net/trade by **+0.2pp** vs taking everything — Finding A pays as a filter here (small N, directional).

## 4c. Pre-registered filters (tracking vs HYPOTHESES.md)

Each filter **skips** some picks; we want the kept subset to beat baseline on avg net/trade. Registered 2026-06-22 from an in-sample cut — only **post-2026-06-22** picks are the honest test. Both windows shown; judge on the post-registration column as it grows.

| filter | all-time | | | post-reg (out-of-sample) | | |
|---|---|---|---|---|---|---|
| | n | win% | avg net | n | win% | avg net |
| Baseline (all picks) | n=1184 | 31% | -1.9% †1 | n=1077 | 31% | -1.8% †1 |
| H-F1 skip <$1 | n=935 | 31% | -1.6% †1 | n=846 | 30% | -1.6% †1 |
| H-F2 skip float≥3M | n=1011 | 32% | -1.5% †1 | n=920 | 32% | -1.5% †1 |
| H-F3 skip gap≥+20% | n=1160 | 31% | -1.9% †1 | n=1059 | 31% | -1.9% †1 |
| H-F4 skip A/B (Finding A) | n=1063 | 31% | -1.7% †1 | n=977 | 30% | -1.6% †1 |
| H-CLEAN (all filters) | n=772 | 32% | -1.0% †1 | n=707 | 31% | -1.0% †1 |

**H-SI — short-interest cut (open question, two-sided):**
- SI ≥ 20%: n=110, win 35%, avg -2.3%   ·   SI < 20%: n=1022, win 30%, avg -1.9% †1  (graded picks carrying short interest: 1132)

_Exit-rule study: see reports/exit-study-LATEST.md (in-sample, exploratory)._

## 4d. Pre-registered exit rule — H-EX1 (the candidate edge)

Registered 2026-06-23. The screen finds names that **spike then fade**; H-EX1 tests whether a disciplined target monetizes the spike. Rule: rest a **+10% limit** over the 5-day hold — if the 5-day high reaches it, realize **+8% net**, else exit at the 5-day close. Judged on **avg net/trade** vs the current same-day-close exit, on **post-2026-06-23** picks. Median/win% secondary.

| arm | n | win% | avg net | median |
|---|---|---|---|---|
| _all-time (in-sample context, NOT the test)_ |  |  |  |  |
| Same-day close (baseline) | n=1184 | 31% | -1.9% †1 | -2.4% |
| H-EX1 +10% target | n=1184 | 48% | -4.7% | -1.3% |
| _post-registration (the honest test)_ |  |  |  |  |
| Same-day close (baseline) | n=1062 | 31% | -1.8% †1 | -2.4% |
| H-EX1 +10% target | n=1062 | 47% | -4.8% | -2.0% |

- Post-registration expectancy delta (H-EX1 − baseline): **-2.9pp** on n=1062. ⚠️ **One stock drives this:** without JAGX 2026-09-22 (+1116%) the delta is **-1.9pp**.
- ⚠️ Fills assumed exactly at +10%; thin-float gap-through means real fills are worse (see HYPOTHESES.md H-EX1 slippage caveat). `exit_sim.py` walks the daily path as the rigorous cross-check.

## 4e. Pre-registered exit rule — H-EX2 (does a stop add value?)

Registered 2026-06-24. H-EX1 monetizes the spike but ignores the fat left tail (median MAE ≈ −16%, 17% rug rate). H-EX2 pairs the **+10% target with a −20% disaster stop** (first level the daily path touches wins; conservative same-day tie → stop first). Judged on **avg net/trade vs H-EX1 (target alone)** on **post-2026-06-24** path-bearing picks; same-day-close is the secondary baseline.

| arm | n | win% | avg net | median |
|---|---|---|---|---|
| _all-time, path-bearing (in-sample context, NOT the test)_ |  |  |  |  |
| Same-day close (baseline) | n=1132 | 31% | -1.9% †1 | -2.4% |
| H-EX1 +10% target | n=1132 | 47% | -5.0% | -2.0% |
| H-EX2 +10% target / −20% stop | n=1132 | 45% | -4.3% | -3.2% |
| _post-registration, path-bearing (the honest test)_ |  |  |  |  |
| Same-day close (baseline) | n=1047 | 30% | -1.8% †1 | -2.4% |
| H-EX1 +10% target | n=1047 | 47% | -4.8% | -2.0% |
| H-EX2 +10% target / −20% stop | n=1047 | 45% | -4.3% | -3.1% |

- Post-registration expectancy delta (H-EX2 − H-EX1): **+0.5pp** on n=1047 path-bearing picks. Positive ⇒ the stop earns its keep; a null/negative keeps H-EX1 stop-less.
- ⚠️ Thin-float names **gap through stops**; the 2% haircut doesn't model gap-through, so realized H-EX2 (esp. the stop arm) would be **worse** than shown (HYPOTHESES.md H-EX2 caveat).

## 4f. Pre-registered exit batch #2 — H-EX3..H-EX9

Registered 2026-07-02 (HYPOTHESES.md, seven hypotheses frozen together). **Family-wise honesty note: with this many arms, one can beat baseline by luck.** The batch is a *ranked screen*, not seven independent claims — a winner must beat its baseline on avg net/trade, hold direction across ≥3 consecutive weekly snapshots, and survive as n grows; prefer the simplest rule among ties. Only **post-2026-07-02** picks are the test; directional until n≥30 per arm. Slippage caveat as H-EX1/H-EX2 (fills assumed at level; thin floats gap through — any edge <~+1pp is noise).

**(i) Arms evaluable from the graded log (target fills read off `mfe_5d`):**

| arm | all-time | | | post-reg (the test) | | |
|---|---|---|---|---|---|---|
| | n | win% | avg net | n | win% | avg net |
| Same-day close (baseline) | n=1184 | 31% | -1.9% †1 | n=958 | 30% | -1.8% †1 |
| 5-day close (baseline) | n=1184 | 26% | -7.1% | n=958 | 26% | -7.3% |
| H-EX1 +10% target (reference) | n=1184 | 48% | -4.7% | n=958 | 46% | -5.0% |
| H-EX3 +5% target | n=1184 | 68% | -3.9% | n=958 | 66% | -4.2% |
| H-EX3 +15% target | n=1184 | 38% | -5.7% | n=958 | 36% | -6.2% |
| H-EX3 +20% target | n=1184 | 34% | -5.9% | n=958 | 32% | -6.6% |
| H-EX6 half at +10%, half to 5d close | n=1184 | 36% | -5.9% | n=958 | 35% | -6.2% |
| H-EX8 tier target (A/B +20%, C/D +10%) | n=1184 | 47% | -4.8% | n=958 | 45% | -5.3% |

**(ii) Arms needing touch order (scored from the committed daily path, `paths.csv`):**

| arm | all-time path-bearing | | | post-reg (the test) | | |
|---|---|---|---|---|---|---|
| | n | win% | avg net | n | win% | avg net |
| Same-day close (baseline) | n=1132 | 31% | -1.9% †3 | n=958 | 30% | -1.8% †3 |
| H-EX1 +10% target (reference) | n=1132 | 47% | -5.0% | n=958 | 46% | -5.1% |
| H-EX2 +10% / −20% stop (reference) | n=1132 | 45% | -4.3% | n=958 | 44% | -4.5% |
| H-EX4 +10% target, day-2 time stop | n=1132 | 41% | -3.5% | n=958 | 40% | -3.6% |
| H-EX5a day-1 close | n=1132 | 29% | -3.1% †4 | n=958 | 29% | -2.9% †4 |
| H-EX5b day-2 close | n=1132 | 29% | +nan% | n=958 | 28% | +nan% |
| H-EX7 trail 15% after +10% touch | n=1132 | 29% | -3.5% †5 | n=958 | 29% | -3.4% †5 |
| H-EX9a +10% / −10% stop | n=1132 | 39% | -3.2% | n=958 | 39% | -3.3% |
| H-EX9b +10% / −30% stop | n=1132 | 47% | -4.4% | n=958 | 46% | -4.6% |

_All-time columns are in-sample context, NOT the test. Post-reg columns fill as picks logged after 2026-07-02 reach the 5-day grade (first land ~2026-07-10)._

## 5. Integrity checks (verifiability standard)

- ⚠️ 7 weekday(s) with no VALID scan because the cohort was logged after the open and excluded: 2026-06-15, 2026-07-06, 2026-07-07, 2026-07-09, 2026-07-13, 2026-07-27, 2026-08-03 (see AUDIT_LOG.md 2026-08-04)
- ⚠️ 10 weekday(s) with no scan (may be US market holidays): 2026-07-03, 2026-08-27, 2026-08-28, 2026-08-31, 2026-09-01, 2026-09-02, 2026-09-03, 2026-09-07…

## 6. v0.3 market-wide cohort (H-UNIV1 — registered 2026-07-08)

- **857 picks** across **88 scan days** (2026-07-09 → 2026-11-20); **546 unique tickers** (the H-IND1 effective-N readout the v0.2 cohort lacked).
- Graded: n=786, win 37%, median net -3.2%, mean -1.7%.
- Candidate pool + non-published eligibles: `candidates.csv` (forward-only control pool for H-CTRL).
- Young cohort — directional only; no v0.3 rule is registered yet, so nothing here feeds any verdict.

---
*Generated by weekly_report.py on 2026-11-21T20:23:00.993769Z. Forward log is the canonical record; backtest CSVs are gitignored and exploratory.*
