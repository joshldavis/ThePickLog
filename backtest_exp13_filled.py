#!/usr/bin/env python3
"""backtest_exp13_filled.py — second run of the EXPLORATORY Experiment 13 backtest, with the
point-in-time universe's missing members filled from free sources.

Plan: HYPOTHESES.md, "Exploratory backtest for Experiment 13 — second run with filled coverage,
plan fixed 2026-11-27". Everything is backtest_exp13.py unchanged (rules, exit, control, cost,
statistics, labels); only universe B's price data is filled:
  1. renamed companies: an old symbol whose Alpaca SIP close matches a current Yahoo symbol's
     close within 1% on >= 95% of >= 60 common dates uses that Yahoo history, all years;
  2. otherwise Alpaca SIP daily bars (split-adjusted, no dividends), 2016 on.
Writes to backtests/exp13-history/run2-filled/. Not a verdict; does not count toward EXP13.

  python backtest_exp13_filled.py selftest   # no network
  python backtest_exp13_filled.py run        # GitHub Actions (Yahoo + Alpaca keys)
"""
import csv
import io
import os
import sys
from datetime import date

import backtest_exp13 as B
import coverage_probe_exp13 as P

OUT2 = os.path.join(B.HERE, "backtests", "exp13-history", "run2-filled")
MATCH_TOL, MATCH_SHARE, MATCH_MIN = 0.01, 0.95, 60
ALPACA_START, ALPACA_END = "2016-01-01", B.FETCH_END
MAP = {}          # old member symbol -> current Yahoo symbol (renames)
FILL_LOG = []

_yahoo_fetch = B.fetch_history
_members_on = B.members_on


def alpaca_rows(bars):
    rows = []
    for b in sorted(bars, key=lambda x: x["t"]):
        try:
            rows.append({"d": b["t"][:10], "o": float(b["o"]), "h": float(b["h"]),
                         "l": float(b["l"]), "c": float(b["c"])})
        except Exception:
            continue
    return rows


def best_segment(rows, spans):
    """Split at gaps over 10 calendar days (a delisting, or a recycled symbol) and keep the
    segment that overlaps the member's own dates most."""
    if not rows:
        return rows
    segs, cur = [], [rows[0]]
    for a, b in zip(rows, rows[1:]):
        if (date.fromisoformat(b["d"]) - date.fromisoformat(a["d"])).days > 10:
            segs.append(cur)
            cur = []
        cur.append(b)
    segs.append(cur)

    def overlap(seg):
        return sum(1 for r in seg if any(x <= r["d"] < y for x, y in spans))
    return max(segs, key=overlap)


