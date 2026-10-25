#!/usr/bin/env python3
"""
One-off, reproducible correction for the 5-DAY WINDOW DEFECT found 2026-10-25.

WHAT WAS WRONG
    40 graded picks have a stored 5-day window (paths.csv) that SKIPS a real NYSE session:
    2026-08-11 (19 windows), 2026-08-28 (9) and 2026-09-22 (12). Yahoo's daily history was
    missing that session when the grader ran, so the "5th session after entry" the grader
    used was really the 6th. Anyone can find these with paths.csv and the NYSE calendar
    alone — no price feed needed:

        python fix_window5d_2026_10_25.py --find

    The headline figure (same-day open->close) is NOT affected: the entry bar is identical
    in every case and is kept byte-for-byte. Affected: ret_open_5dclose_net, mfe_5d, mae_5d.

WHAT THIS DOES
    Applies corrections/window5d-2026-10-25.csv to outcomes.csv and paths.csv:
      * 38 windows re-graded on the true 6-session window from Yahoo's final daily bars,
        same grader formula ((close5-open)/open*100-2, max high / min low over the window).
        Where a later split re-scaled Yahoo's history, bars are shown on the grade-time
        scale so they line up with entry_open.
      * 2 windows (HKIT, IPW 2026-09-16) are no longer priceable, so the true window cannot
        be fetched; they get an explicit note instead of a guessed number.
      * every cell is checked against its expected OLD value before it is changed; only the
        affected lines are rewritten, every other line stays byte-identical; idempotent.

    Then seal the ledger:  python log_integrity.py --event=correction-window5d-2026-10-25
"""
import csv, io, sys, datetime as dt
from collections import defaultdict

CORR = "corrections/window5d-2026-10-25.csv"


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


def find_misaligned():
    from market_time import is_session

    def nxt(d):
        d = dt.date.fromisoformat(d)
        while True:
            d += dt.timedelta(days=1)
            if is_session(d.isoformat()):
                return d.isoformat()

    bars = defaultdict(dict)
    for r in csv.DictReader(open("paths.csv")):
        bars[r["pick_id"]][int(r["session_idx"])] = r
    out = []
    for pid, b in bars.items():
        ds = [b[i]["bar_date"] for i in sorted(b)]
        exp = [ds[0]]
        while len(exp) < len(ds):
            exp.append(nxt(exp[-1]))
        if ds != exp:
            out.append((b[0]["ticker"], b[0]["trading_date"], sorted(set(exp) - set(ds))))
    return out


def main():
    if "--find" in sys.argv:
        bad = find_misaligned()
        print(f"{len(bad)} stored 5-day window(s) skip a real NYSE session")
        for t, d, miss in sorted(bad, key=lambda x: (x[1], x[0])):
            print(f"  {t:<6} {d}  missing {','.join(miss)}")
        return 0

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
    left = find_misaligned()
    print(f"outcomes.csv: {n_o} rows changed · paths.csv: {n_p} rows changed · "
          f"misaligned windows remaining: {len(left)} (expected 2: HKIT, IPW 2026-09-16, unpriceable, noted)")
    return 0 if len(left) <= 2 else 1


if __name__ == "__main__":
    sys.exit(main())
