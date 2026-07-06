# ThePickLog — Validity Principles

**The single source of truth for *why this project is allowed to claim anything.***
Updated 2026-06-24. Framing: personal research instrument (no subscribers, no billing).
These principles are framing-independent — they held when this was scoped as a product and
they hold now that it isn't. Everything else in the repo is downstream of this file.

---

## 0. The North Star

> **"Can a stranger visit this site, pull the raw data, and verify that every claim is true?"**

This is the **verifiability standard**. It is the one test every shipped change must pass.
A number is allowed on the site only if a skeptic with no trust in Josh, starting from the
committed CSVs and the published method, can reproduce it and arrive at the same value. If
they can't, it doesn't ship — however true it might privately be.

Verifiability is not a marketing nicety. The honestly-graded track record *is* the core
deliverable; the ability to re-derive it is what makes the record worth anything.

---

## 1. The five operating principles

These are the verifiability standard broken into rules you can actually check a change against.

### P1 — The forward log is the only judge
`picks.csv` and `outcomes.csv` are the canonical record. They are **append-only and
immutable**: a pick row is written once, before the outcome is known, and never edited.
Grading writes to a *separate* outcomes table keyed by `pick_id`. Backtests are for
**variable selection only** — they never constitute a claim about performance. If a result
isn't in the forward log, it isn't evidence.

*Why:* a record you can quietly edit is a record that proves nothing. Immutability is what
turns "trust me" into "check me."

### P2 — Pre-register every rule, judge it out-of-sample
Any new rule or filter is frozen **with a date** in `HYPOTHESES.md` *before* it counts. Only
picks logged **after** the registration date are the real (out-of-sample) test. Patterns
spotted in an in-sample cut overfit by construction; `weekly_report.py` tracks all-time and
post-registration performance separately so the forward log — not the author — decides.

*Why:* a hypothesis chosen after seeing the data is not a test of that data. The date stamp
is what makes it a test.

### P3 — Measure something realizable, and show the downside
The grading metric is the **regular-session open → close**, **net of a 2% friction haircut**
for wide low-float spreads — not the pre-market print nobody can actually get filled at, and
not "ever touched +20% intraday" (which scores volatility, not a return). Worst-drawdown
(`mae_5d`) is shown alongside every result. Best-case excursion (`mfe_5d`) is recorded but
always labeled "not an achievable return."

*Why:* a claim can be perfectly verifiable and still mislead about what it implies for
action. Honesty about the gap between best-case and realizable *is* the standard, taken to
its rigorous end.

### P4 — Expectancy and drawdown, never win rate alone
The objective is **mean net return per trade and the drawdown that bought it**, with the full
distribution published (mean, median, % positive, MAE) — not a lone win-rate headline. A win
rate is the easiest number to game and the easiest to misread.

*Why:* a few big winners can carry a low win rate to positive expectancy, and a high win rate
can hide ruinous tails. Distribution is harder to fake and closer to the truth.

### P5 — Don't fool yourself: no overfitting to small N
No rule gets promoted into the live score off a handful of picks. Sample bars are explicit
(target ~200 graded total, ~30 per tier before the tier ordering is trusted; hold out the
most recent ~25% out-of-sample). Until the data clears the bar, **the model is labeled
unvalidated** everywhere it appears.

*Why:* the most dangerous reader of these numbers is the person who made them. The sample
bar is the guardrail against believing noise.

---

## 2. How each principle is enforced in the code

| Principle | Enforced by | Verifiable artifact |
|---|---|---|
| P1 immutable log | `ignitionscan.py scan/grade` append-only writes; row-locked picks, separate outcomes | `picks.csv`, `outcomes.csv`, `paths.csv` (committed) |
| P2 pre-registration | rules frozen + dated; report splits all-time vs post-registration | `HYPOTHESES.md`, `weekly_report.py` §4 |
| P3 realizable metric | open→close net of 2% haircut; MAE recorded; MFE labeled | grader logic + `VALIDATION-PLAN.md` Part 2 |
| P4 expectancy + distribution | full distribution in every report, not a bare win rate | `reports/LATEST.md`, dashboard.html |
| P5 small-N discipline | explicit sample gates; "unvalidated" labels until cleared | `VALIDATION-PLAN.md` Part 3/4 |

