#!/usr/bin/env python3
"""ThePickLog — EXPERIMENT HARNESS.

WHY THIS EXISTS
    The project's output is verdicts on public trading claims, so THROUGHPUT is the
    product. Experiment 02 needed a bespoke scanner (~330 lines). That is the binding
    constraint on how many claims can be under test at once. This harness reduces a new
    experiment to a DECLARATION — universe, entry condition, exits, control, cost, pass
    bar, prior — so several can run in parallel.

WHAT IT GUARANTEES FOR EVERY EXPERIMENT (so no experiment can quietly cut a corner)
    * Forward-only. Only signals dated strictly after `registered_at` are ever scored.
    * Append-only. Signals are written before their entry session and never edited.
    * A DAY-MATCHED CONTROL, always. Every signal is scored against the equal-weight
      return of its own frozen universe over the identical window, computed from the same
      fetch. The scored quantity is the EXCESS. Market moves difference out. No experiment
      ships without one — that was Experiment 01's structural flaw.
    * Costs applied explicitly and declared up front.
    * Mean AND median AND a ticker-clustered CI reported together. Experiment 01 proved a
      mean here can be a single lucky trade, so the mean alone can never carry a verdict.
    * Win rate reported but never a pass criterion.

WHAT IT DELIBERATELY DOES NOT DO
    It does not let anyone re-run an experiment with different parameters and keep the
    best result. Constants are frozen in the declaration; changing one voids the test and
    requires a new registration with a new window. That restriction is the product.

ADDING AN EXPERIMENT
    Append a dict to EXPERIMENTS. Required: id, title, registered_at, status, universe,
    entry (callable), hold_sessions, cost_roundtrip, prior. Everything else has defaults.
    Set status="draft" to develop it without starting the clock; "registered" starts it.

USAGE
    python3 experiment_harness.py scan        # log today's signals for every registered exp
    python3 experiment_harness.py grade       # grade matured signals + day-matched control
    python3 experiment_harness.py report      # rewrite reports/experiments-LATEST.md
    python3 experiment_harness.py --selftest  # offline logic check, no network
"""
import argparse
import csv
import io
import os
import random
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "experiments")
REPORT = os.path.join(HERE, "reports", "experiments-LATEST.md")

MIN_N = 30          # global minimum before any experiment is ruled on
# --- AMENDMENT 2026-08-07: one experiment, one look -------------------------------------
# The verdict used to be recomputed on EVERY run from n>=MIN_N onward, with no alpha
# spending, so across a year of weekly snapshots a no-effect claim had roughly a 1-in-5
# chance of printing a pass at least once. Two additions fix that, and they are REPORTING
# logic only — not one stored signal or outcome row is affected:
#   (1) a CLUSTER floor. n counts trades; the clustered CI's precision is governed by the
#       number of distinct NAMES, since repeated bets on one ticker are not independent
#       evidence. 30 trades on 4 names is not 30 pieces of evidence.
#   (2) ONE pre-declared VERDICT DATE per experiment. A floor alone only delays the first
#       look; after it the verdict would still be re-tested every run. The verdict is now
#       computed at the first run on or after that date at which both floors are met,
#       written once to an append-only verdicts file, and thereafter displayed from that
#       file and NEVER recomputed.
# The dates below are the batch's ALREADY-PLANNED continue/kill read (~1 Nov 2026). They
# were set from that pre-existing plan, deliberately WITHOUT inspecting any current result.
MIN_CLUSTERS = 20   # distinct tickers required before any verdict is computed
VERDICT_ON = {
    "EXP03-MACD": "2026-11-02",
    "EXP06-SUPERTREND": "2026-11-02",
    "EXP07-SMAPULL": "2026-11-02",
    "EXP08-BOLLREVERT": "2026-11-02",
    "EXP09-NR7": "2026-11-02",
}
DEFAULT_VERDICT_LAG_DAYS = 90   # any future declaration that omits an explicit date


def verdict_date(e):
    """Explicit `verdict_on` in the declaration wins; then the table above; otherwise a
    default lag from registration, so a new experiment can never accidentally ship with an
    unbounded number of looks."""
    if e.get("verdict_on"):
        return e["verdict_on"]
    if e["id"] in VERDICT_ON:
        return VERDICT_ON[e["id"]]
    d = datetime.strptime(e["registered_at"], "%Y-%m-%d") + timedelta(days=DEFAULT_VERDICT_LAG_DAYS)
    return d.date().isoformat()

BOOT = 3000
SEED = 7

# --------------------------------------------------------------- indicators
def sma(xs, n):
    return sum(xs[-n:]) / float(n) if len(xs) >= n else None


def ema_series(xs, n):
    if len(xs) < n:
        return []
    k = 2.0 / (n + 1.0)
    out = [sum(xs[:n]) / float(n)]
    for x in xs[n:]:
        out.append(x * k + out[-1] * (1 - k))
    return out


