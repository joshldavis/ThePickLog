#!/usr/bin/env python3
"""
universe.py — v0.3 market-wide candidate discovery (H-UNIV1, registered 2026-07-08).

WHY
    The v0.2 record scans a FIXED 16-ticker list, and 13–16 of the 16 pass every day.
    That makes the "screen" a watchlist: effective sample size ≈ 16 names, no
    unscreened control group, no external validity beyond those names (HYPOTHESES.md
    batch #3, H-IND1 / H-UNIV1). This module makes the universe CRITERIA-DEFINED:
    the candidate pool is the whole US-listed market (via Alpaca's screener), and the
    engine genuinely selects a small daily subset.

WHAT IT DOES (all frozen — changing any gate requires a new registration)
    1. Candidate pool  = Alpaca top-50 pre-market gainers  ∪  top-100 most-actives
                         (by volume). Symbol hygiene drops obvious warrants/units.
    2. Batch snapshot  → price, prev close, day volume for every candidate (1 call).
    3. ELIGIBILITY GATES (frozen 2026-07-08):
         price          0.50 ≤ p ≤ 10.00          (same band as v0.2 FILTERS)
         gap            gap_pct ≥ +10.0           (up-gaps only; this is a gap screen)
         rvol           rvol ≥ 2.0                (needs a real avg-volume base, >0)
         float proxy    0 < shares ≤ 50,000,000   (EDGAR shares outstanding; the
                                                   over-count caveat of data_provider
                                                   applies — missing data EXCLUDES,
                                                   it never scores a free 100)
    4. Score survivors with the UNCHANGED v0.2 formula (PRINCIPLES P5 — no weight,
       cutpoint, or tier change), publish the TOP 10 by score as model_version
       "v0.3-alpaca" picks.
    5. Log EVERY screened candidate (eligible or not, published or not) to
       candidates.csv with a reject_reason / published flag. The eligible-but-not-
       published names are the forward-only control pool H-CTRL needs.

DATA
    Requires Alpaca data keys (ALPACA_KEY_ID / ALPACA_SECRET_KEY) and realistically
    the SIP feed (ALPACA_DATA_FEED=sip, Algo Trader Plus) — IEX-only coverage is too
    thin for low-float names (see ALPACA-DATA-KEYS-SETUP.md). Float proxy and the
    scoring engine are shared with data_provider.py / ignitionscan.py.

    All failures are LOUD (SystemExit) — a market-wide scan that silently logs a
    partial or fake candidate pool would poison the cohort. The GitHub Action wraps
    this step with continue-on-error so a v0.3 failure never blocks the v0.2 commit.

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

from data_provider import AlpacaProvider, edgar_shares_outstanding

SCREENER_BASE = "https://data.alpaca.markets/v1beta1/screener/stocks"
SNAPSHOT_URL = "https://data.alpaca.markets/v2/stocks/snapshots"

# Frozen H-UNIV1 parameters (2026-07-08). Do NOT tune in place — re-register instead.
GATES = {
    "price_min": 0.50,
    "price_max": 10.00,
    "gap_min_pct": 10.0,
    "rvol_min": 2.0,
    "float_max_shares": 50_000_000,
    "top_gainers": 50,
    "top_actives": 100,
    "max_published": 10,
}


def _hygiene_ok(symbol):
    """Heuristic filter for common stock only: drop units/warrants/rights/preferreds.
    (Alpaca screener returns plain US equities; suffix conventions cover the rest.
    Documented heuristic — a wrongly excluded common ticker costs one candidate,
    a wrongly included warrant would poison the pick log.)"""
    s = symbol.upper()
    if "." in s or "/" in s or "-" in s:
        return False  # preferred / class shares like BRK.A, share-class dashes
    if len(s) == 5 and s[-1] in ("W", "U", "R"):
        return False  # 5-letter warrant/unit/right suffixes (e.g. ABCDW)
    if s.endswith("WS"):
        return False
    return True


class _AlpacaScreener:
    """Thin stdlib client for the two screener endpoints (movers / most-actives).
    Same keys as AlpacaProvider; separate class because the screener lives under
    /v1beta1 and takes no `feed` param."""

    def __init__(self):
        self.key = os.environ.get("ALPACA_KEY_ID") or os.environ.get("APCA_API_KEY_ID", "")
        self.secret = os.environ.get("ALPACA_SECRET_KEY") or os.environ.get("APCA_API_SECRET_KEY", "")
        if not (self.key and self.secret):
            sys.exit("universe.py: ALPACA_KEY_ID / ALPACA_SECRET_KEY not set "
                     "(GitHub secrets — see ALPACA-DATA-KEYS-SETUP.md). v0.3 scan aborted.")

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
        j = self._get(f"{SCREENER_BASE}/movers", {"top": top})
        return j.get("gainers") or []

    def most_actives(self, top):
        j = self._get(f"{SCREENER_BASE}/most-actives", {"by": "volume", "top": top})
        return j.get("most_actives") or []

    def snapshots(self, symbols, feed):
        """Batch snapshots, chunked to stay under URL limits."""
        out = {}
        syms = list(symbols)
        for i in range(0, len(syms), 100):
            chunk = syms[i:i + 100]
            j = self._get(SNAPSHOT_URL, {"symbols": ",".join(chunk), "feed": feed})
            # response is {symbol: snapshot} (possibly nested under "snapshots")
            body = j.get("snapshots") if isinstance(j.get("snapshots"), dict) else j
            for s, snap in (body or {}).items():
                if isinstance(snap, dict):
                    out[s.upper()] = snap
            time.sleep(0.2)
        return out


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


def discover(score_fn, verbose=True):
    """Run the full market-wide discovery. Returns (candidates, feed_name) where
    candidates is a list of dicts: every screened symbol with metrics, an
    `eligible` reject-reason field ("" = eligible), and score fields (eligible
    names only; scored with the caller-supplied UNCHANGED v0.2 score_fn).
    score_fn(price, prev, vol, avg, float_shares) -> dict of score fields."""
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
        sys.exit("universe.py: screener returned an empty candidate pool — feed/plan "
                 "problem or closed market. Nothing logged; run flagged failed.")
    if verbose:
        print(f"  candidate pool: {len(pool)} symbols "
              f"({len(gainers)} gainers ∪ {len(actives)} most-active, hygiene-filtered)")

    snaps = scr.snapshots(pool, feed)
    prov = AlpacaProvider()  # for per-symbol avg volume on gate survivors

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
                "rvol": None, "float_shares": None}

        # Cheap gates first (price/gap need no extra calls).
        why = gate_check(price, gap, None, None)
        if why in ("price_band", "gap_lt_min"):
            cand["eligible"] = why
            candidates.append(cand)
            continue

        # Survivors earn the expensive lookups: trailing avg volume + EDGAR shares.
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
        time.sleep(0.15)  # SEC EDGAR + Alpaca courtesy throttle

    n_elig = sum(1 for c in candidates if c["eligible"] == "")
    if verbose:
        print(f"  gates: {n_elig} eligible of {len(candidates)} screened")
    return candidates, feed


# ---------------------------------------------------------------- selftest (offline)
def _selftest():
    ok = True

    def chk(name, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {name}: got {got!r}, want {want!r}")

    # symbol hygiene
    chk("common ok", _hygiene_ok("GCDT"), True)
    chk("4-letter W ok (real ticker like 'PW' unaffected)", _hygiene_ok("PW"), True)
    chk("warrant 5W", _hygiene_ok("ABCDW"), False)
    chk("unit 5U", _hygiene_ok("ABCDU"), False)
    chk("right 5R", _hygiene_ok("ABCDR"), False)
    chk("WS suffix", _hygiene_ok("ABCWS"), False)
    chk("class dot", _hygiene_ok("BRK.A"), False)

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

    # frozen params sanity — if someone edits GATES, this screams
    chk("frozen gates", (GATES["price_min"], GATES["price_max"], GATES["gap_min_pct"],
                         GATES["rvol_min"], GATES["float_max_shares"], GATES["max_published"]),
        (0.50, 10.00, 10.0, 2.0, 50_000_000, 10))

    print("universe selftest:", "OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    # Live dry-run: discover + print, write nothing. Needs Alpaca keys.
    from ignitionscan import score_inputs  # unchanged v0.2 scorer
    cands, feed = discover(score_inputs)
    elig = sorted((c for c in cands if c["eligible"] == ""),
                  key=lambda c: c.get("score", 0), reverse=True)
    print(f"\nDRY RUN (feed={feed}) — top {GATES['max_published']} of {len(elig)} eligible:")
    for c in elig[:GATES["max_published"]]:
        print(f"  {c['ticker']:<6} score {c.get('score')} tier {c.get('tier')} "
              f"px {c['price']} gap {c['gap_pct']}% rvol {c['rvol']} "
              f"float {c['float_shares'] / 1e6:.1f}M")
    print("(nothing written — use `python3 ignitionscan.py scan-market` to log)")
