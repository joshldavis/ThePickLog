# IgnitionScan — Validation Plan & Pick-Log Spec

**Purpose:** Convert the prototype + the review feedback into something executable. This defines (1) exactly what to log on every pick, (2) a grading rule that measures something a real subscriber could actually capture, and (3) the validation tables that must be filled — and the bar they must clear — *before* you charge for access.

Companion files: `prototype/index.html`, `REQUIREMENTS.md`, `prefire-style-scanner-blueprint.md`.

**The one-line thesis this plan tests:** *Do A-rated picks outperform B, which outperform C, on a tradeable, cost-adjusted basis — and does that ordering hold out-of-sample?* If yes, you have signal. If no, you have a ranking system and should price/position it as a media product, not a predictive one.

---

## Part 1 — The pick log (capture on every pick, every day)

Three groups of columns. **Group A** drives the current score. **Group B** is instrumented now but *not* scored yet — you capture it from day one so you can later test whether it predicts, and let the data assign weights instead of guessing them. **Group C** is audit/identity.

### Group A — scored inputs (already in the model)
| Column | Type | Notes |
|---|---|---|
| `float_shares` | int | True public float (production data source), not shares outstanding |
| `rvol` | float | Volume ÷ average volume at screen time |
| `gap_pct` | float | Pre-market move vs prior close |
| `price_at_screen` | float | Reference price when logged |
| `float_score`,`rvol_score`,`gap_score`,`price_score` | float | Component sub-scores (0–100) |
| `score` | float | Weighted total |
| `tier` | A/B/C/D | Derived from score |

### Group B — instrumented, NOT scored yet (the review's missing variables)
| Column | Type | Notes |
|---|---|---|
| `catalyst_type` | enum | earnings / FDA / contract / M&A / partnership / reverse-split / offering / PR-only / none / unknown |
| `catalyst_time` | timestamp | When the news hit (pre-market vs prior close matters) |
| `dilution_flag` | green/yellow/red | Shelf/ATM/recent-offering history → dilution risk |
| `short_interest_pct` | float | % of float short (FINRA, lagged) |
| `days_to_cover` | float | SI ÷ avg volume |
| `halt_history_30d` | int | LULD halts in last 30 days |
| `prior_close_to_open_extended` | bool | Was the move already extended pre-market? |
| `market_regime` | enum | risk-on / neutral / risk-off (e.g. from SPY trend + VIX bucket) — same value tagged on all picks that day |

> Do **not** add any Group B field to the score until Part 3 shows it separates winners from losers. Capturing ≠ scoring.

### Group C — audit / identity (non-negotiable for the trust story)
| Column | Type | Notes |
|---|---|---|
| `pick_id` | uuid | Immutable |
| `published_at` | timestamp (ET) | When the pick was made public — set once, never edited |
| `trading_date` | date | Session the pick is for |
| `model_version` | string | So a weight change doesn't silently rewrite history |
| `row_locked` | bool | Pick row is append-only; grading writes to a separate outcomes table |

---

## Part 2 — The grading rule (measure something tradeable)

**The problem with the current rule:** "WIN = touched +20% within 5 days" counts a stock that ticks +20% pre-market then closes -40% as a win. On low-float names that's the base case, not the exception. A win rate built on "did it ever touch the level" describes volatility, not a return a subscriber could realize.

**Replace it with a defined, realizable rule.** Assume the only fill a subscriber can actually get at scale is the **regular-session open** on the pick's trading date (you cannot promise the 7:30am pre-market print). Then measure outcomes against defined exits, net of friction.

### Returns to record per pick (compute all; pick a headline)
| Metric | Definition | Role |
|---|---|---|
| `ret_open_close` | entry = day's open → exit = same-day close | **Primary headline** (day-trade assumption) |
| `ret_open_5dclose` | open → close of trading_date + 5 | Secondary (swing assumption) |
| `mfe_5d` | max favorable excursion over 5 days (the old "max gain") | Secondary — informative, **not** the headline |
| `mae_5d` | max adverse excursion (worst drawdown) over 5 days | **Show this.** The current product hides downside; this is the "risk area" the brief promises |

