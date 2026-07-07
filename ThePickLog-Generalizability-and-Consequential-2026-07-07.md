# ThePickLog — Generalizability & Consequential Validity

**Closing gap-register rows 5 (generalizability), 8 & 9 (consequential)**
Date: 2026-07-07 · Companion to `ThePickLog-Validity-Framework-Messick-2026-07-06.md`

---

## Part A — Generalizability (row 5)

### A.1 The sampling frame, characterized

Messick requires stating the boundaries within which score meaning holds. The frame:

- **Universe:** US microcaps roughly **$0.50–$5** per share, **thin float** (the graded log is 85% under 3M shares), surfaced by **end-of-day FinViz/Yahoo momentum screens** and ranked by the v0.2 momentum score. Not a random draw of the market — a momentum-selected slice.
- **Size & span:** 269 logged picks; 180 graded across **13 distinct trading days (2026-06-09 → 2026-06-26)**, the matured window as of today.
- **Known frame artifacts:** end-of-day timing means the rvol input rarely catches a live spike (see Empirical Studies §3); Yahoo silently revises microcap lows (mitigated by forward-only `paths.csv`); one market-holiday phantom cohort was caught and voided (AUDIT_LOG 2026-06-28). Survivorship in the screen itself (delisted/halted names) is **not** yet characterized — a registered gap.

### A.2 Does the edge generalize across regime?

Outcome by `market_regime` (graded forward log):

| Regime | n | mean net | 95% CI | win % |
|---|---|---|---|---|
| risk-on | 54 | **−5.49%** | [−8.11, −2.87] | 22% |
| neutral | 55 | −1.74% | [−3.99, +0.51] | 42% |
| risk-off | 71 | −1.70% | [−3.40, +0.01] | 42% |

**Finding.** The screen is **strongly regime-dependent** and **no regime is positive**. It is materially worse in **risk-on** tapes (−5.49%, win 22%) — chasing momentum when everything is ripping buys tops — and merely flat-to-negative otherwise. A number that swings this much across regime cannot be reported as a single context-free figure; the boundary must be stated on any claim.

### A.3 The regime hold-out promotion gate (codified)

**New standing rule (added to `PRINCIPLES.md` P5 and registered as H-REG):** no rule is promoted from "unvalidated" on a single-regime sample. **An edge must hold across at least two of {risk-on, neutral, risk-off}** on post-registration picks before it graduates. This is the generalizability analogue of the pre-registration discipline: surviving one regime is surviving one draw of the world.

**Still deferred (needs new data, registered not faked):**
- **Live-fill validation** — paper→real slippage on thin floats is modeled (2% haircut + `exit_sim.py` gap-through) but not measured against real fills. Registered to run before any monetization (MONETIZATION-GATE Gate 2).
- **Frame survivorship** — begin logging screened names that later halt/delist to quantify selection survivorship.

---

## Part B — Consequential validity

### B.1 Intended use, misuse, and the cost of error (row 9)

**Intended use.** ThePickLog is a **personal research instrument and a public, verifiable record** of an idea being tested in the open. Its legitimate use is to *watch a hypothesis be adjudicated honestly* — not to source trades. The model is labelled **unvalidated** and, on current evidence (Empirical Studies §4; External aspect null), carries **no demonstrated positive edge**.

**Foreseeable misuse.** (1) Treating a high tier as a buy — squarely refuted; tiers rank *intensity/drawdown*, not quality. (2) Over-sizing a single thin-float name the screen surfaced — these are the most gap-prone instruments on the board. (3) Reading the win-rate headline without the drawdown beside it — the reason P4 forbids a lone win rate.

**The loss function is asymmetric, and it sets the default.** A **false positive** (a user acts on an unvalidated pick) costs real money on a volatile microcap; a **false negative** (the user does nothing) costs nothing. Because the downside of over-claiming dwarfs the downside of under-claiming, the conservative posture — stay free, stay personal, keep the "unvalidated" label until the pre-registered gate clears — is not timidity; it is the correct decision under this loss function. This is the consequential-validity justification for the whole `MONETIZATION-GATE`.

### B.2 Reflexivity monitor (row 8)

**The threat (construct-irrelevant variance).** Publishing a thin-float pick can itself move the name, contaminating its own logged outcome — a feedback loop that would inflate or distort the record for reasons unrelated to any real edge.

**Current exposure: ~nil.** Public traffic is effectively zero (family/friends Compete launch not live until ~2026-07-23; only `/u/house` is public). At current reach, publication cannot move a microcap, so today the log is uncontaminated by reflexivity — but this must be monitored *as reach grows*, not assumed.

**Monitor design (registered as H-REFLEX, activates at scale):**
- **Metric.** For each newly published pick, track (a) the screen-price → next-session-open gap and (b) publication-day volume vs the name's trailing baseline. A reflexivity signature is abnormal post-publication drift/volume that scales with ThePickLog's audience size.
- **Trigger.** Begin evaluating once weekly site traffic crosses a set threshold (to be fixed when analytics are wired); until then, log the metric passively.
- **Response if detected.** Widen the publication→entry delay or publish picks only after entry, so the record cannot be moved by its own disclosure. Documented here so the response is pre-committed, not improvised.

---

*All figures reproduce from the committed CSVs. This document is part of the standing validity argument; see the framework doc and the §15 dossier for how it fits.*
