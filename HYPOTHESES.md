# Pre-registered hypotheses — ThePickLog

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
| **H-INS** | does net open-market insider buying (`insider_net` = +1) separate winners from losers? | insiders buying their own money in is a classic conviction tell → plausibly *better* forward returns, **but** in spike-prone microcaps a filed buy can also be a pump signal, so direction is not assumed | net open-market insider buy/sell (Form 4 codes P/S only, 90-day window) capture began **2026-07-08** via free SEC EDGAR (`edgar_lens.py`) → `edgar_snapshot.csv`; **no graded pick carries it yet**. Forward-only. Most microcap picks show *no* open-market activity in-window (`insider_net` blank), so expect this to accumulate slowly like H-DIL. Evaluate once enough insider-bearing picks have graded. |

**Data note — `catalyst_type` is a filing proxy, not a news classifier.** It is derived only from
SEC filings (`offering` = 424B* in 7d · `8K` = recent 8-K · `filing` = other recent filing · `none`),
because a true news/PR catalyst is not reliably in EDGAR. Per the roadmap guardrail "don't half-build
a lever off an unreliable source," only the EDGAR-truthful part is captured, and it is labelled as such.

**Data note — `insider_net` is open-market ONLY, and insider *ownership %* is deliberately not
synthesized.** `insider_net` nets only Form 4 discretionary trades (code `P` buy / `S` sell); grants,
option exercises, tax-withholding and gifts (`A`/`M`/`F`/`G`…) are excluded so a "+1" means an insider
chose to put their own money in, not comp mechanics. Insider *ownership %* stays "not checked" because
an honest figure needs an all-insiders aggregate against shares outstanding that Form 4 alone can't
give — same guardrail as above. `insider_net` also feeds the point-in-time Quality-Lens grade (the
`management` category) via the `insiderNet` input, so the snapshot grade reflects it going forward.

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
- **Bayesian read-out (added 2026-07-02, priors frozen that date):** `bayes_h_ex1.py`
  maintains a Beta-Binomial posterior on the +10% touch rate (headline flat Beta(1,1);
  Jeffreys(0.5,0.5) and skeptical Beta(10,10) as sensitivity), reporting P(touch rate >
  breakeven) for both the beat-baseline and absolute-profit lines →
  `reports/bayes-h-ex1-LATEST.md` + a live dashboard panel (browser recomputes
  independently from the CSVs; parity-tested). This is a *read-out* of how much the log
  has learned, not a new pass/fail criterion — §4d expectancy vs baseline stays the
  registered judge, and the breakeven lines are plug-in translations whose own noise is
  not propagated (see BAYESIAN-ROADMAP.md R3).

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

## Exit-rule batch #2 — registered 2026-07-02

Seven further exit hypotheses, frozen together on this date. All follow the H-EX1/H-EX2
conventions unless stated: 2% cost haircut, fills assumed exactly at the level, conservative
same-day-collision rules (ambiguity resolves against the strategy), deterministic from
outcomes.csv / paths.csv, no discretion. **Judged on post-2026-07-02 graded picks only.**

**⚠️ Family-wise honesty note (must stay attached):** registering seven rules at once means
one may beat baseline **by luck**. No single arm from this batch is "validated" merely by
winning its own comparison — the batch is a *ranked screen*. Any winner must (a) beat its
baseline on avg net/trade, (b) hold direction across ≥3 consecutive weekly snapshots, and
(c) remain the winner while the sample keeps growing. Prefer the simplest rule among
statistical ties.

