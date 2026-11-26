"""Experiment 01 (H-EX1) verdict, recomputed with the pre-open seal. Read-only.

The published verdict (2026-07-29: n=309, delta -3.0pp, 95% CI [-4.4, -1.5]) predates
the 2026-08-04 pre-open seal. This script reproduces that figure from the public CSVs,
then applies the same seal every other figure on the site uses (market_time.split_timely)
and prints both. It writes nothing.

Sample: v0.2 picks, trading_date after 2026-06-23 (registration), graded on or before
2026-07-29 (verdict date), with same-day close, 5-day close and mfe_5d all present.
H-EX1 arm: +8% net if mfe_5d >= 10, else the 5-day close. Baseline: same-day close.
CI: pooled normal approximation on per-trade differences (not ticker-clustered).

Run: python3 exp01_preopen_recheck_2026_11_26.py
"""
import csv, os, statistics as st
from market_time import split_timely

HERE = os.path.dirname(os.path.abspath(__file__))
REG, VERDICT = "2026-06-23", "2026-07-29"


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def delta(rows):
    d = [a - b for a, b in rows]
    n, mu = len(d), st.mean(d)
    se = st.stdev(d) / n ** 0.5
    return n, mu, mu - 1.96 * se, mu + 1.96 * se


def main():
    picks = [p for p in csv.DictReader(open(os.path.join(HERE, "picks.csv")))
             if (p.get("model_version") or "").startswith("v0.2")]
    timely, _late = split_timely(picks)
    timely_ids = {p["pick_id"] for p in timely}
    by_id = {p["pick_id"]: p for p in picks}
    raw, sealed = [], []
    for o in csv.DictReader(open(os.path.join(HERE, "outcomes.csv"))):
        p = by_id.get(o["pick_id"])
        if not p or p["trading_date"] <= REG or o["graded_at"][:10] > VERDICT:
            continue
        c0, mfe, c5 = _f(o["ret_open_close_net"]), _f(o["mfe_5d"]), _f(o["ret_open_5dclose_net"])
        if None in (c0, mfe, c5):
            continue
        pair = (8.0 if mfe >= 10 else c5, c0)
        raw.append(pair)
        if o["pick_id"] in timely_ids:
            sealed.append(pair)
    for label, rows in (("as published (no seal)", raw), ("pre-open seal applied", sealed)):
        n, mu, lo, hi = delta(rows)
        print(f"{label:24s} n={n}  delta={mu:+.2f}pp  95% CI [{lo:+.1f}, {hi:+.1f}]")


if __name__ == "__main__":
    main()
