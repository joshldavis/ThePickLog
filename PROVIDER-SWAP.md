# Swapping the logger off Yahoo → Alpaca (drop-in)

`data_provider.py` lets the engine switch its market-data feed with one env var. It's
**inert until you flip it** — default `DATA_PROVIDER=yfinance` reproduces today's
behavior exactly. This is the wiring guide for moving the logger off the unofficial
Yahoo scraper (the P1 data-licensing item).

**Chosen feed: Alpaca.** You already have the account, it's ~$99/mo for the coverage you
need (vs Polygon's $1,999/mo business tier), and the logger is backend/own-use — not
public redistribution — so it fits a standard subscription. Polygon is kept in the
adapter as an alternative (`DATA_PROVIDER=polygon`). See the audit doc
`ThePickLog-DataSource-Audit-2026-07-07.md` for the full comparison.

## Why move off Yahoo
`yfinance` scrapes Yahoo's unofficial endpoints; Yahoo's ToS restricts commercial
redistribution. Fine for the free/personal tool, but the weakest link at monetization.

## Before you rely on Alpaca — verify these
1. **Use the SIP feed.** Set `ALPACA_DATA_FEED=sip`. The free IEX feed is ~2-3% of
   market volume and unreliable for low-float microcaps (your actual universe). SIP
   (full market) needs **Algo Trader Plus, $99/mo** — subscribe before cutover.
2. **Business/own-use terms.** Confirm with Alpaca support that your LLC using the
   $99 tier for internal/own data processing (not public redistribution) is fine —
   internal use normally is; redistribution/display is the restricted part.
3. **Float is approximated.** Alpaca returns no share count, so the adapter fills
   `float_shares` from **free SEC EDGAR shares outstanding** (over-counts vs true
   float; flagged via `float_is_outstanding`). Acceptable for the screen, but know it.
4. **Short interest** comes from FINRA later (returns "" for now) — same as before the
   swap; Yahoo's `shortPercentOfFloat` was the only free source and it's captured-not-scored.

## Test it first (no engine changes)
```bash
export ALPACA_KEY_ID=...  ALPACA_SECRET_KEY=...
DATA_PROVIDER=alpaca ALPACA_DATA_FEED=sip python data_provider.py   # selftest: SPY+BJDX
```
Confirm the quote dict looks sane (price/prev/vol/avg/float) before wiring it in.

## The wiring (3 edits in ignitionscan.py) — same for any provider

**0. Provenance — bump the model version** so picks stay attributable to their feed:
```python
MODEL_VERSION = "v0.3-alpaca"   # was "v0.2-yf"
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
(You can keep `_yf`, `fetch_one`, `market_regime` — unused when `DATA_PROVIDER=alpaca`.)

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
The logger runs on GitHub Actions, so the Alpaca keys must be **repo secrets** (the ones
in Vercel are for the trading proxy, not the Actions runner). Add under repo
**Settings → Secrets → Actions**: `ALPACA_KEY_ID`, `ALPACA_SECRET_KEY`. Then in
`.github/workflows/ignitionscan.yml` add to the job env (and you can drop the
`pip install yfinance` once fully on Alpaca — the Alpaca path is stdlib-only):
```yaml
    env:
      DATA_PROVIDER: alpaca
      ALPACA_DATA_FEED: sip
      ALPACA_KEY_ID: ${{ secrets.ALPACA_KEY_ID }}
      ALPACA_SECRET_KEY: ${{ secrets.ALPACA_SECRET_KEY }}
```
Leave `DATA_PROVIDER` unset (or `yfinance`) to instantly roll back.

## Cutover guidance (protect the immutable record)
- **Don't regrade old picks with the new feed.** Prices differ slightly vendor-to-vendor;
  regrading history would rewrite the immutable record. Let existing picks finish grading
  on Yahoo; start Alpaca for **new** picks only (the model-version bump marks the seam).
- Keep EDGAR for fundamentals/catalyst/dilution + the float proxy, and FINRA for short
  interest — this swap is only the price/OHLC/volume layer.
- `data_provider.py` ships mock-tested; still run the live selftest against your keys
  (with `ALPACA_DATA_FEED=sip`) before the first real Alpaca scan.

## Alternative: Polygon (kept in the adapter)
`DATA_PROVIDER=polygon` + `POLYGON_API_KEY` works too, but Polygon's business/public-use
tier is $1,999/mo — only worth it if you also need it for **public** real-time display.
For the backend logger, Alpaca at $99 is the better fit.
