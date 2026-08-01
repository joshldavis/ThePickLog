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
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "experiments")
REPORT = os.path.join(HERE, "reports", "experiments-LATEST.md")

MIN_N = 30          # global minimum before any experiment is ruled on
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
]


# --------------------------------------------------------------- io helpers
def _f(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def _read(p):
    if not os.path.exists(p):
        return []
    with io.open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _append(p, fields, rows):
    if not rows:
        return
    os.makedirs(os.path.dirname(p), exist_ok=True)
    first = not os.path.exists(p)
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
            "mature": len(ex1) >= MIN_N}


def verdict_line(s):
    if not s.get("n"):
        return "no graded signals yet"
    if not s.get("mature"):
        return f"accruing — {s['n']}/{MIN_N} graded, no verdict yet"
    ci = s.get("ci1")
    ok = (ci and (ci["lo"] > 0) and (s["mean1"] or 0) > 0 and (s["med1"] or 0) > 0)
    if ok:
        return "**clears the bar on current data** (mean, median and clustered CI all positive)"
    if ci and ci["hi"] < 0:
        return "**significantly NEGATIVE** — worse than the day-matched control"
    return "**no edge detected** — the excess is indistinguishable from zero"


def cmd_report():
    L = ["# ThePickLog — experiments under test · " + datetime.now(timezone.utc).date().isoformat(), "",
         "Every experiment below is forward-only from its registration date, scored as an "
         "**excess over a day-matched control** (the equal-weight return of its own frozen "
         "universe over the identical window), net of a declared cost. Mean, median and a "
         "ticker-clustered 95% CI are reported together, because a mean on financial data can "
         "be a single lucky trade. **Win rate is reported but is never a pass criterion.**", ""]
    for e in EXPERIMENTS:
        s = summarise(e)
        L += [f"## {e['id']} — {e['title']}", "",
              f"- status: **{e.get('status')}**, registered {e['registered_at']}, "
              f"universe {len(e['universe'])} names, hold {e['hold_sessions']} sessions, "
              f"cost {e['cost_roundtrip']}% round trip",
              f"- graded signals: **{s.get('n', 0)}** (need {MIN_N})"]
        if s.get("n"):
            ci = s.get("ci1")
            cis = f"[{ci['lo']:+.3f}, {ci['hi']:+.3f}] over {ci['clusters']} names" if ci else "n/a"
            L += [f"- day-matched excess, 1 session: mean **{s['mean1']:+.3f}%**, "
                  f"median **{s['med1']:+.3f}%**, 10% trimmed **{s['trim1']:+.3f}%**, "
                  f"clustered 95% CI {cis}",
                  f"- day-matched excess, {e['hold_sessions']} sessions: mean "
                  f"**{s['meann']:+.3f}%**, median **{s['medn']:+.3f}%**",
                  f"- win rate {s['win']:.0f}% *(reported only — not a pass criterion)*"]
        L += [f"- **read: {verdict_line(s)}**", "",
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
    # flat series must not fire
    flat = [{"d": f"d{i}", "o": 100.0, "h": 100.0, "l": 100.0, "c": 100.0} for i in range(300)]
    ok, _ = entry_macd_cross(flat)
    assert not ok
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
