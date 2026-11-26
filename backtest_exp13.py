#!/usr/bin/env python3
"""backtest_exp13.py — an EXPLORATORY historical replay of the six Experiment 13 rules.

NOT A VERDICT. Experiment 13 is judged only by its forward test (experiment_harness.py, signals
dated after 2026-11-27, one look at the floors). This script replays the same six entry rules,
the same exit, the same control and the same cost on past prices, 2005-2025, as an early read.
ROADMAP.md's guardrail holds: the forward log is the only judge; a backtest selects variables.
Nothing here writes to experiments/ or changes any registered rule.

The plan (window, universes, statistics, labels) is fixed in HYPOTHESES.md, "Exploratory backtest
for Experiment 13 — plan fixed 2026-11-26", and was committed before this script was ever run on
real data. The commit that adds this file is the proof of order.

Two universes, both reported:
  A  the frozen Experiment 13 list (universes/sp500-2026-11-26.csv, 503 names) on every date.
     Today's members looked back on: survivorship bias by construction.
  B  point-in-time S&P 500 members on each date (universes/sp500-pit-fja05680-2026-08-18.csv),
     limited to names Yahoo still serves. Delisted names are mostly missing; the gap is measured
     and written to coverage.csv. B is the headline read.

Usage:
  python backtest_exp13.py selftest   # equivalence with the harness rules, no network
  python backtest_exp13.py run        # fetch (GitHub Actions only: Yahoo), compute, write
"""
import csv
import gzip
import hashlib
import io
import math
import os
import random
import sys
from datetime import datetime, timezone

import experiment_harness as H

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "backtests", "exp13-history")

# ---------------------------------------------------------------- the fixed plan (see HYPOTHESES.md)
WINDOW = ("2005-01-03", "2025-12-31")          # signal dates, inclusive
HALVES = (("2005-01-03", "2014-12-31"), ("2015-01-01", "2025-12-31"))
FETCH_START, FETCH_END = "2003-01-01", "2026-01-31"   # warm-up before, exits after
N = H.V2_COMMON["hold_sessions"]               # 5: exit at the close 5 sessions after entry day
C = H.V2_COMMON["cost_roundtrip"]              # 0.10 pp, charged on the trade only
MAX_PER_DAY = H.V2_COMMON["max_per_day"]       # 10
SESOI = H.V2_COMMON["sesoi"]                   # 0.75 pp
MIN_BARS = 210                                 # the harness keeps names with > 210 bars
BENCH_MIN = 10                                 # the harness needs >= 10 names in a control
ARMS = [("EXP13A-MACD", "macd"), ("EXP13B-RSI2", "rsi2"), ("EXP13C-SUPERTREND", "supertrend"),
        ("EXP13D-SMAPULL", "smapull"), ("EXP13E-BOLLREVERT", "bollrevert"),
        ("EXP13F-NR7", "nr7")]
HARNESS_ENTRY = {"macd": H.entry_macd_cross, "rsi2": H.entry_rsi2,
                 "supertrend": H.entry_supertrend_flip, "smapull": H.entry_sma_pullback,
                 "bollrevert": H.entry_bollinger_revert, "nr7": H.entry_nr7_uptrend}
UNIVERSE_A_FILE = os.path.join("universes", "sp500-2026-11-26.csv")
PIT_FILE = os.path.join("universes", "sp500-pit-fja05680-2026-08-18.csv")


# ---------------------------------------------------------------- indicator series (full history)
# Each is a straight port of the harness function, run once over a name's whole history rather
# than once per day on a trailing window. Same seeds, same recursions. selftest() checks every arm
# bar-for-bar against the harness's own entry functions.
def _sma_series(xs, n):
    out = [None] * len(xs)
    s = 0.0
    for i, x in enumerate(xs):
        s += x
        if i >= n:
            s -= xs[i - n]
        if i >= n - 1:
            # recompute exactly every 500 bars so float drift cannot accumulate
            if i % 500 == 0:
                s = sum(xs[i - n + 1:i + 1])
            out[i] = s / float(n)
    return out


