# IgnitionScan — Advancing the Model, Product & Marketing

**Owner:** Josh
**Date:** June 15, 2026
**Companion files:** `SYNTHESIS.md`, `IMPROVEMENTS-v0.3.md`, `REQUIREMENTS.md`, `VALIDATION-PLAN.md`, `prefire-style-scanner-blueprint.md`

This is the strategic layer above the v0.3 spec. Where `IMPROVEMENTS-v0.3.md` lists *what to build next*, this document argues *how the bet itself should change* — across model, product, and marketing — given the three lenses in `SYNTHESIS.md` (Jobs to be Done, Psychology of Influence, Messick construct validity). Each move names the framework it serves so the reasoning is auditable.

---

## The one-line thesis

The upside is unpredictable, but the **honesty is scarce**. So the highest-expected-value path is to build a transparency-driven accountability brand *now*, run a rigorous validity machine in the background, and upgrade to a "predictive" claim only if and when the immutable forward log earns it — never before.

---

## 1. Model — predict the *survivable* move, not the explosion

### 1.1 Reframe the core hypothesis (the biggest single idea)
The blueprint already concluded that predicting which sub-$5 low-float name explodes is noise-dominated. The synthesis points somewhere more tractable: **the real edge is most likely the Quality Lens as a downside filter, not the momentum score as an upside predictor.**

- **Old hypothesis (hard, likely false):** "A-tier names go up more than B/C/D."
- **New hypothesis (tractable, testable today):** "Quality-Green names have shallower drawdown (MAE) and far fewer catastrophic rugs than Red/Black names."

Downside is far more predictable than upside, and MAE is now captured on every pick — so this is directly testable with the data already being logged. If it holds, the headline claim becomes: *"We don't tell you what moons — we tell you which movers won't gut you."* More honest, more defensible, and a better fit for the real job (see §2).
*Framework: Messick (a claim you can actually validate); JTBD (the "don't get burned" job).*

### 1.2 Fix two validity threats before any table means anything
- **The 16-ticker seed universe is a hidden selection bias.** A hand-picked list quietly curves the sample; you cannot generalize from it. Widening to a full-market screen (REQUIREMENTS FR-1) is not just a feature — it is what makes the track record *valid*. *(Messick: generalizability.)*
- **Forward-logging alone is too slow.** ~12 picks/day means months to reach the N≥200 / ≥30-per-tier bar. Run a **two-track model:**
  - *Backtest track* — run the deterministic score over history to get thousands of picks now, for **variable selection only** (which Group-B fields separate winners from losers). Label it loudly: in-sample, overfit-prone.
  - *Forward track* — the immutable live log, the only thing that backs the public credibility claim.
  - **Never let the backtest contaminate the forward log.** Backtest does Messick's *substantive/structural* exploration; the forward log does the *external/generalizability* proof.

### 1.3 Publish calibration, not just tiers
Replace (or augment) A/B/C/D with a **calibration curve**: "names we scored 75+ closed positive X% of the time." Calibration is the gold standard of a validity claim and is nearly impossible to fake — the verifiability standard taken to its rigorous end.
*Framework: Messick (external validity); Influence (un-fakeable proof).*

---

## 2. Product — the moat is the accountability engine, not the watchlist

You have built something rarer than a screener: a machine that grades its own calls honestly and immutably. **That is the product.** Three ways to advance it.

### 2.1 Turn the grader outward (the wedge)
Extend the same immutable grading to *other people's* public calls — the gurus, the Discord pumpers, the incumbents whose records read "all pending." An accountability layer is product, moat, and marketing simultaneously, and no competitor can copy it without exposing their own record. It aims the JTBD "help me not get burned" job at the entire category, not just your own picks. (The blueprint's "Hall of Shame," generalized.)
*Framework: JTBD (category-level job); Influence (social proof + authority).*

### 2.2 Activate the dormant paper-trading loop
Let users paper-trade the screen via the existing Alpaca integration and watch *their* realized results accumulate against the model. Converts passive readers into engaged users and generates honest social proof. **Constraint:** keep it strictly user-driven, never per-user advice, or it breaks the publisher's exclusion (REQUIREMENTS §7).
*Framework: JTBD (engagement); Legal (impersonality).*

### 2.3 Make the funnel the proof
Free = the full audited history (lets a stranger verify before paying). Paid = today's edge and the morning brief (timeliness). The product advance is making the proof so good it sells itself — the upgrade prompt points at *today's* brief, not at hidden history.
*Framework: JTBD (verify-before-hire); Influence (honest social proof).*

---

## 3. Marketing — anti-marketing, and don't sell yet

### 3.1 Lead with what competitors hide
Your one un-copyable asset is radical transparency, so build the brand on the honesty gap: *"We publish every loser. Here's our worst week."* Position directly — carefully and factually — against the category's fakery (e.g. a performance page where every setup reads "pending").
*Framework: Influence (candor as differentiation).*

### 3.2 The grading engine is a content flywheel
The grader already produces honest daily content for free: "here's how yesterday's screen actually did, dogs included." That is the verifiability standard turned into distribution — build-in-public that compounds credibility instead of spending it.
*Framework: Influence (consistency + social proof over time).*

### 3.3 Sequencing beats messaging
**Do not turn on billing or hard marketing until there is a real 6–8 week graded record** (REQUIREMENTS §9). A paywall over an empty record is exactly the incumbent's mistake. The marketing move *right now* is audience-building through transparency content — banking credibility to spend at launch, not selling.
*Framework: Messick (don't claim what the data doesn't yet support — gate A7).*

---

## 4. How it sequences (recommended)

| Phase | Model | Product | Marketing |
|---|---|---|---|
| **Now → 4 wks** | Widen universe; stand up backtest track for variable selection; keep forward log immutable | Ship A1–A3 (done); build the brief (B1) | Start the transparency content flywheel; **no selling** |
| **4–8 wks** | Test the downside/MAE hypothesis; build calibration curve | Outward-facing "graded calls" accountability feature | Position vs. category fakery; grow waitlist on proof |
| **8 wks +** | If forward log + out-of-sample clear the bar → earn the predictive claim | Activate paper-trading loop; turn on Stripe | Launch against a real, audited record |

---

## 5. The decision this forces

The data fork in `VALIDATION-PLAN.md` Part 4 (predictor vs. media product) will most likely resolve toward **media / accountability brand** — because the upside is unpredictable but the honesty is scarce. That is not a downgrade; it is the more durable business, and the one you can start truthfully today. The predictive claim is an *upgrade you unlock later* with the forward log — and the discipline of this whole strategy is refusing to claim it before then.

---

*Strategic plan, not legal or financial advice. The model is unvalidated until VALIDATION-PLAN Part 3 clears its bar; obtain securities counsel before charging subscribers (gate G4).*
