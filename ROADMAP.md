# IgnitionScan — Roadmap

**Updated:** 2026-06-23 (rev 2) · **Framing:** personal instrument (not a product — no subscribers,
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
- **H-EX1 registered 2026-06-23** — the candidate edge is in the **exit, not the selection**.
  The screen finds names that *spike then fade* (82% touch +5% intraday in 5d, 63% touch +10%;
  median MFE +16.4% vs same-day-close −2.8%). Rule: +10% target over the 5-day hold, else 5-day
  close. Tracked all-time + out-of-sample in the weekly report §4d (HYPOTHESES.md).
- **Reproducible exit study** — grader now persists each pick's grade-time daily OHLC path to
  `paths.csv` (immutable, forward-only); `exit_sim.py` prefers it over re-fetching so the study
  is verifiable from committed data. (Discovered re-fetch drift: Yahoo silently revises microcap
  daily lows, so backfilling old picks would disagree with the record — hence forward-only.)

## Next — in priority order
1. **Let it run, then act on what survives (highest value; ~late July).** As the
   out-of-sample columns fill (filters **and now H-EX1**), whichever rule beats its OOS
   baseline gets wired into the brief as a real rule. The payoff loop — patience, not code.
   First post-registration H-EX1 grades land ~next week.
2. ~~**Capture the last two blank Group-B variables** — `catalyst_type` and `dilution_flag`.~~
   ✅ **DONE 2026-06-28** via free **SEC EDGAR** (`edgar_lens.py`) — no paid feed needed after all.
   `dilution_flag` (offering/shelf/none from 424B*/S-3* filings) + `catalyst_type` (filing proxy:
   offering/8K/filing/none) now populate the formerly-blank picks.csv columns going forward, and a
   **Quality-Lens snapshot** (point-in-time, look-ahead-safe) writes to the forward-only sidecar
   `edgar_snapshot.csv` — which also re-opens the *option* to test Finding B out-of-sample. All
   capture is non-fatal (SEC down ⇒ blanks, picks still log). Registered as **H-DIL** (HYPOTHESES.md,
   two-sided). Next: let it accumulate, then evaluate H-DIL like H-SI once enough picks carry it.
3. **Phase 2 — full-market, point-in-time test of Finding B** (PHASE2-SCOPE.md). Gated on a
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
