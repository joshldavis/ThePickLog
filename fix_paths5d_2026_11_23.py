#!/usr/bin/env python3
"""
One-off, reproducible correction for the paths.csv carry-over flagged by the weekly audits
of 2026-10-31, 11-07, 11-14 and 11-21 (issues #22, #26, #28): graded rows whose 5-day values
do not recompute from their own stored bars.

WHAT WAS WRONG
    All of them are rows the 2026-10-07 NaN correction (fix_nan5d_2026_10_07.py) touched.
    That correction had two gaps:
      * It swapped each unfinished 5th-session bar in paths.csv for Yahoo's final bar, but
        only rewrote mfe_5d / mae_5d where the swap moved them noticeably (7 rows). On 7 more
        rows the swap moved the window's high or low by a hair (the unfinished bar carried
        one more decimal), and the old MFE/MAE stayed. Off by 0.01-0.05pp:
        AVX 09-22 and CUPR 09-22 MFE; ATPC 09-23, QNME 09-23, ONCO 09-24, IFBD 09-25 and
        EZGO 09-25 MAE.
      * For the 4 GCDT rows (09-24 x2, 09-25, 09-28) it computed the 5-day net from a
        re-fetched, split-adjusted series and left the unfinished bar (close = nan) in
        paths.csv, so nobody could rebuild that net from the public file.

WHAT THIS DOES
    Applies corrections/paths5d-2026-11-23.csv to outcomes.csv and paths.csv:
      * GCDT: the unfinished session-5 bar is replaced with the final bar for the same session
        that the grader itself already stored in a neighbouring GCDT window (2026-10-01 from
        the 09-25 window, 10-02 from the 09-28 window, 10-05 from the 09-30 window, which is on
        the post-split scale and is divided by 6, volume x6). No new price feed is used: every
        new number is already in paths.csv. The 5-day net (and the 09-24 MAE) are then
        recomputed with the grader's own formula.
      * the 7 MFE/MAE cells are recomputed from the bars already stored.
      * every cell is checked against its expected OLD value before it is changed; only the
        affected lines are rewritten, every other line stays byte-identical; idempotent.
    The entry bar is untouched, so entry_open, same_day_close, ret_open_close_net and win
    (the headline figures) do not change.

    Check that every graded row recomputes from its bars (what the weekly audit's paths
    spot-check does; exits 1 on any failure):

        python fix_paths5d_2026_11_23.py --check

    No separate ledger event: the first scheduled CI scan or grade after merge seals the
    corrected files (see AUDIT_LOG 2026-11-23).
"""
import csv, io, math, sys
from collections import defaultdict

CORR = "corrections/paths5d-2026-11-23.csv"
FIELDS = ("ret_open_5dclose_net", "mfe_5d", "mae_5d")
# Stored values are rounded to 2dp from an unrounded entry_open; entry_open itself is stored
# at 4dp. Half a cent plus that slack: anything further off does not recompute.
TOL = 0.006


def norm(v):
    return (v or "").strip().lower()


def same(a, b):
    if norm(a) == norm(b):
        return True
    try:
        return abs(float(a) - float(b)) <= 1e-9
    except (TypeError, ValueError):
        return False


def rewrite(path, key_fn, apply_fn):
    raw = open(path, "rb").read().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(nl)
    header = next(csv.reader([lines[0]]))
    changed = 0
    for i in range(1, len(lines)):
        if not lines[i]:
            continue
        row = dict(zip(header, next(csv.reader([lines[i]]))))
        k = key_fn(row)
        if k is None:
            continue
        new = apply_fn(k, row)
        if new is None:
            continue
        buf = io.StringIO()
        csv.writer(buf, lineterminator="").writerow([new.get(h, "") for h in header])
        if buf.getvalue() != lines[i]:
            lines[i] = buf.getvalue()
            changed += 1
    return nl.join(lines).encode("utf-8"), changed


