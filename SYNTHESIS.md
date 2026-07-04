# ThePickLog — Synthesis: JTBD × Influence × Messick

**Owner:** Josh
**Date:** June 15, 2026
**Companion files:** `REQUIREMENTS.md`, `VALIDATION-PLAN.md`, `prefire-style-scanner-blueprint.md`, `IMPROVEMENTS-v0.3.md`

---

## 0. Why this document exists

The product already has a North Star — the **verifiability standard**: *"Can a stranger visit this site and verify that every claim is true?"* That standard is correct but informal. This document layers three established frameworks on top of it, because each one catches a specific way the standard can quietly fail:

- **Jobs to be Done (JTBD)** — tells you *what job* the verifiable claims are being hired to do, and therefore which claims matter.
- **Psychology of Influence (Cialdini, ethical reading)** — tells you *how* to present the proof so a skeptic updates honestly.
- **Messick construct validity** — tells you whether your proof *actually means what you claim it means*.

They stack into one pipeline: **JTBD defines the claim → Messick verifies the claim is true → Influence presents the claim so it lands.** Stated as an upgraded North Star:

> *We publish a Messick-style validity argument in the open, framed to the job the data actually supports, and let persuasion work only through the parts that survive a stranger's scrutiny.*

---

## 1. Jobs to be Done

### 1.1 The job, stated properly
Nobody hires a screener for "screening." The functional job is *"decide which low-float names to act on this morning without doing the 6am work myself."* The deeper emotional/social job is *"act with conviction I won't regret — and be able to justify the decision afterward, to myself and to anyone who asks."*

