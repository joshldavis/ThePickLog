#!/usr/bin/env python3
"""
family_verdict.py — the 2026-11-02 family read: H-EXP02 locked once + Benjamini-Hochberg
across the EXP02-EXP09 family, as declared in HYPOTHESES.md batch #10 ("FAMILY POLICY").

WRITTEN 2026-10-23, BEFORE THE READ, WITHOUT OPENING ANY OUTCOME VALUE. Before this file
existed, the family correction was a written policy with no code (guide.html said so in
public), and H-EXP02 had no automatic lock: rsi2_scanner.py prints "write it ONCE, today"
and relies on a person doing so. Leaving either to be improvised on verdict day is how a
correction gets chosen after the numbers are visible. This file fixes the mechanics in
advance. Every choice below is either already registered, or is the stricter of the
available readings, so none of them can make a pass easier.

WHAT IT DOES, AND THE CHOICES (all frozen here, 2026-10-23)
  1. Refuses to compute anything before 2026-11-02 (the registered read date) except
     --selftest on synthetic data. Running it early prints nothing about the data.
  2. H-EXP02 (rsi2_outcomes.csv). Bar as registered + amended 2026-08-28:
       window   signal_date strictly after 2026-07-29; state = rows with graded_at <= read date
       floors   n >= 30 graded, >= 20 distinct tickers
       pass     mean AND median of excess_1d > 0, ticker-clustered 95% CI excludes zero, AND
                the direction holding across >= 3 consecutive weekly snapshots
     PRIMARY EXIT = excess_1d (same-session). This is what rsi2_scanner.py has printed as its
     headline since registration and what experiment_harness.py scores for EXP03/06-09, so it
     is the existing operationalisation, not a new pick. The 5-session and RSI(2)>70 exits are
     reported alongside as secondary and cannot rescue a fail.
     SNAPSHOTS. The amendment says weekly snapshots "keep being recorded"; none were stored.
     rsi2_outcomes.csv is append-only and stamps graded_at on every row, so the state on any
     past date is exactly the rows graded on or before it, and git history proves the file
     was not rewritten. Snapshot dates = every Saturday (the weekly report day) up to the read.
     "Direction holding across >= 3 consecutive snapshots" = the LAST THREE snapshots each show
     mean AND median excess_1d on the same side of zero as the final read. Stricter than
     "any 3 consecutive": the run must end at the read.
     CI uses the harness's own cluster bootstrap (BOOT=3000, SEED=7), so EXP02's interval is
     computed exactly the way EXP03/06-09's are.
     LOCK: written once to experiments/EXP02-verdict.csv (append-only) at the first run on or
     after 2026-11-02 where both floors are met; displayed verbatim thereafter. If the floors
     are not met it says UNDERPOWERED and writes nothing (the verdict locks at the first run
     where they are), matching the harness.
  3. FAMILY CORRECTION. Two-sided p-value per experiment from the same cluster bootstrap that
     produced its CI: p = 2 * min(share of replicates <= 0, share >= 0), floored at 1/BOOT.
     Benjamini-Hochberg at q = 0.05 (the level the 95% intervals already imply).
     m = 8, ALWAYS — the declared family is EXP02-EXP09. EXP04/EXP05 read in 2027, and any
     experiment not yet locked, enter as p = 1. That is the conservative reading: BH can only
     get harder as m grows, and treating an unread test as p = 1 never helps anyone pass.
     ONE LOOK PER EXPERIMENT: each experiment's corrected status is computed at the run where
     its own verdict first locks, using the p-values locked by then, and appended to
     experiments/FAMILY-fdr.csv. It is never recomputed. A later lock cannot revise an
     earlier row.
     An experiment "survives the family correction" only if its own verdict is CLEARS THE BAR
     (or SIGNIFICANTLY NEGATIVE) AND its BH-adjusted p <= 0.05. Otherwise a pass is published
     as "consistent with chance", exactly as the family policy says.
  4. Writes reports/family-verdict-LATEST.md.

    python3 family_verdict.py              # gated: no-op before 2026-11-02
    python3 family_verdict.py --selftest   # synthetic data only
"""
import argparse
import csv
import io
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import experiment_harness as H  # noqa: E402  (cluster_ci, EXPERIMENTS, locked_verdicts, ...)