def rsi(xs, period):
    """Wilder's RSI."""
    if len(xs) < period + 1:
        return None
    g = [max(xs[i] - xs[i - 1], 0.0) for i in range(1, len(xs))]
    l = [max(xs[i - 1] - xs[i], 0.0) for i in range(1, len(xs))]
    ag, al = sum(g[:period]) / period, sum(l[:period]) / period
    for i in range(period, len(g)):
        ag = (ag * (period - 1) + g[i]) / period
        al = (al * (period - 1) + l[i]) / period
    if al == 0:
        return 100.0
    return 100.0 - (100.0 / (1.0 + ag / al))


def macd(xs, fast=12, slow=26, sig=9):
    """Returns (macd_line, signal_line, hist) for the LAST bar, or (None,None,None)."""
    if len(xs) < slow + sig + 1:
        return None, None, None
    ef, es = ema_series(xs, fast), ema_series(xs, slow)
    # align: ema_series(fast) starts (slow-fast) bars earlier than ema_series(slow)
    off = len(ef) - len(es)
    line = [ef[i + off] - es[i] for i in range(len(es))]
    sl = ema_series(line, sig)
    if not sl:
        return None, None, None
    return line[-1], sl[-1], line[-1] - sl[-1]


def macd_hist_series(xs, fast=12, slow=26, sig=9):
    """Histogram for every bar where it is defined (chronological)."""
    if len(xs) < slow + sig + 1:
        return []
    ef, es = ema_series(xs, fast), ema_series(xs, slow)
    off = len(ef) - len(es)
    line = [ef[i + off] - es[i] for i in range(len(es))]
    sl = ema_series(line, sig)
    lag = len(line) - len(sl)
    return [line[i + lag] - sl[i] for i in range(len(sl))]


def stdev_pop(xs):
    """Population standard deviation (Bollinger convention)."""
    if not xs:
        return None
    m = sum(xs) / float(len(xs))
    return (sum((x - m) ** 2 for x in xs) / float(len(xs))) ** 0.5


def atr_wilder_series(bars, period=10):
    """Wilder-smoothed ATR. Returns list aligned to bars (None until warm)."""
    n = len(bars)
    atr = [None] * n
    if n <= period:
        return atr
    tr = [None] * n
    for i in range(1, n):
        tr[i] = max(bars[i]["h"] - bars[i]["l"],
                    abs(bars[i]["h"] - bars[i - 1]["c"]),
                    abs(bars[i]["l"] - bars[i - 1]["c"]))
    atr[period] = sum(tr[1:period + 1]) / float(period)
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def supertrend_state(bars, period=10, mult=3.0):
    """Standard Supertrend with band ratcheting.
    Returns (trend, line): trend[i] in {+1, -1, None}; line[i] = the active band."""
    n = len(bars)
    atr = atr_wilder_series(bars, period)
    trend, line = [None] * n, [None] * n
    fu, fl = [None] * n, [None] * n
    for i in range(n):
        if atr[i] is None:
            continue
        mid = (bars[i]["h"] + bars[i]["l"]) / 2.0
        bu, bl = mid + mult * atr[i], mid - mult * atr[i]
        if i == 0 or fu[i - 1] is None:
            fu[i], fl[i], trend[i] = bu, bl, 1
        else:
            fu[i] = bu if (bu < fu[i - 1] or bars[i - 1]["c"] > fu[i - 1]) else fu[i - 1]
            fl[i] = bl if (bl > fl[i - 1] or bars[i - 1]["c"] < fl[i - 1]) else fl[i - 1]
            if trend[i - 1] == 1:
                trend[i] = -1 if bars[i]["c"] < fl[i] else 1
            else:
                trend[i] = 1 if bars[i]["c"] > fu[i] else -1
        line[i] = fl[i] if trend[i] == 1 else fu[i]
    return trend, line


# --------------------------------------------------------------- statistics
def median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def trimmed_mean(xs, frac=0.10):
    if not xs:
        return None
    s = sorted(xs)
    k = int(len(s) * frac)
    t = s[k:len(s) - k] if len(s) - 2 * k > 0 else s
    return sum(t) / float(len(t))


def cluster_ci(vals, keys, B=BOOT, seed=SEED):
    """Mean + 95% CI, resampling CLUSTERS (tickers) — repeated bets on one name are not
    independent evidence. Returns None if too thin."""
    if len(vals) < 10:
        return None
    by = {}
    for v, k in zip(vals, keys):
        by.setdefault(k, []).append(v)
    ks = list(by)
    rnd = random.Random(seed)
    out = []
    for _ in range(B):
        s = []
        for _ in range(len(ks)):
            s.extend(by[ks[rnd.randrange(len(ks))]])
        if s:
            out.append(sum(s) / float(len(s)))
    if len(out) < 100:
        return None
    out.sort()
    return {"mean": sum(vals) / float(len(vals)),
            "lo": out[int(0.025 * len(out))],
            "hi": out[min(len(out) - 1, int(0.975 * len(out)))],
            "n": len(vals), "clusters": len(ks)}


# --------------------------------------------------------------- experiments
UNIVERSE_LARGECAP40 = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "AVGO", "ORCL", "CRM", "ADBE",
    "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "AXP", "BLK", "SCHW",
    "JNJ", "UNH", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT",
    "XOM", "CVX", "COP", "WMT", "COST", "PG", "KO", "PEP", "HD", "MCD", "CAT", "HON",
]


