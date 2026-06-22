# IgnitionScan — Audit Log

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
