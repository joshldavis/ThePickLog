# ThePickLog — Pick-Up / Resume (as of 2026-07-10)

One place to restart from. Start here + your project memory. Repo is clean and in sync
(HEAD `728bf9a`); nothing uncommitted.

---

## Live right now (deployed + verified)
- **Site:** thepicklog.vercel.app (+ ignitionscan.vercel.app), Vercel Hobby.
- **Autopilot:** GitHub Actions daily scan/grade + weekly report + hypothesis tracking.
  v0.3 market-wide discovery now runs on **free Yahoo screeners** (`UNIV_SOURCE=yahoo`,
  cohort `v0.3-yf`); Alpaca is an *optional* upgrade, not required.
- **Infra safety net:** tamper-evident hash-chain ledger, offsite artifact backups,
  GitHub-issue watchdog, healthchecks.io email dead-man's-switch (both monitors green),
  Vercel deploy-hook fallback. All secrets set.
- **Legal pages:** `/disclaimer` + `/privacy` live (AMD Ventures, LLC), footer links
  site-wide — marked "pending legal review."
- **FMP licensing gate:** `/api/fmp` is owner-only (`FMP_UI_TOKEN`). Visitors see labeled
  "Sample data"; you get live data via your `?t=<token>` link. Token is in Vercel env
  (not stored in any doc). The record/KPIs/EDGAR panels are unaffected.

## Shipped this session (7/06–7/10)
Risk review → decision table; infra safety net (item 4); legal pages (items 1/2/6/8);
data-source audit (item 3); FMP owner-only gate; and a ready-to-flip data-provider
adapter (`data_provider.py` with Alpaca/Polygon/yfinance + `PROVIDER-SWAP.md` +
`ALPACA-DATA-KEYS-SETUP.md`). Details in `ThePickLog-DataSource-Audit-2026-07-07.md`,
`ThePickLog-Risk-Decision-Table-2026-07-06.md`, `ThePickLog-Launch-Copy-P0-2026-07-06.md`.

## Open / next actions
| # | Item | Next step | Priority | Blocks 7/23 launch? |
|---|------|-----------|----------|---------------------|
| 1 | Lawyer review of disclaimer + privacy wording | Your offline task | P1 | No |
| 2 | Alpaca data cutover (now OPTIONAL) | If wanted: subscribe Algo Trader Plus ($99, SIP), add `ALPACA_KEY_ID`/`ALPACA_SECRET_KEY` GitHub secrets, then `UNIV_SOURCE=alpaca` (v0.3) or `DATA_PROVIDER=alpaca` (logger). Guide: `ALPACA-DATA-KEYS-SETUP.md` | P2 | No |
| 3 | Per-user "connect your Alpaca paper account" feature | Parked (you paused it). Users don't need Alpaca for anything | Nice-to-have | No |
| 4 | FMP public live panels | Leave gated owner-only ($0). Only if you want them public: FMP display license, or Polygon business, or delayed data | P2 | No |
| 5 | `thepicklog.com` domain + "ThePickLog" trademark | Secure domain + knockout search | P1 | No |
| 6 | Vercel Hobby → Pro | At monetization only | P2 | No |
| 7 | Portfolio-wide FDR / multiplicity view (risk item 5) | Partly covered by H-IND1 cluster work; confirm | P1 | No |
| 8 | "Go big" repositioning drafts | Pending your review; not deployed (`stock screener/ThePickLog-*` strategy docs) | P2 | No |
| 9 | Soft-launch readiness (7/02 audit B1–B4) | Mobile pass done; re-check Compete signup tested + pricing section before launch | P1 | Yes-ish |

## On the calendar (automated + dates)
- **~7/23** — family/friends Compete soft launch (your target).
- **7/27 10:30am ET** — `thepicklog-gate1-external-validity-verdict` scheduled task fires:
  reads OOS results, renders the Gate-1 (external-validity + monetization) verdict, and
  publishes it to the repo + site. **Single owner of the verdict** — nothing for you to do
  unless you want to review first. Honest prior: the edge likely does *not* survive, which
  is a process success.
- **Saturdays 9am ET** — `ignitionscan-verifiability-audit` (weekly "stranger can verify" check).
- **8/3** — `ignitionscan-timesfm-reminder` (test Google TimesFM on the exit edge).
- **~late Aug** — H-DIL hypothesis matures.

## Loose-end checks (all clear)
- Repo clean, in sync with origin. ✅
- Secrets set: `FMP_UI_TOKEN`, `HEALTHCHECK_URL`(+`_WEEKLY`), `VERCEL_DEPLOY_HOOK`. ✅
  (Alpaca GitHub secrets only needed if/when you do the optional cutover.)
- Recurring nuisance: a stale `.git/index.lock` reappears sometimes — cleared on each push;
  root cause still unknown (flagged 7/02). Not blocking.

## Key docs (all in `~/Documents/AMD Ventures/stock screener/`)
Audit: `ThePickLog-DataSource-Audit-2026-07-07.md` · Risk table:
`ThePickLog-Risk-Decision-Table-2026-07-06.md` · Launch copy:
`ThePickLog-Launch-Copy-P0-2026-07-06.md` · In repo: `INTEGRITY.md`, `PROVIDER-SWAP.md`,
`ALPACA-DATA-KEYS-SETUP.md`, `ROADMAP.md`.
