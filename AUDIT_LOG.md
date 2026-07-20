# ThePickLog — Audit Log

## 2026-07-18 — Weekly verifiability audit — **✅ All claims verify**

Live site checked directly (fetched same-origin from https://thepicklog.vercel.app). All six data checks pass and the six-aspect validity labelling is honest. One minor data-hygiene note (holiday-orphaned picks), no claim is affected.

**Six data checks:**
- **1. Data served — PASS.** `/picks.csv` HTTP 200 (81.6 KB, 470 rows), `/outcomes.csv` HTTP 200 (44.8 KB, 347 rows). Both non-empty.
- **2. Real data shown — PASS.** Track record renders the live log ("this page re-derives from them"; "Live data — quotes pulled from Financial Modeling Prep"). The only "sample" string on the page is "out-of-sample," not a sample-fallback badge.
- **3. No silent gaps — PASS.** 28 distinct trading dates, 2026-06-09 → 2026-07-17. Every US market weekday present; the only absences are Juneteenth (06-19) and the observed July 4 holiday (07-03). No weekday silently missing.
- **4. Claims == data — PASS.** Recomputed from the raw CSVs: 470 logged / 333 graded / win rate 33.9% → site shows 470 / 333 / **34%** (match). Best 5d-net = **+170.5% (CUPR)**. Win-rate-by-tier: A 30.3% (n=33), B 55.0% (n=20), C 36.2% (n=127), D 30.1% (n=153) — reconciles to the graded set.
- **5. Honest grading — PASS.** Spot-checked 4 rows across the file (PW, NCT, MASK, PTLE): entry = pick-day open; 2% cost haircut applied exactly (`ret_open_close_net == (close−open)/open×100 − 2.0` within rounding); win column = sign of net return on every checked row; no duplicate pick_ids (no regrades).
- **6. Disclaimers — PASS.** Educational, "not advice," and "not a broker-dealer" all present.

**Six-aspect validity (Messick):**
- **Structural — honest.** method.html states plainly: "the momentum tiers rank intensity (and drawdown), not forward return — the top tier historically has the worst mean net and the deepest drawdown." This week's data confirms it: A-tier has the **worst** mean 5d-net (−10.8%). No "higher tier = better" claim anywhere.
- **Unvalidated label — present.** "Until the data clears the bar the model is treated as unvalidated." Gate-1 external verdict correctly deferred (owned by the 2026-07-27 task; not rendered here).
- **Validity docs — reachable + linked.** All three referenced from method.html §9 and return HTTP 200: Messick Framework, Domain-Coverage Spec, Structural-Justification (plus Empirical-Validity-Studies and Validity-Dossier-UG15 also linked).

**Minor note (no claim affected):** 14 picks carry `trading_date 2026-06-19` (Juneteenth — market closed), so they can never grade and sit permanently in the ungraded pool. They're correctly excluded from the 333 graded count and don't touch any published number, but worth checking why the scan logged a holiday cohort.

**Grading in the coming week:** 137 picks currently ungraded. The recent cohorts reach their 5-trading-day mark next week — 07-13 (21 picks) ~07-20, 07-14 (26) ~07-21, 07-15 (26) ~07-22, 07-16 (26) ~07-23, 07-17 (24) ~07-24 — ~123 fresh grades landing 07-20→07-24. (The 14 06-19 holiday picks will not grade.)

## 2026-07-06 — First six-aspect validity audit (Messick) — **⚠️ 1 fail, 5 partial/absent (all labeled)**

New audit dimension per `PRINCIPLES.md §3 item 5`: each of Messick's six aspects of construct
validity is either backed by stranger-reproducible evidence or explicitly labeled *unvalidated*.
Standing rubric: `ThePickLog-Validity-Framework-Messick-2026-07-06.md`. This first run establishes the
baseline verdicts; nothing here contradicts the North Star — every verdict below is reproducible from
the committed CSVs and code.

- **Content — Partial.** Domain now written down (`ThePickLog-Domain-Coverage-Spec-2026-07-06.md`):
  the score samples 4 of ~15 domain drivers, all from 2 of 7 families. Momentum-only
  **underrepresentation** is labeled, not hidden. Technical quality (point-in-time capture) solid.
- **Substantive — Partial.** Process model (spike→fade) + `exit_sim.py` fills-fidelity check exist;
  rival mechanisms not yet discriminated. No unvalidated claim on the site.
- **Structural — FAIL for the quality interpretation (backed & reproducible).** Monotonicity check on
  165 graded rows (`ThePickLog-Structural-Justification-2026-07-06.md`): tier ordering is
  non-monotonic on return (top tier A worst mean net −4.59%; B best) and monotonic on drawdown the
  wrong way (A −24.7% MAE deepest → C −16.2% shallowest — Finding A confirmed). **Action:** re-label
  A–D as an intensity/heat scale, not a quality ranking. Also corrected: true tier cutpoints are
  **75/60/45** (not the 90/75/50 an earlier inventory recorded) — verified against `tier_of()`.
- **Generalizability — Partial.** Machinery Established (pre-registration, OOS windows, `paths.csv`,
  haircut, min-n gates); evidence thin — single ~18-day regime. `market_regime` captured but not yet
  a promotion gate. Model labeled *unvalidated* everywhere, so no over-claim.
- **External — Absent-to-date (honestly labeled).** 0/6 hypotheses significant; H-EX1 Δ +1.7pp
  (CI [−3.2,+5.8], n=30), Bayesian P(beat)≈4%. Criterion validity unsupported so far. Gate-1 verdict
  fires **2026-07-27** and will be published either way.
- **Consequential — Partial.** Safeguards active (unvalidated labels, no monetization pre-gate, null
  publishing, haircut, gap-through warning, North Star). Pending: written intended-use/misuse +
  cost-of-error note, and a **reflexivity monitor** (does publishing move the thin-float name?).

**Net:** no aspect makes an unbacked on-site claim; the one hard **FAIL** (structural) is a labeling
defect with a concrete, shippable fix. External validity remains the open question the whole project
is gated on. Re-audit these six alongside the weekly verifiability run.

---

## 2026-06-28 — Resolution of the 06-27 finding (Juneteenth phantom cohort) — **✅ Fixed**

The market-holiday issue flagged below is resolved before the affected rows could grade (~06-29).

**Verified phantom:** all **14** picks dated **2026-06-19** (Friday, Juneteenth, NYSE closed) carry
`price_at_screen` **byte-identical to the 2026-06-22 session** (and *not* to the true prior session
06-18). Confirmed stale/duplicate quotes — not a real screen. None had graded yet (0/14).

**Fix 1 — voided the cohort (immutability-respecting).** Rather than delete the immutable picks
rows (they stay as evidence the scanner misfired), appended a terminal **VOID** outcome for each of
the 14: blank returns/win + an explanatory `note`. Effect: they are now "resolved" (the grader skips
them — 0 of the 06-19 cohort remain pending, so the ~06-29 run cannot grade them off a bogus open),
and every performance stat already filters on non-empty return, so they are **excluded from all
metrics**. `weekly_report.py` §1 now reports them as a separate **voided** count (106 graded / 74
pending / 14 voided). Integrity checks still pass.

**Fix 2 — scanner guard (so it can't recur).** `ignitionscan.py` `cmd_scan` now (a) skips known
**NYSE_HOLIDAYS** as a clean no-op (logs nothing, exit 0), and (b) has a source-agnostic
**stale/duplicate-quote backstop**: if ≥80% of the day's quotes are byte-identical to the most
recent logged session (the closed-market/frozen-feed signature), it fails loudly and logs nothing.
The backstop is what catches anything the calendar misses (future years, half-days, feed outages).
Both tested offline.

---

## 2026-06-27 — Weekly verifiability audit — **⚠️ Issues found (1)**

Every claim the live site *displays* verifies exactly against the raw CSVs. One data-hygiene issue: a scan ran on a market holiday. Audit ran clean via Chrome (last week's tooling block is resolved).

**✅ What verified**
- **Data served:** `/picks.csv` and `/outcomes.csv` both HTTP 200, non-empty — 194 picks, 106 graded rows.
- **Real log, not sample:** Track record renders "Pulled live from the public pick log — 194 picks across 14 trading days (2026-06-09 → 2026-06-26)" with real WIN/MISS/pending rows. No sample fallback.
- **Claims == data (all match):** picks 194 ✓ · graded 106 ✓ · win rate 37% (recomputed 36.8%) ✓ · median net −3.0% (−2.96) ✓ · mean net −2.8% (−2.81) ✓ · avg worst dip −18.0% (−17.96) ✓ · avg 5d swing −5.4% (−5.35) ✓ · Best Net +20% (best same-day 19.9%) ✓.
- **Win-rate by tier — exact:** A 33% (n=9) · B 56% (n=9) · C 41% (n=41) · D 30% (n=47).
- **Honest grading:** 106/106 graded rows reproduce from entry=pick-day open, (close−open)/open − 2% cost; win = positive net. 0 sign mismatches, 0 duplicate pick_ids, 0 missing entry_open.
- **Disclaimers present:** educational/informational, not advice, not a broker-dealer, not affiliated with Buffett — all on Overview and Track record.

**⚠️ Issue — scan ran on a market holiday (2026-06-19, Juneteenth, NYSE closed)**
No trading weekday is *missing* (all 14 in 06-09→06-26 present). But 2026-06-19 is Juneteenth — NYSE was closed — yet 14 picks are logged that day, and their `price_at_screen` values are **byte-identical to the 06-22 session** (stale/duplicate quotes). The scan did not fail loudly on a closed market; it produced a phantom screen. These rows are still **pending** (ungraded), so no displayed performance stat is corrupted *yet* — but they will hit the 5-day grading mark ~06-29 and would grade off a bogus 06-19 "open." **Fix before then:** void/remove the 06-19 cohort, and add a US-market-holiday skip (or a "fail loudly on stale/duplicate quote" guard) to the scanner so a closed day produces no log rather than a copy of the next session.

**Grading in the coming week:** graded through the 06-18 cohort. Reaching the 5-trading-day mark next: **06-19 cohort ~06-29** (the anomalous rows — void first), **06-22 ~06-30**, **06-23 ~07-01**.

## 2026-06-22 — Weekly verifiability audit — **⚠️ COULD NOT RUN (tooling, not site)**

The audit could not be completed this week because the live site was unreachable from the audit environment. This is an environment/tooling failure — **it is NOT evidence that the site is broken.** No live check (CSV fetch, Track-record render, claims==data, grading) could be performed, so nothing is certified this week.

**What blocked it:**
- Chrome browser tool offline — 8+ retries, "Claude in Chrome is not connected." This is the path prior audits used to reach the live site.
- `web_fetch` is provenance-gated: it only fetches URLs that appeared in an actual user chat message; the scheduled-task URLs don't qualify, so `/picks.csv` and `/outcomes.csv` returned "URL not in provenance set."
- WebSearch doesn't return the site or raw CSVs.
- curl/wget intentionally not used (prohibited as a web_fetch workaround).

**Why the local clone can't substitute:** `~/Documents/AMD Ventures/stock screener/ignitionscan` is 1 unpushed local commit ahead of origin/main (HEAD b5be38a vs origin d4aa3ac), has **no outcomes.csv** at all, and its picks.csv only runs through 2026-06-15. It can't verify what a stranger sees on the live site today.

**To unblock next run (any one works):** open Chrome with the Claude extension signed in before the scheduled time; or run the audit interactively so the live URLs enter the chat provenance; or add a permitted server-side fetch path for the two static CSVs.

**Upcoming grades (UNVERIFIED — from last week's 06-16 snapshot, not today's live data):** as of 06-16 only the 06-09 cohort (13 picks) was graded. On a 5-trading-day mark the 06-10 cohort grades ~06-17, 06-11→~06-18, 06-12→~06-19, 06-15→~06-23, 06-16→~06-24 — so several cohorts should have graded by now; confirm on the next successful run.

## 2026-06-16 — First-grades integrity check — **PASS**

Scan resumed, grades landed, and the live Track record matches the data. Claims == data.

**1. picks.csv — 200, scan resumed, no weekday gap.**
HTTP 200. 78 picks across 6 trading days (2026-06-09 → 2026-06-16). 6-15 (Mon) and 6-16 (Tue) both present, so the scan resumed cleanly. Every US market weekday in the window is present (6-09 Tue, 6-10 Wed, 6-11 Thu, 6-12 Fri, 6-15 Mon, 6-16 Tue). Note: 2026-06-13 is a **Saturday** (6-14 Sunday) — correctly no scan; the flagged "6-13 miss" doesn't apply because 6-13 was never a trading day. No gaps.

**2. outcomes.csv — exists, grader ran.**
HTTP 200. 13 graded rows = the full 2026-06-09 cohort, which reached the 5-trading-day grading mark. Grader confirmed running.

**3. Live Track record — REAL log, not the sample fallback.**
"Pulled live from the public pick log — 78 picks across 6 trading days." The only "sample" string on the page is a prototype disclaimer ("Educational sample for development hand-off"), not a fallback badge. Headline: 78 logged / 13 graded / **Win rate 38%** / median net -2.5% / mean net -2.2% / avg worst dip -18.3%. Win-rate-by-tier populates: A 50% (n=2), B 33% (n=3), C 40% (n=5), D 33% (n=3).

**4. Recomputed win rate matches.**
Independently from outcomes.csv: 5 wins / 13 graded = **38.5%** → site rounds to 38%. MATCH. Tier counts reconcile exactly to the 6-09 cohort (A 2, B 3, C 5, D 3 = 13).

**5. Methodology spot-check — clean.**
- Entry = pick-day open: grader uses the trading_date bar's Open; all 13 entry_open > 0.
- 2% cost haircut applied: verified all 13 rows satisfy ret_open_close_net == (close − open)/open × 100 − 2.0 within rounding (max diff < 0.005).
- Win = positive net return: win column matches sign of ret_open_close_net on all 13 rows (0 mismatches) — not an "ever touched +20%" definition.
- No regrades: 0 duplicate pick_ids.

**Most important fix:** None blocking. Minor housekeeping — the local git clone is stale (no outcomes.csv locally; local picks.csv only to 6-15), but the live/remote is correct, so this is a working-copy nit, not a product issue. `git pull` to resync the local clone when convenient.
