# IgnitionScan — Roadmap

**Updated:** 2026-07-02 (rev 3) · **Framing:** personal instrument (not a product — no subscribers,
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
- Model validation dashboard → https://ignitionscan.vercel.app/dashboard.html — live, and as of
  **2026-07-02 linked from the main site** (nav "Validation" tab + Track-record cross-link). It was
  unlisted; surfacing it was the one cheap, on-brand take from the 2026-07-02 external feedback
  review (below).
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
3. **Insider data (Form 4) from free SEC EDGAR** — the last Quality-Lens fields still shown as
   "not checked" (insider ownership, insider buy/sell) are assumed to need a paid feed, but Form 4
   transactions are free in EDGAR. Extend `edgar_lens.py` to parse recent Form 4s (net buy/sell
   over a window) and feed the Lens + `edgar_snapshot.csv`. Scoped task, not a rider: Form 4 XML
   parsing + net-transaction math done carefully, non-fatal on EDGAR outage like the rest of the
   lens. Closes the honest-but-unsatisfying "not checked" gaps without abandoning the free-data
   constraint. (From the 2026-07-02 feedback review.)
4. **Phase 2 — full-market, point-in-time test of Finding B** (PHASE2-SCOPE.md). Gated on a
   paid historical-float feed. **Recommended: skip** unless deciding to actively sharpen the
   score — low leverage, and a backtest can't back a personal-confidence claim anyway.

## Parked / needs a Josh decision
- **Real money vs paper** — purely Josh's call, and not now. Alpaca is pinned to paper;
  going live needs two deliberate env flags.
- **Accountability wedge** (WEDGE-accountability.md) — design only. Mostly **moot** under the
  personal-tool framing (no public scoreboard). Revisit only if the project ever goes public,
  and only with legal review.

## Parked — productization only (moot under personal-tool framing)
Resurrect *only* if Josh re-decides to build this for an audience. All from the synthesis/strategy
thread (SYNTHESIS.md · IMPROVEMENTS-v0.3.md · STRATEGY-advancing.md).
- **Public-trust features** — A4 mean-net-return by tier on the site; A5 self-serve "re-derive it
  yourself" CSV download; A6 per-pick permalink + daily hash-of-picks.csv proof. (Verifiability-for-
  strangers; no value for a private tool.)
- **Morning brief → live site** (B1 is built as a local generator only) — publishing it shifts the
  posture to "recommending specific setups to all subscribers"; needs **G4 securities-counsel** review
  of copy/Terms/disclaimers first.
- **Marketing / growth** (STRATEGY §3, IMPROVEMENTS D1–D5) — transparency content flywheel, position
  vs. category fakery, free-vs-paid funnel, genuine-scarcity cohort, disclosure-as-feature.
- **Legal gates** — G4 securities review + IP review ("Buffett-style" name use) before any charging
  or public launch.

## External feedback review — 2026-07-02 (decisions on record)
An outside product review proposed a growth/monetization roadmap. Dispositions, so the same
suggestions don't get re-litigated later:

**Taken.**
- Surface the validation dashboard from the main site (done, see Done list above).
- Insider (Form 4) capture to close the Quality-Lens "not checked" fields (Next #3).
- Show intraday-touch stats alongside open→close grading — *already built* (dashboard spike-fade
  panels, MFE dots, Bayesian touch-rate posterior); noted here because it independently confirms
  the H-EX1 framing.
- Short interest as a signal — *already built* (capture live since 2026-06-16, H-SI registered).

**Rejected, with reasons.**
- *Seed the Compete SIM leaderboard with demo accounts* — fabricated activity on a site whose
  premise is stranger-verifiability. Violates the North Star outright.
- *Make Quality Lens a score multiplier / "conviction boost."* Phase-1 as-of test of Finding B was
  a NULL after removing look-ahead. Promoting quality into the score would bake in unvalidated
  weight — the exact failure mode HYPOTHESES.md exists to prevent. Revisit only if a forward OOS
  test (now possible via `edgar_snapshot.csv`) says otherwise.
- *Ad-hoc momentum reweighting (RVOL 40–45%, etc.)* — any weight change enters as a registered
  hypothesis with an OOS window, or the track record stops being interpretable.
- *Client-side "what if we changed the weights?" simulator* — an invitation to overfit in the
  browser; implies weights are casually revisable, cutting against pre-registration.
- *The acquisition→retention→monetization roadmap (waitlist nurture, Discord, gamification,
  virality)* — moot under the personal-tool framing; monetization is gated on OOS evidence
  (Gate-1 review fires 2026-07-27). The review optimizes for *looking* convincing; this system is built to
  *be* convincing, and those diverge at exactly the rejected items.

## Reference docs
STRATEGY-advancing.md · VALIDATION-PLAN.md · SYNTHESIS.md · TEST-PLAN-quality-downside.md ·
PHASE2-SCOPE.md · HYPOTHESES.md · QA_REPORT.md · IMPROVEMENTS-v0.3.md · REQUIREMENTS.md

---
*Personal project plan, not investment advice.*