| id | rule (frozen) | baseline to beat | data needed |
|----|---------------|------------------|-------------|
| **H-EX3** | **Target sweep:** as H-EX1 but at **+5%** (net +3%), **+15%** (net +13%), **+20%** (net +18%); unfilled → 5-day close | H-EX1 (+10%) and same-day close | outcomes.csv (`mfe_5d`) |
| **H-EX4** | **Time stop:** +10% limit; if unfilled by the **day-2 close**, exit at day-2 close (don't wait out days 3–5) | H-EX1 | paths.csv (touch day + day-2 close) |
| **H-EX5** | **Hold-length baselines:** no target — exit at **day-1 close** (arm a) or **day-2 close** (arm b) | same-day close AND 5-day close | paths.csv |
| **H-EX6** | **Partial exit:** sell **half** at +10% (net +8%), half rides to the 5-day close | H-EX1 (does keeping half the tail beat full exit?) | outcomes.csv |
| **H-EX7** | **Trail after target:** once a daily high touches +10%, arm a trailing stop **15% below the running max daily high** (trail level computed from *prior* days' highs only — no same-day ratchet); exit when a day's low touches it; never armed → 5-day close | H-EX1 | paths.csv |
| **H-EX8** | **Tier-conditioned target:** tier A/B → **+20%** target, tier C/D → **+10%**; unfilled → 5-day close | H-EX1 (uniform +10%) | outcomes.csv + picks.csv tier |
| **H-EX9** | **Stop sweep:** as H-EX2 but with **−10%** and **−30%** stops (same stop-first collision convention) | H-EX2 (−20%) and H-EX1 (no stop) | paths.csv |

Registration rationale (in-sample context, not the test): most picks touch +5% (82%) and
+10% (63%) but finish negative (median 5-day −7.9%); MFE clusters early in the window;
the return distribution is fat-tailed right (a few +100%+ runs) and fat-tailed left
(≈16% rug rate) — so target level, exit timing, tail participation, and disaster stops
are the four levers worth sweeping. Prior expectations, stated for honesty: H-EX9 tighter
stops likely **hurt** (gap-through), H-EX5 short holds likely **beat** 5-day hold, H-EX7
trailing is the most slippage-fragile arm in the batch.

- **Slippage caveat (inherited from H-EX1/H-EX2, applies to every arm):** thin floats gap
  through limits and stops; real fills are worse than the proxy. Any edge under ~+1%/trade
  is treated as noise.
- **Tracked by:** wiring into `exit_sim.py` / `weekly_report.py` is a follow-up; **the
  registration date above governs the out-of-sample window, not the code date.** Until
  wired, arms are computable by hand from the committed CSVs.

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

## Validity-study registrations (frozen 2026-07-07)

Emerged from the empirical validity studies (`ThePickLog-Empirical-Validity-Studies-2026-07-07.md`).
In-sample findings are diagnostics only; these are frozen here so only picks logged **after
2026-07-07** count, and none changes the live model (P5).

| id | test | direction / rationale |
|----|------|-----------------------|
| **H-SUB1** | does 5-day MFE (spike size) scale monotonically with rvol at screen time? | the unique prediction of the fade thesis; absence means the "spike" label is mis-specified |
| **H-STR1** | does a **float-only** score reproduce the 4-factor tier ordering? | rvol sub-score is <10 for 81% of picks → the .35 rvol weight may add no ordering info |
| **H-STR2** | re-derive weights + cutpoints from post-reg data, register, judge OOS vs v0.2 | cutpoints/weights are currently unjustified; never promote an in-sample fit |
| **H-REG** | skip picks tagged `market_regime = risk-on`; does the kept subset beat baseline OOS? | in-sample risk-on was −5.49% vs −1.7% otherwise (regime-fragile) |
| **H-CTRL** | capture matched random in-universe microcaps the screen did **not** pick (forward-only) | enables a proper screened-vs-unscreened discriminant test |
| **H-REFLEX** | does publishing a pick move the name? (post-publication drift/volume vs audience size) | reflexivity is CIV; ~nil now (no traffic), monitor as reach grows |

---

## Batch #3 — exit rule + methods registrations (frozen 2026-07-08)

Registered together on this date. Only picks logged **after 2026-07-08** count toward any
verdict below. Conventions inherited from H-EX1/H-EX2 (2% haircut, fills at level,
conservative collisions, deterministic from committed CSVs).

### H-EX10 — tier-gated, amplitude-matched exit

**Rule (frozen):** tier **A/B** picks → **+20% target** (net +18%), unfilled → 5-day close.
Tier **C/D** picks → **same-day close** (no overnight hold, no target).

**Baselines to beat:** same-day close on all picks (primary) and H-EX8 (secondary — does
gating C/D out of the target beat giving them a +10% target?). Judged on avg net/trade.

**Registration rationale (in-sample context, NOT the test):** tiers rank spike *intensity*
(A/B median 5-day MFE 23–28%, P(touch +10%) 75–81%; C/D ≈ 10–13% and ~50%), so the target
should be scaled to the tier's amplitude and withheld where the amplitude isn't there. In
the daily-path replay, A/B + 20% target returned +2.8% avg vs −0.6% same-day baseline
(n=15), while every C/D target variant lost to same-day close.

**⚠️ Concentration caveat (must stay attached):** 7 of 28 in-sample A/B picks are CUPR —
the single best ticker in the log (median MFE +61.7%). The in-sample signal may be one
name's pump. **Robustness clause:** a post-registration win only counts if it (a) survives
a leave-one-ticker-out check (drop the largest-contributing ticker; direction must hold)
and (b) survives the H-IND1 cluster bootstrap. Slippage caveat applies with extra force:
A/B names are the thinnest in the log.

### H-IND1 — effective sample size / independence correction (methods, not a trading rule)

**Registered acknowledgment:** the scan universe is a **fixed 16-ticker list**
(`CONFIG["UNIVERSE"]`), and 13–16 of the 16 pass the screen on every scan day. Outcomes on
the same ticker across consecutive days share overlapping 5-day price paths and are
mechanically correlated. Headline stats quoted as "n=165 picks" therefore carry the
precision of roughly **n≈16 name-level bets** (fewer, counting episodes: the 31 rug rows
collapse to ~10 tickers / a handful of collapse events). Per-ticker avg net spans −13.3%
(HKIT) to +1.9% (CUPR) — ticker fixed effects plausibly dominate every subgroup table.

**Rule (frozen):** from this date, every hypothesis verdict (including the Gate-1 verdict
scheduled 2026-07-27) must report, alongside the pooled stat: (a) a **cluster bootstrap by
ticker** (resample tickers with replacement, recompute the arm-vs-baseline delta; report
the bootstrap interval), and (b) the **per-ticker sign count** (how many of the 16 names
individually favor the arm). A pooled win that fails both is reported as **not
established**, not as a win. This applies retroactively as a re-read of prior tables, and
prospectively to all OOS windows. The R1 Beta-Binomial tracker's iid assumption is flagged
as violated; its posterior is directional only until re-specified with clustering.

### H-DEDUP — one-entry-per-episode re-read

**Rule (frozen):** re-evaluate the headline stats and every registered filter/exit arm on a
**deduplicated pick set**: keep only the *first* pick of each ticker per episode, where an
episode ends after 5 consecutive trading days without that ticker being re-picked (i.e., no
overlapping holds of the same name). In the current log this collapses ~300 picks to
roughly one row per ticker-episode.

**Question:** does *any* in-sample or OOS finding (Finding A, H-F1..F4, H-EX1..EX9, tier
tables) survive dedup? A finding that exists only in the duplicated view is an artifact of
repeated sampling, not a property of the picks.

### H-UNIV1 — universe expansion (structural, forward-only)

**Registered intent:** nothing in this log generalizes beyond the 16 hardcoded names. The
external-validity claim ("this screen finds low-float spike-fade names") requires a
market-wide candidate pool. Plan: replace or augment `CONFIG["UNIVERSE"]` with a true
market-wide low-float gap scan (or, minimally, a rotating universe), version-bump the model
(v0.3), and treat the fixed-16 record as its own closed cohort. Complements H-CTRL: the
matched-control test is uninterpretable while the "screen" admits ~100% of its universe
daily — there is no unscreened in-universe control to match against.

**Execution (frozen 2026-07-08; free-feed amendment 2026-07-09):** implemented as
`universe.py` + `ignitionscan.py scan-market`. **Operating source = free Yahoo
screeners** (`UNIV_SOURCE=yahoo`), cohort tag `model_version = v0.3-yf` — zero data
cost, same feed lineage as the v0.2 record. An optional later upgrade to Alpaca SIP
(`UNIV_SOURCE=alpaca`) would start a NEW sub-cohort tag (`v0.3-alpaca`); tags are
never mixed, so provenance stays attributable per row.

- **Candidate pool (yahoo):** custom market-wide criteria query (percent change ≥
  the +10% gap gate, price inside the frozen 0.50–10 band, US-listed; paged) ∪
  predefined lists (day gainers, small-cap gainers, aggressive small caps, most
  actives). OTC / pink sheets excluded; symbol hygiene drops
  units/warrants/rights/share-classes. Per-name quotes are premarket-aware
  (preMarketPrice preferred at scan time); float = Yahoo floatShares (fallback
  sharesOutstanding), same as v0.2.
  **Documented limitation:** before the open Yahoo's list rankings lag, so a name
  moving ONLY in today's premarket may not surface until the open; yesterday's
  movers gapping again are caught (the premarket gap gate does the real selection).
  This biases v0.3-yf toward continuation gappers — acceptable and disclosed; the
  Alpaca upgrade closes it.
- **Candidate pool (alpaca, dormant):** Alpaca screener, top-50 pre-market gainers ∪
  top-100 most-actives (by volume), same hygiene; float = free SEC EDGAR
  shares-outstanding proxy.
- **Eligibility gates (frozen):** price 0.50–10.00 (the v0.2 band) · gap ≥ **+10%**
  (up-gaps only) · rvol ≥ **2.0** · EDGAR shares-outstanding float proxy
  **0 < shares ≤ 50M** (missing share data EXCLUDES — never a free float score).
- **Scoring:** the UNCHANGED v0.2 formula/weights/tier cutpoints (PRINCIPLES P5).
  Selection = **top 10 by score** per day.
- **Control pool:** every screened candidate — eligible or not, published or not — is
  logged to `candidates.csv` with a reject reason / published flag. The
  eligible-but-unpublished names are H-CTRL's forward-only unscreened control group.
- **Cohort separation:** the v0.2 fixed-16 record is CLOSED. `weekly_report.py`,
  `hypo_eval.py` (leaderboard/gate), `bayes_h_ex1.py`, and `exit_sim.py` all read the
  v0.2 cohort only; v0.3 appears as its own report section. No existing hypothesis
  verdict (incl. Gate-1 on 2026-07-27) reads a v0.3 row. New v0.3 rules require new
  registrations with their own baselines.
- **Changing any gate or the top-N cap requires a new registration** — they are part
  of the frozen definition, not tunables.

---
*Pre-registration, not investment advice. The forward log (picks.csv/outcomes.csv) is the
only judge; everything here is a hypothesis until post-registration data says otherwise.*
