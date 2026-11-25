#!/usr/bin/env python3
"""
null_bounds.py — what a locked harness verdict rules out, and what it could have detected.

READ-ONLY. Re-derives, from the committed outcomes file, the numbers the experiment pages quote
beside a locked "NO EDGE DETECTED" verdict. It never writes to experiments/, never re-decides a
verdict and never changes a locked number: it uses exactly the first `n` outcome rows that the
locked verdict saw (the outcomes file is append-only), as family_verdict.harness_p does.

What it reports, for the same-session excess (the registered primary):
  * the locked mean, median and ticker-clustered 95% CI (the harness's own bootstrap, BOOT=3000,
    SEED=7), reproduced as a check;
  * a date-clustered 95% CI (CR1 standard error, t with G-1 df) — same-day signals share a
    market session, and in EXP03 the within-date correlation is positive while the within-ticker
    correlation is not, so this is the more conservative interval;
  * a 90% ticker-clustered interval — the two one-sided tests (TOST) bound: the verdict
    establishes equivalence to zero only for bounds at least this wide;
  * the minimum detectable effect at 80% power, and power at a few true edge sizes, from the
    bootstrap standard error (normal approximation);
  * the secondary hold-period excess, and the mean excess with the cost charged to the strategy
    only (the control in the harness pays the same cost, so it cancels in `excess_1d`).

    python3 null_bounds.py --id EXP03-MACD
    python3 null_bounds.py --selftest
"""
import argparse
import math
import os
import random
import statistics as st
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import experiment_harness as H  # noqa: E402

Z975, Z95, Z80 = 1.959964, 1.644854, 0.841621
T975 = {d: v for d, v in [(10, 2.228), (15, 2.131), (20, 2.086), (25, 2.060), (30, 2.042),
                         (40, 2.021), (60, 2.000), (120, 1.980)]}


def _t975(df):
    """Two-sided 95% t critical value, rounded to the tabled df at or BELOW `df` (conservative:
    never smaller than the exact value)."""
    below = [k for k in T975 if k <= df]
    return T975[max(below)] if below else 2.262


def _phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def boot_reps(vals, keys, B=H.BOOT, seed=H.SEED):
    """Identical resampling to experiment_harness.cluster_ci, returning the replicate means."""
    by = defaultdict(list)
    for v, k in zip(vals, keys):
        by[k].append(v)
    ks = list(by)
    rnd = random.Random(seed)
    out = []
    for _ in range(B):
        s = []
        for _ in range(len(ks)):
            s.extend(by[ks[rnd.randrange(len(ks))]])
        out.append(sum(s) / float(len(s)))
    out.sort()
    return out


def cr1_se(vals, keys):
    m = sum(vals) / len(vals)
    g = defaultdict(float)
    for v, k in zip(vals, keys):
        g[k] += v - m
    G = len(g)
    return math.sqrt(G / (G - 1.0) * sum(u * u for u in g.values())) / len(vals), G


def bounds(rows, cost):
    x = [float(r["excess_1d"]) for r in rows]
    tk = [r["ticker"] for r in rows]
    dt = [r["signal_date"] for r in rows]
    n, m = len(x), sum(x) / len(x)
    reps = boot_reps(x, tk)
    q = lambda p: reps[min(len(reps) - 1, int(p * len(reps)))]
    se_b = st.stdev(reps)
    se_d, gd = cr1_se(x, dt)
    xn = [float(r["excess_nd"]) for r in rows]
    cin = H.cluster_ci(xn, tk)
    power = {d: 1 - _phi(Z975 - d / se_b) + _phi(-Z975 - d / se_b) for d in (0.05, 0.10, 0.20, 0.50)}
    return {
        "n": n, "clusters": len(set(tk)), "dates": gd, "mean": m, "median": H.median(x),
        "sd": st.stdev(x), "ci95_ticker": (q(0.025), q(0.975)), "ci90_ticker": (q(0.05), q(0.95)),
        "se_boot": se_b, "se_date": se_d,
        "ci95_date": (m - _t975(gd - 1) * se_d, m + _t975(gd - 1) * se_d),
        "mde80": (Z975 + Z80) * se_b, "power": power,
        "hold_mean": sum(xn) / len(xn), "hold_median": H.median(xn),
        "hold_ci95": (cin["lo"], cin["hi"]) if cin else None,
        "mean_vs_passive": m - cost,
    }


