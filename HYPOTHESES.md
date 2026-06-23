# Pre-registered hypotheses — IgnitionScan

**Registered:** 2026-06-22 · **Why this file exists:** these filters were spotted in an
*in-sample* cut of the first 52 graded picks. In-sample patterns overfit. To be honest,
the rules are frozen here **with a date**, and only picks logged **after** the registration
date count as the real (out-of-sample) test. `weekly_report.py` tracks both all-time and
post-registration performance automatically, so the forward log is the judge — not me.

## Baseline at registration (N=52 graded)
- Win rate (same-day open→close, net of 2% haircut): **44%**
- Avg net/trade: **−2.4%** · median **−2.8%**
- 5-day hold: 31% win, **+0.3%** mean (a few big winners carry it → expectancy, not win
  rate, is the real target).

## Selection-filter hypotheses
Each says "**skip** these picks." A filter passes only if, on **post-registration** picks,
the kept subset beats the unfiltered baseline on **avg net/trade** (the expectancy metric),
without shrinking the sample to uselessness.

| id | rule (skip if…) | rationale | in-sample signal at registration |
|----|------------------|-----------|-----------------------------------|
| **H-F1** | price < $1.00 | sub-$1 = manipulation / delisting risk | sub-$1 win 22% vs ≥$1 49% |
| **H-F2** | float ≥ 3M shares | the screen's edge is the *thinnest* floats | ≥3M win 25% vs <3M 48% |
| **H-F3** | gap ≥ +20% at screen | chasing an extended gap buys the top | ≥+20% was 0/2 |
| **H-F4** | tier A or B (hot) | Finding A: hottest momentum = deepest drawdown | already holds out-of-sample |
| **H-CLEAN** | any of F1–F4 | combined "only the clean setups" filter | — |

## Open question (no pre-set direction)
| id | question | why two-sided | data status |
|----|----------|---------------|-------------|
| **H-SI** | does short interest ≥20% separate winners from losers? | high SI is squeeze-prone — violent *both* ways, so neither direction is assumed | short-interest capture began 2026-06-16; **no graded pick carries it yet** (all 65 graded predate capture). Tracked in the weekly report; evaluate once enough SI-bearing picks have graded. |

## Exit-rule hypothesis
- **H-EX1 (pending):** the exit study (`exit_sim.py` → `reports/exit-study-LATEST.md`)
  explores profit-target / stop / trailing rules in-sample. **Do not adopt a rule from the
  study directly.** Pick one candidate, register it here with a date, then judge it only on
  post-registration picks — same discipline as the filters.

## Success / kill criteria
- **Evaluate** once there are **≥ 30 post-registration graded picks** per arm (directional
  before that).
- **Keep** a filter only if post-registration kept-subset avg net/trade **> baseline** and
  the direction is stable across the weekly snapshots.
- **Kill** any filter that doesn't separate winners from losers out-of-sample. A null is a
  valid, honest result — most patterns in 52 picks will not survive.
- Win rate is a **secondary** readout; the objective is positive expectancy with bounded
  drawdown. Never optimize win rate at the expense of expectancy.

---
*Pre-registration, not investment advice. The forward log (picks.csv/outcomes.csv) is the
only judge; everything here is a hypothesis until post-registration data says otherwise.*
