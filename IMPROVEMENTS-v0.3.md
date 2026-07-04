# ThePickLog — v0.3 Improvement Spec

**Owner:** Josh
**Date:** June 15, 2026
**Companion files:** `SYNTHESIS.md`, `REQUIREMENTS.md`, `VALIDATION-PLAN.md`
**Status legend:** ✅ shipped in this pass (local, awaiting your review + push) · 🔜 proposed next · 🧪 needs data/legal gate first

This spec turns `SYNTHESIS.md` into concrete product moves across the four focus areas you chose: **Trust & track record**, **Morning brief (JTBD)**, **Scoring validity**, and **Growth & conversion**. Each item names the framework it serves so the *why* is auditable, not just the *what*.

---

## A. Trust & track record (the moat)

The whole differentiator is "a record a stranger can verify." These deepen it.

- ✅ **A1 — Show the full return distribution, not a lone win rate.** Track record page now surfaces **median net, mean net, % positive, and average worst-dip (MAE)** alongside win rate. *(Messick: external + consequential validity; Influence: candor.)*
- ✅ **A2 — Show the downside.** Added a **Worst dip (MAE)** column to every graded pick and an avg-MAE stat card + plain-English distribution sentence. The product no longer hides the drawdown you'd have to sit through. *(JTBD anxiety: "how far does it drop first?")*
- ✅ **A3 — Honest WIN definition, stated on the page.** "WIN = realizable open→close after 2% costs, never 'ever touched +20%'" is now in the Honesty-checks list. *(Messick: the consequential-validity fix.)*
- 🔜 **A4 — Return-by-tier on *mean net*, not just win rate.** The bars show hit rate; add a small mean-net-return number per tier so the monotonicity test (A>B>C>D) is visible to users, not just in the `report` command. *(Messick: structural validity, made public.)*
- 🔜 **A5 — "Re-derive this yourself" link.** A one-click download of `picks.csv` + `outcomes.csv` and a one-paragraph "how we grade" so a stranger can literally recompute every number. *(Verifiability standard, taken to its logical end.)*
- 🔜 **A6 — Per-pick permalink + timestamp proof.** Each pick row links to its immutable `published_at`. Optional later: publish a daily hash of `picks.csv` (e.g. to a gist) so the "we didn't edit history" claim is cryptographically checkable. *(Influence: commitment & consistency.)*
- 🧪 **A7 — Don't headline a win rate until N is sufficient.** Keep "Grading soon" / honest small-N labelling until ≥~30 graded per tier (per VALIDATION-PLAN 3.1). *(Messick: generalizability — small N is the current top threat.)*

## B. Morning brief / JTBD (engagement + retention)

The richer brief is what turns a screen into a daily habit — and it's still legal as an impersonal newsletter (VALIDATION-PLAN Part 5), provided it stays identical for all subscribers and discloses positions.

- 🔜 **B1 — "What we like / what we don't / watch level / risk area" brief.** A short daily note generated from the same screen + Quality Lens, identical for everyone. Serves the real job ("do the morning work for me") far better than a raw table. *(JTBD: the functional job; Influence: authority via candor on what we *don't* like.)*
- 🔜 **B2 — Per-pick one-liner rationale.** Auto-generated, deterministic ("float 3.1M, RVOL 10×, gapped 12%, Quality: Yellow — momentum real, balance sheet thin"). No "buy" language. *(JTBD: "help me learn the pattern.")*
- 🔜 **B3 — Regime banner.** Surface the `market_regime` tag already captured (risk-on/neutral/risk-off) at the top of the brief, so picks are read in context. *(Messick: generalizability cue for the reader.)*
- 🧪 **B4 — Legal posture fork.** The brief moves you from "we only publish data" toward "we recommend specific setups to all subscribers" — still inside the exclusion, but it raises the bar on G4 (counsel review of copy/Terms) before charging. Keep it impersonal; disclose positions.

## C. Scoring validity (toward a *validated* score)

Capture now, score later — never the reverse (VALIDATION-PLAN Part 1).

- ✅ **C1 — Instrument short interest, free.** The scan now captures `short_interest_pct` from the `.info` dict it *already* fetches — **zero extra network calls**, so no added throttle risk. Captured, **not** scored. *(Messick: content validity — closing the under-representation gap.)*
- 🔜 **C2 — Instrument the rest of Group B.** `dilution_flag` (share-count change YoY from filings), `catalyst_type`, `halt_history_30d`, `days_to_cover`. These need feeds beyond Yahoo `.info`; add as data sources land. *(Messick: content.)*
- 🔜 **C3 — Variable-evaluation tables.** For each Group-B field, the `report` command should print the "does it separate winners from losers?" table from VALIDATION-PLAN 3.2 before anything is promoted into the score. *(Messick: substantive — earn a place in the score with evidence.)*
- 🧪 **C4 — Re-fit weights from data, model-versioned.** Only after C3 shows separation. Any weight change **must** bump `MODEL_VERSION` so history isn't silently rewritten. *(This is the "Full build" option you deferred — gated behind real data.)*

## D. Growth & conversion (ethical funnel)

Use only influence mechanisms that survive the "would it work if they knew?" test (SYNTHESIS §2.2).

- 🔜 **D1 — Lead with the verifiable proof, above the fold.** The hero already promises auditability; once N is sufficient, put the live distribution (median net, % positive, worst dip) on the landing page as the headline — proof, not adjectives. *(Influence: social proof, the honest kind.)*
- 🔜 **D2 — Genuine, non-resetting scarcity.** The "first 500 / $99 early" cohort is real scarcity; show actual remaining slots, never a fake timer. *(Influence: scarcity, ethical.)*
- 🔜 **D3 — Free tier = the trust funnel.** Yesterday's screen + full public track record is the right free offer (it lets a stranger verify before paying). Make the upgrade prompt point at *today's* brief, not at hidden history. *(JTBD: let them verify the job is done before hiring.)*
- 🔜 **D4 — Disclosure as a feature, not fine print.** A visible "operator positions" line and "we never take payment to feature a ticker" build more trust than any badge — and they're required for the exclusion anyway. *(Influence: authority; Legal: §7.3.)*
- 🧪 **D5 — No billing until the record is real.** Per REQUIREMENTS §9: run the tracker on real data 6–8 weeks before turning on Stripe. The worst launch is a paywall over an empty/"pending" record.

---

## Priority order (recommended)

1. **Ship & push A1–A3** (done locally) — immediate trust upgrade, zero risk.
2. **A4 + A5** — make the validity argument fully self-serve.
3. **B1–B3** — the brief, the single biggest retention lever (gate on B4 legal note before charging).
4. **C2–C3** — keep instrumenting; let data, not intuition, drive any scoring change.
5. **D1–D4** — turn the proof into conversion, only once N is sufficient (A7) and the record is real (D5).

## What is explicitly NOT changed in this pass
- The scoring formula and weights (unchanged → `MODEL_VERSION` stays `v0.2-yf`; existing graded comparisons remain valid).
- The immutable `picks.csv` / `outcomes.csv` (never edited).
- Anything requiring securities-counsel review before charging (gate G4).

---

*Strategic/technical plan, not legal or financial advice. The model is unvalidated until VALIDATION-PLAN Part 3 says otherwise; obtain securities counsel before charging subscribers.*