### Friction haircut (don't skip)
Low-float spreads are wide. Apply a configurable round-trip cost (start at **2%**, sensitivity-test 1%–3%) to every realized-return metric. Headline numbers are always **net of haircut**.

### What "WIN" means now
A WIN is `ret_open_close_net > 0` (configurable threshold). Also publish the full distribution (mean, median, % positive, and the MAE), not a lone win-rate number — distribution is harder to game and matches the transparency promise.

> Keep `mfe_5d` visible but clearly labeled "best-case intraday move, not an achievable return." Honesty about the gap between the two *is* the brand.

---

## Part 3 — Validation tables to fill before charging

### 3.1 The core table (the business lives or dies here)
Fill once you have enough graded picks (see sample bar below).

| Tier | N picks | Mean net ret (open→close) | Median | % positive | Mean MAE (drawdown) |
|---|---|---|---|---|---|
| A | ? | ? | ? | ? | ? |
| B | ? | ? | ? | ? | ? |
| C | ? | ? | ? | ? | ? |
| D | ? | ? | ? | ? | ? |

**Pass criteria (all four):**
1. **Monotonic:** A > B > C > D on both mean and median net return.
2. **Edge clears costs:** A-tier mean net return > 0 *after* the 2% haircut.
3. **Sample:** ≥ ~200 graded picks total and ≥ ~30 per tier before you trust the ordering. (30 trading days of ~a dozen picks is too few — that's noise.)
4. **Out-of-sample:** hold out the most recent ~25% of picks, fit nothing to it, and confirm the ordering still holds there. If it only works in-sample, it's curve-fit.

### 3.2 Variable-evaluation tables (decide what earns a place in the score)
One table per Group-B variable. Example — short interest:

| SI bucket | N | Mean net ret | % positive |
|---|---|---|---|
| <5% | ? | ? | ? |
| 5–15% | ? | ? | ? |
| 15–30% | ? | ? | ? |
| >30% | ? | ? | ? |

Repeat for `catalyst_type`, `dilution_flag`, `market_regime`, `prior_close_to_open_extended`. **Only** variables that visibly separate outcomes get promoted into the score — and then you re-fit weights from the data, not from intuition. (This is the disciplined version of the reviewer's reweighting table.)

---

## Part 4 — Go / no-go gates before you charge a dollar

| Gate | Requirement |
|---|---|
| G1 — Data | ≥ ~200 picks logged with immutable timestamps + stored inputs |
| G2 — Signal | Core table passes all four criteria in 3.1 (incl. out-of-sample) |
| G3 — Net edge | A-tier mean net return > 0 after the cost haircut |
| G4 — Legal | Securities-counsel review of copy, disclaimers, Terms complete |

**If G2/G3 pass:** you have a predictive product — charge for the screen + brief, with the track record as proof.
**If G2/G3 fail:** the score is a *ranking/triage* tool, not a predictor. That's not failure — it's the signal to position as a **media/community product** (morning brief, transparency, Hall of Shame, Discord) and price it as "we do the morning work for you," not "our algorithm predicts." Either way you ship something honest; the data tells you which business you're in.

---

## Part 5 — Legal posture fork (don't miss this)

The richer "morning brief" — *what we like / what we don't like / watch levels / risk area* — is more engaging and is **still legal as an impersonal newsletter** (the publisher's exclusion in *Lowe v. SEC* protects specific recommendations as long as they're the same for everyone, bona fide, and on a regular schedule). But it moves you off the ultra-conservative "we only publish data/screens" posture the prototype's disclaimer currently assumes, toward "we recommend specific setups to all subscribers." That's a fine place to be — it's just a different place, and it raises the bar on getting Terms and disclaimers reviewed (G4) before charging. Keep the brief **impersonal** (identical to all subscribers, no per-user tailoring) and **disclose your own positions**, and you stay inside the exclusion.

---

## Suggested immediate next step
Start logging (Part 1) and grading (Part 2) **now**, before any further UI work. The single most valuable asset you can build between today and launch is a real, immutable, cost-honest track record. Everything in Part 3 needs that data, and you can't fake your way to it later.

*This is a strategic/technical plan, not legal or financial advice. Obtain securities counsel before charging subscribers, and remember the model is unvalidated until the Part 3 tables say otherwise.*
