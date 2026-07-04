# ThePickLog — QA review · 2026-06-22

Full review/QA pass over the analysis + automation code (the parts the "don't fool
yourself" standard depends on). Scope, method, findings, fixes, and what was verified
clean — so the work is auditable.

## Method
1. **Independent port-fidelity audit** — a separate reviewer diffed `quality_lens.py`
   line-by-line against the source-of-truth JavaScript (`computeQuality` + helpers +
   `fetchFundamentals`) in `index.html`, checking every band table, weight, risk
   penalty, label threshold, classification rule, rounding, and null-handling site.
2. **Edge-case / crash harness** — ran every script with empty, `None`, zero-revenue,
   missing-year, and all-null inputs to find crashes and silent-wrong results.
3. **Regression check** — re-graded the 14 real tickers after fixes to confirm outputs
   are unchanged.
4. **Repo hygiene** — secret scan over all tracked files, gitignore verification,
   `py_compile` on every module, YAML parse on both workflows.

## Findings & fixes

### BUG 1 (fixed) — `compute_quality` crashed on a present-FCF / zero-revenue company
`s_fcf = band(fcf_margin, …)` returned `None` when `freeCashFlow[0]` was present but
`revenue[0]` ≤ 0, then `None * 0.25` raised `TypeError`. The JavaScript silently treats
that term as 0 (`null * number === 0`). **Fix:** replicate the JS — when `s_fcf` is
`None`, contribute `0.0`. Exposed by pre-revenue shells with a reported cash-flow line.
*Confirmed crashing before, scores cleanly after.*

### BUG 2 (fixed) — consistency sub-score diverged on a missing revenue year
With an interior `None` in the revenue array (a gap year), the Python skipped that point
while the JS coerces `null → 0` (treating it as a −100% growth year), producing a
different `business`/`overall` score. **Fix:** replicate the JS coercion so a null year
is scored identically to the live site. (Fidelity over our own preference — the goal is
that the as-of grade equals what the site would have shown.)

### HARDENING 1 — SEC fetch (`asof_grader._get`)
Was requesting `gzip, deflate` but only decompressing gzip; a non-gzip response would
break a backtest mid-run. **Now:** handles gzip (by header *and* magic bytes) and
deflate, with 2 retries + backoff for transient SEC hiccups.

### HARDENING 2 — GitHub Actions push races
Both `ignitionscan.yml` (daily scan/grade + brief) and `report.yml` (weekly) pushed
without rebasing. If a manual push or an overlapping run landed first, the push would be
rejected and that day's commit silently lost. **Now:** `git pull --rebase --autostash`
+ retry loop before push in both workflows.

## Verified clean (no change needed)
- **Port fidelity:** every band threshold table, all category weights and sub-weights,
  every risk penalty magnitude, the label thresholds + black-label override, the
  classification regex/thresholds, and all assembly ratio formulas (roic NOPAT×0.79,
  roe, D/E, current ratio, ps, pe, pfcf sentinel, evEbitda) match the JS exactly.
- **Rounding:** `js_round` reproduces JS `Math.round` over the (non-negative) score
  domain in use.
- **Regression:** the 14 real tickers grade identically before/after the fixes
  (ATPC Yellow 46 … RKDA Black 39) — fixes touch only degenerate inputs.
- **Empty-input safety:** `compare_asof` and `weekly_report` stat helpers return `nan`
  (not exceptions) on empty buckets; `compare_asof` exits gracefully when the as-of file
  is absent.
- **Self-tests:** `asof_grader --selftest` passes and its as-of-today view still
  reproduces the live `/api/edgar` array exactly (fidelity intact).
- **Secrets:** no hardcoded keys/tokens in any tracked file; all API keys are read from
  env vars only (`process.env.*`). Backtest/quality/brief artifacts are gitignored; only
  the canonical `picks.csv` / `outcomes.csv` are tracked.
- **Compile:** all 7 Python modules `py_compile` clean; both workflows parse.

## Known, accepted limitations (not bugs)
- The offline grader can't see live RVOL, so the momentum sub-score (5% weight) is always
  the neutral 50 in `quality_lens.py` — faithful to `fetchFundamentals` in isolation.
- The JS `mockFundamentals` sample path is intentionally not ported (the grader only runs
  on real EDGAR data).
- Phase-1 universe is still the 16 seeds; the power limitation is documented in
  TEST-PLAN-quality-downside.md and PHASE2-SCOPE.md.

---

# Round 2 — web app + scan/grade core · 2026-06-22

Independent review of `ignitionscan.py` (the scan/grade core that writes the immutable
log), the four `api/*.js` Vercel proxies, and `index.html`. No Critical issues: no secret
leaks, no SSRF/open-proxy, no triggerable XSS, and the log is genuinely append-only
(verified: 0 duplicate `(ticker, trading_date)` pairs, 0 duplicate outcome `pick_id`s).
Two HIGH bugs biased the track record and are now fixed.

### BUG 3 (fixed, HIGH) — transient fetch failure permanently dropped a pick from the record
`cmd_grade` wrote a terminal `"no history"` outcome on any empty Yahoo response, and the
`done` set then blocked it from ever being re-graded. A momentary Yahoo hiccup on grade
night would silently delete a real win/loss from the denominator → survivorship bias in
win rate / mean / calibration. **Fix:** a missing fetch is now treated as transient — the
pick is left ungraded so the next run retries; a terminal note is written only after the
pick is genuinely stale (>20 weekday-days old, i.e. delisted/halted). Happy path unchanged.

### BUG 4 (fixed, HIGH) — grading ignored market holidays, grading a session early
`_trading_days_since` counted Mon–Fri with no holiday calendar, so in any week with a
market holiday (Juneteenth, July 4, Thanksgiving…) a pick hit the 5-day mark one session
early and was graded off a 4-session window — mis-stating the return and making the
"graded 5 trading days later" claim literally false for those rows. **Fix:** grading now
keys off the *actual trading bars* in the fetched data — if the 5th session hasn't closed
(`len(window) < 6`), it defers to the next run instead of grading short. Removes the
holiday bug and the timezone fragility at once. (Note: pre-fix rows graded during a
holiday week may have used a short window; not rewritten, since the log is immutable —
flagged here as an erratum. Going forward it's correct. Relevant: July 4 falls in the
away-month window.)

### HARDENING 3 (fixed, MEDIUM) — accidental live-money orders
`api/alpaca.js` routed to the live endpoint whenever `ALPACA_PAPER=false` — one stray env
var from real orders, while the UI still said "PAPER." **Fix:** paper is now the floor;
going live requires TWO deliberate signals (`ALPACA_PAPER=false` **and**
`ALPACA_ALLOW_LIVE=yes_i_understand`). A single typo can no longer place real trades.

### Logged for later (lower severity, not yet changed)
- **M2** — `api/*.js` in-memory caches are per-warm-instance and unbounded; the free-tier
  rate-limit protection is weaker than the comments imply, and `factsCache` can grow.
  Bound with an LRU when convenient.
- **M3** — `index.html` track-record table trusts the `win` column rather than deriving it
  from `ret_open_close_net`. Clean today (grader sets them consistently); derive-from-return
  would keep the "stranger can verify" property even if a row were ever hand-edited.
- **M4** — `index.html` risk settings use `localStorage` (unsupported here); wrapped in
  try/catch so it degrades to defaults — settings just don't persist.
- **L1–L4** — gap proxy depends on which Yahoo `.info` field is populated; CSV appends
  aren't atomic; agent grounding is same-user prompt-injectable (text-only, contained);
  symbol sanitizer verified safe. All low / informational.

### Verified clean (core + proxies)
- Scan + grade are append-only and idempotent; the `(ticker, date)` dedupe works.
- Scoring math (`score_inputs`, `tier_of`, float/rvol/gap/price) and the grade math
  (entry=open, 2% haircut, MFE/MAE, win=positive net) are internally consistent.
- `agent.js` / `edgar.js` clean; keys env-only; Alpaca order validation (qty/side/type/price)
  is solid; symbol sanitizer blocks traversal.
- Post-fix: `ignitionscan.py` compiles, `api/alpaca.js` passes `node --check`, grader
  happy-path window selection is unchanged (regression-checked).

---
*QA pass on the analysis + automation layer AND the scan/grade core + web app. Not
investment advice. Backtest outputs stay in-sample/exploratory; the forward log remains
the only public-credibility source.*