READ_ON = "2026-11-02"
EXP02_REGISTERED = "2026-07-29"
EXP02_MIN_N = 30
EXP02_MIN_TICKERS = 20
EXP02_SNAPSHOTS = 3
Q = 0.05
FAMILY = ["EXP02-RSI2", "EXP03-MACD", "EXP04-CAL", "EXP05-CAL",
          "EXP06-SUPERTREND", "EXP07-SMAPULL", "EXP08-BOLLREVERT", "EXP09-NR7"]
M = len(FAMILY)  # 8, fixed by the declared family — never the number read so far

RSI2_OUT = os.path.join(HERE, "rsi2_outcomes.csv")
EXP02_LOCK = os.path.join(H.DATA, "EXP02-verdict.csv")
FDR_LOCK = os.path.join(H.DATA, "FAMILY-fdr.csv")
REPORT = os.path.join(HERE, "reports", "family-verdict-LATEST.md")
EXP02_FIELDS = ["experiment", "locked_at", "n", "clusters", "mean1", "med1", "ci_lo", "ci_hi",
                "p_two", "snapshots", "mean5", "med5", "mean_rsiexit", "med_rsiexit", "verdict"]
FDR_FIELDS = ["experiment", "decided_at", "own_verdict", "p_two", "m", "p_values_used",
              "bh_adjusted_p", "q", "family_status"]


# ------------------------------------------------------------------ statistics
def boot_means(vals, keys, B=H.BOOT, seed=H.SEED):
    """The exact resampling experiment_harness.cluster_ci uses (same RNG, same order), but
    returning the sorted replicate means, so the p-value comes from the same distribution as
    the published interval. Returns None when cluster_ci would."""
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
    return out


def p_two_sided(reps):
    n = float(len(reps))
    le = sum(1 for x in reps if x <= 0) / n
    ge = sum(1 for x in reps if x >= 0) / n
    return max(min(1.0, 2.0 * min(le, ge)), 1.0 / n)


