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

## Gate-1 verdict — 2026-07-29: **FAILED → No-Go** (decision recorded)

The late-July decision tree resolves to its base-rate branch. On `leaderboard.json` (2026-07-29):
H-EX1 n_post 309, avg −5.9% vs baseline −2.9%, **Δ −3.0pp**, pooled CI [−4.4, −1.5] and cluster CI
[−6.0, −0.6] both excluding zero, 5/16 names favor, stability stable. The pre-registered exit edge
is **significantly negative** out-of-sample and survives the clustering correction. Selection
filters show no edge. Across 11 rules: 6 positive point estimates vs 5.5 expected by chance, 2
significant, both negative.

**Decision: No-Go.** Gate 1 is the binding gate and it failed, so Gates 2–4 stay closed. ThePickLog
remains a personal research instrument. This is the "success of the process" outcome anticipated on
2026-06-25 — the forward log refused to confirm the edge, so there is nothing to sell, and the
honest record (now including a published null) was always the only real moat.

**Gate 2's reference metric was broken and is now fixed.** Gate 2 sets its floor on the
`exit_sim.py` path-walked number (≥ +1.0%/trade). That file was inflating every bar-priced rule via
a live bar re-fetch against unadjusted stored entries; the same-day-close baseline read +8.0% when
it is −2.9%. Fixed 2026-07-29 (paths-only + per-pick reconciliation). **After the fix no exit rule
in the study beats the same-day close at all**, so nothing is within ~4pp of the Gate-2 floor. Any
future Gate-2 evaluation must use the corrected file.

**Re-open this file only if** a *new* pre-registered hypothesis clears the H-EX1 bars on its own
forward log — not on a re-cut of the data that produced this verdict.

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

---
*Decision framework, not investment or legal advice. The forward log is the only judge.*
