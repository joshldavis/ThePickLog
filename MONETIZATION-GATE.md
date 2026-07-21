# ThePickLog — Monetization Go/No-Go

**Drafted:** 2026-06-25 · **Framing:** decision framework only. Default remains personal tool
(ROADMAP.md). This file says *what would have to be true* to revisit that, and in what order.
Not investment or legal advice.

## The core principle

Monetization is **downstream** of edge validation, not a parallel track. There is nothing to
sell until the pre-registered edge survives out-of-sample — and even then, a statistically
real edge is necessary but not sufficient to be a product. Four gates, in order. Fail any
early gate and the later ones are moot.

The honest prior: per HYPOTHESES.md, *most patterns in 52 in-sample picks will not survive
OOS.* So the base-rate expectation for Gate 1 is **fail → stay personal.** Everything below is
conditional on beating that prior.

## Gate 1 — Does the edge survive out-of-sample? (inherits HYPOTHESES.md)

This is already pre-registered; monetization just adopts it verbatim so we can't move the
goalposts later.

| check | threshold (frozen) | where it's tracked | est. ready |
|---|---|---|---|
| Sample size | ≥ 30 post-2026-06-23 graded picks per arm | report §4d | mid-July |
| H-EX1 expectancy | post-reg **avg net/trade > same-day-close baseline** | report §4d | ~late July |
| Direction stability | sign holds across ≥3 consecutive weekly snapshots | report §4d | early Aug |
| Selection filters | ≥1 of H-F1–F4 kept-subset beats baseline OOS (or accept selection has no edge, exit-only) | report §4c | late July |

**Pass = at least the exit edge (H-EX1) clears.** Selection filters are a bonus, not required —
the whole thesis is the edge is in the exit.

## Gate 2 — Is the *realistic* edge big enough to sell?

A positive proxy isn't enough. Two things kill near-zero edges commercially:

1. **Slippage-real, not idealized.** §4d assumes fills exactly at +10%; thin floats gap
   through. The bar must be the **`exit_sim.py` path-walked** number (real touch order), and
   it must stay **clearly positive after that haircut** — not statistically-positive-but-tiny.
   Suggested floor: **path-walked avg net/trade ≥ +1.0%/trade.** Below that, the edge is real
   but unsellable (a subscriber's own slippage eats it).
2. **Capacity.** The edge lives in the *thinnest* floats (H-F2). That is a hard ceiling: a
   newsletter that more than a handful of people trade **moves the stock and destroys its own
   signal.** This likely caps any product at a small, high-price subscriber base — or pushes
   toward selling the *method/record* rather than live actionable tickers. Decide which before
   building.

## Gate 3 — Is the record long and clean enough to stand on?

- **≥ 8 weeks of graded forward record** (your own pre-billing gate; ~2/8 as of 2026-06-24).
- **Integrity checks green** (report §5) every week through the window — one unexplained gap
  or grader bug resets credibility to zero under the verifiability standard.
- The record must be **publishable as-is** — the differentiator is honesty, so a stranger has
  to be able to reproduce it from picks.csv/outcomes.csv. (This is the actual moat, more than
  the alpha.)

## Gate 4 — Commercial / legal / operational (only if 1–3 pass)

These are the items ROADMAP.md parked. None worth touching until the edge is proven.

- **Legal:** investment-advice exposure. Publisher's exemption vs. RIA registration is a real
  lawyer question, not a guess. ToS + disclaimers reviewed. **Hard blocker — no revenue before
  this clears.**
- **Distribution:** is there a cheap path to an audience, or does CAC swamp a capacity-limited
  product? Be honest about whether you'll actually do the marketing.
- **Unit economics:** operating cost vs. realistic subscriber revenue at the capacity ceiling
  from Gate 2. Data cost is now **near-zero**: `catalyst_type`/`dilution_flag` (2026-06-28) and
  `insider_net` (2026-07-08) are captured from **free SEC EDGAR**, not a paid feed as originally
  assumed. The only remaining paid-feed item is **Phase 2's** point-in-time historical float
  (ROADMAP #4, recommended skip). So operating cost is not a real barrier here — distribution and
  the capacity ceiling are.

## Decision tree (late July, when Gate 1 data lands)

- **Edge fails OOS (most likely):** No-go. Keep it personal, stop here. This is a *success* of
  the process — you avoided selling noise.
- **Edge validates but Gate 2 fails (tiny or capacity-capped):** No productized signal service.
  Possible narrow play: sell the *method + verifiable record* (course / "honest-record"
  newsletter about disciplined exits), not live tickers. Low priority.
- **Edge validates AND Gate 2 clears AND record clean (Gate 3):** *Then* open Gate 4. Build the
  minimum: legal review first, then a small paid alert/screen with the public record as the
  pitch. Price for the capacity ceiling (few subscribers, high price), not scale.

## What actually moves this

Nothing in code. The binding input is **post-registration graded picks accumulating through
late July.** First post-reg H-EX1 grades land ~next week; the expectancy sign and its stability
across the following ~6 weekly snapshots decide Gate 1. Re-read this file when §4d has ≥30
post-reg picks with a stable sign.

## Appendix — competitor pricing reference (Fynca, captured 2026-07-13)

**Status: reference only. Inert until Gates 1–3 pass.** Filed here so that *if* Gate 4 ever
opens we aren't designing tiers from scratch. Nothing here changes the current free posture —
everything on the site stays free until the edge validates OOS and legal clears.

[fynca.io](https://fynca.io) is an adjacent retail-research tool (node-based "visual canvas,"
research-not-execution — same legal posture as ours). Not a direct competitor: they sell a
*workspace*, we publish a *verified record*. Useful only as evidence of what a retail audience
will actually pay to unlock.

| Their tier | Price | What it unlocks |
|---|---|---|
| Free | $0 | core charts/news, 1 saved view, 10 AI calls/mo |
| Starter | $19/mo | 3 views, shared (viewer), AI heatmaps, analyst opinions, **insider flow**, 50 AI calls |
| Pro *(their "recommended")* | $59/mo | 8 views, editor sharing, **SEC filings & advanced research**, earnings-call transcripts, 150 AI calls |
| Max | $99/mo | unlimited views, 300 AI calls |

Packaging conventions worth copying if we ever charge: 14-day trial with no card, annual
billing at ~21% off, and "early-access pricing locked in while in beta."

**Two reads that matter for our Gate 4:**

1. **Insider flow is a paid-tier feature elsewhere — and costs us ~nothing.** They gate it at
   $19+. We already capture `insider_net` from **free SEC EDGAR** (2026-07-08), and Form 4
   capture is Next #3 in ROADMAP.md. Same for SEC filings/fundamentals, which they gate at $59
   and we get free from EDGAR. This reinforces the Gate 4 finding that **data cost is not our
   barrier** — distribution and the Gate 2 capacity ceiling are.
2. **The free→paid line is a usable default.** If the narrow "sell the method + record" play
   from the decision tree ever runs, their split (free = current//summary view; paid = depth,
   history, filings, higher limits) is a sane starting shape — *not* live tickers, which the
   capacity ceiling rules out anyway.

**What this appendix does not do:** it does not imply a paid tier is planned, does not set a
price, and does not move any gate threshold. Gate 1 still governs, and its honest prior is
still *fail → stay personal.*

---
*Decision framework, not investment or legal advice. The forward log is the only judge.*
