#!/usr/bin/env python3
"""
data_provider.py — pluggable market-data layer for the ThePickLog logger.

WHY
    The logger currently pulls quotes/OHLC from Yahoo via the unofficial `yfinance`
    scraper. That's fine for a free/personal tool, but Yahoo's ToS restricts
    commercial redistribution and yfinance is unsanctioned — so it's the weakest
    link the day ThePickLog monetizes. This module lets the engine switch to a
    licensed source (Polygon) by flipping one env var, WITHOUT changing any of the
    engine's logic or the shape of the immutable log.

DESIGN
    One interface, two implementations, a factory:

        P = get_provider()               # reads $DATA_PROVIDER (default "yfinance")
        q = P.get_quote("BJDX")          # -> dict matching ignitionscan.fetch_one()
        bars = P.get_daily_bars(t, a, b) # -> list of {date,open,high,low,close,volume}
        r = P.get_market_regime()        # -> "risk-on" | "risk-off" | "neutral" | "unknown"

    Default is "yfinance" so importing/using this module changes NOTHING until you
    set DATA_PROVIDER=polygon + POLYGON_API_KEY. See PROVIDER-SWAP.md for wiring.

    PolygonProvider uses only the standard library (urllib) — no new dependency.

⚠️ TWO FIELDS POLYGON CANNOT CLEANLY REPLACE — verify before you rely on them:
    - float_shares: Polygon returns shares *outstanding*, not free float. The screen's
      float filter/score wants FREE FLOAT. This adapter falls back to outstanding and
      sets `float_is_outstanding=True` so the caller can flag it. For true float you
      still need FMP/another source (or accept the approximation, loudly).
    - short_interest_pct: Polygon's short-interest feed is FINRA-sourced on a two-week
      cadence and may require a specific plan. Returns "" if unavailable.

⚠️ PROVENANCE: switching the price source changes the record's lineage. When you flip
    to Polygon, BUMP MODEL_VERSION in ignitionscan.py (e.g. "v0.2-yf" -> "v0.3-poly")
    so every picks.csv row stays attributable to the feed that produced it. This is a
    verifiability-standard requirement, not optional.
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta


# ============================================================ yfinance (default)
class YFinanceProvider:
    """Wraps the engine's existing Yahoo logic so behavior is byte-identical."""

    name = "yfinance"

    def __init__(self):
        try:
            import yfinance as yf
        except ImportError:
            sys.exit("yfinance not installed. Run:  pip install yfinance")
        self.yf = yf

    def get_quote(self, symbol, retries=3):
        info = None
        for attempt in range(retries):
            try:
                info = self.yf.Ticker(symbol).info
                if info and (info.get("regularMarketPrice") or info.get("currentPrice")):
                    break
            except Exception:
                if attempt == retries - 1:
                    raise
            time.sleep(1.5 * (attempt + 1))
        if not info:
            return None
        price = info.get("regularMarketPrice") or info.get("currentPrice")
        if price is None:
            return None
        prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
        vol = info.get("regularMarketVolume") or info.get("volume")
        avg = (info.get("averageVolume") or info.get("averageDailyVolume3Month")
               or info.get("averageVolume10days"))
        flt = info.get("floatShares") or info.get("sharesOutstanding")
        si = info.get("shortPercentOfFloat")
        si_pct = round(si * 100, 2) if isinstance(si, (int, float)) else ""
        return {"symbol": symbol, "price": float(price), "prev": float(prev or 0),
                "vol": float(vol or 0), "avg": float(avg or 0),
                "float_shares": int(flt or 0), "short_interest_pct": si_pct,
                "float_is_outstanding": not bool(info.get("floatShares"))}

    def get_daily_bars(self, symbol, start, end):
        """start/end are 'YYYY-MM-DD' strings (end exclusive, like the current code)."""
        df = self.yf.Ticker(symbol).history(start=start, end=end, auto_adjust=False)
        bars = []
        for idx, row in df.iterrows():
            bars.append({"date": idx.strftime("%Y-%m-%d"),
                         "open": float(row["Open"]), "high": float(row["High"]),
                         "low": float(row["Low"]), "close": float(row["Close"]),
                         "volume": float(row.get("Volume", 0) or 0)})
        return bars

    def get_market_regime(self):
        try:
            info = self.yf.Ticker("SPY").info
            p = info.get("regularMarketPrice")
            pc = info.get("regularMarketPreviousClose")
            chg = (p - pc) / pc * 100 if (p and pc) else 0
            return "risk-on" if chg > 0.3 else "risk-off" if chg < -0.3 else "neutral"
        except Exception:
            return "unknown"


