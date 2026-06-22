#!/usr/bin/env python3
"""
compare_asof.py — score the as-of-date test against the pre-registered bars in
TEST-PLAN-quality-downside.md, and show how much look-ahead actually moved things.

Reads:
  backtest_quality_asof.csv   (from: asof_grader.py --backtest ...)  REQUIRED
  backtest_quality.csv        (from: backtest_quality.py)            optional, for the
                                                                     current-vs-as-of flip view

Does three things:
  1. Per-ticker CURRENT vs AS-OF grade — how often the look-ahead grade differs.
  2. The pre-registered §1.1 test on the AS-OF grades, with TICKER-CLUSTERED stats
     (the fix for the effective-N=14 error) + a cluster bootstrap CI on the gaps.
  3. A held-out time split (first half vs second half of the window).
Then prints PASS/FAIL against the four success bars and a one-line verdict.

Offline (reads CSVs only). NOT investment advice; backtest is in-sample/exploratory.
"""
import csv, os, random, statistics as st
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ASOF = os.path.join(HERE, "backtest_quality_asof.csv")
CUR = os.path.join(HERE, "backtest_quality.csv")
SAFE = {"Green", "Yellow"}
RISKY = {"Red", "Black"}
RUG = -30.0           # catastrophic-rug threshold (MAE < -30%)
MIN_GAP = 5.0         # bar #2: median-MAE gap, percentage points
MIN_PICKS, MIN_BUCKET, MIN_TICKERS = 200, 30, 25  # bar #3
B = 10000             # cluster-bootstrap resamples
random.seed(7)


def med(xs): return st.median(xs) if xs else float("nan")


def load(path):
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        out = []
        for r in csv.DictReader(fh):
            try:
                r["mae_5d"] = float(r["mae_5d"])
            except (TypeError, ValueError):
                continue
            out.append(r)
        return out


def bucket(label):
    if label in SAFE:
        return "Safe"
    if label in RISKY:
        return "Risky"
    return None


def rug_rate(xs):
    return 100.0 * sum(1 for x in xs if x < RUG) / len(xs) if xs else float("nan")


def cluster_bootstrap_gap(by_ticker, stat):
    """Resample TICKERS with replacement; recompute (safe_stat - risky_stat). 95% CI."""
    tickers = list(by_ticker)
    gaps = []
    for _ in range(B):
        safe, risky = [], []
        for _ in range(len(tickers)):
            t = random.choice(tickers)
            for lab_bucket, mae in by_ticker[t]:
                (safe if lab_bucket == "Safe" else risky).append(mae)
        if safe and risky:
            gaps.append(stat(safe) - stat(risky))
    gaps.sort()
    if not gaps:
        return (float("nan"), float("nan"), float("nan"))
    lo = gaps[int(0.025 * len(gaps))]
    hi = gaps[int(0.975 * len(gaps))]
    return (st.median(gaps), lo, hi)


def section(title): print("\n" + title + "\n" + "-" * len(title))


