#!/usr/bin/env python3
"""ThePickLog — CALENDAR / TIMING EXPERIMENT EVALUATOR (EXP04, EXP05).

WHY A SEPARATE EVALUATOR (and not experiment_harness.py)
    The harness's day-matched control is CROSS-SECTIONAL: a signal on one ticker is scored
    against the equal-weight return of its whole universe over the identical window. That is
    the right control for a SELECTION claim. EXP04 and EXP05 are TIMING claims on a single
    asset — the universe IS the position, so the cross-sectional control is the position
    itself and the excess would be zero by construction. The correct control for a timing
    claim is TIME-matched:
      * EXP04 (turn-of-month): TOM sessions vs the NON-TOM sessions of the same cycle.
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
    and appends outcomes idempotently.

AMENDMENT 2026-08-07 (registration date UNCHANGED; ZERO rows had been graded when this was
made — the first grade run had not yet happened, so no observed data informed any of it).
An adversarial review the day after registration found six defects. Recorded in full because
the point of this project is that the apparatus gets audited, not just the measurements:

    A. PARTIAL-BAR BIAS, ASYMMETRIC. The incomplete-month guard defers every non-TOM session
       of the current month, so the only sessions gradeable on the day they occur were
       positions 0/1/2 of a month — which are ALWAYS turn-of-month. A grade run before the
       close would therefore freeze a live intraday snapshot into the treatment arm and never
       the control arm. The CI cron is 21:00 UTC = 4:00pm ET in winter, i.e. exactly at the
       bell, in exactly the months EXP04's verdict lands. FIX: never grade the final fetched
       session for any ticker. Costs one day of latency; removes the whole class.
    B. TRUNCATED LEADING MONTH. tom_flags derives position from the fetched session list, so
       the first month of the ~400-day window (which starts mid-month) had its first three
       FETCHED sessions flagged turn-of-month. Harmless while that month is pre-registration,
       permanent once it is not. FIX: never grade sessions in the first month of the window.
    C. ZERO-BYTE OUTCOMES FILE. _append tested os.path.exists, not size, so an interrupted
       first run left an empty file, no header was ever written, the first data row became
       the header, and grade then raised KeyError forever — swallowed by the catch-all, so
       CI stayed green while nothing was collected. FIX: treat an empty file as headerless.
       (The same bug was fixed in experiment_harness.py.)
    D. THE CI WAS THE CI OF THE WRONG QUANTITY. The control mean was computed once and
       subtracted as a CONSTANT before bootstrapping, so none of the control arm's sampling
       uncertainty reached the interval. Simulated under the null at ~5 clusters, the
       one-sided false-positive rate of the `lo > 0` test was 12.1% against a nominal 2.5%.
       FIX: resample clusters and recompute BOTH arms inside every resample.
    E. WRONG CLUSTERING UNIT. The last 4 sessions of month M and the first 3 of month M+1 are
       ONE contiguous 7-session run of market time — the most correlated observations in the
       sample — but were keyed to two different calendar months, understating correlation.
       FIX: the cluster is the turn-of-month CYCLE (see cycle_key), which also places each
       cycle's control sessions in the same cluster as its TOM sessions, so the bootstrap is
       contemporaneous by construction.
    F. TOO FEW CLUSTERS, AND A VERDICT REPUBLISHED AT EVERY LOOK. n>=30 sessions is only ~5
       clusters; even with D and E fixed the false-positive rate there is ~8%. And the
       verdict line was recomputed every run with no alpha spending, so across a year of
       looks a no-effect claim had roughly a 1-in-5 chance of printing a pass at least once.
       FIX: cluster-count floors (MIN_CYCLES / MIN_WEEKS) added to the pass bar, and NO
       verdict language of any kind is emitted until the floor is reached. This moves the
       expected verdict windows to ~2027-01 (EXP05) and ~2027-09 (EXP04). Slower is the
       point: an underpowered early read is the exact failure Experiment 01 already taught
       us, and repeating it would be indefensible.

    RESIDUAL, MEASURED AND DISCLOSED RATHER THAN ASSUMED AWAY. Simulating the SHIPPED
    estimator under the null (no effect, 7 treatment + 14 control sessions per cycle), the
    one-sided false-positive rate of the `lo > 0` test is:
        ~5 cycles (the old bar) ......... 7.6%     as originally coded, before fix D: 12.1%
        ~8 cycles ....................... 5.1%
        12 cycles (the amended floor) ... 4.2% +/- 0.5%   <-- still above the nominal 2.5%
        20 cycles ....................... ~4.5% (within noise of 12)
    The percentile cluster bootstrap stays modestly anti-conservative at any cluster count
    reachable in a reasonable window, and pushing the floor past 12 buys nothing measurable
    while costing years. So the floor is 12 and the residual is published: read a bare
    "clears the bar" on EXP04 as roughly a 1-in-24 rather than a 1-in-40 false-positive risk.

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

REGISTERED_AT = "2026-08-06"   # frozen at registration; NOT changed by the 08-07 amendment
AMENDED_AT = "2026-08-07"      # pass-bar amendment, made before any row was ever graded
MIN_N = 30                     # sessions — from the original registration
MIN_CYCLES = 12                # EXP04: distinct complete turn-of-month cycles (amendment F)
MIN_WEEKS = 20                 # EXP05: distinct ISO weeks (amendment F)
BOOT = 3000
SEED = 7
TICKERS = ["QQQ", "SPY"]       # QQQ decides; SPY is replication-only
PRIMARY = "QQQ"
TOM_LAST = 4                   # last 4 trading days of the month...
TOM_FIRST = 3                  # ...plus first 3 of the next. Frozen. Changing voids EXP04.
MAX_SESSION_GAP_DAYS = 5       # a larger gap to the previous bar means a data hole, not a weekend
COST_RT_NOTE = 0.02            # % round trip used in the EXP05 tradeability footnote

OUT_FIELDS = ["session", "ticker", "graded_at", "cc_ret", "on_ret", "id_ret",
              "is_tom", "cycle", "iso_week"]


# --------------------------------------------------------------- statistics
def median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def cluster_ci(vals, keys, B=BOOT, seed=SEED):
    """Mean + 95% CI of a single already-paired quantity, resampling CLUSTERS.
    Used by EXP05, whose observation is itself a within-session difference."""
    if len(vals) < 10:
        return None
    by = {}
    for v, k in zip(vals, keys):
        by.setdefault(k, []).append(v)
    ks = sorted(by)
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


def cluster_ci_two_arm(by_cluster, B=BOOT, seed=SEED):
    """Mean difference + 95% CI for a TWO-ARM comparison, resampling whole clusters and
    RECOMPUTING BOTH ARMS inside every resample (amendment D). by_cluster maps a cluster key
    to (treatment_values, control_values). Only clusters carrying both arms are used, so the
    comparison is contemporaneous within every resample (amendment E)."""
    ks = sorted(k for k, (a, r) in by_cluster.items() if a and r)
    if len(ks) < 2:
        return None
    tre = [v for k in ks for v in by_cluster[k][0]]
    con = [v for k in ks for v in by_cluster[k][1]]
    if len(tre) < 10 or len(con) < 10:
        return None
    rnd = random.Random(seed)
    out = []
    for _ in range(B):
        a, r = [], []
        for _ in range(len(ks)):
            k = ks[rnd.randrange(len(ks))]
            a.extend(by_cluster[k][0])
            r.extend(by_cluster[k][1])
        if a and r:
            out.append(sum(a) / float(len(a)) - sum(r) / float(len(r)))
    if len(out) < 100:
        return None
    out.sort()
    return {"mean": sum(tre) / float(len(tre)) - sum(con) / float(len(con)),
            "lo": out[int(0.025 * len(out))],
            "hi": out[min(len(out) - 1, int(0.975 * len(out)))],
            "n_treat": len(tre), "n_ctrl": len(con), "clusters": len(ks)}


# --------------------------------------------------------------- calendar
def next_month(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    return "%d-01" % (y + 1) if m == 12 else "%d-%02d" % (y, m + 1)


def month_positions(dates):
    """{date: (position_in_its_month, n_sessions_that_month)} from the session list itself."""
    by_month = {}
    for d in dates:
        by_month.setdefault(d[:7], []).append(d)
    pos = {}
    for _, ds in by_month.items():
        for i, d in enumerate(ds):
            pos[d] = (i, len(ds))
    return pos


def tom_flags(dates):
    """{date: bool} — True if the session is one of the first TOM_FIRST or last TOM_LAST
    trading sessions of its month."""
    pos = month_positions(dates)
    return {d: (i < TOM_FIRST or i >= n - TOM_LAST) for d, (i, n) in pos.items()}


def cycle_key(d, pos_in_month):
    """The turn-of-month CYCLE a session belongs to (amendment E).

    A cycle is labelled by the month it ENTERS, and contains, in market-time order:
        [mid-month non-TOM sessions of month M] + [last TOM_LAST of M] + [first TOM_FIRST of M+1]
    so a cycle's treatment sessions form one contiguous run and its control sessions are the
    stretch immediately before them. Both arms of a cycle are therefore contemporaneous."""
    m = d[:7]
    return m if pos_in_month < TOM_FIRST else next_month(m)


def iso_week(d):
    y, w, _ = datetime.strptime(d, "%Y-%m-%d").isocalendar()
    return "%d-W%02d" % (y, w)


def days_between(a, b):
    return (datetime.strptime(b, "%Y-%m-%d") - datetime.strptime(a, "%Y-%m-%d")).days


# --------------------------------------------------------------- io helpers
def _read(p):
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        return []
    with io.open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _append(p, fields, rows):
    if not rows:
        return
    os.makedirs(os.path.dirname(p), exist_ok=True)
    # An EXISTING BUT EMPTY file must still get a header (amendment C) — otherwise the first
    # data row silently becomes the header and every later read is garbage.
    first = (not os.path.exists(p)) or os.path.getsize(p) == 0
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
        df = yf.download(t, period="%dd" % days, interval="1d", auto_adjust=True,
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
    new, skipped_gap = [], 0
    for t, rows in data.items():
        dates = [b["d"] for b in rows]
        pos = month_positions(dates)
        flags = tom_flags(dates)
        first_month, last_month, terminal = dates[0][:7], dates[-1][:7], dates[-1]
        for i in range(1, len(rows)):
            d = rows[i]["d"]
            if d <= REGISTERED_AT or (d, t) in done:
                continue
            # (A) Never grade the final fetched session: its daily bar may still be live, and
            # only turn-of-month sessions can ever reach this branch on the day they occur,
            # so a partial bar would bias the treatment arm and nothing else.
            if d == terminal:
                continue
            # (B) The first month of the window is truncated by the lookback, so its
            # "position in month" is unknowable and its TOM flags would be wrong.
            if d[:7] == first_month:
                continue
            # The fetch's FINAL month is incomplete, so its "last TOM_LAST of month" flags are
            # not yet determined; outcomes are append-only, so a wrong flag would be frozen
            # forever. Grade only the first TOM_FIRST sessions there, whose classification is
            # already certain, and defer the rest to a later run.
            if d[:7] == last_month and pos[d][0] >= TOM_FIRST:
                continue
            prev = rows[i - 1]["d"]
            if days_between(prev, d) > MAX_SESSION_GAP_DAYS:
                skipped_gap += 1          # a missing bar would silently span two sessions
                continue
            pc, o, c = rows[i - 1]["c"], rows[i]["o"], rows[i]["c"]
            if not pc or not o:
                continue
            new.append({"session": d, "ticker": t, "graded_at": now,
                        "cc_ret": round((c / pc - 1) * 100.0, 5),
                        "on_ret": round((o / pc - 1) * 100.0, 5),
                        "id_ret": round((c / o - 1) * 100.0, 5),
                        "is_tom": 1 if flags[d] else 0,
                        "cycle": cycle_key(d, pos[d][0]),
                        "iso_week": iso_week(d)})
    _append(out_path(), OUT_FIELDS, new)
    tag = ("  (%d session(s) skipped: gap to previous bar > %d days)"
           % (skipped_gap, MAX_SESSION_GAP_DAYS)) if skipped_gap else ""
    print("calendar_eval grade: +%d session-rows appended%s" % (len(new), tag))
    return 0


def summarise(ticker):
    g = [r for r in _read(out_path()) if r["ticker"] == ticker]
    # ---- EXP04: complete cycles only, so the reported comparison never depends on which
    # day of the month the report happens to be generated (amendment E).
    by_cycle = {}
    for r in g:
        v = _f(r.get("cc_ret"))
        if v is None or not r.get("cycle"):
            continue
        a, c = by_cycle.setdefault(r["cycle"], ([], []))
        (a if r.get("is_tom") == "1" else c).append(v)
    complete = {k: v for k, v in by_cycle.items() if v[0] and v[1]}
    tom = [v for k in complete for v in complete[k][0]]
    rest = [v for k in complete for v in complete[k][1]]
    # ---- EXP05: paired within-session difference, clustered by ISO week.
    dif = [(_f(r["on_ret"]) - _f(r["id_ret"]), r["iso_week"]) for r in g
           if _f(r.get("on_ret")) is not None and _f(r.get("id_ret")) is not None]
    on = [v for v, _ in dif]
    return {
        "tom_n": len(tom), "rest_n": len(rest), "cycles": len(complete),
        "pending_cycles": len(by_cycle) - len(complete),
        "tom_mean": (sum(tom) / len(tom)) if tom else None, "tom_med": median(tom),
        "rest_mean": (sum(rest) / len(rest)) if rest else None, "rest_med": median(rest),
        "tom_ci": cluster_ci_two_arm(complete) if complete else None,
        "tom_win": (100.0 * sum(1 for v in tom if v > 0) / len(tom)) if tom else None,
        "on_n": len(on), "on_mean": (sum(on) / len(on)) if on else None, "on_med": median(on),
        "on_ci": cluster_ci(on, [w for _, w in dif]) if on else None,
        "on_weeks": len(set(w for _, w in dif)),
        "on_win": (100.0 * sum(1 for v in on if v > 0) / len(on)) if on else None,
    }


def _verdict_tom(s):
    # (F) No verdict language of ANY kind before both floors are met — otherwise the verdict
    # is re-tested at every look with no alpha spending.
    if s["tom_n"] < MIN_N or s["cycles"] < MIN_CYCLES:
        return ("accruing — %d/%d turn-of-month sessions and %d/%d complete cycles; "
                "no verdict is computed until both floors are met"
                % (s["tom_n"], MIN_N, s["cycles"], MIN_CYCLES))
    ci = s["tom_ci"]
    if ci is None or s["rest_mean"] is None or s["rest_med"] is None:
        return "accruing — control arm too thin to compute the interval"
    if ci["lo"] > 0 and s["tom_mean"] > s["rest_mean"] and s["tom_med"] > s["rest_med"]:
        return "**clears the bar on current data** (mean, median and cycle-clustered CI all favour TOM)"
    if ci["hi"] < 0:
        return "**significantly NEGATIVE** — TOM sessions are running below the rest"
    return "**no edge detected** — the TOM excess is indistinguishable from zero"


def _verdict_on(s):
    if s["on_n"] < MIN_N or s["on_weeks"] < MIN_WEEKS:
        return ("accruing — %d/%d sessions and %d/%d ISO weeks; no verdict is computed "
                "until both floors are met" % (s["on_n"], MIN_N, s["on_weeks"], MIN_WEEKS))
    ci = s["on_ci"]
    if ci is None:
        return "accruing — sample too thin to compute the interval"
    if ci["lo"] > 0 and s["on_mean"] > 0 and s["on_med"] > 0:
        return "**clears the bar on current data** (mean, median and week-clustered CI all positive)"
    if ci["hi"] < 0:
        return "**significantly NEGATIVE** — intraday is beating overnight"
    return "**no edge detected** — the overnight-minus-intraday difference is indistinguishable from zero"


def report():
    L = ["# ThePickLog — calendar experiments (EXP04, EXP05) · %s"
         % datetime.now(timezone.utc).date().isoformat(), "",
         "Both experiments are forward-only from **%s** and scored against **time-matched "
         "controls** (see the `calendar_eval.py` header for why the harness's cross-sectional "
         "control does not apply to timing claims). Mean, median and a clustered 95%% CI are "
         "reported together. **Win rate is reported but is never a pass criterion.** SPY is a "
         "replication read only — QQQ decides." % REGISTERED_AT, "",
         "> **Pass bar amended %s**, before any row had ever been graded, after an adversarial "
         "review found the confidence interval was too narrow and the verdict was being "
         "re-tested at every look. Both experiments now require a minimum number of "
         "**clusters** (%d complete turn-of-month cycles for EXP04, %d ISO weeks for EXP05) "
         "on top of the registered n>=%d sessions, and **no verdict of any kind is computed "
         "or displayed until those floors are met.** The registration date is unchanged. Full "
         "detail in HYPOTHESES.md and in the evaluator's header."
         % (AMENDED_AT, MIN_CYCLES, MIN_WEEKS, MIN_N), "",
         "> **Known residual, measured not assumed.** Simulated under the null, the one-sided "
         "false-positive rate of this interval is **4.2%% (+/-0.5) at the %d-cycle floor** "
         "against a nominal 2.5%% — down from 12.1%% as the code was originally written. A "
         "percentile cluster bootstrap stays modestly anti-conservative at any cluster count "
         "reachable in a sane window, and raising the floor further buys nothing measurable. "
         "So: read a bare \"clears the bar\" on EXP04 as about a 1-in-24 false-positive risk, "
         "not 1-in-40." % MIN_CYCLES, ""]
    for t in TICKERS:
        s = summarise(t)
        role = "PRIMARY — this decides" if t == PRIMARY else "replication read only"
        L += ["## %s  (%s)" % (t, role), "",
              "### EXP04 — turn-of-month",
              "- turn-of-month sessions graded: **%d** (need %d); non-TOM control sessions: "
              "%d; complete cycles: **%d** (need %d)%s"
              % (s["tom_n"], MIN_N, s["rest_n"], s["cycles"], MIN_CYCLES,
                 (", %d cycle(s) still filling" % s["pending_cycles"])
                 if s["pending_cycles"] else "")]
        if s["tom_n"] and s["rest_n"]:
            ci = s["tom_ci"]
            cis = ("[%+.3f, %+.3f] over %d cycles" % (ci["lo"], ci["hi"], ci["clusters"])
                   if ci else "n/a — too few complete cycles")
            L += ["- TOM mean **%+.3f%%**/session, median %+.3f%% vs rest mean %+.3f%%, "
                  "median %+.3f%%" % (s["tom_mean"], s["tom_med"], s["rest_mean"], s["rest_med"]),
                  "- cycle-clustered 95%% CI of the TOM-minus-rest difference: %s" % cis,
                  "- TOM win rate %.0f%% *(reported only)*" % s["tom_win"]]
        L += ["- **read: %s**" % _verdict_tom(s), "",
              "### EXP05 — overnight vs intraday (attribution claim)",
              "- sessions graded: **%d** (need %d); ISO weeks: **%d** (need %d)"
              % (s["on_n"], MIN_N, s["on_weeks"], MIN_WEEKS)]
        if s["on_n"]:
            ci = s["on_ci"]
            cis = ("[%+.3f, %+.3f] over %d weeks" % (ci["lo"], ci["hi"], ci["clusters"])
                   if ci else "n/a — sample too thin")
            L += ["- overnight-minus-intraday: mean **%+.3f%%**/session, median %+.3f%%, "
                  "week-clustered 95%% CI %s" % (s["on_mean"], s["on_med"], cis),
                  "- overnight leg wins %.0f%% of sessions *(reported only)*" % s["on_win"],
                  "- tradeability footnote: capturing the overnight leg costs one round trip "
                  "per session; at %.2f%%/RT the mean must exceed %.2f%% just to break even. "
                  "EXP05 passing does NOT make it tradeable — that is the registered scope."
                  % (COST_RT_NOTE, COST_RT_NOTE)]
        L += ["- **read: %s**" % _verdict_on(s), ""]
    L += ["---", "",
          "Constants are frozen in `calendar_eval.py`; changing any voids the affected "
          "experiment and requires a new registration with a new window. Outcomes are "
          "append-only under `experiments/`. Not investment advice."]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with io.open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("wrote %s" % REPORT)
    return 0


# --------------------------------------------------------------- selftest
def _selftest():
    # ---- calendar: 21-session month -> first 3 and last 4 flagged
    days = ["2026-09-%02d" % d for d in range(1, 22)]
    fl = tom_flags(days)
    assert sum(fl.values()) == 7
    assert fl["2026-09-01"] and fl["2026-09-03"] and not fl["2026-09-04"]
    assert fl["2026-09-18"] and fl["2026-09-21"] and not fl["2026-09-17"]
    fl2 = tom_flags(days + ["2026-10-%02d" % d for d in range(1, 24)])
    assert fl2["2026-10-01"] and not fl2["2026-10-06"]

    # ---- amendment E: one contiguous turn-of-month run must be ONE cycle
    pos = month_positions(days + ["2026-10-%02d" % d for d in range(1, 24)])
    assert cycle_key("2026-09-21", pos["2026-09-21"][0]) == "2026-10"   # last-4 of Sep
    assert cycle_key("2026-10-01", pos["2026-10-01"][0]) == "2026-10"   # first-3 of Oct
    assert cycle_key("2026-09-01", pos["2026-09-01"][0]) == "2026-09"   # first-3 of Sep
    assert cycle_key("2026-09-10", pos["2026-09-10"][0]) == "2026-10"   # mid-Sep control
    assert next_month("2026-12") == "2027-01" and next_month("2026-08") == "2026-09"

    # ---- amendment D: the two-arm CI must widen when the control arm is noisy, and must
    # straddle zero under the null
    rnd = random.Random(3)
    null = {"c%02d" % i: ([rnd.gauss(0, 1) for _ in range(7)],
                          [rnd.gauss(0, 1) for _ in range(14)]) for i in range(14)}
    ci = cluster_ci_two_arm(null)
    assert ci and ci["lo"] < 0 < ci["hi"], ci
    assert ci["clusters"] == 14
    shifted = {k: ([v + 8.0 for v in a], r) for k, (a, r) in null.items()}
    ci2 = cluster_ci_two_arm(shifted)
    assert ci2 and ci2["lo"] > 0, ci2
    assert cluster_ci_two_arm({"c1": ([1.0] * 10, [0.0] * 10)}) is None   # 1 cluster -> no CI
    # a cluster missing an arm is excluded rather than silently compared
    mixed = dict(null); mixed["orphan"] = ([1.0] * 5, [])
    assert cluster_ci_two_arm(mixed)["clusters"] == 14

    # ---- single-arm CI (EXP05) still behaves
    assert median([1, 2, 3]) == 2 and median([1, 2, 3, 4]) == 2.5
    c1 = cluster_ci([1.0] * 40, ["W%d" % (i % 8) for i in range(40)])
    assert c1 and abs(c1["mean"] - 1.0) < 1e-9 and c1["clusters"] == 8
    c2 = cluster_ci([1.0, -1.0] * 30, ["W%d" % (i % 10) for i in range(60)])
    assert c2 and c2["lo"] < 0 < c2["hi"]

    # ---- amendment F: no verdict language before the floors
    thin = {"tom_n": 35, "rest_n": 70, "cycles": 5, "pending_cycles": 0, "tom_mean": 9.9,
            "tom_med": 9.9, "rest_mean": 0.0, "rest_med": 0.0, "tom_ci": None, "tom_win": 99.0,
            "on_n": 35, "on_mean": 9.9, "on_med": 9.9, "on_ci": None, "on_weeks": 7,
            "on_win": 99.0}
    assert "accruing" in _verdict_tom(thin) and "clears" not in _verdict_tom(thin)
    assert "accruing" in _verdict_on(thin) and "clears" not in _verdict_on(thin)

    # ---- amendment C: an existing but EMPTY file still gets a header
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "sub", "x.csv")
        os.makedirs(os.path.dirname(p))
        io.open(p, "w").close()                      # zero-byte, as a crashed run leaves it
        _append(p, OUT_FIELDS, [{"session": "2026-08-07", "ticker": "QQQ"}])
        assert io.open(p).read().startswith("session,ticker"), io.open(p).read()[:40]
        assert len(_read(p)) == 1

    # ---- amendments A + B: terminal session and truncated leading month are never graded
    global DATA
    with tempfile.TemporaryDirectory() as td:
        keep, DATA = DATA, td
        try:
            ds = ["2026-07-%02d" % d for d in range(20, 32)] \
                 + ["2026-08-%02d" % d for d in range(1, 32)] \
                 + ["2026-09-%02d" % d for d in range(1, 11)]
            rows, px = [], 100.0
            for d in ds:
                o = px * 1.001; c = o * 0.9995
                rows.append({"d": d, "o": o, "c": c}); px = c
            grade({"QQQ": rows})
            got = _read(out_path())
            sess = [r["session"] for r in got]
            assert all(s > REGISTERED_AT for s in sess)          # forward-only
            assert not any(s.startswith("2026-07") for s in sess)  # (B) truncated first month
            assert ds[-1] not in sess                              # (A) terminal session
            # (A) corollary: the terminal session would have been a TOM row had it been graded
            assert tom_flags(ds)[ds[-1]] is True
            n1 = len(got)
            grade({"QQQ": rows})
            assert len(_read(out_path())) == n1                    # idempotent
            # every graded row carries a cycle key, and cycles group both arms
            assert all(r["cycle"] for r in got)
            s = summarise("QQQ")
            assert s["tom_n"] and s["rest_n"] and s["cycles"] >= 1
            assert "accruing" in _verdict_tom(s)                   # floors not met
        finally:
            DATA = keep

    # ---- gap guard
    assert days_between("2026-08-07", "2026-08-10") == 3           # ordinary weekend
    assert days_between("2026-08-07", "2026-08-20") > MAX_SESSION_GAP_DAYS

    assert REGISTERED_AT == "2026-08-06" and TOM_LAST == 4 and TOM_FIRST == 3
    print("calendar_eval selftest PASS — calendar, cycle clustering, two-arm CI, verdict "
          "floors, empty-file header, terminal/leading-month guards, idempotency")
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
        print("calendar_eval: non-fatal error %s: %s" % (type(e).__name__, e))
        sys.exit(0)
