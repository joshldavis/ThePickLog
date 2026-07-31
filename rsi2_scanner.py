#!/usr/bin/env python3
"""ThePickLog — EXPERIMENT 02: the 2-period RSI mean-reversion trade.

WHAT IS BEING TESTED
    One of the most widely published retail strategies of the last twenty years: buy a
    large-cap when its 2-period RSI collapses while the stock is still above its 200-day
    moving average, then exit on a short bounce. It is almost always marketed on its WIN
    RATE. Experiment 01 showed on our own data that a high win rate and a positive
    expectancy are different things (a +5% target produced a 67% win rate at -4.4%/trade).
    This tests whether the published claim survives that distinction, on liquid names where
    trading costs cannot be blamed for the answer.

WHY THIS UNIVERSE
    Experiment 01 failed partly because the raw drift in low-float microcaps (<1%/session)
    was smaller than a realistic round-trip cost (~2%). Nothing could work there in either
    direction. Large caps invert that: a 0.10% round trip is small enough that a real effect
    would be DETECTABLE. If this fails, it fails on the merits, not on friction.

THE CONTROL — the design fix Experiment 01 lacked
    Every signal is scored against a DAY-MATCHED BENCHMARK: the equal-weight return of the
    entire frozen universe over the identical window. So the question is never "did it make
    money" (which mostly measures whether the market went up) but "did it beat holding the
    same universe on the same day." Market moves difference out. This is the discriminant
    control H-CTRL was supposed to provide and never could.

FROZEN 2026-07-29 — every constant below defines the pre-registration.
    Changing any of them voids the test; a re-derivation is a NEW experiment with a new
    window. Only signals with a signal_date strictly AFTER the registration date count.

PASS BAR (frozen, and deliberately strict)
    n >= 30 post-registration graded signals; BOTH the mean AND the median day-matched
    excess return positive net of costs; ticker-clustered 95% CI on the excess excluding
    zero; direction holding across >= 3 consecutive weekly snapshots.
    WIN RATE IS REPORTED BUT IS NOT A PASS CRITERION — that is the entire point of the
    experiment, and it is frozen here so it cannot be quietly substituted later.

REGISTERED PRIOR (honest, stated before any data)
    Short-horizon mean reversion in liquid equities is a real and documented effect, but it
    has been publicly known and heavily traded since roughly 2008-09. Expectation: the high
    win rate REPLICATES (probably 65-75%), and the day-matched excess return is small or
    zero after costs. Genuinely uncertain — call it a 1-in-3 chance it clears the bar. A
    high win rate with no excess return would be the single most useful outcome, because it
    is exactly what the strategy is sold on.

USAGE
    python3 rsi2_scanner.py scan       # log today's signals (run after the close)
    python3 rsi2_scanner.py grade      # grade matured signals + the day-matched benchmark
    python3 rsi2_scanner.py --selftest # offline logic check, no network
"""
import argparse
import csv
import io
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SIGNALS = os.path.join(HERE, "rsi2_signals.csv")
OUTCOMES = os.path.join(HERE, "rsi2_outcomes.csv")

# ---- FROZEN PRE-REGISTRATION CONSTANTS (2026-07-29) ------------------------
REGISTERED_AT = "2026-07-29"
EXPERIMENT = "EXP02-RSI2"
RSI_PERIOD = 2
RSI_ENTRY = 5.0          # Connors' classic oversold threshold
RSI_EXIT = 70.0          # Connors' classic exit trigger
SMA_TREND = 200          # only buy above the long-term trend
HOLD_SESSIONS = 5        # time exit if the RSI exit never triggers
MAX_PER_DAY = 5          # cap so one day cannot dominate the sample
COST_ROUNDTRIP = 0.10    # % — realistic for liquid large caps (vs 2.0% for microcaps)
MIN_N = 30

# Frozen universe: 40 liquid US large caps across sectors. Chosen for liquidity and
# survivability, fixed at registration. Adding or removing a name voids the test.
UNIVERSE = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "AVGO", "ORCL", "CRM", "ADBE",
    "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "AXP", "BLK", "SCHW",
    "JNJ", "UNH", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT",
    "XOM", "CVX", "COP", "WMT", "COST", "PG", "KO", "PEP", "HD", "MCD", "CAT", "HON",
]
# ---------------------------------------------------------------------------

