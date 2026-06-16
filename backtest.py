#!/usr/bin/env python3
"""
IgnitionScan — BACKTEST harness (two-track model, exploratory ONLY)
===================================================================
This is the *fast* track from SYNTHESIS.md §1.2 and VALIDATION-PLAN.md.
It runs the SAME deterministic score (imported from ignitionscan.py — single
source of truth) over historical daily bars to get N up quickly, so you can do
*variable selection*: which inputs / Group-B fields actually separate winners
from losers.

  ⚠️  THIS IS NOT A PERFORMANCE CLAIM.  ⚠️
  - In-sample / overfit-prone by nature.
  - It writes to backtest_*.csv ONLY. It NEVER touches the immutable forward
    log (picks.csv / outcomes.csv). The forward log is the only thing that
    backs any public credibility claim.

Honest reconstruction limits (read these):
  - The live model screens pre-market using *same-day* RVOL. EOD bars can't
    reconstruct that without lookahead, so the backtest uses the PRIOR day's
    volume / 20-day average as an RVOL proxy known at the open. Conservative,
    but it means backtest scores are indicative, not identical to live.
  - Float and short interest are CURRENT values (yfinance .info), applied to
    historical dates. Point-in-time float history isn't available here, so the
    short-interest table is exploratory only.
  - Entry = that day's OPEN, exit = same-day CLOSE, net of the same cost
    haircut as live. MFE/MAE computed over the same 5-trading-day window.

USAGE
  pip install yfinance
  python3 backtest.py run  --period 2y      # build backtest_results.csv
  python3 backtest.py report                # tier table + calibration + SI table

NOTHING HERE IS INVESTMENT ADVICE.
"""

import argparse, csv, os, statistics, sys, time
from datetime import datetime

import ignitionscan as ig  # reuse scoring (score_inputs, tier_of, CONFIG, _f)

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_CSV = os.path.join(HERE, "backtest_results.csv")

FIELDS = [
    "trading_date","ticker","score","tier",
    "float_shares","rvol_proxy","gap_pct","price_open",
    "short_interest_pct_current",
    "ret_open_close_net","ret_open_5dclose_net","mfe_5d","mae_5d","win",
]

GRADE_DAYS = ig.CONFIG["GRADE_AFTER_DAYS"]
HAIRCUT    = ig.CONFIG["COST_HAIRCUT_PCT"]
FILTERS    = ig.CONFIG["FILTERS"]


def _avg20(vols, i):
    """20-day average volume using days strictly BEFORE i (no lookahead)."""
    lo = max(0, i - 20)
    w = vols[lo:i]
    return sum(w) / len(w) if w else 0.0