def run(eid):
    e = next((x for x in H.EXPERIMENTS if x["id"] == eid), None)
    lk = H.locked_verdicts().get(eid)
    if e is None or lk is None:
        print(f"{eid}: no locked verdict — nothing to bound (this script never computes one)")
        return 1
    allr = H._read(H.out_path(e))
    n = int(lk["n"])
    rows = allr[:n]
    if len(rows) != n or any((r.get("graded_at") or "")[:10] > lk["locked_at"] for r in rows):
        print(f"{eid}: outcome rows do not match the locked sample — refusing")
        return 1
    b = bounds(rows, e["cost_roundtrip"])
    f = lambda v: f"{v:+.3f}"
    print(f"{eid} — locked {lk['locked_at']}, n={b['n']} over {b['clusters']} names, "
          f"{b['dates']} signal dates")
    print(f"  check vs locked row: mean {f(b['mean'])} ({lk['mean1']}), median {f(b['median'])} "
          f"({lk['med1']}), ticker-clustered 95% CI [{f(b['ci95_ticker'][0])}, "
          f"{f(b['ci95_ticker'][1])}] ([{lk['ci_lo']}, {lk['ci_hi']}])")
    print(f"  sd per trade {b['sd']:.3f} pp; bootstrap se {b['se_boot']:.3f}; "
          f"date-clustered se {b['se_date']:.3f}")
    print(f"  date-clustered 95% CI [{f(b['ci95_date'][0])}, {f(b['ci95_date'][1])}]")
    print(f"  90% ticker-clustered CI (TOST bound) [{f(b['ci90_ticker'][0])}, "
          f"{f(b['ci90_ticker'][1])}]")
    print(f"  minimum detectable effect, 80% power, two-sided .05: {b['mde80']:.2f} pp")
    print("  power at a true edge of " + ", ".join(
        f"{d:.2f} pp = {p:.0%}" for d, p in b["power"].items()))
    hc = b["hold_ci95"]
    print(f"  {e['hold_sessions']}-session excess: mean {f(b['hold_mean'])}, median "
          f"{f(b['hold_median'])}, 95% CI [{f(hc[0])}, {f(hc[1])}]" if hc else "")
    print(f"  mean excess with cost on the strategy only (vs a passive holder): "
          f"{f(b['mean_vs_passive'])}")
    return 0


def _selftest():
    rnd = random.Random(1)
    rows = [{"ticker": f"T{i % 30}", "signal_date": f"D{i % 34}",
             "excess_1d": rnd.gauss(0, 1.4), "excess_nd": rnd.gauss(0, 4.0)} for i in range(60)]
    b = bounds(rows, 0.10)
    assert b["ci95_ticker"][0] < b["mean"] < b["ci95_ticker"][1]
    assert b["ci90_ticker"][0] > b["ci95_ticker"][0] and b["ci90_ticker"][1] < b["ci95_ticker"][1]
    assert 0.2 < b["mde80"] < 1.0, b["mde80"]
    assert b["power"][0.05] < b["power"][0.50]
    assert abs(b["mean_vs_passive"] - (b["mean"] - 0.10)) < 1e-12
    # parity with the harness interval on the same data
    ci = H.cluster_ci([r["excess_1d"] for r in rows], [r["ticker"] for r in rows])
    assert abs(ci["lo"] - b["ci95_ticker"][0]) < 1e-9 and abs(ci["hi"] - b["ci95_ticker"][1]) < 1e-9
    print("null_bounds selftest PASS — bootstrap parity with harness, TOST nesting, power monotone")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default="EXP03-MACD")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(_selftest() if a.selftest else run(a.id))
