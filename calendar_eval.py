#!/usr/bin/env python3
"""ThePickLog — CALENDAR / TIMING EXPERIMENT EVALUATOR (EXP04, EXP05).

WHY A SEPARATE EVALUATOR (and not experiment_harness.py)
    The harness's day-matched control is CROSS-SECTIONAL: a signal on one ticker is scored
    against the equal-weight return of its whole universe over the identical window. That is
    the right control for a SELECTION claim. EXP04 and EXP05 are TIMING claims on a single
    asset — the universe IS the position, so the cross-sectional control is the position
    itself and the excess would be zero by construction. The correct control for a timing
    claim is TIME-matched:
      * EXP04 (turn-of-month): TOM sessions vs all OTHER sessions in the same forward window.
      * EXP05 (overnight vs intraday): the same day's OTHER leg — a paired, per-session
        control, the cleanest control in the whole project.
    Everything else follows the harness guarantees unchanged: forward-only from the
    registration date, append-only CSVs under experiments/, declared costs, mean AND median
    AND a clustered 95% CI reported together, win rate reported but never a pass criterion,
    constants frozen — changing one voids the test.

WHAT MAKES CALENDAR CLAIMS DIFFERENT (and easier to keep honest)
    There is no signal-capture race: whether a future session is a turn-of-month session is
    fixed by the exchange calendar, and every session has an overnight and an intraday leg.
    So there is no scan step — `grade` derives every post-registration session from prices
    and appends outcomes idempotently. The pre-open gate problem of Experiment 01 cannot
    occur here by construction.

REGISTERED EXPERIMENTS (frozen 2026-08-06 — see HYPOTHESES.md batch #9)
    EXP04-TOM   QQQ mean close->close return on turn-of-month sessions (last 4 + first 3
                trading days of the month) exceeds the mean on all other sessions.
                Cluster = calendar month. n >= 30 TOM sessions (~4.5 months).
    EXP05-ON    QQQ overnight leg (prev close -> open) exceeds the intraday leg
                (open -> close), per session, as an ATTRIBUTION claim — explicitly NOT a
                claim that the gap is tradeable at retail after costs.
                Cluster = ISO week. n >= 30 sessions (~6 weeks).
    SPY is graded in parallel for both as a REPLICATION READ — reported, never a pass
    criterion.

USAGE
    python3 calendar_eval.py grade       # derive + append post-registration outcomes
    python3 calendar_eval.py report      # rewrite reports/calendar-experiments-LATEST.md
    python3 calendar_eval.py --selftest  # offline logic check, no network
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
REPORT = os.path.join(HERE, "reports", "calendar-experiments-LATEST.md")

REGISTERED_AT = "2026-08-06"   # frozen; only sessions strictly after this date are scored
MIN_N = 30
BOOT = 3000
SEED = 7
TICKERS = ["QQQ", "SPY"]       # QQQ decides; SPY is replication-only
PRIMARY = "QQQ"
TOM_LAST = 4                   # last 4 trading days of the month...
TOM_FIRST = 3                  # ...plus first 3 of the next. Frozen. Changing voids EXP04.
COST_RT_NOTE = 0.02            # % round trip used in the tradeability footnote (QQQ spread-scale)

OUT_FIELDS = ["session", "ticker", "graded_at", "cc_ret", "on_ret", "id_ret",
              "is_tom", "month", "iso_week"]


# --------------------------------------------------------------- statistics
def median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def cluster_ci_diff(vals, keys, B=BOOT, seed=SEED):
    """Mean + 95% CI of `vals`, resampling CLUSTERS (months for EXP04, weeks for EXP05) —
    sessions inside one month/week are not independent evidence."""
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


# --------------------------------------------------------------- calendar
def tom_flags(dates):
    """dates: sorted list of 'YYYY-MM-DD' trading sessions. Returns {date: bool} where True
    means the session is one of the last TOM_LAST sessions of its month or the first
    TOM_FIRST of its month. Derived purely from the session list itself."""
    by_month = {}
    for d in dates:
        by_month.setdefault(d[:7], []).append(d)
    flags = {}
    for _, ds in sorted(by_month.items()):
        for i, d in enumerate(ds):
            flags[d] = (i < TOM_FIRST) or (i >= len(ds) - TOM_LAST)
    return flags


def iso_week(d):
    y, w, _ = datetime.strptime(d, "%Y-%m-%d").isocalendar()
    return f"{y}-W{w:02d}"


# --------------------------------------------------------------- io helpers
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


def out_path():
    return os.path.join(DATA, "EXP0405-CAL-outcomes.csv")


def _f(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------- data
def fetch(days=400):
    """Adjusted open AND close (auto_adjust adjusts both), one fresh download —
    never mix stored and re-downloaded prices (see the split-adjustment field note)."""
    import yfinance as yf
    out = {}
    for t in TICKERS:
        df = yf.download(t, period=f"{days}d", interval="1d", auto_adjust=True,
                         progress=False)
        try:
            if hasattr(df.columns, "get_level_values"):
                df.columns = df.columns.get_level_values(0)
        except Exception:
            pass
        rows = []
        for idx, r in df.dropna().iterrows():
            try:
                rows.append({"d": str(idx)[:10], "o": float(r["Open"]), "c": float(r["Close"])})
            except Exception:
                continue
        if len(rows) > 30:
            out[t] = rows
    return out


# --------------------------------------------------------------- commands
def grade(data=None):
    data = data or fetch()
    if not data or PRIMARY not in data:
        print("calendar_eval: no data (non-fatal)")
        return 0
    done = {(r["session"], r["ticker"]) for r in _read(out_path())}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new = []
    for t, rows in data.items():
        dates = [b["d"] for b in rows]
        flags = tom_flags(dates)
        last_month = dates[-1][:7]
        pos_in_month = {}
        for d in dates:
            pos_in_month[d] = sum(1 for x in dates if x[:7] == d[:7] and x < d)
        for i in range(1, len(rows)):
            d = rows[i]["d"]
            # forward-only: only sessions strictly after registration are scored.
            if d <= REGISTERED_AT or (d, t) in done:
                continue
            # The fetch's FINAL month is incomplete, so its "last 4 of month" flags are
            # not yet determined (a session flagged last-4 today may not be once more
            # sessions arrive, and outcomes are append-only — a wrong flag would be
            # frozen forever). In that month, grade only the first TOM_FIRST sessions,
            # whose classification is already certain; defer the rest to a later run
            # when the month is complete in the fetch.
            if d[:7] == last_month and pos_in_month[d] >= TOM_FIRST:
                continue
            pc, o, c = rows[i - 1]["c"], rows[i]["o"], rows[i]["c"]
            if not pc or not o:
                continue
            new.append({"session": d, "ticker": t, "graded_at": now,
                        "cc_ret": round((c / pc - 1) * 100.0, 5),
                        "on_ret": round((o / pc - 1) * 100.0, 5),
                        "id_ret": round((c / o - 1) * 100.0, 5),
                        "is_tom": 1 if flags[d] else 0,
                        "month": d[:7], "iso_week": iso_week(d)})
    _append(out_path(), OUT_FIELDS, new)
    print(f"calendar_eval grade: +{len(new)} session-rows appended")
    return 0


def summarise(ticker):
    g = [r for r in _read(out_path()) if r["ticker"] == ticker]
    cc = [(_f(r["cc_ret"]), int(r["is_tom"]), r["month"]) for r in g if _f(r["cc_ret"]) is not None]
    dif = [(_f(r["on_ret"]) - _f(r["id_ret"]), r["iso_week"]) for r in g
           if _f(r["on_ret"]) is not None and _f(r["id_ret"]) is not None]
    tom = [v for v, f, _ in cc if f]
    rest = [v for v, f, _ in cc if not f]
    # EXP04 scored quantity: per-TOM-session excess over the CONTEMPORANEOUS non-TOM mean
    rest_mean = (sum(rest) / len(rest)) if rest else None
    ex = [(v - rest_mean, m) for v, f, m in cc if f] if rest_mean is not None else []
    on = [v for v, _ in dif]
    return {
        "tom_n": len(tom), "rest_n": len(rest),
        "tom_mean": (sum(tom) / len(tom)) if tom else None, "tom_med": median(tom),
        "rest_mean": rest_mean, "rest_med": median(rest),
        "tom_ci": cluster_ci_diff([v for v, _ in ex], [m for _, m in ex]) if ex else None,
        "tom_win": (100.0 * sum(1 for v in tom if v > 0) / len(tom)) if tom else None,
        "on_n": len(on), "on_mean": (sum(on) / len(on)) if on else None, "on_med": median(on),
        "on_ci": cluster_ci_diff(on, [w for _, w in dif]) if on else None,
        "on_win": (100.0 * sum(1 for v in on if v > 0) / len(on)) if on else None,
    }


def _verdict_tom(s):
    if s["tom_n"] < MIN_N:
        return f"accruing — {s['tom_n']}/{MIN_N} TOM sessions graded, no verdict yet"
    ci = s["tom_ci"]
    ok = (ci and ci["lo"] > 0 and (s["tom_mean"] or 0) > (s["rest_mean"] or 0)
          and (s["tom_med"] or 0) > (s["rest_med"] or 0))
    if ok:
        return "**clears the bar on current data** (mean, median and month-clustered CI all favour TOM)"
    if ci and ci["hi"] < 0:
        return "**significantly NEGATIVE** — TOM sessions are running below the rest"
    return "**no edge detected** — TOM excess indistinguishable from zero"


def _verdict_on(s):
    if s["on_n"] < MIN_N:
        return f"accruing — {s['on_n']}/{MIN_N} sessions graded, no verdict yet"
    ci = s["on_ci"]
    ok = (ci and ci["lo"] > 0 and (s["on_mean"] or 0) > 0 and (s["on_med"] or 0) > 0)
    if ok:
        return "**clears the bar on current data** (mean, median and week-clustered CI all positive)"
    if ci and ci["hi"] < 0:
        return "**significantly NEGATIVE** — intraday is beating overnight"
    return "**no edge detected** — the overnight-minus-intraday difference is indistinguishable from zero"


def report():
    L = [f"# ThePickLog — calendar experiments (EXP04, EXP05) · "
         f"{datetime.now(timezone.utc).date().isoformat()}", "",
         f"Both experiments are forward-only from **{REGISTERED_AT}** and scored against "
         "**time-matched controls** (see `calendar_eval.py` header for why the harness's "
         "cross-sectional control does not apply to timing claims). Mean, median and a "
         "clustered 95% CI are reported together. **Win rate is reported but is never a "
         "pass criterion.** SPY is a replication read only — QQQ decides.", ""]
    for t in TICKERS:
        s = summarise(t)
        role = "PRIMARY — this decides" if t == PRIMARY else "replication read only"
        L += [f"## {t}  ({role})", "",
              "### EXP04 — turn-of-month",
              f"- TOM sessions graded: **{s['tom_n']}** (need {MIN_N}); non-TOM: {s['rest_n']}"]
        if s["tom_n"]:
            ci = s["tom_ci"]
            cis = (f"[{ci['lo']:+.3f}, {ci['hi']:+.3f}] over {ci['clusters']} months"
                   if ci else "n/a")
            L += [f"- TOM mean **{s['tom_mean']:+.3f}%**/session, median {s['tom_med']:+.3f}% "
                  f"vs rest mean {s['rest_mean']:+.3f}%, median {s['rest_med']:+.3f}%",
                  f"- month-clustered 95% CI of the TOM excess: {cis}",
                  f"- TOM win rate {s['tom_win']:.0f}% *(reported only)*"]
        L += [f"- **read: {_verdict_tom(s)}**", "",
              "### EXP05 — overnight vs intraday (attribution claim)",
              f"- sessions graded: **{s['on_n']}** (need {MIN_N})"]
        if s["on_n"]:
            ci = s["on_ci"]
            cis = (f"[{ci['lo']:+.3f}, {ci['hi']:+.3f}] over {ci['clusters']} weeks"
                   if ci else "n/a")
            L += [f"- overnight-minus-intraday: mean **{s['on_mean']:+.3f}%**/session, "
                  f"median {s['on_med']:+.3f}%, week-clustered 95% CI {cis}",
                  f"- overnight leg wins {s['on_win']:.0f}% of sessions *(reported only)*",
                  f"- tradeability footnote: capturing the overnight leg costs one round trip "
                  f"per session; at {COST_RT_NOTE:.2f}%/RT the mean must exceed "
                  f"{COST_RT_NOTE:.2f}% just to break even. EXP05 passing does NOT make it "
                  f"tradeable — that is the registered scope."]
        L += [f"- **read: {_verdict_on(s)}**", ""]
    L += ["---", "",
          "Constants are frozen in `calendar_eval.py`; changing any voids the affected "
          "experiment and requires a new registration with a new window. Outcomes are "
          "append-only under `experiments/`. Not investment advice."]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with io.open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"wrote {REPORT}")
    return 0


# --------------------------------------------------------------- selftest
def _selftest():
    # tom_flags: 21-session month -> first 3 and last 4 flagged
    days = [f"2026-09-{d:02d}" for d in range(1, 22)]
    fl = tom_flags(days)
    assert sum(fl.values()) == 7
    assert fl["2026-09-01"] and fl["2026-09-03"] and not fl["2026-09-04"]
    assert fl["2026-09-18"] and fl["2026-09-21"] and not fl["2026-09-17"]
    # two months independent
    fl2 = tom_flags(days + [f"2026-10-{d:02d}" for d in range(1, 24)])
    assert fl2["2026-10-01"] and not fl2["2026-10-06"]
    # stats
    assert median([1, 2, 3]) == 2 and median([1, 2, 3, 4]) == 2.5
    ci = cluster_ci_diff([1.0] * 40, [f"M{i%8}" for i in range(40)])
    assert ci and abs(ci["mean"] - 1.0) < 1e-9 and ci["clusters"] == 8
    ci2 = cluster_ci_diff([1.0, -1.0] * 30, [f"M{i%10}" for i in range(60)])
    assert ci2 and ci2["lo"] < 0 < ci2["hi"]
    # verdict wording without data
    empty = {"tom_n": 0, "rest_n": 0, "tom_mean": None, "tom_med": None, "rest_mean": None,
             "rest_med": None, "tom_ci": None, "tom_win": None, "on_n": 0, "on_mean": None,
             "on_med": None, "on_ci": None, "on_win": None}
    assert "accruing" in _verdict_tom(empty) and "accruing" in _verdict_on(empty)
    # iso week sanity
    assert iso_week("2026-08-06") == "2026-W32"
    # frozen constants present
    assert REGISTERED_AT == "2026-08-06" and TOM_LAST == 4 and TOM_FIRST == 3
    print("calendar_eval selftest PASS — tom flags, cluster stats, verdict wording verified")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs="?", default="report", choices=["grade", "report"])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if a.command == "grade":
        grade()
    return report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"calendar_eval: non-fatal error {type(e).__name__}: {e}")
        sys.exit(0)
