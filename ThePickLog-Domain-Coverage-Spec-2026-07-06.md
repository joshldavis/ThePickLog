# ThePickLog — Construct Domain & Coverage Spec

**Content-validity artifact (P2, gap register row 1)**
Date: 2026-07-06 · Companion to `ThePickLog-Validity-Framework-Messick-2026-07-06.md` §2.1

Messick's content aspect asks one question: *do the score's inputs representatively and relevantly sample the domain of the construct, without irrelevant contamination?* You cannot answer that without first writing down the domain. This document does that, then maps each driver to how (or whether) the current model represents it — and states, in the open, where the model is underrepresented.

---

## 1. The construct domain

**Construct (restated):** the forward, tradeable favorable-move potential of a microcap at screen time.

The domain of plausible **drivers** of that construct — the full space content validity says we should be sampling from — breaks into seven families. This list is the standard against which "does the score cover the domain?" is judged.

| Family | Drivers | Why it plausibly matters to spike-and-fade |
|---|---|---|
| **A. Supply / float mechanics** | Free float, share structure, dilution/offering risk (ATM, S-1, warrants), lockups | Thin float is the amplifier; active dilution is the fade's fuel |
| **B. Demand / flow** | Relative volume, gap, pre-market volume, order-flow imbalance, retail/social attention | The spike is a demand shock; its size and durability set the move |
| **C. Price / level** | Absolute price band, prior-day range, distance from key levels/round numbers | Cheap thin names behave differently; levels shape reversal points |
| **D. Catalyst** | News type (PR vs earnings vs FDA vs contract), catalyst "hardness," recency | A hard catalyst sustains; a soft PR fades — this is the fade's *cause* |
| **E. Liquidity / microstructure** | Bid-ask spread, depth, borrow availability, short interest, halt status | Determines whether the move is *realizable* and how violently it fades |
| **F. Regime / context** | Market regime (risk-on/off), sector heat, time-of-day | The same setup pays differently across regimes |
| **G. Fundamentals / quality** | Cash runway, going-concern, governance, valuation | The Quality Lens domain; separates durable from doomed names |

---

## 2. Coverage matrix

For each driver: **Scored** (in the live momentum composite), **Captured-unscored** (logged forward-only, awaiting validation), or **Not captured**.

| Driver | Status | How represented | Notes |
|---|---|---|---|
| Free float | **Scored** | `float_score`, weight 0.30 | Thinnest floats → 100 |
| Relative volume | **Scored** | `rvol_score`, weight 0.35 | Largest input weight |
| Gap | **Scored** | `gap_score`, weight 0.25 | **Uses `abs(gap)` — see §4 CIV flag** |
| Price band | **Scored** | `price_score`, weight 0.10 | 100 inside the 0.50–5 band |
| Dilution / offering | Captured-unscored | `dilution_flag` (2026-06-28+) | Group B; awaiting OOS (H-DIL) |
| Short interest | Captured-unscored | `short_interest_pct` (06-28+) | Group B; awaiting OOS (H-SI) |
| Catalyst type | Captured-unscored | `catalyst_type` (06-28+) | Group B; the fade's likely cause, unscored |
| Market regime | Captured-unscored | `market_regime` (06-28+) | Generalizability gate input |
| Fundamentals / quality | Captured-unscored | Quality Lens 7 components, `edgar_snapshot.csv` | Deliberately separate, not in score |
| Spread / depth | **Not captured** | — | Proxied only as the flat 2% haircut |
| Borrow availability | **Not captured** | — | Central to a fade thesis; absent |
| Order-flow imbalance | **Not captured** | — | Requires L2 data; out of scope for now |
| Retail / social attention | **Not captured** | — | The demand shock's origin; unmeasured |
| Prior-day range / levels | **Not captured** | — | Derivable from `paths.csv` later |
| Time-of-day / halt status | **Not captured** | — | Screen is EOD-oriented; halts unlogged |

**Coverage summary:** the live score samples **4 of ~15 drivers, and all 4 come from only two families (A supply, B demand)**. Families D (catalyst), E (liquidity/microstructure), and F (regime) — which contain the most plausible *causes of the fade* — are entirely unscored, though several are now being captured.

---

## 3. The underrepresentation finding (stated openly)

Messick's first threat is construct underrepresentation. Here it is explicit and, per the North Star, admitted rather than hidden:

**The scored composite is a momentum/heat index, not a representation of the fade thesis it serves.** The project's claimed edge is that names *spike then fade*, and the money is in a disciplined exit. But the drivers that would *explain and predict the fade* — active dilution, catalyst hardness, borrow/spread, regime — are exactly the ones **not** in the score. The score measures the size of the spike (supply × demand); it says nothing about the fade's depth or timing.

This is consistent with, and now corroborated by, the structural evidence (see companion `ThePickLog-Structural-Justification-2026-07-06.md`): the momentum tiers order *drawdown*, not *return* — precisely what you'd expect from an index that captures heat but underrepresents the fade.

**The honest label:** the momentum score is a validly-constructed **activity/heat meter over families A–B**. It is *not* a representation of the full favorable-move construct, and it should be described that way on-site — matching the code's own comment that "a high score measures activity, not safety."

---

## 4. Construct-irrelevant variance flags in the inputs

Two content-relevance issues worth a decision:

1. **`gap_score` uses `|gap|`.** A name gapping **down** 15% scores identically to one gapping **up** 15%. If the construct is *favorable*-move potential, direction is relevant, so rewarding raw magnitude injects construct-irrelevant variance. Decide deliberately: is the thesis direction-agnostic (magnitude = volatility = opportunity for the exit rule), or should gap be signed? Either is defensible; the current choice is undocumented.
2. **Flat 2% haircut as the only liquidity representation.** Spread on thin floats varies enormously; a single constant both under- and over-penalizes. It's an honest *conservative* proxy for grading (good for P3), but it means liquidity is absent as a *selection* input where it most plausibly predicts the fade.

---

## 5. What this licenses and what it forbids

- **Licensed:** describing and using the score as a heat/activity index over supply-and-demand, with tiers presented as *intensity*, not *quality*.
- **Forbidden (until validated):** any claim that a higher tier means a better name. The domain it samples is too narrow to support that, and §3 says why.
- **Path to wider coverage:** the Group B captures (dilution, SI, catalyst, regime) are the pre-registered route to representing families D–F. Each must clear its own OOS test (H-DIL, H-SI, and new registrations for catalyst/regime) before entering the score — never added on in-sample plausibility alone.

---

*Content validity is not "the factors sound reasonable." It is "the inputs representatively sample a written-down domain, and where they don't, we say so." This document is that written-down domain.*