def bh_adjust(ps):
    """Benjamini-Hochberg adjusted p-values, same order as input."""
    m = len(ps)
    order = sorted(range(m), key=lambda i: ps[i])
    adj = [0.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        running = min(running, ps[i] * m / rank)
        adj[i] = min(1.0, running)
    return adj


# ------------------------------------------------------------------ H-EXP02
def _f(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v == v else None


def _gdate(r):
    return (r.get("graded_at") or "")[:10]


def exp02_rows(rows, asof):
    return [r for r in rows
            if (r.get("signal_date") or "") > EXP02_REGISTERED
            and _gdate(r) and _gdate(r) <= asof
            and _f(r.get("excess_1d")) is not None]


def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def _sign_holds(rows, sign):
    xs = [_f(r["excess_1d"]) for r in rows]
    if not xs:
        return False
    mu, md = _mean(xs), H.median(xs)
    return (mu > 0 and md > 0) if sign > 0 else (mu < 0 and md < 0)


def saturdays_upto(asof):
    d = datetime.strptime(asof, "%Y-%m-%d").date()
    d -= timedelta(days=(d.weekday() - 5) % 7)          # last Saturday on/before asof
    out = []
    start = datetime.strptime(EXP02_REGISTERED, "%Y-%m-%d").date()
    while d > start:
        out.append(d.isoformat())
        d -= timedelta(days=7)
    return sorted(out)


def exp02_read(all_rows, asof):
    rows = exp02_rows(all_rows, asof)
    xs = [_f(r["excess_1d"]) for r in rows]
    tk = [r["ticker"] for r in rows]
    s = {"n": len(xs), "clusters": len(set(tk))}
    if s["n"] < EXP02_MIN_N or s["clusters"] < EXP02_MIN_TICKERS:
        s["verdict"] = None
        return s
    reps = boot_means(xs, tk)
    ci = H.cluster_ci(xs, tk)
    s.update(mean1=_mean(xs), med1=H.median(xs), ci=ci, p=p_two_sided(reps) if reps else 1.0)
    for col, key in (("excess_5d", "5"), ("excess_rsiexit", "rsiexit")):
        v = [_f(r.get(col)) for r in rows if _f(r.get(col)) is not None]
        s["mean" + key], s["med" + key] = _mean(v), H.median(v) if v else None
    sign = 1 if s["mean1"] > 0 else -1
    snaps = saturdays_upto(asof)[-EXP02_SNAPSHOTS:]
    held = [d for d in snaps if _sign_holds(exp02_rows(all_rows, d), sign)]
    s["snapshots"] = f"{len(held)}/{EXP02_SNAPSHOTS} ({','.join(snaps)})"
    snap_ok = len(snaps) == EXP02_SNAPSHOTS and len(held) == EXP02_SNAPSHOTS
    if ci and ci["lo"] > 0 and s["mean1"] > 0 and s["med1"] > 0 and snap_ok:
        s["verdict"] = "CLEARS THE BAR — mean, median and clustered CI all positive, direction held 3 weekly snapshots"
    elif ci and ci["hi"] < 0:
        s["verdict"] = "SIGNIFICANTLY NEGATIVE — worse than the day-matched control"
    else:
        s["verdict"] = "NO EDGE DETECTED — the bar is not met"
    return s


def lock_exp02(s, asof):
    if any(r["experiment"] == "EXP02-RSI2" for r in H._read(EXP02_LOCK)):
        return
    ci = s["ci"] or {}
    r5 = lambda v: "" if v is None else round(v, 5)
    H._append(EXP02_LOCK, EXP02_FIELDS, [{
        "experiment": "EXP02-RSI2", "locked_at": asof, "n": s["n"], "clusters": s["clusters"],
        "mean1": r5(s["mean1"]), "med1": r5(s["med1"]), "ci_lo": r5(ci.get("lo")),
        "ci_hi": r5(ci.get("hi")), "p_two": r5(s["p"]), "snapshots": s["snapshots"],
        "mean5": r5(s.get("mean5")), "med5": r5(s.get("med5")),
        "mean_rsiexit": r5(s.get("meanrsiexit")), "med_rsiexit": r5(s.get("medrsiexit")),
        "verdict": s["verdict"]}])


# ------------------------------------------------------------------ harness experiments
def harness_p(e, locked_row):
    """Recompute the p-value from exactly the rows the locked verdict saw. The outcomes file
    is append-only, so those are its first `n` rows (a date filter would wrongly pull in rows
    graded later on the lock date itself). Refuses (returns None) if the file is shorter than
    the locked n or the rows were graded after the lock, rather than attaching a p-value to a
    different sample."""
    allr = H._read(H.out_path(e))
    n = int(locked_row["n"])
    g = allr[:n]
    if len(g) != n or any((r.get("graded_at") or "")[:10] > locked_row["locked_at"] for r in g):
        return None
    xs = [_f(r["excess_1d"]) for r in g if _f(r["excess_1d"]) is not None]
    tk = [r["ticker"] for r in g if _f(r["excess_1d"]) is not None]
    reps = boot_means(xs, tk)
    return p_two_sided(reps) if reps else None


# ------------------------------------------------------------------ family
def family_pass(today):
    locked = H.locked_verdicts()
    exp02 = {r["experiment"]: r for r in H._read(EXP02_LOCK)}
    decided = {r["experiment"]: r for r in H._read(FDR_LOCK)}
    pv, verdicts = {}, {}
    for e in H.EXPERIMENTS:
        if e["id"] in locked:
            p = harness_p(e, locked[e["id"]])
            if p is not None:
                pv[e["id"]] = p
                verdicts[e["id"]] = locked[e["id"]]["verdict"]
            else:
                print(f"  {e['id']}: locked n does not reproduce from graded_at — p withheld, flag for review")
    if "EXP02-RSI2" in exp02:
        pv["EXP02-RSI2"] = float(exp02["EXP02-RSI2"]["p_two"])
        verdicts["EXP02-RSI2"] = exp02["EXP02-RSI2"]["verdict"]
    vec = [pv.get(x, 1.0) for x in FAMILY]
    adj = dict(zip(FAMILY, bh_adjust(vec)))
    new = []
    for x in FAMILY:
        if x in decided or x not in pv:
            continue
        own = verdicts[x]
        sig = own.startswith("CLEARS") or own.startswith("SIGNIFICANTLY NEGATIVE")
        if sig and adj[x] <= Q:
            status = "SURVIVES the family correction"
        elif sig:
            status = "CONSISTENT WITH CHANCE after the family correction"
        else:
            status = "no discovery to correct"
        new.append({"experiment": x, "decided_at": today, "own_verdict": own,
                    "p_two": round(pv[x], 5), "m": M,
                    "p_values_used": ";".join(f"{k}={pv.get(k, 1.0):.4g}" for k in FAMILY),
                    "bh_adjusted_p": round(adj[x], 5), "q": Q, "family_status": status})
    if new:
        H._append(FDR_LOCK, FDR_FIELDS, new)
    return {r["experiment"]: r for r in H._read(FDR_LOCK)}


def write_report(today, exp02_state, fdr):
    L = [f"# ThePickLog — family verdict (EXP02–EXP09) · {today}", "",
         f"Read date {READ_ON}. Benjamini–Hochberg at q = {Q} across the declared family of "
         f"**m = {M}** (EXP02–EXP09); experiments not yet locked count as p = 1. Each row below "
         "was computed once, at the run where that experiment's own verdict locked, and is "
         "never recomputed. Rules: `family_verdict.py` (frozen 2026-10-23, before the read).", ""]
    e2 = {r["experiment"]: r for r in H._read(EXP02_LOCK)}.get("EXP02-RSI2")
    if e2:
        L += [f"**EXP02 (locked {e2['locked_at']}):** {e2['verdict']} — n={e2['n']} over "
              f"{e2['clusters']} names; excess (1 session) mean {float(e2['mean1']):+.3f}%, median "
              f"{float(e2['med1']):+.3f}%, clustered 95% CI [{e2['ci_lo']}, {e2['ci_hi']}]; weekly "
              f"snapshots {e2['snapshots']}. Secondary exits (cannot rescue a fail): 5-session mean "
              f"{e2['mean5']}, RSI-exit mean {e2['mean_rsiexit']}.", ""]
    else:
        L += [f"**EXP02:** not locked — n={exp02_state.get('n')}/{EXP02_MIN_N}, "
              f"{exp02_state.get('clusters')}/{EXP02_MIN_TICKERS} names. Underpowered, not failed; "
              "it locks at the first run where both floors are met.", ""]
    L += ["| experiment | own verdict | p (two-sided) | BH-adjusted p | family status | decided |",
          "|---|---|---|---|---|---|"]
    for x in FAMILY:
        r = fdr.get(x)
        if r:
            L.append(f"| {x} | {r['own_verdict']} | {r['p_two']} | {r['bh_adjusted_p']} | "
                     f"**{r['family_status']}** | {r['decided_at']} |")
        else:
            L.append(f"| {x} | not locked yet | — | — | counts as p = 1 | — |")
    L += ["", "A single pass that does not survive the correction is reported as *consistent with "
          "chance* until it survives a fresh forward window. EXP06–EXP09 share one universe, so "
          "they are correlated tests, not independent replications. Not investment advice."]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with io.open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"wrote {REPORT}")


def run(today=None):
    today = today or datetime.now(timezone.utc).date().isoformat()
    if today < READ_ON:
        print(f"family_verdict: not due — the single read is on/after {READ_ON} (today {today}). "
              "Nothing computed, nothing printed.")
        return 0
    rows = H._read(RSI2_OUT)
    s = exp02_read(rows, today)
    if s.get("verdict"):
        lock_exp02(s, today)
    fdr = family_pass(today)
    write_report(today, s, fdr)
    return 0


# ------------------------------------------------------------------ selftest
def _selftest():
    fails = []

    def check(name, got, want):
        if got != want:
            fails.append(f"{name}: got {got!r}, want {want!r}")

    # BH against a hand-worked case.
    adj = bh_adjust([0.01, 0.04, 0.03, 0.2, 1, 1, 1, 1])
    check("BH smallest", round(adj[0], 4), 0.08)
    check("BH ties step-up", round(adj[2], 4), round(adj[1], 4))
    check("BH monotone", all(a <= 1 for a in adj), True)
    check("m=8 makes p=.01 fail q=.05", adj[0] <= Q, False)
    check("p=.005 alone survives at m=8", bh_adjust([0.005] + [1] * 7)[0] <= Q, True)

    # Bootstrap must reproduce the harness interval exactly.
    rnd = random.Random(1)
    xs = [rnd.gauss(0.3, 1) for _ in range(60)]
    tk = [f"T{i % 25}" for i in range(60)]
    reps, ci = boot_means(xs, tk), H.cluster_ci(xs, tk)
    check("CI lo matches harness", reps[int(0.025 * len(reps))], ci["lo"])
    check("CI hi matches harness", reps[min(len(reps) - 1, int(0.975 * len(reps)))], ci["hi"])
    check("strong effect p small", p_two_sided(boot_means([1.0 + 0.01 * i for i in range(40)],
                                                          [f"T{i % 20}" for i in range(40)])) < 0.01, True)

    # Snapshot calendar: Saturdays, ending on/before the read.
    sat = saturdays_upto("2026-11-02")
    check("last snapshot is the Saturday before", sat[-1], "2026-10-31")
    check("all Saturdays", all(datetime.strptime(d, "%Y-%m-%d").weekday() == 5 for d in sat), True)

    # EXP02 read on synthetic rows: positive, then a run that flips sign in the last week.
    def mk(i, ex, gd):
        return {"signal_date": "2026-08-%02d" % (1 + i % 28), "graded_at": gd + "T21:00:00+00:00",
                "ticker": f"T{i % 24}", "excess_1d": str(ex), "excess_5d": "0", "excess_rsiexit": "0"}
    pos = [mk(i, 0.8 + 0.01 * i, "2026-09-01") for i in range(40)]
    st = exp02_read(pos, "2026-11-02")
    check("EXP02 positive clears", (st["verdict"] or "").startswith("CLEARS"), True)
    late_neg = pos + [mk(100 + i, -5.0, "2026-10-30") for i in range(40)]
    st2 = exp02_read(late_neg, "2026-11-02")
    check("EXP02 recent flip does not clear", (st2["verdict"] or "").startswith("CLEARS"), False)
    thin = exp02_read(pos[:20], "2026-11-02")
    check("EXP02 underpowered writes no verdict", thin["verdict"], None)
    pre = [dict(r, signal_date="2026-07-29") for r in pos]
    check("EXP02 window excludes registration day", exp02_read(pre, "2026-11-02")["n"], 0)

    check("gate before read date", run("2026-10-23"), 0)

    if fails:
        print("SELFTEST FAILED:")
        [print("  -", f) for f in fails]
        return 1
    print("family_verdict selftest PASS — BH (m=8), bootstrap parity with harness, snapshots, "
          "EXP02 bar, date gate")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(_selftest() if a.selftest else run())
