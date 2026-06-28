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
| **H-DIL** | does an active offering/shelf (`dilution_flag` = offering/shelf) separate winners from losers? | dilution caps a squeeze (new supply at the top) → plausibly *worse* forward returns, **but** an offering is also the very catalyst that ignites these names, so direction is not assumed | `dilution_flag` + `catalyst_type` capture began **2026-06-28** via free SEC EDGAR (`edgar_lens.py`); **no graded pick carries it yet**. Forward-only. Evaluate once enough dilution-bearing picks have graded. |

**Data note — `catalyst_type` is a filing proxy, not a news classifier.** It is derived only from
SEC filings (`offering` = 424B* in 7d · `8K` = recent 8-K · `filing` = other recent filing · `none`),
because a true news/PR catalyst is not reliably in EDGAR. Per the roadmap guardrail "don't half-build
a lever off an unreliable source," only the EDGAR-truthful part is captured, and it is labelled as such.

**Finding B (quality → shallower drawdown) is now testable forward.** Phase-1 (in-sample, as-of
grader) was a **NULL** after removing look-ahead. The blocker to a forward test was that quality was
never logged at screen time. As of **2026-06-28** the Quality-Lens grade (overall/label/classification
+ 7 category scores) is snapshotted per pick into the forward-only sidecar `edgar_snapshot.csv`
(point-in-time via `asof_grader.grade_asof`, so no Yahoo-style revision drift). This does **not**
re-open Finding B as a claim — it merely preserves the *option* to test it OOS later. Still
recommended-skip unless a real reason to sharpen the score emerges.

## Exit-rule hypothesis

**H-EX1 — registered 2026-06-23.** *The screen's edge is in the exit, not the selection.*

The in-sample evidence (first 65 graded picks) is that these names **spike then fade**:
82% touch +5% intraday within the 5-day window, 63% touch +10%, 54% touch +15%; the
typical pick reaches **+16.4%** max-favorable (median MFE) while the current same-day-close
exit realizes **−2.8%** avg. The hypothesis is that a disciplined profit target monetizes
the spike the screen is genuinely good at finding.

- **Rule (frozen):** rest a **+10% limit** over the 5-trading-day hold. If the 5-day high
  (`mfe_5d`) reaches +10%, the order fills → realized **+8% net** (target −2% cost haircut).
  Otherwise exit at the 5-day close (`ret_open_5dclose_net`). Deterministic from the forward
  log; no discretion.
- **Baseline to beat:** the **current** exit = same-day open→close, net (avg **−2.8%**,
  median −3.6%, win 40% at registration).
- **Pass criterion:** on **post-2026-06-23** graded picks, the H-EX1 arm's **avg net/trade
  (expectancy)** must exceed the same-day-close baseline, with the direction stable across
  weekly snapshots. Median and win% are secondary readouts.
- **In-sample signal at registration (not the test):** +10% target → 63% win, **+8.0%
  median**, −1.6% avg vs −2.8% same-day-close — i.e. **+1.2pp expectancy, +11.6pp median.**
- **Slippage caveat (must stay attached to every report):** fills are assumed exactly at
  +10%. On thin low-float names, limits gap through and fill quality is poor, so **real-world
  results will be worse than the proxy.** The 2% haircut does not capture gap-through. This
  is why H-EX1 is a *hypothesis to be falsified forward*, not a result.
- **Tracked by:** `weekly_report.py` §4d (all-time + post-registration), alongside the
  exit study (`exit_sim.py` → `reports/exit-study-LATEST.md`) which walks the daily path
  as the rigorous cross-check.

## Exit-rule hypothesis #2 — does a stop add value?

**H-EX2 — registered 2026-06-24.** *A profit target without a stop ignores the fat left
tail.* H-EX1 monetizes the spike but says nothing about the downside; the live log shows a
brutal left tail (median 5-day MAE ≈ −16%, worst −50%, **17% catastrophic-rug rate** with
MAE < −30%). H-EX2 asks whether pairing H-EX1's target with a disaster stop **improves
expectancy** versus the target alone.

- **Rule (frozen):** over the 5-trading-day hold, rest a **+10% limit AND a −20% stop**.
  Whichever level the daily path touches first exits the trade; if neither is touched, exit
  at the 5-day close. **Conservative same-day-collision convention: if a single session's
  range spans BOTH levels, assume the STOP filled first** (results can't be optimistically
  inflated). Fills assumed exactly at the level; same 2% cost haircut. Deterministic from
  the committed daily path (`paths.csv`); no discretion.
- **Why −20% (and not tighter):** the median pick already dips ≈ −16%, so a stop inside that
  would book a loss on the *typical* wobble and shred the spike H-EX1 is trying to catch.
  −20% sits **beyond** the median drawdown — it is a *disaster* stop aimed only at the
  −30%-and-worse rug tail, not a tight trade-management stop. (Frozen, not tuned; OOS judges.)
- **Baselines to beat (two):** primary = **H-EX1 (+10% target alone)** — does adding the stop
  raise avg net/trade? secondary = the current same-day-close exit. All three arms are
  computed on the **same path-bearing subset** so the comparison is apples-to-apples.
- **Pass criterion:** on **post-2026-06-24** graded, path-bearing picks, H-EX2's **avg
  net/trade (expectancy)** must exceed H-EX1's, with the direction stable across weekly
  snapshots. A null (the stop costs more in booked losses than it saves in avoided rugs) is a
  fully valid, expected outcome and would *keep H-EX1 stop-less*.
- **Data dependency / honesty note:** unlike H-EX1 (evaluable from `mfe_5d`), a target+stop
  rule needs the **order** of touches, which only the daily path resolves. `paths.csv` is
  **forward-only** (capture began ~2026-06-22), so the post-registration, path-bearing sample
  starts near zero and accumulates — exactly like H-SI. Until it does, §4e reports *pending*,
  not a result.
- **Slippage caveat (must stay attached):** thin low-float names **gap through stops** — a
  −20% stop can fill far below −20% on a halt-and-reopen. The 2% haircut does **not** capture
  gap-through, so realized H-EX2 results will be **worse** than this proxy, and worse for the
  stop arm specifically. This is why H-EX2 is a hypothesis to be **falsified forward**.
- **Tracked by:** `weekly_report.py` §4e (all-time context + post-registration test), with
  `exit_sim.py` (rule *"H-EX2 +10% target / −20% stop"*) walking the full daily path as the
  in-sample cross-check.

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