def entry_macd_cross(bars):
    """EXP03 entry: MACD(12,26,9) histogram crosses from <=0 to >0 on the latest bar,
    with the close above its 200-day SMA. Long-only trend-following, the most widely
    taught indicator signal in retail trading."""
    closes = [b["c"] for b in bars]
    h = macd_hist_series(closes)
    if len(h) < 2:
        return False, {}
    s200 = sma(closes, 200)
    if s200 is None:
        return False, {}
    crossed = h[-2] <= 0.0 < h[-1]
    ok = bool(crossed and closes[-1] > s200)
    return ok, {"macd_hist": round(h[-1], 5), "macd_hist_prev": round(h[-2], 5),
                "sma200": round(s200, 4), "close": round(closes[-1], 4),
                "rank_metric": -h[-1]}   # strongest crossover first


def entry_supertrend_flip(bars):
    """EXP06 entry: Supertrend(10, 3) trend state flips -1 -> +1 on the latest bar.
    Deliberately NO trend filter — the claim as sold has none; adding one would test
    our idea, not theirs."""
    if len(bars) < 60:
        return False, {}
    trend, line = supertrend_state(bars, period=10, mult=3.0)
    if trend[-1] is None or trend[-2] is None:
        return False, {}
    ok = bool(trend[-2] == -1 and trend[-1] == 1)
    if not ok:
        return False, {}
    c = bars[-1]["c"]
    dist = (c - line[-1]) / c if c else 0.0
    return True, {"st_line": round(line[-1], 4), "close": round(c, 4),
                  "dist_pct": round(dist * 100.0, 4),
                  "rank_metric": -dist}   # largest distance above the flip line first


def entry_sma_pullback(bars):
    """EXP07 entry: uptrend pullback — close above SMA(200), today's low touches or
    pierces SMA(20), close back above SMA(20). The most widely taught swing entry."""
    closes = [b["c"] for b in bars]
    s200, s20 = sma(closes, 200), sma(closes, 20)
    if s200 is None or s20 is None or not s20:
        return False, {}
    c, lo = bars[-1]["c"], bars[-1]["l"]
    ok = bool(c > s200 and lo <= s20 < c)
    if not ok:
        return False, {}
    depth = lo / s20
    return True, {"sma20": round(s20, 4), "sma200": round(s200, 4),
                  "close": round(c, 4), "low_over_sma20": round(depth, 5),
                  "rank_metric": depth}   # deepest touch first


def entry_bollinger_revert(bars):
    """EXP08 entry: close below the lower Bollinger Band (20, 2.0) with the close above
    SMA(200) — the taught, Connors-style long-only version of the high-win-rate pitch."""
    closes = [b["c"] for b in bars]
    s200, s20 = sma(closes, 200), sma(closes, 20)
    if s200 is None or s20 is None:
        return False, {}
    sd = stdev_pop(closes[-20:])
    if not sd:
        return False, {}
    c = closes[-1]
    z = (c - s20) / sd
    ok = bool(c < s20 - 2.0 * sd and c > s200)
    if not ok:
        return False, {}
    return True, {"bb_mid": round(s20, 4), "bb_sd": round(sd, 4), "z": round(z, 4),
                  "close": round(c, 4),
                  "rank_metric": z}   # most negative z first


def entry_nr7_uptrend(bars):
    """EXP09 entry: today's high-low range is strictly the narrowest of the last 7
    sessions, with the close above SMA(200). Tests whether volatility contraction in an
    uptrend precedes upward expansion — the honest daily-bar version of the sold
    intraday-breakout claim (entry is next open, not an intraday range break)."""
    closes = [b["c"] for b in bars]
    s200 = sma(closes, 200)
    if s200 is None or len(bars) < 7:
        return False, {}
    ranges = [b["h"] - b["l"] for b in bars[-7:]]
    today = ranges[-1]
    c = closes[-1]
    ok = bool(c > s200 and today >= 0 and all(today < r for r in ranges[:-1]) and c)
    if not ok:
        return False, {}
    rel = today / c
    return True, {"range": round(today, 4), "range_pct": round(rel * 100.0, 4),
                  "close": round(c, 4), "sma200": round(s200, 4),
                  "rank_metric": rel}   # narrowest relative range first


