# Swapping the logger off Yahoo → Polygon (drop-in)

`data_provider.py` lets the engine switch its market-data feed with one env var. It's
**inert until you flip it** — default `DATA_PROVIDER=yfinance` reproduces today's
behavior exactly. This file is the wiring guide for when you have a Polygon key and are
ready to move off the unofficial Yahoo scraper (the P1 data-licensing item).

## Why
`yfinance` scrapes Yahoo's unofficial endpoints; Yahoo's ToS restricts commercial
redistribution. Fine for the free/personal tool, but it's the weakest link the day you
monetize. Polygon is a licensed feed with clear commercial terms. See the audit doc
`ThePickLog-DataSource-Audit-2026-07-07.md` in the stock-screener folder.

## Before you rely on it — 3 things to verify on your Polygon plan
1. **Pre-market data.** The scan runs ~7:30am ET (pre-market). Polygon's snapshot starts
   updating ~4:00am ET, but confirm your tier serves pre-market (Starter is 15-min
   delayed; real-time is a higher tier). If not, the gap%/price at screen will be wrong.
2. **Free float.** Polygon returns shares *outstanding*, not free float. The screen's
   float filter + float_score want FREE FLOAT. The adapter falls back to outstanding and
   sets `float_is_outstanding=True`. For true float keep FMP/another source, or accept the
   approximation knowingly (it will change which names screen).
3. **Short interest.** Polygon's short-interest feed is FINRA-sourced, ~2-week cadence,
   possibly plan-gated. Verify the endpoint path in `_short_interest_pct()` and that your
   plan includes it; otherwise it returns "" (same as Yahoo when unavailable).

## Test it first (no engine changes)
```bash
export POLYGON_API_KEY=...          # your key
DATA_PROVIDER=polygon python data_provider.py     # selftest: SPY + BJDX quote, regime, bars
```
Confirm the quote dict looks sane (price/prev/vol/avg/float) before wiring it in.

## The wiring (3 edits in ignitionscan.py)

**0. Provenance — bump the model version** so picks stay attributable to their feed:
```python
MODEL_VERSION = "v0.3-poly"   # was "v0.2-yf"
```

**1. Top of file:** `import data_provider as dp`

**2. cmd_scan** — replace the Yahoo bits:
```python
# was: yf = _yf()
P = dp.get_provider()
# was: regime = market_regime(yf)
regime = P.get_market_regime()
...
# was: q = fetch_one(yf, sym)
q = P.get_quote(sym)          # same dict shape: price/prev/vol/avg/float_shares/short_interest_pct
```
(You can keep `_yf`, `fetch_one`, `market_regime` in the file — they're just unused when
`DATA_PROVIDER=polygon`.)

**3. cmd_grade + persist_path** — the provider returns a list of dict bars (sorted asc,
keys: date/open/high/low/close/volume) instead of a pandas DataFrame:
```python
P = dp.get_provider()
bars = P.get_daily_bars(p["ticker"], start, end)      # was: df = yf.Ticker(...).history(...)
if not bars:
    if stale: append_outcome(p, "no history (gave up after retries)"); graded += 1
    continue
idx = [i for i, b in enumerate(bars) if b["date"] == start]
if not idx:
    if stale: append_outcome(p, "no entry bar"); graded += 1
    continue
window = bars[idx[0]: idx[0] + GRADE + 1]
if len(window) < GRADE + 1:
    continue
o = window[0]["open"]; c = window[0]["close"]
close_5d = window[GRADE]["close"]
hi = max(b["high"] for b in window); lo = min(b["low"] for b in window)
# ... rest unchanged ...
persist_path(p, window)
```
And in `persist_path`, iterate the list instead of the DataFrame:
```python
for i, bar in enumerate(window):
    append_row(PATHS_CSV, PATH_FIELDS, {
        "pick_id": p["pick_id"], "ticker": p["ticker"],
        "trading_date": p["trading_date"], "session_idx": i,
        "bar_date": bar["date"],
        "open": round(bar["open"], 4), "high": round(bar["high"], 4),
        "low": round(bar["low"], 4), "close": round(bar["close"], 4),
        "volume": int(bar["volume"]) if bar["volume"] == bar["volume"] else "",
    })
```

## The GitHub Actions change
In `.github/workflows/ignitionscan.yml`, add to the job env and (optionally) drop the
yfinance install once you're fully on Polygon (the adapter's Polygon path is stdlib-only):
```yaml
    env:
      DATA_PROVIDER: polygon
      POLYGON_API_KEY: ${{ secrets.POLYGON_API_KEY }}
```
Add `POLYGON_API_KEY` under repo **Settings → Secrets → Actions** (same place as the
healthcheck secrets). Keep `DATA_PROVIDER` unset (or `yfinance`) to instantly roll back.

## Cutover guidance (protect the immutable record)
- **Don't regrade old picks with the new feed.** Prices differ slightly vendor-to-vendor;
  regrading history would rewrite the immutable record. Let existing picks finish grading
  on Yahoo; start Polygon for **new** picks only (the model-version bump marks the seam).
- Keep EDGAR for fundamentals/catalyst/dilution (free, redistributable) and FINRA for
  short interest — this swap is only the price/OHLC/volume layer.
- `data_provider.py` ships with a mock-tested parser; still run the live selftest against
  your key before the first real Polygon scan.
