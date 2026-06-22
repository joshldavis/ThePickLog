#!/usr/bin/env python3
"""
weekly_report.py — autonomous progress + integrity snapshot of the FORWARD LOG.

Reads the canonical, immutable record (picks.csv + outcomes.csv) and writes a
dated markdown report to reports/forward-YYYY-MM-DD.md. Run weekly by GitHub
Actions (.github/workflows/report.yml) so the record's maturation is tracked
hands-free — no Mac, no wifi, no API key (stdlib only).

What it reports:
  1. Maturation — picks logged, graded, pending, date span, grading cadence.
  2. Realized performance — win rate, median/mean net return (open->close and 5d),
     drawdown (MAE) distribution, catastrophic-rug rate.
  3. By-tier table — does the momentum tier separate winners? (forward, out-of-sample)
  4. Finding A out-of-sample check — does higher momentum tier = DEEPER drawdown
     on the LIVE log, as the backtest showed? (the one bankable signal)
  5. Integrity — dup pick_ids, orphan outcomes, win-definition consistency,
     weekday scan-coverage gaps. Flags anything that would fail the
     "a stranger can verify every claim" standard.

NOT investment advice. This summarizes the public record; it makes no prediction.
"""
import csv, os, statistics as st
from collections import defaultdict
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(HERE, "reports")
RUG = -30.0


