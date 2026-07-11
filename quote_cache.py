#!/usr/bin/env python3
"""
quote_cache.py — keep the Compete leaderboard's marks fresh with real (free) prices.

WHY
    The Compete sim ($100k play money) ranks players by total return, and
    is_get_leaderboard() values every position at `is_quotes.price` (falling back to
    cost when there's no quote). Nothing kept is_quotes populated, so every position
    marked at its cost → all returns pinned at 0 → the leaderboard was a flat tie.
    This job writes current prices for the tradeable universe into is_quotes on a
    schedule, so portfolios and the leaderboard actually MOVE.

WHY NOT the FMP feed
    FMP is licensed owner-only (no public redistribution) — that's why /api/fmp is
    gated. Caching FMP quotes into a table every signed-in player can read would
    redistribute them. So this uses the SAME free source the scan/grade pipeline
    already uses (Yahoo via yfinance). Delayed/last prices are fine for play money.

AUTH
    Writes need the Supabase SERVICE ROLE key (is_cache_quote is not granted to anon;
    RLS on is_quotes). Set SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY in the GitHub
    Action secrets. NON-FATAL: if either is missing, the job logs and exits 0 (so the
    workflow never fails just because the cache isn't wired yet).

USAGE
    SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... python3 quote_cache.py
    python3 quote_cache.py --dry-run     # fetch + print prices, no DB write
NOT INVESTMENT ADVICE. Play-money marks only.
"""
import json
import os
import sys
import urllib.request

# Tradeable Compete universe = the seed-16 the Watchlist exposes (single source of truth).
try:
    from ignitionscan import CONFIG
    UNIVERSE = list(CONFIG["UNIVERSE"])
except Exception:
    UNIVERSE = ["BJDX", "MASK", "SUGP", "GCDT", "CODX", "VMAR", "PW", "NCT",
                "HKIT", "IOTR", "SVRN", "RKDA", "BNZI", "CUPR", "ATPC", "JAGX"]


def fetch_prices(symbols):
    """Last/current price per symbol via yfinance (free, no key). NON-FATAL per name:
    a symbol that fails is skipped, not raised. Returns {ticker: price}."""
    import yfinance as yf
    out = {}
    for sym in symbols:
        px = None
        try:                                  # fast_info is the cheap, reliable path
            fi = yf.Ticker(sym).fast_info
            px = fi.get("last_price") or fi.get("lastPrice")
        except Exception:
            px = None
        if not px or px <= 0:                 # fallback: last daily close
            try:
                h = yf.Ticker(sym).history(period="5d", auto_adjust=False)
                if len(h):
                    px = float(h["Close"].dropna().iloc[-1])
            except Exception:
                px = None
        if px and px > 0:
            out[sym] = round(float(px), 4)
    return out


def upsert_quotes(url, key, prices):
    """Bulk upsert into public.is_quotes (ticker unique) with the service role key.
    One request; PostgREST merge-duplicates on the ticker conflict target."""
    rows = [{"ticker": t, "price": p} for t, p in prices.items()]
    body = json.dumps(rows).encode()
    req = urllib.request.Request(
        f"{url.rstrip('/')}/rest/v1/is_quotes?on_conflict=ticker",
        data=body, method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def main():
    dry = "--dry-run" in sys.argv
    prices = fetch_prices(UNIVERSE)
    print(f"quote_cache: fetched {len(prices)}/{len(UNIVERSE)} prices: "
          + ", ".join(f"{t}={p}" for t, p in sorted(prices.items())))
    if not prices:
        print("quote_cache: no prices fetched — nothing to write.")
        return
    if dry:
        print("quote_cache: --dry-run, not writing.")
        return
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        # NON-FATAL: the Action shouldn't fail just because the cache isn't wired yet.
        print("quote_cache: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set — skipping "
              "the DB write (add them as GitHub secrets to enable). Exiting 0.")
        return
    try:
        status = upsert_quotes(url, key, prices)
        print(f"quote_cache: upserted {len(prices)} quotes into is_quotes (HTTP {status}).")
    except Exception as e:
        # Still non-fatal: a transient Supabase/network hiccup must not fail the workflow.
        print(f"quote_cache: upsert failed ({type(e).__name__}: {str(e)[:120]}) — skipped.")


if __name__ == "__main__":
    main()