EXPERIMENTS = [
    {
        "id": "EXP03-MACD",
        "title": "The MACD bullish crossover",
        "registered_at": "2026-07-31",
        "status": "registered",
        "universe": UNIVERSE_LARGECAP40,
        "lookback_days": 500,
        "entry": entry_macd_cross,
        "hold_sessions": 5,
        "max_per_day": 5,
        "cost_roundtrip": 0.10,
        "prior": ("The most widely taught indicator signal in retail trading — on every "
                  "platform, in every beginner course. Published, universally known, and "
                  "therefore the least likely thing in the world to still contain an edge. "
                  "Registered expectation: the day-matched excess is indistinguishable from "
                  "zero. Estimated probability it clears the bar: ~1 in 6. Being widely "
                  "believed is not evidence, which is the point of testing it."),
    },
    # ------------------------------------------------------------------
    # TIER-A BATCH, registered together 2026-08-06 (one family, one clock).
    # FAMILY POLICY, declared before any result exists: with ~8 experiments running
    # concurrently at ~1-in-6 priors, ~1 chance pass is EXPECTED. The published
    # family verdict applies Benjamini-Hochberg FDR across all concurrently
    # registered experiments; a single pass is reported as consistent with chance
    # until it survives that correction and a fresh forward window. Experiments
    # sharing this universe are correlated tests, not independent replications,
    # and same-day signal overlap across experiments is reported.
    # ------------------------------------------------------------------
    {
        "id": "EXP06-SUPERTREND",
        "title": "The Supertrend flip",
        "registered_at": "2026-08-06",
        "status": "registered",
        "universe": UNIVERSE_LARGECAP40,
        "lookback_days": 500,
        "entry": entry_supertrend_flip,
        "hold_sessions": 5,
        "max_per_day": 5,
        "cost_roundtrip": 0.10,
        "prior": ("Currently the most heavily marketed single indicator in retail video "
                  "content, almost always at exactly these default settings (10, 3). It is "
                  "a mechanically sane ATR trailing band, which is why it demos well — and "
                  "why, on forty of the most liquid names on earth, it should already be "
                  "arbitraged flat. Deliberately tested with NO trend filter because the "
                  "claim as sold has none. Registered expectation: excess indistinguishable "
                  "from zero; ~1 in 6 it clears."),
    },
    {
        "id": "EXP07-SMAPULL",
        "title": "The moving-average pullback (buy the dip in an uptrend)",
        "registered_at": "2026-08-06",
        "status": "registered",
        "universe": UNIVERSE_LARGECAP40,
        "lookback_days": 500,
        "entry": entry_sma_pullback,
        "hold_sessions": 5,
        "max_per_day": 5,
        "cost_roundtrip": 0.10,
        "prior": ("The most widely taught swing entry in existence — nearly every course "
                  "teaches some form of buying the pullback to the 20-day in an uptrend. "
                  "The mechanism (short-term reversion inside medium-term momentum) is at "
                  "least coherent, which earns it a slightly better prior than a raw "
                  "indicator flip: call it ~1 in 5. Registered expectation is still that "
                  "the day-matched excess is indistinguishable from zero — textbook status "
                  "is exactly what arbitrages an edge away."),
    },
    {
        "id": "EXP08-BOLLREVERT",
        "title": "Bollinger Band mean reversion",
        "registered_at": "2026-08-06",
        "status": "registered",
        "universe": UNIVERSE_LARGECAP40,
        "lookback_days": 500,
        "entry": entry_bollinger_revert,
        "hold_sessions": 5,
        "max_per_day": 5,
        "cost_roundtrip": 0.10,
        "prior": ("The same high-win-rate sales pitch as Experiment 02's RSI(2), through a "
                  "different mechanism: the band adapts to volatility. Win-rate-flattering "
                  "by construction — many small reverts punctuated by occasional large "
                  "losses — which is precisely the shape the mean/median/clustered-CI "
                  "reporting exists to expose. Registered expectation: excess "
                  "indistinguishable from zero; ~1 in 6 it clears."),
    },
    {
        "id": "EXP09-NR7",
        "title": "Volatility contraction (NR7) in an uptrend",
        "registered_at": "2026-08-06",
        "status": "registered",
        "universe": UNIVERSE_LARGECAP40,
        "lookback_days": 500,
        "entry": entry_nr7_uptrend,
        "hold_sessions": 5,
        "max_per_day": 5,
        "cost_roundtrip": 0.10,
        "prior": ("That contraction precedes expansion (Crabel's NR7) is well documented; "
                  "what is SOLD is the direction, and direction is the part with no "
                  "documented edge. This is also the honest daily-bar version of an "
                  "intraday claim: entry is the next open, not a break of the range, "
                  "because our pre-open logging gate forbids acting on the open print. "
                  "That deviation is disclosed wherever this experiment is published. "
                  "Registered expectation: excess indistinguishable from zero; ~1 in 6."),
    },
]