def match_rename(arows, ydata):
    """The Yahoo symbol whose close matches these Alpaca closes, or (None, share, n)."""
    if len(arows) < MATCH_MIN:
        return None, 0.0, 0
    step = max(1, len(arows) // 150)
    sample = arows[::step]
    best = (None, 0.0, 0)
    for y, bars in ydata.items():
        idx = {b["d"]: b["c"] for b in bars}
        n = hit = 0
        for r in sample:
            c = idx.get(r["d"])
            if c is None or not r["c"]:
                continue
            n += 1
            if abs(c / r["c"] - 1.0) <= MATCH_TOL:
                hit += 1
        if n >= MATCH_MIN and hit / n > best[1]:
            best = (y, hit / n, n)
    return best if best[1] >= MATCH_SHARE else (None, best[1], best[2])


def filled_fetch(symbols):
    ydata = _yahoo_fetch(symbols)
    usable = {t: b for t, b in ydata.items() if len(b) > B.MIN_BARS}
    spans = P.member_spans(B.load_pit())
    missing = [t for t in sorted(spans) if t not in usable]
    print(f"filling: {len(missing)} point-in-time members with no usable Yahoo history")
    ap = P.alpaca_bars([t.replace("-", ".") for t in missing], ALPACA_START, ALPACA_END)
    if ap is None:
        raise SystemExit("no Alpaca keys: refusing to write a 'filled' run without the fill")
    out = dict(ydata)
    for t in missing:
        arows = best_segment(alpaca_rows(ap.get(t.replace("-", "."), [])), spans[t])
        y, share, n = match_rename(arows, usable)
        if y:
            MAP[t] = y
            out[t] = [dict(b) for b in usable[y]]
            FILL_LOG.append({"symbol": t, "method": "rename", "source_symbol": y,
                             "match_share": round(share, 4), "dates_compared": n,
                             "bars": len(out[t])})
        elif arows:
            out[t] = arows
            FILL_LOG.append({"symbol": t, "method": "alpaca", "source_symbol": t.replace("-", "."),
                             "match_share": round(share, 4), "dates_compared": n,
                             "bars": len(arows)})
        else:
            FILL_LOG.append({"symbol": t, "method": "none", "source_symbol": "",
                             "match_share": "", "dates_compared": "", "bars": 0})
    print(f"filled: {sum(1 for r in FILL_LOG if r['method'] == 'rename')} renames, "
          f"{sum(1 for r in FILL_LOG if r['method'] == 'alpaca')} from Alpaca, "
          f"{sum(1 for r in FILL_LOG if r['method'] == 'none')} still missing")
    return out


def members_dedup(pit, d):
    """Members on d, leaving out an old symbol when the symbol it maps to is listed too."""
    mem = _members_on(pit, d)
    drop = {t for t in mem if t in MAP and MAP[t] in mem}
    return mem - drop if drop else mem


def run():
    B.OUT = OUT2
    if os.path.exists(os.path.join(OUT2, "summary.csv")):
        print("run 2 outputs exist; writing a dated rerun folder beside them")
    B.fetch_history = filled_fetch
    B.members_on = members_dedup
    rc = B.run()
    with io.open(os.path.join(B.OUT, "fill_log.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["symbol", "method", "source_symbol", "match_share",
                                           "dates_compared", "bars"])
        w.writeheader()
        w.writerows(FILL_LOG)
    return rc


def selftest():
    # renames: a series that copies a Yahoo one is matched; an unrelated one is not
    base = B._synthetic(11, 400)
    other = B._synthetic(12, 400)
    ydata = {"NEW": base, "OTH": other}
    arows = [dict(b) for b in base[200:300]]
    y, share, n = match_rename(arows, ydata)
    assert y == "NEW" and share == 1.0 and n >= MATCH_MIN, (y, share, n)
    assert match_rename([dict(b) for b in other[:50]], ydata)[0] is None      # too few dates
    noisy = [dict(b, c=b["c"] * 1.05) for b in base[200:300]]
    assert match_rename(noisy, ydata)[0] is None                               # 5% off
    # segments: a 3-year gap splits the series; the member's segment is kept
    rows = [{"d": "2016-01-04", "o": 1, "h": 1, "l": 1, "c": 1},
            {"d": "2016-01-05", "o": 1, "h": 1, "l": 1, "c": 1},
            {"d": "2019-06-03", "o": 9, "h": 9, "l": 9, "c": 9}]
    seg = best_segment(rows, [("2016-01-01", "2016-12-31")])
    assert [r["d"] for r in seg] == ["2016-01-04", "2016-01-05"]
    # dedup: old symbol dropped only when its target is listed the same day
    MAP.clear()
    MAP["OLD"] = "NEW"
    pit = [("2005-01-03", {"OLD", "X"}), ("2010-01-04", {"OLD", "NEW"})]
    assert members_dedup(pit, "2006-01-03") == {"OLD", "X"}
    assert members_dedup(pit, "2010-06-01") == {"NEW"}
    MAP.clear()
    print("backtest_exp13_filled selftest OK")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "selftest"
    sys.exit(selftest() if cmd == "selftest" else run() if cmd == "run" else 2)
