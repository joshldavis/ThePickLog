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

# Reuse the audited exit-rule core so §4e (H-EX2) can't diverge from exit_sim.py.
# exit_sim imports only stdlib at module level (yfinance is lazy), so this stays
# stdlib-only and never touches the network on import.
try:
    from exit_sim import net as exit_net, load_paths as _load_paths
except Exception:  # pragma: no cover — report must run even if exit_sim is unavailable
    exit_net = None
    _load_paths = None


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
    # A "void" outcome (e.g. a phantom market-holiday scan) is resolved but carries no return,
    # so it must NOT count as a real grade. Real grades have a non-empty open→close return.
    n_void = sum(1 for o in outs if (o.get("note") or "").startswith("VOID"))
    n_real = sum(1 for o in outs if (o.get("ret_open_close_net") or "") != "")
    w(f"- **{len(picks)} picks** logged across **{n_days} scan days** ({span}); ~{weeks_live:.1f} weeks live.")
    w(f"- **{n_real} graded**, **{len(picks) - len(graded_ids)} pending**"
      + (f", **{n_void} voided** (phantom/holiday rows — excluded from every stat below)" if n_void else "")
      + " (grading runs at 5 trading days).")
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

    # ---- 4b. follow-the-screen reality check + Finding-A counterfactual ----
    w("## 4b. Would following the screen have paid? (personal reality check)")
    w("")
    # equal-weight: average net 5-day return per pick = avg % P&L if you took every pick same size
    r5_all = [(by_id.get(o["pick_id"], {}).get("tier"), col(o, "ret_open_5dclose_net"))
              for o in outs if col(o, "ret_open_5dclose_net") is not None]
    if r5_all:
        allr = [r for _, r in r5_all]
        skip_ab = [r for t, r in r5_all if t not in ("A", "B")]  # Finding-A rule: skip the hot names
        only_ab = [r for t, r in r5_all if t in ("A", "B")]
        w("Equal-weight, every graded pick held to the 5-day close, net of the 2% cost haircut "
          "(an honest 'if I'd taken them all' proxy — not advice):")
        w("")
        w("| strategy | n | avg net/trade | median | win% |")
        w("|---|---|---|---|---|")
        def line(name, xs):
            if not xs:
                w(f"| {name} | 0 | — | — | — |"); return
            wr = pct(sum(1 for r in xs if r > 0), len(xs))
            w(f"| {name} | {len(xs)} | {mean(xs):+.1f}% | {med(xs):+.1f}% | {wr:.0f}% |")
        line("Take every pick", allr)
        line("Skip A/B (Finding-A rule)", skip_ab)
        line("Only A/B (the hot names)", only_ab)
        w("")
        if skip_ab and only_ab:
            delta = mean(skip_ab) - mean(allr)
            verdict = (f"Skipping the hot A/B names changes avg net/trade by **{delta:+.1f}pp** vs taking everything"
                       f" — {'Finding A pays as a filter here' if delta > 0 else 'no edge from the filter yet'} "
                       "(small N, directional).")
            w(verdict)
    else:
        w("- No 5-day-graded picks yet.")
    w("")

    # ---- 4c. pre-registered filter hypotheses (HYPOTHESES.md) ----
    REG = "2026-06-22"   # registration date — only later picks are the out-of-sample test
    w("## 4c. Pre-registered filters (tracking vs HYPOTHESES.md)")
    w("")
    w(f"Each filter **skips** some picks; we want the kept subset to beat baseline on avg "
      f"net/trade. Registered {REG} from an in-sample cut — only **post-{REG}** picks are the "
      f"honest test. Both windows shown; judge on the post-registration column as it grows.")
    w("")

    def keep(p, fid):
        pr, fl, gp, t = _f(p.get("price_at_screen")), _f(p.get("float_shares")), _f(p.get("gap_pct")), p.get("tier")
        if fid == "F1":    return pr is None or pr >= 1.0
        if fid == "F2":    return fl is None or fl < 3e6
        if fid == "F3":    return gp is None or gp < 20
        if fid == "F4":    return t not in ("A", "B")
        if fid == "CLEAN": return all(keep(p, x) for x in ("F1", "F2", "F3", "F4"))
        return True

    def arm(fid, post_only):
        kept = []
        for o in outs:
            p = by_id.get(o["pick_id"])
            r = col(o, "ret_open_close_net")
            if not p or r is None:
                continue
            if post_only and not (p.get("trading_date", "") > REG):
                continue
            if fid == "ALL" or keep(p, fid):
                kept.append((r, int(o["win"]) if o.get("win") not in (None, "") else (1 if r > 0 else 0)))
        return kept

    def fmt(kept):
        if not kept:
            return "n=0", "—", "—"
        rs = [r for r, _ in kept]
        return f"n={len(kept)}", f"{pct(sum(wv for _, wv in kept), len(kept)):.0f}%", f"{mean(rs):+.1f}%"

    labels = {"ALL": "Baseline (all picks)", "F1": "H-F1 skip <$1", "F2": "H-F2 skip float≥3M",
              "F3": "H-F3 skip gap≥+20%", "F4": "H-F4 skip A/B (Finding A)", "CLEAN": "H-CLEAN (all filters)"}
    w("| filter | all-time | | | post-reg (out-of-sample) | | |")
    w("|---|---|---|---|---|---|---|")
    w("| | n | win% | avg net | n | win% | avg net |")
    for fid in ["ALL", "F1", "F2", "F3", "F4", "CLEAN"]:
        a_n, a_w, a_m = fmt(arm(fid, False))
        p_n, p_w, p_m = fmt(arm(fid, True))
        w(f"| {labels[fid]} | {a_n} | {a_w} | {a_m} | {p_n} | {p_w} | {p_m} |")
    w("")
    # short-interest cut (H-SI) — two-sided; squeeze-prone both ways. Capture began
    # 2026-06-16, so this populates only as those (and later) picks reach grading.
    si_rows = []
    for o in outs:
        p = by_id.get(o["pick_id"]); r = col(o, "ret_open_close_net")
        si = _f((p or {}).get("short_interest_pct"))
        if p and r is not None and si is not None:
            si_rows.append((si, r, int(o["win"]) if o.get("win") not in (None, "") else (1 if r > 0 else 0)))

    def f2(k):
        return (f"n={len(k)}, win {pct(sum(wv for _, wv in k), len(k)):.0f}%, avg {mean([r for r, _ in k]):+.1f}%"
                if k else "n=0")
    w("**H-SI — short-interest cut (open question, two-sided):**")
    if si_rows:
        hi = [(r, wv) for si, r, wv in si_rows if si >= 20]
        lo = [(r, wv) for si, r, wv in si_rows if si < 20]
        w(f"- SI ≥ 20%: {f2(hi)}   ·   SI < 20%: {f2(lo)}  (graded picks carrying short interest: {len(si_rows)})")
    else:
        w("- 0 graded picks carry short interest yet — capture began 2026-06-16; this fills in as "
          "those picks reach the 5-day grade (first ones land ~this week).")
    w("")
    w("_Exit-rule study: see reports/exit-study-LATEST.md (in-sample, exploratory)._")
    w("")

    # ---- 4d. pre-registered exit rule (H-EX1) ----
    EX_REG = "2026-06-23"          # H-EX1 registration date — only later picks are the test
    EX_TARGET = 10.0
    EX_FILL_NET = EX_TARGET - 2.0  # +10% target minus the 2% cost haircut = +8% net realized
    w("## 4d. Pre-registered exit rule — H-EX1 (the candidate edge)")
    w("")
    w(f"Registered {EX_REG}. The screen finds names that **spike then fade**; H-EX1 tests "
      f"whether a disciplined target monetizes the spike. Rule: rest a **+{EX_TARGET:.0f}% "
      f"limit** over the 5-day hold — if the 5-day high reaches it, realize **+{EX_FILL_NET:.0f}% "
      f"net**, else exit at the 5-day close. Judged on **avg net/trade** vs the current "
      f"same-day-close exit, on **post-{EX_REG}** picks. Median/win% secondary.")
    w("")

    def _ex_filter(post_only):
        rows = []
        for o in outs:
            p = by_id.get(o["pick_id"])
            if not p:
                continue
            if post_only and not (p.get("trading_date", "") > EX_REG):
                continue
            rows.append((p, o))
        return rows

    def ex_arm(post_only):
        rs = []
        for _, o in _ex_filter(post_only):
            mfe, c5 = col(o, "mfe_5d"), col(o, "ret_open_5dclose_net")
            if mfe is None or c5 is None:
                continue
            rs.append(EX_FILL_NET if mfe >= EX_TARGET else c5)
        return rs

    def base_arm(post_only):
        return [r for _, o in _ex_filter(post_only)
                if (r := col(o, "ret_open_close_net")) is not None]

    def exline(name, rs):
        if not rs:
            w(f"| {name} | n=0 | — | — | — |"); return
        wr = pct(sum(1 for r in rs if r > 0), len(rs))
        w(f"| {name} | n={len(rs)} | {wr:.0f}% | {mean(rs):+.1f}% | {med(rs):+.1f}% |")

    w("| arm | n | win% | avg net | median |")
    w("|---|---|---|---|---|")
    w("| _all-time (in-sample context, NOT the test)_ |  |  |  |  |")
    exline("Same-day close (baseline)", base_arm(False))
    exline("H-EX1 +10% target", ex_arm(False))
    w("| _post-registration (the honest test)_ |  |  |  |  |")
    exline("Same-day close (baseline)", base_arm(True))
    exline("H-EX1 +10% target", ex_arm(True))
    w("")
    post_b, post_e = base_arm(True), ex_arm(True)
    if post_e and post_b:
        dp = mean(post_e) - mean(post_b)
        tail = " Directional only until n≥30 per arm." if len(post_e) < 30 else ""
        w(f"- Post-registration expectancy delta (H-EX1 − baseline): **{dp:+.1f}pp** on "
          f"n={len(post_e)}.{tail}")
    else:
        w(f"- No post-{EX_REG} graded picks yet — fills in as picks logged after registration "
          "reach the 5-day grade (first ones land ~next week). The all-time row is in-sample "
          "context, **not** the test.")
    w("- ⚠️ Fills assumed exactly at +10%; thin-float gap-through means real fills are worse "
      "(see HYPOTHESES.md H-EX1 slippage caveat). `exit_sim.py` walks the daily path as the "
      "rigorous cross-check.")
    w("")

    # ---- 4e. pre-registered exit rule #2 (H-EX2 — does a stop add value?) ----
    EX2_REG = "2026-06-24"          # H-EX2 registration date — only later picks are the test
    EX2_RULE = {"type": "target_stop", "target": 10, "stop": 20}
    EX1_RULE = {"type": "target", "target": 10}
    w("## 4e. Pre-registered exit rule — H-EX2 (does a stop add value?)")
    w("")
    w(f"Registered {EX2_REG}. H-EX1 monetizes the spike but ignores the fat left tail "
      "(median MAE ≈ −16%, 17% rug rate). H-EX2 pairs the **+10% target with a −20% disaster "
      "stop** (first level the daily path touches wins; conservative same-day tie → stop "
      "first). Judged on **avg net/trade vs H-EX1 (target alone)** on **post-"
      f"{EX2_REG}** path-bearing picks; same-day-close is the secondary baseline.")
    w("")

    # A target+stop rule needs the ORDER of touches, so it can only be evaluated from the
    # committed daily path (paths.csv), not from mfe/mae magnitudes. paths.csv is
    # forward-only, so the path-bearing sample starts ~empty and accumulates honestly.
    paths = _load_paths() if _load_paths else {}

    def ex2_rows(post_only):
        """(ret_baseline, ret_h_ex1, ret_h_ex2) per graded pick that HAS a daily path,
        all net of the 2% haircut and computed on the same subset for apples-to-apples."""
        out_rows = []
        if exit_net is None:
            return out_rows
        for o in outs:
            p = by_id.get(o.get("pick_id"))
            if not p:
                continue
            if post_only and not (p.get("trading_date", "") > EX2_REG):
                continue
            entry = col(o, "entry_open")
            bars = paths.get(o.get("pick_id"))
            base = col(o, "ret_open_close_net")
            if entry is None or not bars or base is None:
                continue
            out_rows.append((base, exit_net(entry, bars, EX1_RULE),
                             exit_net(entry, bars, EX2_RULE)))
        return out_rows

    def ex2line(name, vals):
        if not vals:
            w(f"| {name} | n=0 | — | — | — |"); return
        wr = pct(sum(1 for v in vals if v > 0), len(vals))
        w(f"| {name} | n={len(vals)} | {wr:.0f}% | {mean(vals):+.1f}% | {med(vals):+.1f}% |")

    all_rows, post_rows = ex2_rows(False), ex2_rows(True)
    if not all_rows:
        if exit_net is None or _load_paths is None:
            w("- ⏳ **Pending** — exit-rule core (`exit_sim.py`) unavailable to this run; "
              "the in-sample cross-check still lives in `reports/exit-study-LATEST.md`.")
        else:
            w("- ⏳ **Pending** — no graded pick carries a committed daily path yet "
              "(`paths.csv` is forward-only, capture began ~2026-06-22). H-EX2 needs the "
              "touch *order* a target+stop implies, so it can't be back-filled from "
              "mfe/mae. The post-registration sample fills in as path-bearing picks grade. "
              "In-sample context meanwhile: `reports/exit-study-LATEST.md`.")
    else:
        w("| arm | n | win% | avg net | median |")
        w("|---|---|---|---|---|")
        w("| _all-time, path-bearing (in-sample context, NOT the test)_ |  |  |  |  |")
        ex2line("Same-day close (baseline)", [r[0] for r in all_rows])
        ex2line("H-EX1 +10% target", [r[1] for r in all_rows])
        ex2line("H-EX2 +10% target / −20% stop", [r[2] for r in all_rows])
        w("| _post-registration, path-bearing (the honest test)_ |  |  |  |  |")
        ex2line("Same-day close (baseline)", [r[0] for r in post_rows])
        ex2line("H-EX1 +10% target", [r[1] for r in post_rows])
        ex2line("H-EX2 +10% target / −20% stop", [r[2] for r in post_rows])
        w("")
        if post_rows:
            dp = mean([r[2] for r in post_rows]) - mean([r[1] for r in post_rows])
            tail = " Directional only until n≥30." if len(post_rows) < 30 else ""
            w(f"- Post-registration expectancy delta (H-EX2 − H-EX1): **{dp:+.1f}pp** on "
              f"n={len(post_rows)} path-bearing picks. Positive ⇒ the stop earns its keep; "
              f"a null/negative keeps H-EX1 stop-less.{tail}")
        else:
            w(f"- No post-{EX2_REG} path-bearing graded picks yet — the all-time row is "
              "in-sample context, **not** the test.")
    w("- ⚠️ Thin-float names **gap through stops**; the 2% haircut doesn't model gap-through, "
      "so realized H-EX2 (esp. the stop arm) would be **worse** than shown (HYPOTHESES.md "
      "H-EX2 caveat).")
    w("")

    # ---- 4f. pre-registered exit batch #2 (H-EX3..H-EX9) ----
    B2_REG = "2026-07-02"
    w("## 4f. Pre-registered exit batch #2 — H-EX3..H-EX9")
    w("")
    w(f"Registered {B2_REG} (HYPOTHESES.md, seven hypotheses frozen together). **Family-wise "
      "honesty note: with this many arms, one can beat baseline by luck.** The batch is a "
      "*ranked screen*, not seven independent claims — a winner must beat its baseline on avg "
      "net/trade, hold direction across ≥3 consecutive weekly snapshots, and survive as n "
      f"grows; prefer the simplest rule among ties. Only **post-{B2_REG}** picks are the "
      "test; directional until n≥30 per arm. Slippage caveat as H-EX1/H-EX2 (fills assumed "
      "at level; thin floats gap through — any edge <~+1pp is noise).")
    w("")

    def b2_rows(post_only):
        rows = []
        for o in outs:
            p = by_id.get(o.get("pick_id"))
            if not p:
                continue
            if post_only and not (p.get("trading_date", "") > B2_REG):
                continue
            rows.append((p, o))
        return rows

    def b2fmt(rs):
        if not rs:
            return "n=0", "—", "—"
        wr = pct(sum(1 for r in rs if r > 0), len(rs))
        return f"n={len(rs)}", f"{wr:.0f}%", f"{mean(rs):+.1f}%"

    # (i) arms evaluable from the graded log alone (mfe_5d + closes). A +L% target that
    # fills realizes net (L − 2)%; unfilled exits at the 5-day close (already net).
    def _tgt(level):
        return lambda p, mfe, c5, c0: (level - 2.0) if mfe >= level else c5

    B2_OUTCOME_ARMS = [
        ("Same-day close (baseline)", lambda p, mfe, c5, c0: c0),
        ("5-day close (baseline)", lambda p, mfe, c5, c0: c5),
        ("H-EX1 +10% target (reference)", _tgt(10)),
        ("H-EX3 +5% target", _tgt(5)),
        ("H-EX3 +15% target", _tgt(15)),
        ("H-EX3 +20% target", _tgt(20)),
        ("H-EX6 half at +10%, half to 5d close",
         lambda p, mfe, c5, c0: 0.5 * 8.0 + 0.5 * c5 if mfe >= 10 else c5),
        ("H-EX8 tier target (A/B +20%, C/D +10%)",
         lambda p, mfe, c5, c0: ((18.0 if mfe >= 20 else c5) if p.get("tier") in ("A", "B")
                                 else (8.0 if mfe >= 10 else c5))),
    ]

    def b2_outcome_arm(fn, post_only):
        rs = []
        for p, o in b2_rows(post_only):
            mfe, c5, c0 = col(o, "mfe_5d"), col(o, "ret_open_5dclose_net"), col(o, "ret_open_close_net")
            if mfe is None or c5 is None or c0 is None:
                continue
            rs.append(fn(p, mfe, c5, c0))
        return rs

    w("**(i) Arms evaluable from the graded log (target fills read off `mfe_5d`):**")
    w("")
    w("| arm | all-time | | | post-reg (the test) | | |")
    w("|---|---|---|---|---|---|---|")
    w("| | n | win% | avg net | n | win% | avg net |")
    for name, fn in B2_OUTCOME_ARMS:
        a_n, a_w, a_m = b2fmt(b2_outcome_arm(fn, False))
        p_n, p_w, p_m = b2fmt(b2_outcome_arm(fn, True))
        w(f"| {name} | {a_n} | {a_w} | {a_m} | {p_n} | {p_w} | {p_m} |")
    w("")

    # (ii) arms needing the ORDER of touches -> only scorable from the committed daily
    # path (paths.csv, forward-only). Reuses the audited exit_sim core (same as §4e).
    B2_PATH_ARMS = [
        ("Same-day close (baseline)", {"type": "close0"}),
        ("H-EX1 +10% target (reference)", {"type": "target", "target": 10}),
        ("H-EX2 +10% / −20% stop (reference)", {"type": "target_stop", "target": 10, "stop": 20}),
        ("H-EX4 +10% target, day-2 time stop", {"type": "target_timestop", "target": 10, "day": 2}),
        ("H-EX5a day-1 close", {"type": "closeN", "day": 1}),
        ("H-EX5b day-2 close", {"type": "closeN", "day": 2}),
        ("H-EX7 trail 15% after +10% touch", {"type": "target_trail", "target": 10, "trail": 15}),
        ("H-EX9a +10% / −10% stop", {"type": "target_stop", "target": 10, "stop": 10}),
        ("H-EX9b +10% / −30% stop", {"type": "target_stop", "target": 10, "stop": 30}),
    ]

    def b2_path_arm(rule, post_only):
        rs = []
        if exit_net is None:
            return rs
        for p, o in b2_rows(post_only):
            entry = col(o, "entry_open")
            bars = paths.get(o.get("pick_id"))
            if entry is None or not bars:
                continue
            rs.append(exit_net(entry, bars, rule))
        return rs

    w("**(ii) Arms needing touch order (scored from the committed daily path, `paths.csv`):**")
    w("")
    if exit_net is None:
        w("- ⏳ **Pending** — exit-rule core (`exit_sim.py`) unavailable to this run.")
    else:
        w("| arm | all-time path-bearing | | | post-reg (the test) | | |")
        w("|---|---|---|---|---|---|---|")
        w("| | n | win% | avg net | n | win% | avg net |")
        for name, rule in B2_PATH_ARMS:
            a_n, a_w, a_m = b2fmt(b2_path_arm(rule, False))
            p_n, p_w, p_m = b2fmt(b2_path_arm(rule, True))
            w(f"| {name} | {a_n} | {a_w} | {a_m} | {p_n} | {p_w} | {p_m} |")
    w("")
    w("_All-time columns are in-sample context, NOT the test. Post-reg columns fill as picks "
      f"logged after {B2_REG} reach the 5-day grade (first land ~2026-07-10)._")
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
