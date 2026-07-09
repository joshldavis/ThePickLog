#!/usr/bin/env python3
"""
universe.py — v0.3 market-wide candidate discovery (H-UNIV1, registered 2026-07-08;
free-feed implementation amended 2026-07-09).

WHY
    The v0.2 record scans a FIXED 16-ticker list, and 13–16 of the 16 pass every day.
    That makes the "screen" a watchlist: effective sample size ≈ 16 names, no
    unscreened control group, no external validity beyond those names (HYPOTHESES.md
    batch #3, H-IND1 / H-UNIV1). This module makes the universe CRITERIA-DEFINED:
    the candidate pool is the whole US-listed market, and the engine genuinely
    selects a small daily subset.

SOURCES (env UNIV_SOURCE)
    yahoo (default, FREE) — cohort tag v0.3-yf
        Pool = Yahoo custom equity screen (percentchange ≥ 10, price 0.50–10, US,
        paged) ∪ predefined lists (day_gainers, small_cap_gainers,
        aggressive_small_caps, most_actives). Same feed as the v0.2 record
        (yfinance), so lineage stays consistent. Per-name quotes are premarket-aware
        (preMarketPrice preferred when present). Float = Yahoo floatShares
        (fallback sharesOutstanding).
        KNOWN LIMITATION (documented, accepted): before the open, Yahoo's list
        rankings lag — a name that only started moving in TODAY's premarket may not
        surface until the open. Yesterday's movers gapping again ARE caught (the
        premarket gap gate does the real selection). Upgrading discovery to Alpaca
        SIP closes this gap.
    alpaca (optional, paid SIP) — cohort tag v0.3-alpaca (a NEW sub-cohort if enabled)
        Pool = Alpaca screener top-50 gainers ∪ top-100 most-actives; float from the
        free SEC EDGAR shares-outstanding proxy. Needs ALPACA_KEY_ID/SECRET + SIP.

WHAT IS FROZEN (changing any of this requires a new registration)
    ELIGIBILITY GATES (2026-07-08):
        price          0.50 ≤ p ≤ 10.00          (same band as v0.2 FILTERS)
        gap            gap_pct ≥ +10.0           (up-gaps only; premarket-aware)
        rvol           rvol ≥ 2.0                (needs a real avg-volume base, >0)
        float          0 < shares ≤ 50,000,000   (missing share data EXCLUDES —
                                                  it never scores a free 100)
    SYMBOL HYGIENE: common stock on listed exchanges only — OTC/pink sheets
    excluded, units/warrants/rights/share-class suffixes excluded.
    SCORING: the UNCHANGED v0.2 formula (PRINCIPLES P5). Publish TOP 10 by score.
    CONTROL POOL: every screened candidate (eligible or not, published or not) is
    logged to candidates.csv — the eligible-but-unpublished names are H-CTRL's
    forward-only control group.

    All hard failures are LOUD (SystemExit) — a market-wide scan that silently logs
    a partial or fake pool would poison the cohort. The GitHub Action wraps this step
    with continue-on-error so a v0.3 failure never blocks the v0.2 commit.

Not investment advice. The v0.3 cohort is unvalidated until its own OOS record says
otherwise; it shares nothing with the v0.2 verdict (Gate-1 reads v0.2 only).
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# Frozen H-UNIV1 parameters (2026-07-08). Do NOT tune in place — re-register instead.
GATES = {
    "price_min": 0.50,
    "price_max": 10.00,
    "gap_min_pct": 10.0,
    "rvol_min": 2.0,
    "float_max_shares": 50_000_000,
    "max_published": 10,
    # discovery sizes (pool plumbing, not selection criteria)
    "top_gainers": 50,        # alpaca path
    "top_actives": 100,       # alpaca path
    "yahoo_pool_max": 250,    # yahoo path: cap on pooled symbols
    "yahoo_quote_max": 80,    # yahoo path: cap on per-name .info lookups (ranked by move)
}

# Yahoo exchange strings that mean OTC / pink sheets — never candidates.
_OTC_MARKERS = ("OTC", "PINK", "PNK", "OBB", "YHD", "GREY", "EXPERT MARKET")


def _hygiene_ok(symbol, exchange_name=""):
    """Common stock on a listed exchange only. Drops OTC/pink sheets and obvious
    units/warrants/rights/share-classes. Heuristic, documented: a wrongly excluded
    common ticker costs one candidate; a wrongly included warrant/OTC pump would
    poison the pick log."""
    s = (symbol or "").upper()
    if not s:
        return False
    ex = (exchange_name or "").upper()
    if any(m in ex for m in _OTC_MARKERS):
        return False
    if "." in s or "/" in s or "-" in s:
        return False  # preferred / class shares like BRK.A
    if len(s) == 5 and s[-1] in ("W", "U", "R"):
        return False  # 5-letter warrant/unit/right suffixes (e.g. ABCDW)
    if s.endswith("WS"):
        return False
    return True


def gate_check(price, gap_pct, rvol, float_shares, g=GATES):
    """Return "" if eligible, else the FIRST reject reason (frozen order:
    price, gap, rvol, float). Pure function — unit-tested in --selftest."""
    if price is None or not (g["price_min"] <= price <= g["price_max"]):
        return "price_band"
    if gap_pct is None or gap_pct < g["gap_min_pct"]:
        return "gap_lt_min"
    if rvol is None or rvol < g["rvol_min"]:
        return "rvol_lt_min"
    if not float_shares or float_shares <= 0:
        return "float_unknown"
    if float_shares > g["float_max_shares"]:
        return "float_gt_max"
    return ""


# ================================================================== yahoo (free)
def _yf():
    try:
        import yfinance as yf
        return yf
    except ImportError:
        sys.exit("yfinance not installed. Run:  pip install yfinance")


def _yahoo_screen_page(yf, query, offset, count, predefined=None):
    """One page of screener results; tolerant of yfinance API drift."""
    try:
        if predefined is not None:
            return (yf.screen(predefined, count=count, offset=offset) or {}).get("quotes") or []
        return (yf.screen(query, sortField="percentchange", sortAsc=False,
                          count=count, offset=offset) or {}).get("quotes") or []
    except TypeError:
        # older yfinance without offset kwarg — first page only
        if offset:
            return []
        if predefined is not None:
            return (yf.screen(predefined, count=count) or {}).get("quotes") or []
        return (yf.screen(query, sortField="percentchange", sortAsc=False,
                          count=count) or {}).get("quotes") or []


def _yahoo_pool(yf, verbose):
    """Market-wide candidate pool from free Yahoo screeners. Returns
    {symbol: screener_row}. Custom criteria query first (the true market-wide
    sweep), predefined mover/actives lists as a supplement."""
    pool = {}

    def add(rows, src):
        for r in rows or []:
            sym = (r.get("symbol") or "").upper()
            if not sym or sym in pool:
                continue
            if not _hygiene_ok(sym, r.get("fullExchangeName") or r.get("exchange") or ""):
                continue
            r["_src"] = src
            pool[sym] = r

    # 1) custom criteria sweep: %chg >= gap gate, price inside the frozen band, US.
    q = yf.EquityQuery("and", [
        yf.EquityQuery("gt", ["percentchange", GATES["gap_min_pct"]]),
        yf.EquityQuery("gte", ["intradayprice", GATES["price_min"]]),
        yf.EquityQuery("lte", ["intradayprice", GATES["price_max"]]),
        yf.EquityQuery("eq", ["region", "us"]),
    ])
    for off in range(0, 100, 25):
        rows = _yahoo_screen_page(yf, q, off, 25)
        add(rows, "criteria")
        if len(rows) < 25:
            break
        time.sleep(0.3)

    # 2) predefined lists (supplement; catch names the ranked query paging missed)
    for name in ("day_gainers", "small_cap_gainers", "aggressive_small_caps", "most_actives"):
        for off in (0, 25, 50, 75):
            try:
                rows = _yahoo_screen_page(yf, None, off, 25, predefined=name)
            except Exception as e:  # noqa: BLE001 — a missing predefined list is non-fatal
                if verbose:
                    print(f"  yahoo list {name} unavailable: {type(e).__name__}")
                rows = []
            add(rows, name)
            if len(rows) < 25 or len(pool) >= GATES["yahoo_pool_max"]:
                break
            time.sleep(0.3)
        if len(pool) >= GATES["yahoo_pool_max"]:
            break
    return pool


def _row_move_pct(r):
    """Best-available up-move %% from a screener row (premarket preferred)."""
    pm = r.get("preMarketChangePercent")
    rg = r.get("regularMarketChangePercent")
    vals = [v for v in (pm, rg) if isinstance(v, (int, float))]
    return max(vals) if vals else None


def _yahoo_candidates(score_fn, verbose):
    yf = _yf()
    pool = _yahoo_pool(yf, verbose)
    if not pool:
        sys.exit("universe.py: Yahoo screeners returned an empty candidate pool — "
                 "feed problem or closed market. Nothing logged; run flagged failed.")
    if verbose:
        print(f"  candidate pool: {len(pool)} listed symbols (criteria sweep ∪ mover lists)")

    # Cheap prefilter from screener-row data, then rank by move so the per-name
    # .info budget goes to the most screen-like names.
    rows = []
    for sym, r in pool.items():
        px = r.get("preMarketPrice") or r.get("regularMarketPrice")
        move = _row_move_pct(r)
        cand = {"ticker": sym, "price": px, "prev": r.get("regularMarketPreviousClose"),
                "vol": r.get("regularMarketVolume"), "gap_pct": round(move, 2) if move is not None else None,
                "rvol": None, "float_shares": None, "short_interest_pct": "", "_src": r.get("_src", "")}
        if px is None or not (GATES["price_min"] <= px <= GATES["price_max"]):
            cand["eligible"] = "price_band"
            rows.append(cand)
            continue
        rows.append(cand)
    quotable = sorted((c for c in rows if "eligible" not in c),
                      key=lambda c: c["gap_pct"] if c["gap_pct"] is not None else -999,
                      reverse=True)[:GATES["yahoo_quote_max"]]
    for c in rows:
        if "eligible" not in c and c not in quotable:
            c["eligible"] = "quote_budget"  # pool overflow; still logged for the record

    # Full premarket-aware quote for the shortlisted names (same .info source as v0.2).
    for c in quotable:
        sym = c["ticker"]
        info = None
        for attempt in range(3):
            try:
                info = yf.Ticker(sym).info
                if info and (info.get("regularMarketPrice") or info.get("preMarketPrice")):
                    break
            except Exception:
                if attempt == 2:
                    info = None
            time.sleep(1.0 * (attempt + 1))
        if not info:
            c["eligible"] = "no_quote"
            continue
        prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
        price = info.get("preMarketPrice") or info.get("regularMarketPrice") or info.get("currentPrice")
        vol = info.get("preMarketVolume") or info.get("regularMarketVolume") or info.get("volume") or 0
        avg = (info.get("averageVolume") or info.get("averageDailyVolume3Month")
               or info.get("averageVolume10days") or 0)
        flt = info.get("floatShares") or info.get("sharesOutstanding") or 0
        si = info.get("shortPercentOfFloat")
        gap = ((price - prev) / prev * 100.0) if (price and prev) else None
        rvol = (vol / avg) if avg else None
        c.update({"price": price, "prev": prev, "vol": vol,
                  "gap_pct": round(gap, 2) if gap is not None else None,
                  "rvol": round(rvol, 2) if rvol is not None else None,
                  "float_shares": int(flt or 0),
                  "short_interest_pct": round(si * 100, 2) if isinstance(si, (int, float)) else ""})
        why = gate_check(price, gap, rvol, flt)
        c["eligible"] = why
        if why == "":
            c.update(score_fn(price, prev, vol, avg, flt))
        time.sleep(0.4)  # same Yahoo courtesy throttle as the v0.2 scan
    return rows


# ================================================================ alpaca (paid SIP)
SCREENER_BASE = "https://data.alpaca.markets/v1beta1/screener/stocks"
SNAPSHOT_URL = "https://data.alpaca.markets/v2/stocks/snapshots"


class _AlpacaScreener:
    """Thin stdlib client for the Alpaca screener endpoints (movers / most-actives).
    Same keys as data_provider.AlpacaProvider; separate class because the screener
    lives under /v1beta1 and takes no `feed` param."""

    def __init__(self):
        self.key = os.environ.get("ALPACA_KEY_ID") or os.environ.get("APCA_API_KEY_ID", "")
        self.secret = os.environ.get("ALPACA_SECRET_KEY") or os.environ.get("APCA_API_SECRET_KEY", "")
        if not (self.key and self.secret):
            sys.exit("universe.py: UNIV_SOURCE=alpaca but ALPACA_KEY_ID / ALPACA_SECRET_KEY "
                     "not set (see ALPACA-DATA-KEYS-SETUP.md). v0.3 scan aborted.")

    def _get(self, url, params=None, retries=3):
        q = ("?" + urllib.parse.urlencode(params)) if params else ""
        last = None
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url + q, headers={
                    "APCA-API-KEY-ID": self.key, "APCA-API-SECRET-KEY": self.secret,
                    "User-Agent": "ThePickLog/1.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    return json.loads(r.read().decode("utf-8"))
            except Exception as e:  # noqa: BLE001 — incl. HTTP 403 (plan) / 429 (rate)
                last = e
                time.sleep(1.5 * (attempt + 1))
        raise last

    def gainers(self, top):
        return (self._get(f"{SCREENER_BASE}/movers", {"top": top}) or {}).get("gainers") or []

    def most_actives(self, top):
        return (self._get(f"{SCREENER_BASE}/most-actives",
                          {"by": "volume", "top": top}) or {}).get("most_actives") or []

    def snapshots(self, symbols, feed):
        out = {}
        syms = list(symbols)
        for i in range(0, len(syms), 100):
            chunk = syms[i:i + 100]
            j = self._get(SNAPSHOT_URL, {"symbols": ",".join(chunk), "feed": feed})
            body = j.get("snapshots") if isinstance(j.get("snapshots"), dict) else j
            for s, snap in (body or {}).items():
                if isinstance(snap, dict):
                    out[s.upper()] = snap
            time.sleep(0.2)
        return out


def _alpaca_candidates(score_fn, verbose):
    from data_provider import AlpacaProvider, edgar_shares_outstanding
    scr = _AlpacaScreener()
    feed = (os.environ.get("ALPACA_DATA_FEED", "sip")).lower()

    gainers = scr.gainers(GATES["top_gainers"])
    actives = scr.most_actives(GATES["top_actives"])
    pool, seen = [], set()
    for row in list(gainers) + list(actives):
        sym = (row.get("symbol") or "").upper()
        if not sym or sym in seen:
            continue
        seen.add(sym)
        if _hygiene_ok(sym):
            pool.append(sym)
    if not pool:
        sys.exit("universe.py: Alpaca screener returned an empty candidate pool — "
                 "feed/plan problem or closed market. Nothing logged; run flagged failed.")
    if verbose:
        print(f"  candidate pool: {len(pool)} symbols "
              f"({len(gainers)} gainers ∪ {len(actives)} most-active, hygiene-filtered)")

    snaps = scr.snapshots(pool, feed)
    prov = AlpacaProvider()

    candidates = []
    for sym in pool:
        snap = snaps.get(sym) or {}
        lt = (snap.get("latestTrade") or {}).get("p")
        db = snap.get("dailyBar") or {}
        mb = snap.get("minuteBar") or {}
        pdb = snap.get("prevDailyBar") or {}
        price = lt or mb.get("c") or db.get("c")
        prev = pdb.get("c")
        vol = db.get("v") or 0
        gap = ((price - prev) / prev * 100.0) if (price and prev) else None
        cand = {"ticker": sym, "price": price, "prev": prev, "vol": vol,
                "gap_pct": round(gap, 2) if gap is not None else None,
                "rvol": None, "float_shares": None, "short_interest_pct": "", "_src": "alpaca"}
        why = gate_check(price, gap, None, None)
        if why in ("price_band", "gap_lt_min"):
            cand["eligible"] = why
            candidates.append(cand)
            continue
        avg = prov._avg_volume(sym)
        rvol = (vol / avg) if avg else None
        flt = edgar_shares_outstanding(sym)
        cand["rvol"] = round(rvol, 2) if rvol is not None else None
        cand["float_shares"] = int(flt or 0)
        why = gate_check(price, gap, rvol, flt)
        cand["eligible"] = why
        if why == "":
            cand.update(score_fn(price, prev, vol, avg, flt))
        candidates.append(cand)
        time.sleep(0.15)
    return candidates


# ==================================================================== entry point
def discover(score_fn, verbose=True):
    """Run market-wide discovery. Returns (candidates, source_tag) where source_tag
    is "yf" or "alpaca" (feeds the cohort's model_version, e.g. v0.3-yf).
    candidates: list of dicts — every screened symbol with metrics, an `eligible`
    reject-reason field ("" = eligible), and score fields for eligible names
    (scored with the caller-supplied UNCHANGED v0.2 score_fn)."""
    source = (os.environ.get("UNIV_SOURCE", "yahoo")).lower()
    if source in ("alpaca", "apca"):
        cands = _alpaca_candidates(score_fn, verbose)
        tag = "alpaca"
    else:
        cands = _yahoo_candidates(score_fn, verbose)
        tag = "yf"
    n_elig = sum(1 for c in cands if c.get("eligible") == "")
    if verbose:
        print(f"  gates: {n_elig} eligible of {len(cands)} screened (source={tag})")
    return cands, tag


# ---------------------------------------------------------------- selftest (offline)
def _selftest():
    ok = True

    def chk(name, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {name}: got {got!r}, want {want!r}")

    # symbol + exchange hygiene
    chk("common ok", _hygiene_ok("GCDT"), True)
    chk("2-letter ok (PW unaffected)", _hygiene_ok("PW"), True)
    chk("warrant 5W", _hygiene_ok("ABCDW"), False)
    chk("unit 5U", _hygiene_ok("ABCDU"), False)
    chk("right 5R", _hygiene_ok("ABCDR"), False)
    chk("WS suffix", _hygiene_ok("ABCWS"), False)
    chk("class dot", _hygiene_ok("BRK.A"), False)
    chk("OTC excluded", _hygiene_ok("ZUUS", "OTC Markets"), False)
    chk("pink excluded", _hygiene_ok("ZUUS", "PINK Current"), False)
    chk("Nasdaq kept", _hygiene_ok("NVVE", "NasdaqCM"), True)
    chk("NYSE American kept", _hygiene_ok("VTAK", "NYSE American"), True)

    # gates — frozen order: price, gap, rvol, float
    chk("eligible", gate_check(2.50, 25.0, 5.0, 8_000_000), "")
    chk("price low", gate_check(0.40, 25.0, 5.0, 8_000_000), "price_band")
    chk("price high", gate_check(12.0, 25.0, 5.0, 8_000_000), "price_band")
    chk("gap low", gate_check(2.50, 9.9, 5.0, 8_000_000), "gap_lt_min")
    chk("gap None", gate_check(2.50, None, 5.0, 8_000_000), "gap_lt_min")
    chk("rvol low", gate_check(2.50, 25.0, 1.9, 8_000_000), "rvol_lt_min")
    chk("rvol None (no avg-vol base)", gate_check(2.50, 25.0, None, 8_000_000), "rvol_lt_min")
    chk("float missing EXCLUDES (never a free 100)", gate_check(2.50, 25.0, 5.0, 0), "float_unknown")
    chk("float too big", gate_check(2.50, 25.0, 5.0, 60_000_000), "float_gt_max")

    # row-move helper prefers the premarket move
    chk("move premarket preferred", _row_move_pct({"preMarketChangePercent": 22.0,
                                                   "regularMarketChangePercent": 3.0}), 22.0)
    chk("move falls back to regular", _row_move_pct({"regularMarketChangePercent": 14.5}), 14.5)
    chk("move none", _row_move_pct({}), None)

    # frozen params sanity — if someone edits GATES, this screams
    chk("frozen gates", (GATES["price_min"], GATES["price_max"], GATES["gap_min_pct"],
                         GATES["rvol_min"], GATES["float_max_shares"], GATES["max_published"]),
        (0.50, 10.00, 10.0, 2.0, 50_000_000, 10))

    print("universe selftest:", "OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    # Live dry-run: discover + print, write nothing.
    from ignitionscan import score_inputs  # unchanged v0.2 scorer
    cands, tag = discover(score_inputs)
    elig = sorted((c for c in cands if c.get("eligible") == ""),
                  key=lambda c: c.get("score", 0), reverse=True)
    print(f"\nDRY RUN (source={tag}) — top {GATES['max_published']} of {len(elig)} eligible:")
    for c in elig[:GATES["max_published"]]:
        print(f"  {c['ticker']:<6} score {c.get('score')} tier {c.get('tier')} "
              f"px {c['price']} gap {c['gap_pct']}% rvol {c['rvol']} "
              f"float {(c['float_shares'] or 0) / 1e6:.1f}M")
    print("(nothing written — use `python3 ignitionscan.py scan-market` to log)")