def _ema_full(xs, n):
    """ema_series over the whole list, aligned to xs (None before the seed)."""
    out = [None] * len(xs)
    if len(xs) < n:
        return out
    k = 2.0 / (n + 1.0)
    v = sum(xs[:n]) / float(n)
    out[n - 1] = v
    for i in range(n, len(xs)):
        v = xs[i] * k + v * (1 - k)
        out[i] = v
    return out


def _macd_hist_full(xs, fast=12, slow=26, sig=9):
    ef, es = _ema_full(xs, fast), _ema_full(xs, slow)
    line = [None if es[i] is None else ef[i] - es[i] for i in range(len(xs))]
    start = slow - 1
    sl = [None] * len(xs)
    if len(xs) >= start + sig:
        k = 2.0 / (sig + 1.0)
        v = sum(line[start:start + sig]) / float(sig)
        sl[start + sig - 1] = v
        for i in range(start + sig, len(xs)):
            v = line[i] * k + v * (1 - k)
            sl[i] = v
    return [None if sl[i] is None else line[i] - sl[i] for i in range(len(xs))]


def _rsi_full(xs, p=2):
    out = [None] * len(xs)
    if len(xs) < p + 1:
        return out
    g = [max(xs[i] - xs[i - 1], 0.0) for i in range(1, len(xs))]
    lo = [max(xs[i - 1] - xs[i], 0.0) for i in range(1, len(xs))]
    ag, al = sum(g[:p]) / p, sum(lo[:p]) / p
    out[p] = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
    for j in range(p, len(g)):
        ag = (ag * (p - 1) + g[j]) / p
        al = (al * (p - 1) + lo[j]) / p
        out[j + 1] = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
    return out


def _sd20_full(xs):
    out = [None] * len(xs)
    for i in range(19, len(xs)):
        out[i] = H.stdev_pop(xs[i - 19:i + 1])
    return out


def signal_series(bars):
    """{arm: {bar index: rank_metric}} for every bar where that arm's rule fires, judged on
    bars[:i+1] exactly as the harness judges the latest bar."""
    n = len(bars)
    c = [b["c"] for b in bars]
    s200, s20 = _sma_series(c, 200), _sma_series(c, 20)
    sd20 = _sd20_full(c)
    hist = _macd_hist_full(c)
    r2 = _rsi_full(c, 2)
    trend, line = H.supertrend_state(bars, period=10, mult=3.0)
    out = {a: {} for _, a in ARMS}
    for i in range(n):
        ci = c[i]
        # RSI(2)
        if s200[i] is not None and r2[i] is not None and r2[i] < 5.0 and ci > s200[i]:
            out["rsi2"][i] = r2[i]
        # MACD cross
        # (the harness returns nothing until it has slow + sig + 1 = 36 bars)
        if (i + 1 >= 36 and hist[i] is not None and hist[i - 1] is not None and s200[i] is not None
                and hist[i - 1] <= 0.0 < hist[i] and ci > s200[i]):
            out["macd"][i] = -hist[i]
        # Supertrend flip (no trend filter, >= 60 bars)
        if (i + 1 >= 60 and trend[i] is not None and trend[i - 1] is not None
                and trend[i - 1] == -1 and trend[i] == 1):
            dist = (ci - line[i]) / ci if ci else 0.0
            out["supertrend"][i] = -dist
        # SMA pullback
        if s200[i] is not None and s20[i]:
            lo = bars[i]["l"]
            if ci > s200[i] and lo <= s20[i] < ci:
                out["smapull"][i] = lo / s20[i]
        # Bollinger reversion
        if s200[i] is not None and s20[i] is not None and sd20[i]:
            if ci < s20[i] - 2.0 * sd20[i] and ci > s200[i]:
                out["bollrevert"][i] = (ci - s20[i]) / sd20[i]
        # NR7 in an uptrend
        if s200[i] is not None and i + 1 >= 7:
            rg = [bars[j]["h"] - bars[j]["l"] for j in range(i - 6, i + 1)]
            t = rg[-1]
            if ci > s200[i] and t >= 0 and all(t < r for r in rg[:-1]) and ci:
                out["nr7"][i] = t / ci
    return out


