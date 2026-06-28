# IgnitionScan — Audit Log

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
