#!/usr/bin/env python3
"""
log_integrity.py — tamper-evident hash chain for ThePickLog's immutable log.

WHY
    The forward log (picks.csv, outcomes.csv, paths.csv) is the entire basis of
    ThePickLog's verifiability claim. Git history makes it hard to change quietly,
    but a hash chain makes any retroactive edit *provable* — and a stranger can
    verify it themselves in one command, which is the north star.

WHAT IT DOES
    On each run (append mode, the default) it records one row in
    integrity_ledger.csv containing the SHA-256 of each log file plus a
    running chain hash that folds in the previous row. Changing any historical
    file, or editing a past ledger row, breaks the chain from that point on and
    `--verify` will report exactly where.

CHAIN DEFINITION (documented so anyone can reproduce it)
    file_sha  = sha256(raw bytes of the file); literal "MISSING" if absent.
    genesis prev_chain = "0" * 64
    chain     = sha256( prev_chain | picks_sha | outcomes_sha | paths_sha | ts | event )
                where "|" is a literal pipe joining the hex/text fields, UTF-8 encoded.

USAGE
    python log_integrity.py                # append a new sealed row for today's files
    python log_integrity.py --verify       # recompute the whole chain, exit 1 on any break
    python log_integrity.py --verify-head  # additionally confirm CURRENT files match the last row
                                           # (only meaningful right after an append/commit)

    Stdlib only — no dependencies, deterministic, safe to run anywhere.
"""

import csv
import hashlib
import os
import sys
from datetime import datetime, timezone

LOG_FILES = ["picks.csv", "outcomes.csv", "paths.csv"]
LEDGER = "integrity_ledger.csv"
GENESIS = "0" * 64
FIELDS = ["ts", "event", "picks_sha256", "outcomes_sha256", "paths_sha256",
          "prev_chain", "chain"]


def sha256_file(path: str) -> str:
    """SHA-256 of the raw file bytes, or the literal 'MISSING' if absent."""
    if not os.path.exists(path):
        return "MISSING"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def chain_hash(prev_chain, picks_sha, outcomes_sha, paths_sha, ts, event) -> str:
    payload = "|".join([prev_chain, picks_sha, outcomes_sha, paths_sha, ts, event])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_ledger():
    if not os.path.exists(LEDGER):
        return []
    with open(LEDGER, newline="") as f:
        return list(csv.DictReader(f))


def last_chain(rows) -> str:
    return rows[-1]["chain"] if rows else GENESIS


def append(event="seal"):
    rows = read_ledger()
    prev = last_chain(rows)
    ts = datetime.now(timezone.utc).isoformat()
    shas = {name: sha256_file(name) for name in LOG_FILES}
    picks_sha, outcomes_sha, paths_sha = (shas["picks.csv"],
                                          shas["outcomes.csv"],
                                          shas["paths.csv"])
    ch = chain_hash(prev, picks_sha, outcomes_sha, paths_sha, ts, event)

    new_file = not os.path.exists(LEDGER)
    with open(LEDGER, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerow({
            "ts": ts, "event": event,
            "picks_sha256": picks_sha,
            "outcomes_sha256": outcomes_sha,
            "paths_sha256": paths_sha,
            "prev_chain": prev, "chain": ch,
        })
    print(f"[integrity] sealed {ts} event={event}")
    for name in LOG_FILES:
        print(f"[integrity]   {name}: {shas[name]}")
    print(f"[integrity]   chain: {ch}")
    return 0


def verify(check_head=False) -> int:
    rows = read_ledger()
    if not rows:
        print("[integrity] no ledger yet — nothing to verify.")
        return 0
    prev = GENESIS
    for i, r in enumerate(rows):
        if r["prev_chain"] != prev:
            print(f"[integrity] BREAK at row {i}: prev_chain mismatch "
                  f"(expected {prev[:12]}…, found {r['prev_chain'][:12]}…)")
            return 1
        recomputed = chain_hash(prev, r["picks_sha256"], r["outcomes_sha256"],
                                r["paths_sha256"], r["ts"], r["event"])
        if recomputed != r["chain"]:
            print(f"[integrity] BREAK at row {i} ({r['ts']}): chain hash does not "
                  f"recompute — a field in this row was altered.")
            return 1
        prev = r["chain"]
    print(f"[integrity] OK — {len(rows)} sealed rows form an unbroken chain "
          f"back to genesis. Head chain: {prev}")

    if check_head:
        last = rows[-1]
        for name, col in zip(LOG_FILES,
                             ["picks_sha256", "outcomes_sha256", "paths_sha256"]):
            now = sha256_file(name)
            if now != last[col]:
                print(f"[integrity] HEAD MISMATCH: {name} on disk ({now[:12]}…) "
                      f"differs from last sealed row ({last[col][:12]}…). "
                      f"Either files changed since the last seal, or were tampered.")
                return 1
        print("[integrity] HEAD OK — current files match the last sealed row.")
    return 0


def main(argv):
    if "--verify-head" in argv:
        return verify(check_head=True)
    if "--verify" in argv:
        return verify(check_head=False)
    event = "seal"
    for a in argv:
        if a.startswith("--event="):
            event = a.split("=", 1)[1]
    return append(event=event)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
