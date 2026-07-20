# ThePickLog — Roadmap

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
- Model validation dashboard → https://thepicklog.vercel.app/dashboard.html — live, and as of
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
3. ~~**Insider data (Form 4) from free SEC EDGAR**~~ ✅ **DONE 2026-07-08.** `edgar_lens.py` now
   parses recent Form 4 XML and nets **open-market** insider buy/sell (`insider_net`: +1/0/−1 over a
   90-day window, codes P/S only — grants/exercises/tax-withholding excluded) into the forward-only
   `edgar_snapshot.csv`, and feeds the point-in-time Quality-Lens grade via the `insiderNet` input
   (`management` category). Non-fatal on EDGAR outage like the rest of the lens; verified live (ZION
   net −1 = 2 open-market sales; AAPL/KEY correctly blank — only comp-code Form 4s in-window). Fixed
   the XSL-rendered-vs-raw primaryDocument trap (basename → raw XML instance). Registered as **H-INS**
   (HYPOTHESES.md, two-sided) — accumulate then evaluate like H-DIL. **Insider ownership %** stays
   honestly "not checked": Form 4 alone can't give a truthful all-insiders aggregate vs shares
   outstanding, so we don't synthesize it (same "don't half-build off an unreliable source" guardrail).
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
- **Legal gates** — G4 securities review + IP review (branding) before any charging
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

## External improvement plan review — 2026-07-19 (dispositions on record)
A second, much larger outside plan (8 phases / 30 steps) framed ThePickLog as a public
verification product. It's directionally aligned with the referee/trust-layer repositioning, but
as a to-do list it's a multi-month program and can't gate the ~7/23 soft launch. The cheap,
high-trust credibility items were pulled *out* of here into a pre-launch checklist
(`ThePickLog-Prelaunch-Credibility-Checklist-2026-07-19.md`, stock screener/): fix the one
"nothing we can edit" overclaim **and surface the already-built hash chain** (A1, copy pack
drafted), get owner/admin controls off public pages (A2 = B2), disambiguate the timing model (A3),
move disclosures next to the numbers (A4), anchor the chain head off-repo (A5). Everything else is
dispositioned below.

**Deferred backlog — revisit after the 7/27 Gate-1 verdict.** Only pursue if the project keeps
moving toward semi-public; none are launch-blocking.
- **Record Integrity & Corrections Policy** — ⚠️ *mostly already built, just invisible.* The
  tamper-evident hash chain (`log_integrity.py` → `integrity_ledger.csv`) has been sealing every
  scan/grade/report since genesis 2026-07-06 and is wired into both workflows; logs + ledger also
  upload as GitHub artifacts. The reviewer's Step 2 is ~80% done — it simply isn't surfaced on the
  site (zero references in any HTML). Remaining: (a) surface it on method.html + dashboard
  [copy drafted, see A1 pack] — **pre-launch**; (b) anchor the chain head off-repo — **promoted to
  pre-launch 7/19**, decided **Wayback Machine** (one non-fatal `curl` per run; ledger already
  serves publicly, verified 7/20) — checklist A5; (c) public change log + written corrections
  policy — stays in this backlog. Supersedes the parked A6 "per-pick permalink + daily hash" idea.
- **Method page vs. technical appendix split** — a plain-language "what gets logged / how it's
  graded / can I reproduce it" page in front of the Messick/validity dossier, not behind it.
- **Score interpretation statements** — for each score, publish what it does *not* measure and its
  known limits (momentum ≠ quality ≠ probability of return).
- **Quality-Lens redesign** — separate data-completeness / financial-distress / operating-quality /
  valuation-context outputs instead of one blended verdict; rename "Too Hard" → "Outside Model
  Scope"; sector-specific treatment where the universal model doesn't fit.
- **One end-to-end verification walkthrough** on the site (single pick: what was logged → what was
  knowable at the time → how it was graded → result → verify links).
- **Publish model-validation thresholds in advance** — largely already encoded in the Gate-1
  criteria; write them down publicly so "supported" has a pre-committed definition.
- **Publisher/"Verified-by" product + demand interviews (15–20)** — the plan's proposed business.
  Plausible and consistent with the go-big thread, but unvalidated; do not start before Gate-1 lands.
- **Launch/trust metrics instrumentation** — % who open the raw log, use the verify tool, view the
  losing results, return after seeing the record.
- **Navigation simplification** — the plan wants 4 items (Record / Test a Rule / Method / About)
  with calculator, guide, glossary, assistant, portfolio demoted to contextual links or footer.
  The diagnosis (too many equal-weight destinations, no single primary journey) is fair; the exact
  4-item cut is not obviously right for the dare-first entry flow. Revisit as "one primary journey,"
  not as their specific IA.
- **Homepage structure** — evidence scorecard directly below the hero (partly exists via the track
  record); a single end-to-end verification walkthrough (above); a compact
  Log→Freeze→Grade→Publish four-step explainer. Cheap and on-brand; the *hero rewrite* they propose
  is **rejected** — it replaces the dare with a flat descriptive headline.
- **Environment separation** — their three-environment split (public / owner-research / staging).
  The public-vs-owner half is handled pre-launch by A2. A real staging deploy is a nice-to-have,
  not a credibility item.

**Deferred — decisions taken, no build required.**
- *Define one primary user for the homepage* (they propose: the skeptical investor asking whether a
  method has a demonstrated edge). Accepted as an editing lens, not a repositioning — it's
  compatible with the dare front door, which targets the same skepticism from the opposite angle.
- *Keep consumer research access free during validation; don't lead with paid alerts.* **Accepted**
  — already the operative posture, and it's why the $99/$199 tiers are being removed pre-launch (B4).
  Monetization stays gated on Gate-1 regardless.
- *Their "minimum viable public product" five functions* (log before outcome, preserve/timestamp,
  grade consistently, publish full distribution, let a stranger reproduce) — this is just the
  existing North Star restated. No action; noted so it isn't re-proposed as new.

**Partial-adopt (not wholesale) — keep the current positioning.**
- *Strip the competition down to methodology-only scoring* — **rejected as written**; the "dare"
  front door is deliberate. Adopt only the nucleus: don't rank Compete on raw fake-portfolio
  returns; add methodological-quality scoring alongside.
- *Rename "pick"→"logged observation", "winner"→"positive graded outcome", etc.* — **partial**; a
  few targeted swaps around genuinely recommendation-flavored words, not a full sterilizing rewrite
  that would kill the brand voice and the dare hook.

**Rejected / already done.**
- Much of the plan's Phase 1/Phase 3 is already shipped: nulls published prominently (validity docs
  + method.html §9, unrefuted-NULL verdict), receipts/verifiability live, disclaimer + privacy pages
  up, mobile pass shipped, legal review already queued. Cross off, don't rebuild.

## Reference docs
STRATEGY-advancing.md · VALIDATION-PLAN.md · SYNTHESIS.md · TEST-PLAN-quality-downside.md ·
PHASE2-SCOPE.md · HYPOTHESES.md · QA_REPORT.md · IMPROVEMENTS-v0.3.md · REQUIREMENTS.md

---
*Personal project plan, not investment advice.*