def check():
    """Every graded row with a full 6-bar window must recompute from its own bars."""
    bars = defaultdict(dict)
    for r in csv.DictReader(open("paths.csv")):
        bars[r["pick_id"]][int(r["session_idx"])] = r
    n, bad, gaps = 0, [], []
    for o in csv.DictReader(open("outcomes.csv")):
        if not o["ret_open_close_net"]:
            continue
        b = bars.get(o["pick_id"], {})
        if sorted(b) != list(range(6)):
            continue
        n += 1
        try:
            op = float(o["entry_open"])
            highs = [float(b[i]["high"]) for i in range(6)]
            lows = [float(b[i]["low"]) for i in range(6)]
            c5 = float(b[5]["close"])
        except ValueError:
            bad.append((o, "unreadable bar"))
            continue
        # The grader takes the window's max/min the way pandas does, skipping a NaN bar.
        # Do the same, but name any such bar: it is a no-trade day or a data hole, not a
        # recompute failure, and deciding what it means is a method call, not a fix.
        if not all(math.isfinite(v) for v in highs + lows):
            gaps.append(o)
        highs = [v for v in highs if math.isfinite(v)] or [float("nan")]
        lows = [v for v in lows if math.isfinite(v)] or [float("nan")]
        hi, lo = max(highs), min(lows)
        calc = {"ret_open_5dclose_net": (c5 - op) / op * 100 - 2,
                "mfe_5d": (hi - op) / op * 100, "mae_5d": (lo - op) / op * 100}
        for f in FIELDS:
            if not o[f]:
                continue
            if not (math.isfinite(calc[f]) and abs(float(o[f]) - calc[f]) <= TOL):
                bad.append((o, f"{f} stored {o[f]} vs bars {calc[f]:.4f}"))
    print(f"{n} graded rows have 6 bars; {len(bad)} do not recompute")
    for o, why in bad:
        print(f"  {o['ticker']:<6} {o['trading_date']}  {why}")
    if gaps:
        print(f"note: {len(gaps)} graded row(s) recompute but hold a non-finite bar inside the window:")
        for o in gaps:
            print(f"  {o['ticker']:<6} {o['trading_date']}")
    return 0 if not bad else 1


def main():
    if "--check" in sys.argv:
        return check()

    corr = list(csv.DictReader(open(CORR)))
    oc, pc = defaultdict(list), defaultdict(list)
    for c in corr:
        if c["file"] == "outcomes.csv":
            oc[c["pick_id"]].append(c)
        else:
            idx, fld = c["field"].split(".", 1)
            pc[(c["pick_id"], idx.replace("session", ""))].append(dict(c, field=fld))
    errors = []

    def apply(cells, label):
        def fn(key, row):
            out = dict(row)
            for c in cells[key]:
                f, cur = c["field"], row.get(c["field"], "")
                if same(cur, c["new"]):
                    continue                                   # already applied
                if not same(cur, c["old"]):
                    errors.append(f"{label} {key} {f}: expected {c['old']!r}, found {cur!r}")
                    return None
                out[f] = c["new"]
            return out
        return fn

    o_bytes, n_o = rewrite("outcomes.csv", lambda r: r["pick_id"] if r["pick_id"] in oc else None,
                           apply(oc, "outcomes"))
    p_bytes, n_p = rewrite("paths.csv",
                           lambda r: (r["pick_id"], r["session_idx"]) if (r["pick_id"], r["session_idx"]) in pc else None,
                           apply(pc, "paths"))
    if errors:
        print("REFUSED — nothing written. First mismatches:")
        print("\n".join(errors[:20]))
        return 1
    open("outcomes.csv", "wb").write(o_bytes)
    open("paths.csv", "wb").write(p_bytes)
    print(f"outcomes.csv: {n_o} rows changed · paths.csv: {n_p} rows changed")
    return check()


if __name__ == "__main__":
    sys.exit(main())