def forward_returns(bars):
    """{bar index: (ret_1d, ret_nd)} gross, in pp: entry at the next open, same-session exit at
    the entry day's close, primary exit at the close N sessions after the entry day — the
    harness's rows[i+1] and rows[i+1+N]."""
    out = {}
    for i in range(len(bars) - 1 - N):
        en = bars[i + 1]["o"]
        if not en:
            continue
        out[i] = ((bars[i + 1]["c"] - en) / en * 100.0, (bars[i + 1 + N]["c"] - en) / en * 100.0)
    return out


# ---------------------------------------------------------------- universes
def load_universe_a():
    with io.open(os.path.join(HERE, UNIVERSE_A_FILE), newline="", encoding="utf-8") as fh:
        return [r["ticker"] for r in csv.DictReader(fh) if r.get("ticker")]


def yahoo_symbol(t):
    return t.strip().replace(".", "-")


def load_pit():
    """[(snapshot date, set of Yahoo symbols)] sorted by date."""
    rows = []
    with io.open(os.path.join(HERE, PIT_FILE), newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append((r["date"], {yahoo_symbol(t) for t in r["tickers"].split(",") if t.strip()}))
    rows.sort()
    return rows


def members_on(pit, d):
    """Members on date d: the latest snapshot dated on or before d."""
    lo, hi = 0, len(pit) - 1
    if d < pit[0][0]:
        return set()
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if pit[mid][0] <= d:
            lo = mid
        else:
            hi = mid - 1
    return pit[lo][1]


# ---------------------------------------------------------------- data
def fetch_history(symbols):
    """Yahoo daily bars, auto_adjust=False (split-adjusted, no dividends) as in the harness.
    Chunks of 100, one retry per chunk. Only runs where Yahoo is reachable (GitHub Actions)."""
    import time
    import yfinance as yf
    out = {}
    for k in range(0, len(symbols), 100):
        part = symbols[k:k + 100]
        for attempt in (1, 2):
            try:
                df = yf.download(part, start=FETCH_START, end=FETCH_END, interval="1d",
                                 auto_adjust=False, group_by="ticker", progress=False,
                                 threads=True)
            except Exception as ex:
                print(f"  chunk {k // 100 + 1} failed ({type(ex).__name__})")
                df = None
            got = {}
            if df is not None:
                for t in part:
                    try:
                        sub = df[t].dropna()
                    except Exception:
                        continue
                    rows = []
                    for idx, r in sub.iterrows():
                        try:
                            rows.append({"d": str(idx)[:10], "o": float(r["Open"]),
                                         "h": float(r["High"]), "l": float(r["Low"]),
                                         "c": float(r["Close"])})
                        except Exception:
                            continue
                    if rows:
                        got[t] = rows
            if len(got) >= 0.5 * len(part) or attempt == 2:
                break
            time.sleep(5)
        out.update(got)
        print(f"  chunk {k // 100 + 1}: {len(got)}/{len(part)} names")
        time.sleep(1)
    return out


def fingerprint(data):
    h = hashlib.sha256()
    for t in sorted(data):
        for b in data[t]:
            h.update(f"{t},{b['d']},{b['o']:.4f},{b['h']:.4f},{b['l']:.4f},{b['c']:.4f}\n"
                     .encode())
    return h.hexdigest()


# ---------------------------------------------------------------- the replay
def prepare(data):
    sigs, fwd, idx = {}, {}, {}
    for t, bars in data.items():
        sigs[t] = signal_series(bars)
        fwd[t] = forward_returns(bars)
        idx[t] = {b["d"]: i for i, b in enumerate(bars)}
    return sigs, fwd, idx


def replay(data, prep, member_fn, tie_order):
    """Returns {arm: [trade dict]} plus counts. member_fn(d) -> set of eligible symbols on d."""
    sigs, fwd, idx = prep
    dates = sorted({b["d"] for bars in data.values() for b in bars
                    if WINDOW[0] <= b["d"] <= WINDOW[1]})
    trades = {a: [] for _, a in ARMS}
    dropped = {a: 0 for _, a in ARMS}
    thin_bench = 0
    for d in dates:
        mem = member_fn(d)
        live = [t for t in mem if t in idx and d in idx[t]]
        # control: every eligible name with a gradable window that day, cost not charged
        bench = {}
        for t in live:
            r = fwd[t].get(idx[t][d])
            if r is not None:
                bench[t] = r
        nb = len(bench)
        s1 = sum(v[0] for v in bench.values())
        sn = sum(v[1] for v in bench.values())
        for _, a in ARMS:
            fires = []
            for t in live:
                i = idx[t][d]
                if i < MIN_BARS:
                    continue
                m = sigs[t][a].get(i)
                if m is not None:
                    fires.append((m, tie_order.get(t, 10 ** 6), t))
            fires.sort()
            for rank, (m, _, t) in enumerate(fires[:MAX_PER_DAY], 1):
                own = bench.get(t)
                if own is None:          # delisted / no exit bar: the harness never grades it
                    dropped[a] += 1
                    continue
                if nb < BENCH_MIN:
                    thin_bench += 1
                    dropped[a] += 1
                    continue
                b1, bn = (s1 - own[0]) / (nb - 1), (sn - own[1]) / (nb - 1)
                r1, rn = own[0] - C, own[1] - C
                trades[a].append({"ticker": t, "date": d, "rank": rank,
                                  "ret_nd": rn, "bench_nd": bn, "excess_nd": rn - bn,
                                  "excess_1d": r1 - b1})
    return trades, dropped, thin_bench, len(dates)


# ---------------------------------------------------------------- statistics
def stats(tr):
    s = {"n": len(tr), "tickers": len({x["ticker"] for x in tr}),
         "sessions": len({x["date"] for x in tr})}
    if len(tr) < 30:
        return s
    x = [r["excess_nd"] for r in tr]
    tk = [r["ticker"] for r in tr]
    se, _ = H.twoway_se(x, tk, [r["date"] for r in tr])
    se_m, _ = H.twoway_se(x, tk, [r["date"][:7] for r in tr])   # robustness: ticker x month
    m = sum(x) / len(x)
    x1 = [r["excess_1d"] for r in tr]
    s.update(mean=m, median=H.median(x), se=se, se_month=se_m,
             ci95=(m - 1.96 * se, m + 1.96 * se), ci90=(m - 1.645 * se, m + 1.645 * se),
             ci95_month=(m - 1.96 * se_m, m + 1.96 * se_m),
             p=(2 * (1 - H._phi(abs(m) / se)) if se > 0 else 1.0),
             mean_1d=sum(x1) / len(x1), mean_ret=sum(r["ret_nd"] for r in tr) / len(tr),
             mean_bench=sum(r["bench_nd"] for r in tr) / len(tr),
             hit=100.0 * sum(1 for v in x if v > 0) / len(x))
    return s


def label(full, h1, h2):
    """Exploratory labels, fixed in the plan. Never verdict language."""
    if "ci95" not in full:
        return "too few trades"
    lo, hi = full["ci95"]
    l9, h9 = full["ci90"]
    if lo > 0 and full["mean"] > 0 and full["median"] > 0 and h1.get("mean", -1) > 0 \
            and h2.get("mean", -1) > 0:
        return "positive in both halves (exploratory)"
    if hi < 0:
        return "negative (exploratory)"
    if -SESOI < l9 and h9 < SESOI:
        return f"inside ±{SESOI:.2f} pp (exploratory)"
    return "unclear (exploratory)"


def split(tr, lo, hi):
    return [r for r in tr if lo <= r["date"] <= hi]


# ---------------------------------------------------------------- run
def _w(path, fields, rows):
    with io.open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def _r(v, k=4):
    return "" if v is None else round(v, k)


def run():
    global OUT
    # The first run's outputs stay as published. A later run never overwrites them: it writes
    # to a dated subfolder beside them.
    if os.path.exists(os.path.join(OUT, "summary.csv")):
        OUT = os.path.join(OUT, "rerun-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M"))
        print(f"first-run outputs exist; this run writes to {OUT}")
    os.makedirs(OUT, exist_ok=True)
    uni_a = load_universe_a()
    pit = load_pit()
    # every symbol that was a member at any point in the window, plus the frozen 503
    first = max(i for i, (d, _) in enumerate(pit) if d <= WINDOW[0])
    ever = set()
    for d, s in pit[first:]:
        if d <= WINDOW[1]:
            ever |= s
    symbols = sorted(set(uni_a) | ever)
    print(f"fetching {len(symbols)} symbols ({len(uni_a)} frozen, {len(ever)} point-in-time)")
    data = fetch_history(symbols)
    data = {t: b for t, b in data.items() if len(b) > MIN_BARS}
    fp = fingerprint(data)
    print(f"usable: {len(data)} symbols; data fingerprint {fp[:16]}")

    # coverage of the point-in-time universe, by year
    have_dates = {t: {b["d"] for b in bars} for t, bars in data.items()}
    all_dates = sorted({d for s in have_dates.values() for d in s
                        if WINDOW[0] <= d <= WINDOW[1]})
    cov = {}
    for d in all_dates:
        mem = members_on(pit, d)
        y = d[:4]
        c = cov.setdefault(y, [0, 0, set(), set()])
        c[0] += len(mem)
        got = {t for t in mem if t in have_dates and d in have_dates[t]}
        c[1] += len(got)
        c[2] |= mem
        c[3] |= (mem - got)
    cov_rows = [{"year": y, "member_days": v[0], "member_days_with_data": v[1],
                 "coverage_pct": _r(100.0 * v[1] / v[0] if v[0] else None, 2),
                 "distinct_members": len(v[2]), "members_missing_any_day": len(v[3])}
                for y, v in sorted(cov.items())]
    _w(os.path.join(OUT, "coverage.csv"), list(cov_rows[0].keys()), cov_rows)
    missing_a = [t for t in uni_a if t not in data]

    order_a = {t: i for i, t in enumerate(uni_a)}
    order_b = {t: i for i, t in enumerate(sorted(ever))}
    set_a = set(uni_a)
    prep = prepare(data)
    print("indicators computed")
    runs = {"A": replay(data, prep, lambda d: set_a, order_a),
            "B": replay(data, prep, lambda d: members_on(pit, d), order_b)}

    summary, by_year = [], []
    for u, (trades, dropped, thin, nd) in runs.items():
        fulls = {}
        for arm_id, a in ARMS:
            tr = trades[a]
            f = stats(tr)
            hs = [stats(split(tr, *h)) for h in HALVES]
            fulls[arm_id] = (f, hs, dropped[a])
            for y in sorted({r["date"][:4] for r in tr}):
                ty = [r for r in tr if r["date"][:4] == y]
                xs = [r["excess_nd"] for r in ty]
                by_year.append({"universe": u, "arm": arm_id, "year": y, "n": len(ty),
                                "mean_excess_nd": _r(sum(xs) / len(xs)),
                                "median_excess_nd": _r(H.median(xs))})
        ps = [fulls[a][0].get("p", 1.0) for a, _ in ARMS]
        adj = H._bh(ps)
        for k, (arm_id, a) in enumerate(ARMS):
            f, hs, dr = fulls[arm_id]
            for period, s in (("2005-2025", f), ("2005-2014", hs[0]), ("2015-2025", hs[1])):
                summary.append({
                    "universe": u, "arm": arm_id, "period": period, "n": s["n"],
                    "tickers": s["tickers"], "sessions": s["sessions"],
                    "mean_excess_nd": _r(s.get("mean")), "median_excess_nd": _r(s.get("median")),
                    "se_twoway": _r(s.get("se")), "ci95_lo": _r(s.get("ci95", (None,))[0]),
                    "ci95_hi": _r(s.get("ci95", (None, None))[1]),
                    "ci90_lo": _r(s.get("ci90", (None,))[0]),
                    "ci90_hi": _r(s.get("ci90", (None, None))[1]),
                    "se_ticker_month": _r(s.get("se_month")),
                    "ci95_month_lo": _r(s.get("ci95_month", (None,))[0]),
                    "ci95_month_hi": _r(s.get("ci95_month", (None, None))[1]),
                    "p_two": _r(s.get("p"), 6),
                    "bh_adjusted_p": _r(adj[k], 6) if period == "2005-2025" else "",
                    "mean_excess_1d": _r(s.get("mean_1d")), "mean_trade_nd": _r(s.get("mean_ret")),
                    "mean_control_nd": _r(s.get("mean_bench")), "pct_trades_beating": _r(s.get("hit"), 2),
                    "signals_not_graded": dr if period == "2005-2025" else "",
                    "label": label(f, hs[0], hs[1]) if period == "2005-2025" else ""})
    _w(os.path.join(OUT, "summary.csv"), list(summary[0].keys()), summary)
    _w(os.path.join(OUT, "by_year.csv"), list(by_year[0].keys()), by_year)
    # the trade log, gzipped, so every number above is re-derivable
    with gzip.open(os.path.join(OUT, "trades.csv.gz"), "wt", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["universe", "arm", "signal_date", "ticker", "rank_in_day", "ret_nd_net",
                    "control_nd", "excess_nd", "excess_1d"])
        for u, (trades, _, _, _) in runs.items():
            for arm_id, a in ARMS:
                for r in trades[a]:
                    w.writerow([u, arm_id, r["date"], r["ticker"], r["rank"], f"{r['ret_nd']:.4f}",
                                f"{r['bench_nd']:.4f}", f"{r['excess_nd']:.4f}",
                                f"{r['excess_1d']:.4f}"])
    meta = {"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "commit": os.environ.get("GITHUB_SHA", "local"),
            "symbols_requested": len(symbols), "symbols_usable": len(data),
            "frozen_list_missing": " ".join(missing_a) or "none",
            "data_fingerprint_sha256": fp,
            "window": f"{WINDOW[0]}..{WINDOW[1]}", "sessions_A": runs["A"][3],
            "sessions_B": runs["B"][3], "thin_control_A": runs["A"][2],
            "thin_control_B": runs["B"][2]}
    try:
        import yfinance
        meta["yfinance"] = yfinance.__version__
    except Exception:
        pass
    _w(os.path.join(OUT, "run.csv"), list(meta.keys()), [meta])
    # log the headline so the run is readable from the Actions log alone
    print("\nuniverse arm label | mean median CI95 n tickers sessions")
    for r in summary:
        if r["period"] == "2005-2025":
            print(f"{r['universe']} {r['arm']:18s} {r['label']:38s} | {r['mean_excess_nd']} "
                  f"{r['median_excess_nd']} [{r['ci95_lo']}, {r['ci95_hi']}] n={r['n']} "
                  f"t={r['tickers']} s={r['sessions']} bh={r['bh_adjusted_p']}")
    for r in cov_rows:
        print(f"coverage {r['year']}: {r['coverage_pct']}% of member-days")
    return 0