def main():
    asof = load(ASOF)
    if not asof:
        print(f"!! {ASOF} not found. Run first:\n   python3 asof_grader.py --backtest backtest_results.csv")
        return
    cur = load(CUR)

    # ---- 1. current vs as-of grade per ticker ----
    section("1. Current vs as-of grade (did removing look-ahead change the grade?)")
    cur_label = {}
    for r in cur:
        cur_label.setdefault(r["ticker"], r.get("q_label", ""))
    asof_labels = defaultdict(set)
    for r in asof:
        asof_labels[r["ticker"]].add(r.get("asof_label", "Ungraded"))
    print(f"{'ticker':<7}{'current':<9}{'as-of label(s) over window':<32}{'changed?'}")
    flips = 0
    for t in sorted(asof_labels):
        a = sorted(asof_labels[t])
        c = cur_label.get(t, "—")
        changed = "yes" if (c not in a or len(a) > 1) else ""
        if changed:
            flips += 1
        print(f"{t:<7}{c:<9}{', '.join(a):<32}{changed}")
    print(f"\n{flips}/{len(asof_labels)} tickers had an as-of grade that differs from the current grade "
          f"(or shifted mid-window) — that is the look-ahead the first run baked in.")

    # ---- 2. pre-registered §1.1 test on AS-OF grades ----
    section("2. §1.1 test on AS-OF grades — ticker-clustered")
    rows = [(r["ticker"], bucket(r.get("asof_label", "")), r["mae_5d"],
             r.get("trading_date", "")) for r in asof]
    rows = [r for r in rows if r[1]]  # graded into Safe/Risky only
    safe_mae = [m for _, b, m, _ in rows if b == "Safe"]
    risky_mae = [m for _, b, m, _ in rows if b == "Risky"]
    by_ticker = defaultdict(list)
    for tkr, b, m, _ in rows:
        by_ticker[tkr].append((b, m))

    n_safe_tk = len({t for t in by_ticker if any(b == "Safe" for b, _ in by_ticker[t])})
    n_risky_tk = len({t for t in by_ticker if any(b == "Risky" for b, _ in by_ticker[t])})

    print(f"{'group':<8}{'nPicks':>7}{'nTickers':>9}{'medMAE':>9}{'rug<-30%':>10}")
    for name, xs, ntk in (("Safe", safe_mae, n_safe_tk), ("Risky", risky_mae, n_risky_tk)):
        print(f"{name:<8}{len(xs):>7}{ntk:>9}{med(xs):>9.2f}{rug_rate(xs):>9.1f}%")

    # per-ticker (the honest unit): each ticker -> its median MAE within each bucket
    per_tk_safe = [med([m for b, m in v if b == "Safe"]) for v in by_ticker.values() if any(b == "Safe" for b, _ in v)]
    per_tk_risky = [med([m for b, m in v if b == "Risky"]) for v in by_ticker.values() if any(b == "Risky" for b, _ in v)]
    print(f"\nPer-ticker median-of-medians:  Safe={med(per_tk_safe):.2f} (n={len(per_tk_safe)})  "
          f"Risky={med(per_tk_risky):.2f} (n={len(per_tk_risky)})")

    # gaps (positive = Safe shallower = hypothesis-consistent)
    mae_gap = med(safe_mae) - med(risky_mae)
    rug_gap = rug_rate(risky_mae) - rug_rate(safe_mae)  # positive = risky rugs more = hypothesis-consistent
    g_med, g_lo, g_hi = cluster_bootstrap_gap(by_ticker, med)
    print(f"\nMedian-MAE gap (Safe − Risky): {mae_gap:+.2f} pp   "
          f"cluster-bootstrap 95% CI [{g_lo:+.2f}, {g_hi:+.2f}]")
    print(f"Rug-rate gap (Risky − Safe):   {rug_gap:+.2f} pp   "
          f"(positive favors the hypothesis; negative is the inverse seen in §6)")

    # ---- 3. held-out time split ----
    section("3. Held-out time split (robustness)")
    dates = sorted({d for _, _, _, d in rows if d})
    split = dates[len(dates) // 2] if dates else None
    def gap_for(subset):
        s = [m for _, b, m, d in subset if b == "Safe"]
        r = [m for _, b, m, d in subset if b == "Risky"]
        return (med(s) - med(r)) if (s and r) else float("nan")
    if split:
        first = [r for r in rows if r[3] < split]
        second = [r for r in rows if r[3] >= split]
        g1, g2 = gap_for(first), gap_for(second)
        print(f"split @ {split}   first-half gap={g1:+.2f}   second-half gap={g2:+.2f}")
        robust = (g1 == g1 and g2 == g2 and (g1 > 0) == (g2 > 0))
    else:
        robust = False
        print("no dates — cannot split")

    # ---- verdict against the four bars ----
    section("VERDICT vs pre-registered success bars (TEST-PLAN §1)")
    h1 = mae_gap > 0
    h2 = rug_gap > 0
    n_total = len(safe_mae) + len(risky_mae)
    power = (n_total >= MIN_PICKS and len(safe_mae) >= MIN_BUCKET and len(risky_mae) >= MIN_BUCKET
             and n_safe_tk >= MIN_TICKERS and n_risky_tk >= MIN_TICKERS)
    magnitude = abs(mae_gap) >= MIN_GAP and h1
    ci_clears = (g_lo > 0)  # CI excludes zero on the hypothesis side

    def mark(ok): return "PASS" if ok else "FAIL"
    print(f"  [{mark(h1 and h2)}] Direction — H1 (Safe shallower) {h1} & H2 (Risky rugs more) {h2}")
    print(f"  [{mark(magnitude)}] Magnitude — |median gap| {abs(mae_gap):.1f}pp ≥ {MIN_GAP}pp in hypothesized direction")
    print(f"  [{mark(power)}] Power — picks {n_total}≥{MIN_PICKS}, per-bucket ≥{MIN_BUCKET}, "
          f"tickers/bucket {n_safe_tk}/{n_risky_tk} ≥ {MIN_TICKERS}")
    print(f"  [{mark(robust)}] Robustness — same sign across the held-out time split")
    print(f"  (supporting) cluster-bootstrap CI excludes zero on hypothesis side: {mark(ci_clears)}")

    all_pass = h1 and h2 and magnitude and power and robust
    print("\nHEADLINE CLAIM:", "EARNED — reframe to the downside-filter claim." if all_pass
          else "NOT earned. Keep quality as a 'real business?' descriptor; do not ship a quality→drawdown claim.")
    if not power:
        print("Most likely blocker: POWER. The 16-seed universe can't hit ≥25 distinct tickers/bucket — "
              "that's Phase 2 (full-market screen), exactly as TEST-PLAN predicted.")


if __name__ == "__main__":
    main()
