# IgnitionScan — Roadmap

**Updated:** 2026-06-23 · **Framing:** personal instrument (not a product — no subscribers,
no billing, no public marketing). The job: a screener + an honest self-grading record + a
validation layer Josh can trust before risking attention or money.

## Guardrails (these govern every item below)
- The **forward log** (picks.csv / outcomes.csv) is the only judge. Backtests are
  variable-selection only, never a claim.
- **Expectancy + drawdown**, not win rate, is the objective.
- Every new rule is **pre-registered** (HYPOTHESES.md) and judged **out-of-sample**.
- "Don't fool yourself": no overfitting to small N; verifiable from raw data.

## Done (running unattended in the cloud)
- Live screener + immutable pick log; daily scan/grade via GitHub Actions (no Mac/wifi).
- Weekly forward-log report → `reports/LATEST.md`; Finding-A-aware morning brief →
  `reports/brief-LATEST.md`.
- Exit-rule study (`exit_sim.py`) → `reports/exit-study-LATEST.md`, weekly.
- Pre-registered filters (HYPOTHESES.md) tracked all-time + out-of-sample in the report.
- Short-interest capture (live since 2026-06-16) + H-SI tracking.
- Model validation dashboard → https://ignitionscan.vercel.app/dashboard.html (live, unlisted).
- QA pass: port-fidelity fixes, 2 track-record grader bugs fixed, Alpaca pinned to paper,
  Actions hardened against push races (QA_REPORT.md).

## Next — in priority order
1. **Let it run, then act on what survives (highest value; ~late July).** As the
   out-of-sample columns fill, whichever pre-registered filter beats its OOS baseline gets
   wired into the brief as a real rule. This is the payoff loop — patience, not code.
2. **Capture the last two blank Group-B variables** — `catalyst_type` and `dilution_flag`
   (same pattern as short interest). Cheap; adds two more testable levers.
3. **Pre-register an exit rule.** Pick one candidate from the exit study, register it with a
   date in HYPOTHESES.md (H-EX1), then judge it on post-registration picks only. Do NOT adopt
   a rule straight from the in-sample study.
4. **Phase 2 — full-market, point-in-time test of Finding B** (PHASE2-SCOPE.md). Gated on a
   paid historical-float feed. **Recommended: skip** unless deciding to actively sharpen the
   score — low leverage, and a backtest can't back a personal-confidence claim anyway.

## Parked / needs a Josh decision
- **Real money vs paper** — purely Josh's call, and not now. Alpaca is pinned to paper;
  going live needs two deliberate env flags.
- **Accountability wedge** (WEDGE-accountability.md) — design only. Mostly **moot** under the
  personal-tool framing (no public scoreboard). Revisit only if the project ever goes public,
  and only with legal review.

## Reference docs
STRATEGY-advancing.md · VALIDATION-PLAN.md · SYNTHESIS.md · TEST-PLAN-quality-downside.md ·
PHASE2-SCOPE.md · HYPOTHESES.md · QA_REPORT.md · IMPROVEMENTS-v0.3.md · REQUIREMENTS.md

---
*Personal project plan, not investment advice.*