SIG_FIELDS = ["signal_id", "experiment", "captured_at", "signal_date", "ticker",
              "close", "sma200", "rsi2", "universe_n", "rank_in_day"]
OUT_FIELDS = ["signal_id", "ticker", "signal_date", "entry_date", "graded_at",
              "entry_open", "same_day_close", "ret_1d_net", "ret_5d_net", "ret_rsiexit_net",
              "exit_session", "bench_1d_net", "bench_5d_net",
              "excess_1d", "excess_5d", "excess_rsiexit", "win_1d", "note"]


def _f(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def _read(path):
    if not os.path.exists(path):
        return []
    with io.open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _append(path, fields, rows):
    if not rows:
        return
    first = not os.path.exists(path)
    with io.open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        if first:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


# ------------------------------------------- PURE CORE (offline-testable, no network)
def sma(closes, n):
    if len(closes) < n:
        return None
    return sum(closes[-n:]) / float(n)


def rsi(closes, period):
    """Wilder's RSI. closes = chronological list. Returns None if too short."""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    # seed with the simple average of the first `period` changes, then Wilder-smooth
    ag = sum(gains[:period]) / period
    al = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        ag = (ag * (period - 1) + gains[i]) / period
        al = (al * (period - 1) + losses[i]) / period
    if al == 0:
        return 100.0
    rs = ag / al
    return 100.0 - (100.0 / (1.0 + rs))


def signal_for(closes):
    """Frozen entry rule. Returns (fires: bool, rsi2, sma200)."""
    r = rsi(closes, RSI_PERIOD)
    s = sma(closes, SMA_TREND)
    if r is None or s is None:
        return False, r, s
    return (closes[-1] > s and r < RSI_ENTRY), r, s


def grade_path(bars, closes_before):
    """bars: [{o,h,l,c}] starting at the ENTRY session (index 0), len >= HOLD+1.
    closes_before: closes up to and including the signal day, for rolling RSI at exit.
    Returns dict of net returns under three exits."""
    e = bars[0]["o"]
    if not e or e <= 0:
        return None
    c1 = bars[0]["c"]
    c5 = bars[HOLD_SESSIONS]["c"]
    hist = list(closes_before)
    exit_i, exit_px = HOLD_SESSIONS, c5
    for i in range(0, HOLD_SESSIONS + 1):
        hist.append(bars[i]["c"])
        r = rsi(hist, RSI_PERIOD)
        if r is not None and r > RSI_EXIT:
            exit_i, exit_px = i, bars[i]["c"]
            break
    pct = lambda x: (x - e) / e * 100.0 - COST_ROUNDTRIP
    return {"entry_open": e, "same_day_close": c1,
            "ret_1d_net": pct(c1), "ret_5d_net": pct(c5),
            "ret_rsiexit_net": pct(exit_px), "exit_session": exit_i}


# ------------------------------------------------------------------- network
def fetch_universe(period_days=400):
    """Daily bars for the frozen universe. Returns {ticker: [{d,o,h,l,c}, ...]}."""
    import yfinance as yf
    df = yf.download(UNIVERSE, period=f"{period_days}d", interval="1d",
                     auto_adjust=False, group_by="ticker", progress=False, threads=True)
    out = {}
    for t in UNIVERSE:
        try:
            sub = df[t].dropna()
        except Exception:
            continue
        rows = []
        for idx, r in sub.iterrows():
            try:
                rows.append({"d": str(idx)[:10], "o": float(r["Open"]), "h": float(r["High"]),
                             "l": float(r["Low"]), "c": float(r["Close"])})
            except Exception:
                continue
        if len(rows) > SMA_TREND:
            out[t] = rows
    return out


def cmd_scan():
    data = fetch_universe()
    if not data:
        print("rsi2 scan: no data returned — skipping (non-fatal)")
        return 0
    asof = max(rows[-1]["d"] for rows in data.values())
    if asof <= REGISTERED_AT:
        print(f"rsi2 scan: latest session {asof} is not after registration {REGISTERED_AT} — nothing counts yet")
    seen = {(r["signal_date"], r["ticker"]) for r in _read(SIGNALS)}
    fires = []
    for t, rows in data.items():
        if rows[-1]["d"] != asof:      # stale/halted name — skip rather than guess
            continue
        closes = [b["c"] for b in rows]
        ok, r2, s200 = signal_for(closes)
        if ok:
            fires.append((t, r2, s200, closes[-1]))
    fires.sort(key=lambda x: x[1])     # most oversold first
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new = []
    for rank, (t, r2, s200, c) in enumerate(fires[:MAX_PER_DAY], 1):
        if (asof, t) in seen:
            continue
        new.append({"signal_id": f"{EXPERIMENT}-{asof}-{t}", "experiment": EXPERIMENT,
                    "captured_at": now, "signal_date": asof, "ticker": t,
                    "close": round(c, 4), "sma200": round(s200, 4), "rsi2": round(r2, 3),
                    "universe_n": len(data), "rank_in_day": rank})
    _append(SIGNALS, SIG_FIELDS, new)
    print(f"rsi2 scan {asof}: {len(fires)} name(s) met the rule, logged {len(new)} "
          f"(cap {MAX_PER_DAY}) from a {len(data)}-name universe")
    return 0


def cmd_grade():
    sigs = [s for s in _read(SIGNALS) if s.get("signal_date", "") > REGISTERED_AT]
    if not sigs:
        print("rsi2 grade: no post-registration signals yet")
        return 0
    done = {r["signal_id"] for r in _read(OUTCOMES)}
    todo = [s for s in sigs if s["signal_id"] not in done]
    if not todo:
        print("rsi2 grade: nothing new to grade")
        return 0
    data = fetch_universe()
    if not data:
        print("rsi2 grade: no data returned — skipping (non-fatal)")
        return 0
    dates = sorted({b["d"] for rows in data.values() for b in rows})
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def bench(signal_date):
        """Day-matched benchmark: equal-weight universe return entering the session AFTER
        signal_date, held 1 and HOLD sessions. Computed from the same fetch as the signal."""
        r1, r5 = [], []
        for t, rows in data.items():
            idx = {b["d"]: i for i, b in enumerate(rows)}
            if signal_date not in idx:
                continue
            i0 = idx[signal_date] + 1
            if i0 + HOLD_SESSIONS >= len(rows):
                continue
            e = rows[i0]["o"]
            if not e:
                continue
            r1.append((rows[i0]["c"] - e) / e * 100.0 - COST_ROUNDTRIP)
            r5.append((rows[i0 + HOLD_SESSIONS]["c"] - e) / e * 100.0 - COST_ROUNDTRIP)
        if len(r1) < 10:
            return None
        return sum(r1) / len(r1), sum(r5) / len(r5)

    rows_out, immature, failed = [], 0, 0
    bench_cache = {}
    for s in todo:
        t, sd = s["ticker"], s["signal_date"]
        rows = data.get(t)
        if not rows:
            failed += 1
            continue
        idx = {b["d"]: i for i, b in enumerate(rows)}
        if sd not in idx:
            failed += 1
            continue
        i0 = idx[sd] + 1
        if i0 + HOLD_SESSIONS >= len(rows):
            immature += 1
            continue
        g = grade_path(rows[i0:i0 + HOLD_SESSIONS + 1], [b["c"] for b in rows[:idx[sd] + 1]])
        if not g:
            failed += 1
            continue
        if sd not in bench_cache:
            bench_cache[sd] = bench(sd)
        b = bench_cache[sd]
        if b is None:
            immature += 1
            continue
        rows_out.append({
            "signal_id": s["signal_id"], "ticker": t, "signal_date": sd,
            "entry_date": rows[i0]["d"], "graded_at": now,
            "entry_open": round(g["entry_open"], 4), "same_day_close": round(g["same_day_close"], 4),
            "ret_1d_net": round(g["ret_1d_net"], 4), "ret_5d_net": round(g["ret_5d_net"], 4),
            "ret_rsiexit_net": round(g["ret_rsiexit_net"], 4), "exit_session": g["exit_session"],
            "bench_1d_net": round(b[0], 4), "bench_5d_net": round(b[1], 4),
            "excess_1d": round(g["ret_1d_net"] - b[0], 4),
            "excess_5d": round(g["ret_5d_net"] - b[1], 4),
            "excess_rsiexit": round(g["ret_rsiexit_net"] - b[1], 4),
            "win_1d": 1 if g["ret_1d_net"] > 0 else 0, "note": ""})
    _append(OUTCOMES, OUT_FIELDS, rows_out)
    graded = _read(OUTCOMES)
    print(f"rsi2 grade: +{len(rows_out)} graded ({immature} not matured, {failed} failed); "
          f"{len(graded)} total")
    if graded:
        ex1 = [_f(r["excess_1d"]) for r in graded if _f(r["excess_1d"]) is not None]
        wins = [int(r["win_1d"]) for r in graded if r.get("win_1d") not in (None, "")]
        if ex1:
            ex1s = sorted(ex1)
            med = ex1s[len(ex1s) // 2]
            print(f"  n={len(ex1)} | day-matched excess (1d): mean={sum(ex1)/len(ex1):+.3f}% "
                  f"median={med:+.3f}% | win rate={100.0*sum(wins)/max(1,len(wins)):.0f}% "
                  f"| {'MATURE' if len(ex1) >= MIN_N else f'immature, need {MIN_N}'}")
            print("  reminder: win rate is NOT a pass criterion (frozen at registration).")
    return 0


def _selftest():
    # RSI sanity: monotonically rising closes -> RSI 100; falling -> RSI 0
    assert rsi([1, 2, 3, 4, 5], 2) == 100.0
    assert rsi([5, 4, 3, 2, 1], 2) == 0.0
    # a real oversold shape should be low
    r = rsi([100, 101, 102, 103, 99, 96], 2)
    assert r is not None and r < 20, r
    assert rsi([1, 2], 5) is None
    # SMA
    assert sma([1, 2, 3, 4], 2) == 3.5
    assert sma([1, 2], 5) is None
    # signal: needs BOTH above-trend AND oversold. Fixtures are a realistic uptrend
    # followed by a two-day flush (a single huge spike would keep Wilder's average
    # elevated and is not the shape the rule is meant to catch).
    up = [100.0 + i * 0.15 for i in range(200)] + [128.0, 124.0]
    fires, r2, s2 = signal_for(up)
    assert s2 is not None and up[-1] > s2, (up[-1], s2)       # above the 200-day trend
    assert r2 is not None and r2 < RSI_ENTRY, r2             # and oversold (~1.5)
    assert fires, (fires, r2, s2)
    below = [100.0 + i * 0.15 for i in range(200)] + [95.0, 88.0]   # oversold, BELOW trend
    f2, r2b, s2b = signal_for(below)
    assert r2b < RSI_ENTRY and below[-1] < s2b and not f2, (f2, r2b, s2b)
    flat = [100.0 + i * 0.15 for i in range(200)] + [129.9, 130.2]  # above trend, NOT oversold
    f3, r3, _ = signal_for(flat)
    assert r3 > RSI_ENTRY and not f3, (f3, r3)
    # grading: entry 100, +5% same-day; cost applied
    bars = [{"o": 100.0, "h": 106.0, "l": 99.0, "c": 105.0}] + \
           [{"o": 105.0, "h": 106.0, "l": 104.0, "c": 105.0}] * 5
    g = grade_path(bars, [100.0, 98.0])
    assert abs(g["ret_1d_net"] - (5.0 - COST_ROUNDTRIP)) < 1e-9, g
    assert g["exit_session"] == 0, g          # a +5% pop lifts RSI(2) above 70 immediately
    # never-triggers case: flat then down -> time exit at HOLD
    bars2 = [{"o": 100.0, "h": 100.0, "l": 90.0, "c": 95.0}] + \
            [{"o": 95.0, "h": 95.0, "l": 88.0, "c": 90.0 - i} for i in range(5)]
    g2 = grade_path(bars2, [100.0, 99.0])
    assert g2["exit_session"] == HOLD_SESSIONS, g2
    print("rsi2_scanner selftest PASS — RSI/SMA/entry rule/3 exits verified")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs="?", default="scan", choices=["scan", "grade"])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    return cmd_scan() if a.command == "scan" else cmd_grade()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:      # never block the daily commit
        print(f"rsi2_scanner: non-fatal error {type(e).__name__}: {e}")
        sys.exit(0)