def _read(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _d(s):
    return date(int(s[0:4]), int(s[5:7]), int(s[8:10]))


def med(xs):
    return st.median(xs) if xs else float("nan")


def mean(xs):
    return st.mean(xs) if xs else float("nan")


def pct(n, d):
    return (100.0 * n / d) if d else float("nan")


def trading_days_between(a, b):
    """Count weekdays in [a, b) — rough scan-coverage check (ignores US holidays)."""
    days, cur = [], a
    while cur < b:
        if cur.weekday() < 5:
            days.append(cur)
        cur += timedelta(days=1)
    return days


def main():
    picks = _read(os.path.join(HERE, "picks.csv"))
    outs = _read(os.path.join(HERE, "outcomes.csv"))
    today = date.today().isoformat()
    L = []
    w = L.append

    w(f"# IgnitionScan — forward-log report · {today}")
    w("")
    w("Auto-generated weekly from the immutable pick log (picks.csv / outcomes.csv). "
      "No predictions; this is the public record summarized. Not investment advice.")
    w("")

    if not picks:
        w("> picks.csv not found or empty.")
        _write(L, today)
        return

    # index
    by_id = {p["pick_id"]: p for p in picks if p.get("pick_id")}
    pick_dates = sorted({_d(p["trading_date"]) for p in picks if p.get("trading_date")})
    graded_ids = {o["pick_id"] for o in outs if o.get("pick_id")}

    # ---- 1. maturation ----
    w("## 1. Maturation")
    w("")
    span = f"{pick_dates[0]} → {pick_dates[-1]}" if pick_dates else "—"
    n_days = len(pick_dates)
    weeks_live = ((pick_dates[-1] - pick_dates[0]).days / 7.0) if len(pick_dates) > 1 else 0
    w(f"- **{len(picks)} picks** logged across **{n_days} scan days** ({span}); ~{weeks_live:.1f} weeks live.")
    w(f"- **{len(outs)} graded**, **{len(picks) - len(graded_ids)} pending** "
      f"(grading runs at 5 trading days).")
    # gate context: strategy wants a 6-8 week graded record before charging
    target_weeks = 8
    w(f"- Toward the pre-billing gate (~{target_weeks} wks of graded record): "
      f"**~{min(weeks_live, target_weeks):.1f} / {target_weeks} weeks**.")
    w("")

    # ---- 2. realized performance ----
    def col(o, k):
        return _f(o.get(k))
    rets_oc = [col(o, "ret_open_close_net") for o in outs if col(o, "ret_open_close_net") is not None]
    rets_5d = [col(o, "ret_open_5dclose_net") for o in outs if col(o, "ret_open_5dclose_net") is not None]
    maes = [col(o, "mae_5d") for o in outs if col(o, "mae_5d") is not None]
    wins = [int(o["win"]) for o in outs if o.get("win") not in (None, "")]
    w("## 2. Realized performance (graded picks)")
    w("")
    if outs:
        w(f"- **Win rate:** {pct(sum(wins), len(wins)):.0f}%  ({sum(wins)}/{len(wins)} positive net, open→close).")
        w(f"- **Open→close net:** median {med(rets_oc):+.1f}%, mean {mean(rets_oc):+.1f}%.")
        w(f"- **5-day net:** median {med(rets_5d):+.1f}%, mean {mean(rets_5d):+.1f}%.")
        w(f"- **Drawdown (MAE 5d):** median {med(maes):+.1f}%, worst {min(maes):+.1f}%.")
        w(f"- **Catastrophic-rug rate (MAE < {RUG:.0f}%):** {pct(sum(1 for m in maes if m < RUG), len(maes)):.0f}%.")
    else:
        w("- No graded outcomes yet.")
    w("")

    # ---- 3. by-tier ----
    w("## 3. By momentum tier (forward, out-of-sample)")
    w("")
    tier_rows = defaultdict(list)
    for o in outs:
        p = by_id.get(o["pick_id"])
        if p:
            tier_rows[p.get("tier", "?")].append(o)
    w("| tier | n | win% | median net | median MAE |")
    w("|---|---|---|---|---|")
    for t in ["A", "B", "C", "D"]:
        g = tier_rows.get(t, [])
        if not g:
            w(f"| {t} | 0 | — | — | — |")
            continue
        ws = [int(x["win"]) for x in g if x.get("win") not in (None, "")]
        oc = [col(x, "ret_open_close_net") for x in g if col(x, "ret_open_close_net") is not None]
        ma = [col(x, "mae_5d") for x in g if col(x, "mae_5d") is not None]
        w(f"| {t} | {len(g)} | {pct(sum(ws), len(ws)):.0f}% | {med(oc):+.1f}% | {med(ma):+.1f}% |")
    w("")

    # ---- 4. Finding A out-of-sample ----
    w("## 4. Finding A check — does hotter momentum = deeper drawdown? (live log)")
    w("")
    hi = [col(o, "mae_5d") for o in outs
          if by_id.get(o["pick_id"], {}).get("tier") in ("A", "B") and col(o, "mae_5d") is not None]
    lo = [col(o, "mae_5d") for o in outs
          if by_id.get(o["pick_id"], {}).get("tier") in ("C", "D") and col(o, "mae_5d") is not None]
    if hi and lo:
        w(f"- High tier (A+B): n={len(hi)}, median MAE {med(hi):+.1f}%, "
          f"rug {pct(sum(1 for m in hi if m < RUG), len(hi)):.0f}%.")
        w(f"- Low tier (C+D): n={len(lo)}, median MAE {med(lo):+.1f}%, "
          f"rug {pct(sum(1 for m in lo if m < RUG), len(lo)):.0f}%.")
        direction = "HOLDS (A+B deeper)" if med(hi) < med(lo) else "does NOT hold yet"
        w(f"- Backtest said A/B draw down deeper. Live log so far: **{direction}** "
          f"(small N — directional only).")
    else:
        w("- Not enough graded picks across tiers yet.")
    w("")

    # ---- 5. integrity ----
    w("## 5. Integrity checks (verifiability standard)")
    w("")
    issues = []
    ids = [p["pick_id"] for p in picks if p.get("pick_id")]
    if len(ids) != len(set(ids)):
        issues.append(f"duplicate pick_ids in picks.csv ({len(ids) - len(set(ids))})")
    orphans = [o["pick_id"] for o in outs if o.get("pick_id") and o["pick_id"] not in by_id]
    if orphans:
        issues.append(f"{len(orphans)} outcome rows reference unknown pick_ids")
    bad_win = 0
    for o in outs:
        r, wv = col(o, "ret_open_close_net"), o.get("win")
        if r is not None and wv not in (None, ""):
            if (r > 0) != (int(wv) == 1):
                bad_win += 1
    if bad_win:
        issues.append(f"{bad_win} rows where win flag disagrees with sign of net return")
    # weekday coverage gap (holidays may cause benign gaps)
    gaps = []
    if len(pick_dates) > 1:
        expected = trading_days_between(pick_dates[0], pick_dates[-1] + timedelta(days=1))
        have = set(pick_dates)
        gaps = [d for d in expected if d not in have]
    if gaps:
        issues.append(f"{len(gaps)} weekday(s) with no scan (may be US market holidays): "
                      + ", ".join(str(d) for d in gaps[:8]) + ("…" if len(gaps) > 8 else ""))
    if issues:
        for i in issues:
            w(f"- ⚠️ {i}")
    else:
        w("- ✅ No integrity issues: unique pick_ids, no orphan outcomes, win flags consistent, no unexplained scan gaps.")
    w("")
    w("---")
    w(f"*Generated by weekly_report.py on {datetime.utcnow().isoformat()}Z. "
      "Forward log is the canonical record; backtest CSVs are gitignored and exploratory.*")

    _write(L, today)


def _write(lines, today):
    os.makedirs(REPORTS, exist_ok=True)
    out = os.path.join(REPORTS, f"forward-{today}.md")
    with open(out, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    # also refresh a stable "latest" pointer for easy phone viewing on GitHub
    with open(os.path.join(REPORTS, "LATEST.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