# ================================================================ Polygon (licensed)
class PolygonProvider:
    """Licensed feed. Stdlib-only. Set POLYGON_API_KEY.

    Endpoints used (verify against your plan/tier at polygon.io/docs):
      snapshot   /v2/snapshot/locale/us/markets/stocks/tickers/{t}
      aggs(day)  /v2/aggs/ticker/{t}/range/1/day/{from}/{to}
      ref        /v3/reference/tickers/{t}          (shares outstanding)
      short int  /stocks/v1/short-interest?ticker={t}   ← VERIFY path/plan
    Pre-market note: snapshot starts updating ~4:00am ET; confirm your plan serves
    pre-market data if the scan runs before the open.
    """

    name = "polygon"
    BASE = "https://api.polygon.io"

    def __init__(self, api_key=None, avg_window_days=30, throttle=0.2):
        self.key = api_key or os.environ.get("POLYGON_API_KEY", "")
        if not self.key:
            sys.exit("POLYGON_API_KEY not set. Export it or set the GitHub Actions secret.")
        self.avg_window_days = avg_window_days
        self.throttle = throttle  # seconds between calls; raise on free tier (5 req/min)

    def _get(self, path, params=None, retries=3):
        params = dict(params or {})
        params["apiKey"] = self.key
        url = self.BASE + path + "?" + urllib.parse.urlencode(params)
        last = None
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "ThePickLog/1.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    return json.loads(r.read().decode("utf-8"))
            except Exception as e:  # noqa: BLE001 — includes HTTP 429 rate limits
                last = e
                time.sleep(1.5 * (attempt + 1))
        raise last

    def get_quote(self, symbol):
        # 1) snapshot -> last price, today's volume, prev close
        try:
            snap = self._get(f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}")
            t = (snap or {}).get("ticker", {})
        except Exception:
            return None
        last_trade = (t.get("lastTrade") or {}).get("p")
        day = t.get("day") or {}
        prev_day = t.get("prevDay") or {}
        # Pre-market: day.c may be 0 until the open; prefer lastTrade, then min-bar close.
        price = last_trade or day.get("c") or (t.get("min") or {}).get("c")
        prev = prev_day.get("c")
        vol = day.get("v") or (t.get("min") or {}).get("av") or 0
        if not price:
            return None
        time.sleep(self.throttle)

        # 2) average volume from trailing daily aggregates
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=self.avg_window_days * 2)  # pad for weekends/holidays
        avg = 0.0
        try:
            aggs = self._get(
                f"/v2/aggs/ticker/{symbol}/range/1/day/{start.isoformat()}/{end.isoformat()}",
                {"adjusted": "false", "sort": "desc", "limit": self.avg_window_days})
            vols = [b.get("v", 0) for b in (aggs.get("results") or [])]
            avg = sum(vols) / len(vols) if vols else 0.0
        except Exception:
            pass
        time.sleep(self.throttle)

        # 3) shares outstanding (NOT free float — see module header caveat)
        flt, float_is_outstanding = 0, True
        try:
            ref = self._get(f"/v3/reference/tickers/{symbol}")
            res = ref.get("results") or {}
            flt = int(res.get("weighted_shares_outstanding")
                      or res.get("share_class_shares_outstanding") or 0)
        except Exception:
            pass
        time.sleep(self.throttle)

        # 4) short interest (optional; FINRA-sourced, ~2wk cadence). Best-effort.
        si_pct = self._short_interest_pct(symbol, flt)

        return {"symbol": symbol, "price": float(price), "prev": float(prev or 0),
                "vol": float(vol or 0), "avg": float(avg or 0),
                "float_shares": int(flt or 0), "short_interest_pct": si_pct,
                "float_is_outstanding": float_is_outstanding}

    def _short_interest_pct(self, symbol, shares):
        """VERIFY endpoint path + plan availability. Returns '' if unavailable."""
        try:
            si = self._get("/stocks/v1/short-interest", {"ticker": symbol, "limit": 1})
            rows = si.get("results") or []
            if rows and shares:
                short = rows[0].get("short_interest") or rows[0].get("settlement_short_interest")
                if short:
                    return round(short / shares * 100, 2)
        except Exception:
            pass
        return ""

    def get_daily_bars(self, symbol, start, end):
        """start/end 'YYYY-MM-DD'. Current engine treats end as EXCLUSIVE (yfinance
        convention); Polygon's range is INCLUSIVE, so we shift end back one day to match."""
        end_incl = (datetime.strptime(end, "%Y-%m-%d").date() - timedelta(days=1)).isoformat()
        try:
            aggs = self._get(
                f"/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end_incl}",
                {"adjusted": "false", "sort": "asc", "limit": 5000})
        except Exception:
            return []
        bars = []
        for b in (aggs.get("results") or []):
            d = datetime.fromtimestamp(b["t"] / 1000, timezone.utc).strftime("%Y-%m-%d")
            bars.append({"date": d, "open": float(b["o"]), "high": float(b["h"]),
                         "low": float(b["l"]), "close": float(b["c"]),
                         "volume": float(b.get("v", 0))})
        return bars

    def get_market_regime(self):
        try:
            snap = self._get("/v2/snapshot/locale/us/markets/stocks/tickers/SPY")
            t = snap.get("ticker", {})
            p = (t.get("lastTrade") or {}).get("p") or (t.get("day") or {}).get("c")
            pc = (t.get("prevDay") or {}).get("c")
            chg = (p - pc) / pc * 100 if (p and pc) else 0
            return "risk-on" if chg > 0.3 else "risk-off" if chg < -0.3 else "neutral"
        except Exception:
            return "unknown"


# ==================================================================== factory
def get_provider(name=None):
    name = (name or os.environ.get("DATA_PROVIDER", "yfinance")).lower()
    if name in ("polygon", "poly"):
        return PolygonProvider()
    return YFinanceProvider()


# ==================================================================== selftest
if __name__ == "__main__":
    prov = get_provider()
    print(f"provider = {prov.name}")
    for sym in ("SPY", "BJDX"):
        try:
            q = prov.get_quote(sym)
            print(f"  {sym}: {q}")
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"  {sym}: ERROR {type(e).__name__} {e}")
    print("regime:", prov.get_market_regime())
    # daily bars smoke test
    today = datetime.now(timezone.utc).date()
    start = (today - timedelta(days=10)).isoformat()
    try:
        bars = prov.get_daily_bars("SPY", start, today.isoformat())
        print(f"SPY bars ({len(bars)}): {bars[:2]}{' ...' if len(bars) > 2 else ''}")
    except Exception as e:  # noqa: BLE001
        print("bars ERROR:", e)
