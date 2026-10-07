#!/usr/bin/env python3
"""
One-off, reproducible correction for INCIDENT 2026-10-07 (NaN 5-day grades).

Applies corrections/nan5d-2026-10-07.csv to outcomes.csv and paths.csv:
  * every listed field is checked against its expected OLD value before it is changed
    (paths rows: the 5th-session bar must currently have Close == 'nan');
  * only the affected lines are rewritten — every other line stays byte-identical;
  * idempotent: re-running after success changes nothing and exits 0.
Then seal the ledger:  python log_integrity.py --event=correction-nan5d-2026-10-07

Anyone can audit it: each new value is reproducible from Yahoo's final daily bars with the
grader's own formula; the CSV lists old value, new value and reason for every cell.
"""
import csv, io, sys
from collections import defaultdict

CORR = "corrections/nan5d-2026-10-07.csv"

def norm(v): return (v or "").strip().lower()

def rewrite(path, key_fn, apply_fn):
    raw = open(path, "rb").read().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(nl)
    header = next(csv.reader([lines[0]]))
    changed = 0
    for i in range(1, len(lines)):
        if not lines[i]: continue
        vals = next(csv.reader([lines[i]]))
        row = dict(zip(header, vals))
        k = key_fn(row)
        if k is None: continue
        new = apply_fn(k, row)
        if new is None: continue
        buf = io.StringIO(); csv.writer(buf, lineterminator="").writerow([new.get(h, "") for h in header])
        if buf.getvalue() != lines[i]:
            lines[i] = buf.getvalue(); changed += 1
    open(path, "wb").write(nl.join(lines).encode("utf-8"))
    return changed

def main():
    corr = list(csv.DictReader(open(CORR)))
    oc = defaultdict(list); pc = defaultdict(list)
    for c in corr:
        (oc if c["file"] == "outcomes.csv" else pc)[c["pick_id"]].append(c)
    errors = []

    def fix_outcome(pid, row):
        out = dict(row)
        for c in oc[pid]:
            f, cur = c["field"], row.get(c["field"], "")
            if f == "note":
                if c["new"] in cur: continue                      # already applied
                out[f] = c["new"] if not cur.strip() else f"{cur} | {c['new']}"
            elif norm(cur) == norm(c["new"]):
                continue                                          # already applied
            elif norm(cur) != norm(c["old"]):
                errors.append(f"{pid} {f}: expected {c['old']!r}, found {cur!r}")
            else:
                out[f] = c["new"]
        return out

    def fix_path(key, row):
        pid, idx = key
        if idx != "5": return None
        out = dict(row)
        want = {c["field"].split(".", 1)[1]: c["new"] for c in pc[pid]}
        if norm(row.get("close")) not in ("nan", norm(want.get("close"))):
            errors.append(f"{pid} paths session5: close is {row.get('close')!r}, expected 'nan'")
            return None
        out.update(want)
        return out

    n_o = rewrite("outcomes.csv", lambda r: r["pick_id"] if r["pick_id"] in oc else None, fix_outcome)
    n_p = rewrite("paths.csv", lambda r: (r["pick_id"], r["session_idx"]) if r["pick_id"] in pc else None, fix_path)
    if errors:
        print("REFUSED on some cells (left unchanged):"); print("\n".join(errors[:20])); return 1
    left = sum(1 for o in csv.DictReader(open("outcomes.csv")) if norm(o["ret_open_5dclose_net"]) == "nan")
    print(f"outcomes.csv: {n_o} rows changed · paths.csv: {n_p} rows changed · remaining NaN 5d: {left}")
    return 0 if left == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