That reframe is why verifiability is not a marketing nicety: **the track record is the core functional deliverable** (it de-risks the decision), and verifiability is the emotional/social job (let me trust this, and let me show I wasn't reckless).

### 1.2 The job resolves the biggest open question in the project
`VALIDATION-PLAN.md` Part 4 frames a go/no-go as **"predictive product vs. media/community product."** That looks like a data question; it is really a JTBD question. The two outcomes serve different hired jobs:

| If the data says… | The job you can charge for is… | What sells it |
|---|---|---|
| G2/G3 pass (tiers separate, A-tier edge clears costs) | "Tell me what to act on" — a **predictive** job | The validated track record |
| G2/G3 fail | "Do the morning work for me, honestly" — a **media/triage** job | Transparency, the brief, the downside honesty |

Either way you ship something honest. The discipline JTBD adds: **decide this fork consciously when the Part 3 tables are in — don't default to "predictor" because it sounds better.**

### 1.3 Anxieties = the claims you must let people verify
Every anxiety in the hiring decision is a job the product must visibly do:

- *"Is this just another pump?"* → the Quality Lens (risk label) on the watchlist row.
- *"Will I actually get filled at that price?"* → grading on the **realizable open→close**, not the pre-market print.
- *"How far does it drop before it works?"* → **MAE / worst-dip** now shown on the Track record page.
- *"Are you cherry-picking?"* → blended stats including every miss; immutable log.

JTBD test for any future feature: *which anxiety in the hiring decision does this resolve?* If none, it is noise that dilutes trust.

---

## 2. Psychology of Influence (the ethical reading)

### 2.1 The legal posture *forces* the ethical version
This is the cleanest fit in the project. The publisher's-exclusion constraints in `REQUIREMENTS.md` §7 (impersonal, regular, bona fide, disinterested) legally **prohibit** the manipulative forms of Cialdini's principles — fabricated scarcity, "DM us for picks," pay-to-feature social proof. Those would void *Lowe v. SEC* protection **and** break the verifiability standard at the same time. So you don't get to choose manipulative influence even if you wanted to. What remains are the honest mechanisms — and they are already your strongest assets:

| Principle | Honest mechanism already in the product | Manipulative version (forbidden) |
|---|---|---|
| **Commitment & consistency** | Immutable, timestamped pick log — you said it *before* the outcome and can't edit it | Quietly editing or deleting losers |
| **Liking (candor)** | Worst misses beside best calls; blended win rate incl. misses; MAE shown | Curated win wall |
| **Authority** | Disclose operator positions; publish the exact formula | "Proprietary AI trained on 830 explosions" |
| **Social proof** | A real, public, growing record anyone can re-derive | Fake "1,247 traders viewing now" |
| **Scarcity** | Genuine early-access cohort cap (first 500 / first $99 tier) | Countdown timers that reset |

### 2.2 The one test
Would the technique still work if the user fully understood you were using it? **Pre-committed public picks pass. A win rate computed on "ever touched +20%" fails** — which is exactly the bridge to Messick.

---

## 3. Messick construct validity

Messick's unified validity says scores are not valid in the abstract — only the **inferences and actions** drawn from them are. `VALIDATION-PLAN.md` is already a construct-validity argument; naming the six facets shows where the gaps are.

| Facet | Question | Where it lives in the project | Status |
|---|---|---|---|
| **Content** | Does the score cover the construct ("ignition setup")? | 4 scored inputs (float/RVOL/gap/price). Group B (catalyst, dilution, short interest, regime) is the plan admitting the construct is **under-represented**. | Partial — instrumenting (short interest now captured) |
| **Substantive** | Is there a theory for *why* each signal predicts? | Guide page explains each input | Stated; not yet tested |
| **Structural** | Does the A/B/C/D scale mirror the outcome structure? | The monotonicity pass criterion (A>B>C>D) | Pending data |
| **Generalizability** | Does it hold out-of-sample / across regimes? | 25% holdout; N≥200 / ≥30 per tier; `market_regime` tag | Pending data (biggest current threat: small N) |
| **External** | Do scores correlate with independent reality? | Core table in 3.1 — grades vs. real net returns | Pending data |
| **Consequential** | What happens to people who *act* on the score — and does it measure what they think? | The "touched +20% = WIN" critique; MAE disclosure; over-concentration risk | **Fixed in metric; surfaced in UI** |

### 3.1 The single most important finding
The original "WIN = touched +20% within 5 days" rule has a **construct-validity defect**: it measures volatility, not a return a subscriber could realize. A user infers "edge" from a number that doesn't carry it. The fix — **open→close, net of a 2% haircut, with MAE shown** — is precisely a consequential-validity correction, and it is now the basis of WIN/MISS and the Track record page.

The payoff of Messick's language: a score can be **statistically real and still invalid in use** if the metric or framing leads people to over-concentrate on illiquid names. That is the one risk the verifiability standard alone does not name — because a claim can be verifiable and still misleading about what it implies for action.

---

## 4. How the three braid into one launch logic

1. **JTBD** picks the job, and therefore the bar (predictor vs. media).
2. **Messick** tells you — via the Part 3 tables, and via an honest headline metric — whether you've cleared the bar.
3. **Influence** presents that validated (or honestly-not-validated) evidence using only the mechanisms the legal posture already permits.

The verifiability standard is the informal union of all three. This document makes the union explicit so each failure mode has a name.

---

## 5. Surface-by-surface checklist

| Surface | JTBD job it serves | Influence mechanism | Messick facet it must respect |
|---|---|---|---|
| **Overview / landing** | "Can I trust this enough to look?" | Authority (formula shown), consistency (immutable log promise) | Don't headline a win rate the data doesn't yet support |
| **Watchlist** | "Where's the action — and which of it is real?" | Candor (Quality Lens flags the rug-risks) | Content: score covers momentum *and* quality |
| **Guide** | "Help me learn the pattern, not just follow" | Authority via full transparency | Substantive: state *why* each input should matter |
| **Track record** | "Prove it — including the losers and the drawdown" | Commitment + liking (misses + MAE shown) | Consequential + external: realizable metric, full distribution |
| **Pricing / waitlist** | "Is it worth it, and am I early?" | Genuine scarcity (cohort cap) | — |

---

*This is a strategic synthesis, not legal or financial advice. The model remains unvalidated until the `VALIDATION-PLAN.md` Part 3 tables clear their bar. Obtain securities counsel before charging subscribers (gate G4).*
