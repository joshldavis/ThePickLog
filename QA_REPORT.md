# IgnitionScan — QA review · 2026-06-22

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
*QA pass on the analysis + automation layer. Not investment advice. Backtest outputs stay
in-sample/exploratory; the forward log remains the only public-credibility source.*
