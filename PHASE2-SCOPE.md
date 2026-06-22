# Phase 2 scope — full-market, point-in-time test of Finding B

**Status:** scoped, not started · **Drafted:** 2026-06-22 · **Prereq for:** settling TEST-PLAN-quality-downside.md
**Decision owner:** Josh (this needs a spend + a go/no-go — see §4)

Phase 1 removed look-ahead and produced a clean null on the 16-seed universe; the
blocker was **power** (12/6 distinct tickers/bucket vs ≥25 required). Phase 2 exists
only to clear that power bar by widening the universe. Read this before spending a
dollar — the honest conclusion may be "not worth it yet."

## 1. What Phase 2 actually requires

Three things, in increasing difficulty:

1. **A historical low-float universe, not 16 seeds.** Need, for each past trading
   day, the set of US sub-$10 names that would have passed the live filter
   (`price 0.50–10`, `float ≤ 50M`, RVOL/gap screen). Daily OHLCV is free
   (`yfinance`); the screen logic already exists in `ignitionscan.py` / `backtest.py`.
2. **Point-in-time FLOAT / shares — the real blocker.** The screen keys on float,
   and free sources only give *current* float. Applying current float to past dates
   reintroduces a look-ahead/selection bias on the universe itself. `backtest.py`
   already flags this limitation. Genuine point-in-time float needs a paid feed.
3. **As-of-date fundamentals at scale.** Already solved — `asof_grader.py` does this
   from free SEC companyfacts (1 request/ticker, cached). Scales to hundreds of
   tickers fine. *This part is done.*

So the only thing standing between here and a valid test is **point-in-time float/
universe data**.

## 2. Data options (pick one)

| Option | Gets you | Cost (approx, verify current) | Verdict |
|---|---|---|---|
| **yfinance + current float** | Wider universe, but float is current-only | free | Cheapest, but keeps a selection-bias caveat — a *better* null, not a clean one |
| **Polygon.io / Financial datasets** | Historical shares outstanding + daily bars | ~$30–100/mo, verify | Most likely best value; check float vs shares-outstanding coverage |
| **FMP paid tier** | Historical statements + some float | ~$20–50/mo, verify | Already half-integrated (api/fmp.js); revisit the paid note in ignitionscan.py |
| **Sharadar / Quandl (Nasdaq Data Link)** | Clean point-in-time fundamentals + tickers | higher | Gold standard if budget allows |

*(All prices are from memory and MUST be re-verified before committing — they change.)*

## 3. Build steps once data is chosen

1. Add a `universe_asof(date)` provider behind an interface so the source is swappable
   (yfinance-current vs paid point-in-time). Keep `ignitionscan.py` the single
   scoring source of truth.
2. Reconstruct daily screens across ~12–24 months → a candidate pick set (thousands
   of rows, many distinct tickers).
3. Grade each with `asof_grader.py` (already built) → as-of quality label per pick.
4. Outcomes via the existing `backtest.py` MAE/return window.
5. Score with `compare_asof.py` (already built) — it already enforces the four
   pre-registered bars incl. ≥25 distinct tickers/bucket and the cluster bootstrap.
6. Log the dated result in STRATEGY §6, same as Phase 1.

Steps 3 and 5 are done; the new work is steps 1–2 (the universe provider) + wiring.

## 4. Go / no-go — do NOT default to "yes"

Phase 2 is the most technically interesting thread and the **lowest-leverage one right
now**, because:

- The backtest can only do **variable selection** — it can never back a public claim.
  The forward log is the only thing that earns the claim (SYNTHESIS §1.2), and it's
  maturing for free.
- Finding A (inverse momentum) is **already holding out-of-sample** on the live log
  (see reports/LATEST.md) — the bankable messaging signal doesn't need Phase 2.
- Spending on point-in-time data to chase a quality→drawdown signal that Phase 1
  suggested is ~zero may be paying to confirm a null.

**Recommended trigger:** only start Phase 2 if (a) the forward log itself hints at a
quality→drawdown effect worth chasing, or (b) you decide to actively sharpen the score
(not just narrate the record). Otherwise let the forward log mature and revisit after
the ~8-week gate. A free-tier "wider but current-float" run is a reasonable cheap
middle step if curiosity wins before then — just keep the selection-bias caveat loud.

---
*Strategic/technical plan, not legal or financial advice. Backtest stays in-sample and
never a performance claim; the forward log remains the only public-credibility source.*