def cmd_run(period="2y", universe=None):
    yf = ig._yf()
    universe = universe or ig.CONFIG["UNIVERSE"]
    rows = []
    for sym in universe:
        try:
            tk = yf.Ticker(sym)
            df = tk.history(period=period, auto_adjust=False)
            if df is None or len(df) < 30:
                print(f"  skip {sym}: insufficient history"); continue
            df = df.reset_index()
            # current short interest as a (rough) proxy for the SI variable table
            si = None
            try:
                v = tk.info.get("shortPercentOfFloat")
                si = round(v * 100, 2) if isinstance(v, (int, float)) else ""
                flt = tk.info.get("floatShares") or tk.info.get("sharesOutstanding") or 0
            except Exception:
                si, flt = "", 0
            opens  = df["Open"].tolist();  closes = df["Close"].tolist()
            highs  = df["High"].tolist();  lows   = df["Low"].tolist()
            vols   = df["Volume"].tolist()
            dates  = df["Date"].astype(str).str[:10].tolist()
            n = len(df)
            picks_here = 0
            # need 20 prior days for the avg, and GRADE_DAYS forward bars to grade
            for i in range(20, n - GRADE_DAYS - 1):
                op, prev_close = opens[i], closes[i - 1]
                prior_vol = vols[i - 1]
                avg = _avg20(vols, i)
                if not (op and prev_close and avg):
                    continue
                s = ig.score_inputs(op, prev_close, prior_vol, avg, flt)
                if not (FILTERS["price_min"] <= s["price_at_screen"] <= FILTERS["price_max"]):
                    continue
                # grade forward, identical basis to live grader
                win_o = op
                same_close = closes[i]
                close_5d = closes[i + GRADE_DAYS]
                hi = max(highs[i:i + GRADE_DAYS + 1]); lo = min(lows[i:i + GRADE_DAYS + 1])
                roc = (same_close - win_o) / win_o * 100 - HAIRCUT
                r5d = (close_5d - win_o) / win_o * 100 - HAIRCUT
                rows.append({
                    "trading_date": dates[i], "ticker": sym,
                    "score": s["score"], "tier": s["tier"],
                    "float_shares": s["float_shares"], "rvol_proxy": s["rvol"],
                    "gap_pct": s["gap_pct"], "price_open": round(op, 4),
                    "short_interest_pct_current": si,
                    "ret_open_close_net": round(roc, 2), "ret_open_5dclose_net": round(r5d, 2),
                    "mfe_5d": round((hi - win_o) / win_o * 100, 2),
                    "mae_5d": round((lo - win_o) / win_o * 100, 2),
                    "win": "1" if roc > 0 else "0",
                })
                picks_here += 1
            print(f"  {sym}: {picks_here} backtest picks")
            time.sleep(0.4)
        except Exception as e:
            print(f"  skip {sym}: {type(e).__name__} {str(e)[:80]}")
    if not rows:
        sys.exit("No backtest rows produced (data feed empty / throttled).")
    with open(RESULTS_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    print(f"\nWrote {len(rows)} backtest rows -> {RESULTS_CSV}")
    print("⚠️  In-sample / overfit-prone. Exploratory variable selection ONLY — not a performance claim.")


def _read():
    if not os.path.exists(RESULTS_CSV):
        sys.exit("No backtest_results.csv — run `python3 backtest.py run` first.")
    with open(RESULTS_CSV, newline="") as f:
        return list(csv.DictReader(f))


def _f(x):
    try: return float(x)
    except (TypeError, ValueError): return None


def _stats(vals):
    pos = 100 * sum(1 for x in vals if x > 0) / len(vals)
    return len(vals), statistics.mean(vals), statistics.median(vals), pos


def cmd_report():
    rows = _read()
    rets = [(_f(r["ret_open_close_net"]), r) for r in rows]
    rets = [(v, r) for v, r in rets if v is not None]
    print(f"\nBACKTEST report — {len(rets)} graded picks   (⚠️ in-sample, overfit-prone)")

    # tier table with downside
    print(f"\nTier table — net open->close (after {HAIRCUT}% haircut)")
    print(f"{'TIER':<6}{'N':>6}{'MEAN%':>9}{'MEDIAN%':>10}{'WIN%':>8}{'MEAN_MAE%':>11}")
    for t in ["A", "B", "C", "D"]:
        v = [val for val, r in rets if r["tier"] == t]
        m = [_f(r["mae_5d"]) for val, r in rets if r["tier"] == t and _f(r["mae_5d"]) is not None]
        if not v: print(f"{t:<6}{0:>6}{'-':>9}{'-':>10}{'-':>8}{'-':>11}"); continue
        n, mean, med, pos = _stats(v)
        mae = statistics.mean(m) if m else float("nan")
        print(f"{t:<6}{n:>6}{mean:>9.2f}{med:>10.2f}{pos:>8.1f}{mae:>11.2f}")

    # calibration by score band
    bands = [(0, 45), (45, 55), (55, 65), (65, 75), (75, 85), (85, 101)]
    print("\nCalibration — % positive by score band")
    print(f"{'BAND':<9}{'N':>6}{'%POS':>8}{'MEAN%':>9}")
    for b in bands:
        v = [val for val, r in rets if (_f(r['score']) is not None and b[0] <= _f(r['score']) < b[1])]
        lbl = f"{b[0]}-{b[1]-1}"
        if not v: print(f"{lbl:<9}{0:>6}{'-':>8}{'-':>9}"); continue
        n, mean, med, pos = _stats(v)
        print(f"{lbl:<9}{n:>6}{pos:>8.1f}{mean:>9.2f}")

    # short-interest variable table (VALIDATION-PLAN 3.2) — current-SI proxy
    print("\nShort-interest table (⚠️ CURRENT SI applied to historical dates — indicative only)")
    print(f"{'SI BUCKET':<11}{'N':>6}{'%POS':>8}{'MEAN%':>9}")
    sib = [("<5%", 0, 5), ("5-15%", 5, 15), ("15-30%", 15, 30), (">30%", 30, 1e9)]
    for lbl, lo, hi in sib:
        v = [val for val, r in rets
             if (_f(r.get("short_interest_pct_current")) is not None
                 and lo <= _f(r["short_interest_pct_current"]) < hi)]
        if not v: print(f"{lbl:<11}{0:>6}{'-':>8}{'-':>9}"); continue
        n, mean, med, pos = _stats(v)
        print(f"{lbl:<11}{n:>6}{pos:>8.1f}{mean:>9.2f}")
    print("\nUse this to DECIDE WHICH VARIABLES EARN A PLACE IN THE SCORE (VALIDATION-PLAN 3.2),")
    print("then confirm on the immutable FORWARD log before believing it. Backtest != proof.")


def main():
    ap = argparse.ArgumentParser(description="IgnitionScan backtest harness (exploratory, in-sample)")
    sub = ap.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run"); r.add_argument("--period", default="2y")
    sub.add_parser("report")
    args = ap.parse_args()
    if args.command == "run":   cmd_run(period=args.period)
    elif args.command == "report": cmd_report()


if __name__ == "__main__":
    main()