# ---------------------------------------------------------------- selftest
def _synthetic(seed, n=900):
    rnd = random.Random(seed)
    p, out = 50.0, []
    for k in range(n):
        drift = 0.0006 if (k // 150) % 2 == 0 else -0.0004
        r = rnd.gauss(drift, 0.018)
        if rnd.random() < 0.02:
            r -= 0.06                       # sharp dips so the oversold rules fire
        o = p * (1 + rnd.gauss(0, 0.004))
        c = p * (1 + r)
        hi = max(o, c) * (1 + abs(rnd.gauss(0, 0.006)) * (0.2 if rnd.random() < 0.1 else 1))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, 0.006)) * (0.2 if rnd.random() < 0.1 else 1))
        out.append({"d": f"D{k:05d}", "o": o, "h": hi, "l": lo, "c": c})
        p = c
    return out


def selftest():
    fired = {a: 0 for _, a in ARMS}
    for seed in (1, 2, 3, 4):
        bars = _synthetic(seed)
        ss = signal_series(bars)
        for _, a in ARMS:
            f = HARNESS_ENTRY[a]
            for i in range(MIN_BARS, len(bars)):
                ok, meta = f(bars[:i + 1])
                mine = ss[a].get(i)
                assert ok == (mine is not None), (a, seed, i, ok, mine)
                if ok:
                    rm = meta["rank_metric"]
                    assert abs(rm - mine) <= 1e-9 * max(1.0, abs(rm)), (a, seed, i, rm, mine)
                    fired[a] += 1
    for a, k in fired.items():
        assert k >= 5, f"selftest data never fired {a} ({k})"
    # returns and control: harness formula on a toy 12-name set
    data = {f"T{j:02d}": _synthetic(100 + j, 260) for j in range(12)}
    d = data["T00"][230]["d"]
    i = 230
    rets = {t: ((b[i + 1 + N]["c"] - b[i + 1]["o"]) / b[i + 1]["o"] * 100.0) for t, b in data.items()}
    want = (rets["T03"] - C) - sum(v for k, v in rets.items() if k != "T03") / 11.0
    fr = {t: forward_returns(b) for t, b in data.items()}
    nb = len(fr)
    sn = sum(fr[t][i][1] for t in fr)
    got = (fr["T03"][i][1] - C) - (sn - fr["T03"][i][1]) / (nb - 1)
    assert abs(want - got) < 1e-9, (want, got)
    assert forward_returns(data["T00"]).get(len(data["T00"]) - 1 - N) is None
    # membership lookup
    pit = [("2005-01-03", {"A"}), ("2005-06-01", {"B"})]
    assert members_on(pit, "2005-03-01") == {"A"} and members_on(pit, "2005-06-01") == {"B"}
    assert members_on(pit, "2004-12-31") == set()
    assert yahoo_symbol("BRK.B") == "BRK-B"
    # labels
    f = {"ci95": (0.1, 0.3), "ci90": (0.12, 0.28), "mean": 0.2, "median": 0.1}
    assert label(f, {"mean": 0.1}, {"mean": 0.3}).startswith("positive")
    assert label(f, {"mean": 0.1}, {"mean": -0.1}).startswith("inside")
    assert label({"ci95": (-0.5, -0.1), "ci90": (-0.4, -0.2), "mean": -0.3, "median": -0.2},
                 {}, {}).startswith("negative")
    assert label({"ci95": (-1.2, 0.9), "ci90": (-1.0, 0.8), "mean": 0, "median": 0},
                 {}, {}).startswith("unclear")
    print(f"backtest_exp13 selftest OK — rules match the harness bar for bar "
          f"({', '.join(f'{a} {k}' for a, k in fired.items())} fires checked)")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "selftest"
    sys.exit(selftest() if cmd == "selftest" else run() if cmd == "run" else 2)