**Reproducible by design:** the grader persists each pick's grade-time daily OHLC path to
`paths.csv` (forward-only) so the exit study runs off committed data instead of re-fetching.
This exists because Yahoo silently revises microcap daily lows — backfilling old picks would
disagree with the record, so paths are captured once at grade time and never re-pulled.

---

## 3. The weekly verifiability audit

Once a week the live site is checked against its own raw data — the standard turned into a
recurring control. A run **passes** only when all of the following hold (see `AUDIT_LOG.md`
for dated results):

1. `picks.csv` and `outcomes.csv` are reachable (HTTP 200) and current — no unexplained
   weekday scan gaps.
2. The live Track-record page is rendering the **real** log, not the sample fallback.
3. **Claims == data:** every headline number (win rate, medians, tier counts) recomputes
   from the raw CSVs to the value shown on the site.
4. **Methodology spot-check:** entry = pick-day open, 2% haircut applied, win = positive net
   return (not "ever touched"), no duplicate/regraded `pick_id`s.
5. **Validity-claim backing (six aspects):** for each of Messick's six aspects of construct
   validity — content, substantive, structural, generalizability, external, consequential —
   the claim the site makes is either backed by evidence a stranger can reproduce from the
   CSVs, or it is explicitly labeled **unvalidated**. An aspect whose on-site claim can't be
   reproduced fails the audit exactly as a bad headline number would. Verdicts are recorded
   per-aspect in `AUDIT_LOG.md`; the standing rubric is the validity framework (see §4).

A run that can't reach the live site is logged as **tooling failure, not certification** —
it never counts as a pass. Silence is not proof.

---

## 4. Why the standard needs three lenses behind it (`SYNTHESIS.md`)

The verifiability standard is correct but informal, and it has one blind spot it can't name
on its own: a claim can be *verifiable and still misleading about what it implies for action.*
`SYNTHESIS.md` layers three established frameworks on top to close that gap, and the
principles above are the operational residue of all three:

- **Jobs to be Done** — *which* claims matter (the ones that de-risk the morning decision).
- **Influence (ethical reading)** — present proof so a skeptic updates honestly; the legal
  posture forbids the manipulative versions anyway.
- **Messick construct validity** — the formal test that a score *means what it claims*. P3
  and P5 are direct consequences (the "touched +20%" defect is a consequential-validity
  failure; small-N is a generalizability threat).

The one-line union: *publish a validity argument in the open, framed to the job the data
actually supports, and let persuasion work only through the parts that survive a stranger's
scrutiny.*

**The Messick lens is now stood up in full.** `ThePickLog-Validity-Framework-Messick-2026-07-06.md`
(committed in-repo) is the **standing validity argument**: it maps the
project to all six aspects of construct validity, grades the current evidence per aspect, and carries
a gap register keyed to the two Messick threats (construct underrepresentation, construct-irrelevant
variance). Two companion artifacts discharge the P1/P2 content and structural gaps —
`ThePickLog-Domain-Coverage-Spec-2026-07-06.md` (the written-down construct domain + coverage matrix)
and `ThePickLog-Structural-Justification-2026-07-06.md` (weights/cutpoints of record + a reproducible
monotonicity check showing the tiers order *heat/drawdown*, not return). Those verdicts are what §3
item 5 audits each week. A Uniform Guidelines reach section stress-tests the same material against
employment-selection law (by analogy only; not legally applicable).

---

## 5. The one question for any future change

Before anything ships, it has to answer:

> **Does this make the record more verifiable, or less?**

If a feature adds a number a stranger can't re-derive, it doesn't ship until they can. If it
removes friction from re-deriving an existing number, it's almost always worth doing. That's
the whole rule.

---

*Personal research tool, not investment advice. The model is unvalidated until the
`VALIDATION-PLAN.md` tables clear their bar. See `DOCS.md` for how this file relates to the
rest of the repo.*