# --------------------------------------------------------------- io helpers
def _f(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def _read(p):
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        return []
    with io.open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _append(p, fields, rows):
    if not rows:
        return
    os.makedirs(os.path.dirname(p), exist_ok=True)
    # An EXISTING BUT EMPTY file must still get a header: an interrupted first run leaves a
    # zero-byte file, and without this the first data row silently becomes the header, every
    # later _read returns garbage, and the catch-all keeps CI green while nothing is
    # collected. Found by the 2026-08-07 review of calendar_eval.py, which shared this code.
    first = (not os.path.exists(p)) or os.path.getsize(p) == 0
    with io.open(p, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        if first:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def sig_path(e):
    return os.path.join(DATA, f"{e['id']}-signals.csv")


def out_path(e):
    return os.path.join(DATA, f"{e['id']}-outcomes.csv")


SIG_FIELDS = ["signal_id", "experiment", "captured_at", "signal_date", "ticker",
              "rank_in_day", "meta"]
OUT_FIELDS = ["signal_id", "experiment", "ticker", "signal_date", "entry_date", "graded_at",
              "entry_open", "ret_1d_net", "ret_nd_net", "bench_1d_net", "bench_nd_net",
              "excess_1d", "excess_nd", "win_1d", "note"]


def fetch(universe, days):
    import yfinance as yf
    df = yf.download(universe, period=f"{days}d", interval="1d", auto_adjust=False,
                     group_by="ticker", progress=False, threads=True)
    out = {}
    for t in universe:
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
        if len(rows) > 210:
            out[t] = rows
    return out


# --------------------------------------------------------------- commands
def scan_one(e, data=None):
    if e.get("status") != "registered":
        print(f"  {e['id']}: status={e.get('status')} — not scanning")
        return 0
    data = data or fetch(e["universe"], e.get("lookback_days", 500))
    if not data:
        print(f"  {e['id']}: no data (non-fatal)")
        return 0
    asof = max(rows[-1]["d"] for rows in data.values())
    seen = {(r["signal_date"], r["ticker"]) for r in _read(sig_path(e))}
    fires = []
    for t, rows in data.items():
        if rows[-1]["d"] != asof:
            continue
        try:
            ok, meta = e["entry"](rows)
        except Exception as ex:
            print(f"  {e['id']} {t}: entry error {type(ex).__name__}")
            continue
        if ok:
            fires.append((t, meta))
    fires.sort(key=lambda x: x[1].get("rank_metric", 0))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new = []
    for rank, (t, meta) in enumerate(fires[:e.get("max_per_day", 5)], 1):
        if (asof, t) in seen:
            continue
        new.append({"signal_id": f"{e['id']}-{asof}-{t}", "experiment": e["id"],
                    "captured_at": now, "signal_date": asof, "ticker": t,
                    "rank_in_day": rank,
                    "meta": ";".join(f"{k}={v}" for k, v in sorted(meta.items())
                                     if k != "rank_metric")})
    _append(sig_path(e), SIG_FIELDS, new)
    tag = "" if asof > e["registered_at"] else "  (PRE-REGISTRATION DATE — will not be scored)"
    print(f"  {e['id']} {asof}: {len(fires)} fired, logged {len(new)}{tag}")
    return len(new)


def grade_one(e, data=None):
    sigs = [s for s in _read(sig_path(e)) if s.get("signal_date", "") > e["registered_at"]]
    if not sigs:
        print(f"  {e['id']}: no post-registration signals yet")
        return 0
    done = {r["signal_id"] for r in _read(out_path(e))}
    todo = [s for s in sigs if s["signal_id"] not in done]
    if not todo:
        print(f"  {e['id']}: nothing new to grade")
        return 0
    data = data or fetch(e["universe"], e.get("lookback_days", 500))
    if not data:
        print(f"  {e['id']}: no data (non-fatal)")
        return 0
    N, C = e["hold_sessions"], e["cost_roundtrip"]
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    idxs = {t: {b["d"]: i for i, b in enumerate(rows)} for t, rows in data.items()}

    def bench(sd):
        r1, rn = [], []
        for t, rows in data.items():
            i = idxs[t].get(sd)
            if i is None or i + 1 + N >= len(rows):
                continue
            en = rows[i + 1]["o"]
            if not en:
                continue
            r1.append((rows[i + 1]["c"] - en) / en * 100.0 - C)
            rn.append((rows[i + 1 + N]["c"] - en) / en * 100.0 - C)
        if len(r1) < 10:
            return None
        return sum(r1) / len(r1), sum(rn) / len(rn)

    cache, rows_out, immature, failed = {}, [], 0, 0
    for s in todo:
        t, sd = s["ticker"], s["signal_date"]
        rows = data.get(t)
        i = idxs.get(t, {}).get(sd) if rows else None
        if rows is None or i is None:
            failed += 1
            continue
        if i + 1 + N >= len(rows):
            immature += 1
            continue
        en = rows[i + 1]["o"]
        if not en:
            failed += 1
            continue
        if sd not in cache:
            cache[sd] = bench(sd)
        b = cache[sd]
        if b is None:
            immature += 1
            continue
        r1 = (rows[i + 1]["c"] - en) / en * 100.0 - C
        rn = (rows[i + 1 + N]["c"] - en) / en * 100.0 - C
        rows_out.append({"signal_id": s["signal_id"], "experiment": e["id"], "ticker": t,
                         "signal_date": sd, "entry_date": rows[i + 1]["d"], "graded_at": now,
                         "entry_open": round(en, 4), "ret_1d_net": round(r1, 4),
                         "ret_nd_net": round(rn, 4), "bench_1d_net": round(b[0], 4),
                         "bench_nd_net": round(b[1], 4), "excess_1d": round(r1 - b[0], 4),
                         "excess_nd": round(rn - b[1], 4), "win_1d": 1 if r1 > 0 else 0,
                         "note": ""})
    _append(out_path(e), OUT_FIELDS, rows_out)
    print(f"  {e['id']}: +{len(rows_out)} graded ({immature} not matured, {failed} failed)")
    return len(rows_out)


VERDICT_FIELDS = ["experiment", "locked_at", "n", "clusters", "mean1", "med1",
                  "ci_lo", "ci_hi", "verdict"]


def verdicts_path():
    return os.path.join(DATA, "HARNESS-verdicts.csv")


def locked_verdicts():
    return {r["experiment"]: r for r in _read(verdicts_path())}


def lock_verdict(row):
    """Append-only, once per experiment. A locked verdict is displayed verbatim ever after
    and never recomputed — that is what makes it ONE look."""
    if row["experiment"] in locked_verdicts():
        return
    _append(verdicts_path(), VERDICT_FIELDS, [row])
    print(f"  LOCKED verdict for {row['experiment']}: {row['verdict']}")


def summarise(e):
    g = _read(out_path(e))
    n = len(g)
    if not n:
        return {"n": 0}
    ex1 = [_f(r["excess_1d"]) for r in g if _f(r["excess_1d"]) is not None]
    exn = [_f(r["excess_nd"]) for r in g if _f(r["excess_nd"]) is not None]
    tk = [r["ticker"] for r in g if _f(r["excess_1d"]) is not None]
    wins = [int(r["win_1d"]) for r in g if r.get("win_1d") not in ("", None)]
    ci1 = cluster_ci(ex1, tk) if len(ex1) >= 10 else None
    return {"n": n, "ci1": ci1,
            "mean1": (sum(ex1) / len(ex1)) if ex1 else None, "med1": median(ex1),
            "trim1": trimmed_mean(ex1), "meann": (sum(exn) / len(exn)) if exn else None,
            "medn": median(exn),
            "win": (100.0 * sum(wins) / len(wins)) if wins else None,
            "clusters": len(set(tk)),
            "mature": len(ex1) >= MIN_N}


def _compute_verdict(s):
    """The verdict text. Only ever called once per experiment, at the pre-declared date."""
    ci = s.get("ci1")
    if not ci:
        return None
    if ci["lo"] > 0 and (s["mean1"] or 0) > 0 and (s["med1"] or 0) > 0:
        return "CLEARS THE BAR — mean, median and clustered CI all positive"
    if ci["hi"] < 0:
        return "SIGNIFICANTLY NEGATIVE — worse than the day-matched control"
    return "NO EDGE DETECTED — the excess is indistinguishable from zero"


def verdict_line(s, e=None, today=None):
    """One experiment, one look (amendment 2026-08-07).

    Before the pre-declared verdict date: progress only, no verdict language of any kind.
    On/after it, once BOTH floors are met: compute once and lock to an append-only file.
    Ever after: display the locked text verbatim, so no amount of re-running this script on
    later data can turn a null into a pass."""
    if not s.get("n"):
        return "no graded signals yet"
    if e is None:
        return f"accruing — {s['n']}/{MIN_N} graded, no verdict yet"
    lk = locked_verdicts().get(e["id"])
    if lk:
        return (f"**{lk['verdict']}** *(locked {lk['locked_at']} at n={lk['n']} over "
                f"{lk['clusters']} names — computed once, at the pre-declared verdict date, "
                f"and never recomputed)*")
    today = today or datetime.now(timezone.utc).date().isoformat()
    vd = verdict_date(e)
    prog = (f"{s['n']}/{MIN_N} graded signals over {s.get('clusters', 0)}/{MIN_CLUSTERS} "
            f"distinct names")
    if today < vd:
        return (f"accruing — {prog}. **No verdict is computed before the single pre-declared "
                f"verdict date of {vd}**, and none is computed then unless both floors are met.")
    if not (s.get("mature") and s.get("clusters", 0) >= MIN_CLUSTERS):
        return (f"past the pre-declared verdict date ({vd}) with the floor not yet met — "
                f"{prog}. The verdict locks at the first run where it is.")
    v = _compute_verdict(s)
    if v is None:
        return (f"past the pre-declared verdict date ({vd}) but the interval could not be "
                f"computed — {prog}")
    ci = s["ci1"]
    lock_verdict({"experiment": e["id"], "locked_at": today, "n": s["n"],
                  "clusters": s.get("clusters", 0), "mean1": round(s["mean1"], 5),
                  "med1": round(s["med1"], 5), "ci_lo": round(ci["lo"], 5),
                  "ci_hi": round(ci["hi"], 5), "verdict": v})
    return (f"**{v}** *(locked {today} at n={s['n']} over {s.get('clusters', 0)} names — "
            f"computed once and never recomputed)*")


def cmd_report():
    L = ["# ThePickLog — experiments under test · " + datetime.now(timezone.utc).date().isoformat(), "",
         "Every experiment below is forward-only from its registration date, scored as an "
         "**excess over a day-matched control** (the equal-weight return of its own frozen "
         "universe over the identical window), net of a declared cost. Mean, median and a "
         "ticker-clustered 95% CI are reported together, because a mean on financial data can "
         "be a single lucky trade. **Win rate is reported but is never a pass criterion.**", "",
         "> **Amended 2026-08-07 — one experiment, one look.** The verdict used to be "
         "recomputed on every run from n>=30 onward, so across a year of snapshots a claim "
         "with no real effect had roughly a 1-in-5 chance of printing a pass at least once. "
         f"Each experiment now also needs **>={MIN_CLUSTERS} distinct names** (repeated bets "
         "on one ticker are not independent evidence) and has **one pre-declared verdict "
         "date**, shown below. The verdict is computed at the first run on or after that date "
         "at which both floors are met, written once to an append-only verdicts file, and "
         "thereafter displayed from that file and **never recomputed**. Before that date this "
         "report shows running numbers and no verdict language of any kind. This changed "
         "REPORTING ONLY — no stored signal or outcome row was altered — and the dates were "
         "set from the batch's already-planned continue/kill read, without inspecting any "
         "current result. Full detail in HYPOTHESES.md.", ""]
    for e in EXPERIMENTS:
        s = summarise(e)
        L += [f"## {e['id']} — {e['title']}", "",
              f"- status: **{e.get('status')}**, registered {e['registered_at']}, "
              f"universe {len(e['universe'])} names, hold {e['hold_sessions']} sessions, "
              f"cost {e['cost_roundtrip']}% round trip",
              f"- graded signals: **{s.get('n', 0)}** (need {MIN_N}) over "
              f"**{s.get('clusters', 0)}** distinct names (need {MIN_CLUSTERS}); "
              f"single pre-declared verdict date **{verdict_date(e)}**"]
        if s.get("n"):
            ci = s.get("ci1")
            cis = f"[{ci['lo']:+.3f}, {ci['hi']:+.3f}] over {ci['clusters']} names" if ci else "n/a"
            L += [f"- day-matched excess, 1 session: mean **{s['mean1']:+.3f}%**, "
                  f"median **{s['med1']:+.3f}%**, 10% trimmed **{s['trim1']:+.3f}%**, "
                  f"clustered 95% CI {cis}",
                  f"- day-matched excess, {e['hold_sessions']} sessions: mean "
                  f"**{s['meann']:+.3f}%**, median **{s['medn']:+.3f}%**",
                  f"- win rate {s['win']:.0f}% *(reported only — not a pass criterion)*"]
        L += [f"- **read: {verdict_line(s, e)}**", "",
              f"> Registered prior: {e['prior']}", ""]
    L += ["---", "",
          "Rules are frozen in `experiment_harness.py`; changing any constant voids that "
          "experiment and requires a new registration with a new window. Signals and outcomes "
          "are append-only under `experiments/`. Not investment advice."]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with io.open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"wrote {REPORT}")
    return 0


def _selftest():
    # indicators
    assert sma([1, 2, 3, 4], 2) == 3.5 and sma([1], 5) is None
    assert rsi([1, 2, 3, 4, 5], 2) == 100.0 and rsi([5, 4, 3, 2, 1], 2) == 0.0
    # a steady uptrend must give a positive MACD histogram at some point
    up = [100.0 + i for i in range(80)]
    m, sg, h = macd(up)
    assert m is not None and m > 0, (m, sg, h)
    hs = macd_hist_series(up)
    assert len(hs) > 5
    # MACD entry: needs a genuine cross from <=0 to >0 AND close above SMA200
    down_then_up = [200.0 - i * 0.5 for i in range(260)] + [70.0 + i * 3.0 for i in range(40)]
    bars = [{"d": f"d{i}", "o": c, "h": c, "l": c, "c": c} for i, c in enumerate(down_then_up)]
    hist = macd_hist_series([b["c"] for b in bars])
    crosses = sum(1 for i in range(1, len(hist)) if hist[i - 1] <= 0 < hist[i])
    assert crosses >= 1, crosses
    # flat series must not fire — for ANY entry
    flat = [{"d": f"d{i}", "o": 100.0, "h": 100.0, "l": 100.0, "c": 100.0} for i in range(300)]
    for fn in (entry_macd_cross, entry_supertrend_flip, entry_sma_pullback,
               entry_bollinger_revert, entry_nr7_uptrend):
        ok, _ = fn(flat)
        assert not ok, fn.__name__
    # supertrend: sustained trends resolve to the matching state
    mkbars = lambda cs: [{"d": f"d{i}", "o": c, "h": c * 1.01, "l": c * 0.99, "c": c}
                         for i, c in enumerate(cs)]
    tu, _ = supertrend_state(mkbars([100.0 + i for i in range(120)]))
    assert tu[-1] == 1
    td, _ = supertrend_state(mkbars([220.0 - i for i in range(120)]))
    assert td[-1] == -1
    # supertrend: a decline then a strong recovery must flip -1 -> +1 somewhere
    tv, _ = supertrend_state(mkbars([200.0 - i * 0.8 for i in range(90)]
                                    + [130.0 + i * 2.0 for i in range(60)]))
    assert any(tv[i - 1] == -1 and tv[i] == 1 for i in range(1, len(tv))
               if tv[i - 1] is not None)
    # SMA pullback: uptrend where the last bar dips to the 20-day and closes back above
    up = [100.0 + i * 0.5 for i in range(260)]
    pb = mkbars(up)
    s20_now = sma([b["c"] for b in pb], 20)
    pb[-1]["l"] = s20_now - 0.01          # touch
    assert pb[-1]["c"] > s20_now          # close back above
    ok, meta = entry_sma_pullback(pb)
    assert ok and meta["rank_metric"] <= 1.0
    # Bollinger revert: uptrend with a sharp last-bar break below the lower band
    bb = mkbars(up)
    closes_bb = [b["c"] for b in bb]
    sd_now = stdev_pop(closes_bb[-20:])
    bb[-1]["c"] = sma(closes_bb, 20) - 2.5 * sd_now
    assert bb[-1]["c"] > sma(closes_bb, 200)   # still above SMA200
    ok, meta = entry_bollinger_revert(bb)
    assert ok and meta["z"] < -2.0
    # NR7: uptrend whose last bar has the narrowest range of the final 7
    nr = mkbars(up)
    nr[-1]["h"], nr[-1]["l"] = nr[-1]["c"] * 1.0001, nr[-1]["c"] * 0.9999
    ok, meta = entry_nr7_uptrend(nr)
    assert ok
    # stdev sanity
    assert abs(stdev_pop([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]) - 2.0) < 1e-9
    # stats
    assert median([1, 2, 3]) == 2 and median([1, 2, 3, 4]) == 2.5
    assert abs(trimmed_mean([0, 1, 2, 3, 100], 0.2) - 2.0) < 1e-9
    ci = cluster_ci([1.0] * 40, [f"T{i%8}" for i in range(40)])
    assert ci and abs(ci["mean"] - 1.0) < 1e-9 and ci["clusters"] == 8
    ci2 = cluster_ci([1.0, -1.0] * 30, [f"T{i%10}" for i in range(60)])
    assert ci2 and ci2["lo"] < 0 < ci2["hi"]     # no effect -> CI straddles zero
    # verdict wording
    assert "accruing" in verdict_line({"n": 5, "mature": False})
    assert "no graded signals" in verdict_line({"n": 0})
    # amendment 2026-08-07: no verdict before the pre-declared date, and locking is final
    import tempfile as _tf
    global DATA
    _keep = DATA
    try:
        DATA = _tf.mkdtemp()
        _e = {"id": "SELFTEST-X", "registered_at": "2026-01-01", "verdict_on": "2026-06-01"}
        _pass = {"n": 99, "mature": True, "clusters": 40, "mean1": 1.0, "med1": 1.0,
                 "ci1": {"lo": 0.5, "hi": 1.5, "clusters": 40}}
        # before the date: progress only, and the date is advertised
        _r = verdict_line(_pass, _e, today="2026-05-31")
        assert "accruing" in _r and "CLEARS" not in _r and "2026-06-01" in _r, _r
        # floors not met on the date: still no verdict
        _thin = dict(_pass, clusters=3)
        assert "floor not yet met" in verdict_line(_thin, _e, today="2026-06-01")
        # on the date with floors met: computed and locked
        _r = verdict_line(_pass, _e, today="2026-06-01")
        assert "CLEARS THE BAR" in _r and "locked" in _r, _r
        # afterwards, with the data flipped NEGATIVE, the locked verdict must not move
        _neg = {"n": 99, "mature": True, "clusters": 40, "mean1": -1.0, "med1": -1.0,
                "ci1": {"lo": -1.5, "hi": -0.5, "clusters": 40}}
        _outs = {verdict_line(_neg, _e, today=d) for d in
                 ("2026-06-02", "2026-09-01", "2027-01-01")}
        assert len(_outs) == 1 and "CLEARS THE BAR" in list(_outs)[0], _outs
        assert len(_read(verdicts_path())) == 1
        # default date for a declaration that omits one
        assert verdict_date({"id": "NEW", "registered_at": "2026-01-01"}) == "2026-04-01"
    finally:
        DATA = _keep

    # every declared experiment is well formed
    for e in EXPERIMENTS:
        for k in ("id", "title", "registered_at", "status", "universe", "entry",
                  "hold_sessions", "cost_roundtrip", "prior"):
            assert k in e, (e.get("id"), k)
        assert e["status"] in ("registered", "draft")
        assert callable(e["entry"])
    print(f"experiment_harness selftest PASS — indicators, MACD entry, cluster stats, "
          f"{len(EXPERIMENTS)} experiment declaration(s) verified")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs="?", default="report",
                    choices=["scan", "grade", "report"])
    ap.add_argument("--id", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    exps = [e for e in EXPERIMENTS if (a.id is None or e["id"] == a.id)]
    if a.command in ("scan", "grade"):
        print(f"experiment_harness {a.command}: {len(exps)} experiment(s)")
        # one fetch per distinct universe, shared across experiments
        cache = {}
        for e in exps:
            key = (tuple(e["universe"]), e.get("lookback_days", 500))
            if key not in cache:
                try:
                    cache[key] = fetch(e["universe"], e.get("lookback_days", 500))
                except Exception as ex:
                    print(f"  fetch failed ({type(ex).__name__}) — skipping")
                    cache[key] = {}
            (scan_one if a.command == "scan" else grade_one)(e, cache[key])
    return cmd_report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"experiment_harness: non-fatal error {type(e).__name__}: {e}")
        sys.exit(0)
