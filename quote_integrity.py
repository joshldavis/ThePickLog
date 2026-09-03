#!/usr/bin/env python3
"""
quote_integrity.py — one definition of "did this quote actually move?"

WHY THIS EXISTS
---------------
On 2026-08-29 the weekly audit found BNZI had been screened for thirteen
consecutive sessions on a quote that never changed: price $1.91, gap **exactly
0.00%**, RVOL 0.59, float 1,352,833 — byte-identical, every session, from
2026-08-11 to 2026-08-26. A live stock does not gap exactly 0.00% thirteen
times running. The stock halted; Yahoo kept returning its last quote forever;
the scanner kept treating that corpse as a fresh screen and logging a pick.

This is the SAME defect as the phantom 2026-06-19 cohort, one level down. That
one was caught by `_is_stale_duplicate_scan`, which compares a WHOLE COHORT to
the previous session and so catches a fully frozen feed. It cannot catch a
single frozen ticker inside an otherwise-live cohort, because the other 23
names moved normally. Hence a per-ticker check.

THE RULE
--------
Within real trading sessions, a pick is a STALE-QUOTE ECHO if another pick for
the same ticker, on a different session, carries a byte-identical
(price_at_screen, gap_pct, rvol, float_shares).

Three properties earn it the right to remove rows from a public count:

  1. It is DERIVED, not stored. Every input is already in the public picks.csv,
     so a stranger recomputes the same set — the same standard the late-cohort
     exclusion is held to. Nothing is deleted.
  2. It is NOT threshold-tuned. Requiring the tuple to repeat 2+ times and 3+
     times give the identical answer on the current log (12 picks, all BNZI),
     so the finding is not an artifact of where the line was drawn.
  3. It VALIDATES ON KNOWN-GOOD DATA. Run without the session filter, it
     independently rediscovers the already-confirmed 06-19 phantom cohort
     (CUPR, GCDT, PW, IOTR, BJDX) without being told it exists. A rule that
     could not reproduce a phantom we already know about would be the defect.

The session filter is what keeps it off the 06-19 pairs' innocent twins: those
tickers screened identically on 06-19 (market closed) and 06-22 (real). 06-19
is not a session, so only the real 06-22 row survives into the comparison and
is correctly left alone.

DELIBERATELY CONSERVATIVE. The first appearance of a frozen tuple is never
flagged — only repeats are. BNZI 08-10 keeps the benefit of the doubt (its
RVOL was still moving, 0.58 → 0.59, before it too froze). When in doubt this
rule under-flags, because the cost of wrongly voiding a real forecast is much
higher than the cost of carrying one dead row.
"""

import csv
import sys
from collections import defaultdict

from market_time import is_session

# The fields that a real pre-market screen cannot repeat by chance. Price alone
# is not enough (a stock can legitimately open at the same price twice); the
# conjunction with gap and RVOL is what makes recurrence impossible.
QUOTE_KEY = ("price_at_screen", "gap_pct", "rvol", "float_shares")

MIN_REPEATS = 2


def _num(v):
    """One quote field in canonical numeric form, from EITHER row shape."""
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        if not v:
            return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _tuple(row):
    """The quote key, normalised so the two row shapes compare correctly.

    This function is handed rows from two places that do NOT look alike:
      * picks.csv via csv.DictReader — every field is a STRING;
      * a live screen from score_inputs() — price/gap/rvol are FLOAT, float_shares INT.

    It originally did `(row.get(k) or "").strip()`, which works only for the first.
    Production calls it with the second (is_stale_candidate, from cmd_scan), so it
    raised AttributeError on the very first candidate of every scan from the day it
    shipped, 2026-08-29 — unseen until 09-03 because the pre-open gate had refused
    every scan in between, so the scan body never ran. Its selftest fed only strings.

    Comparing numerically also fixes a second, quieter bug: string-comparing a live
    float 4.9 against the stored "4.90" could never match, so the guard would have
    silently never fired even without the crash. score_inputs() already rounds to the
    precision picks.csv stores (price 4dp, rvol/gap 2dp, float int), so the normalised
    values are exact on both sides. Verified against the live log: the derived
    exclusion set is byte-identical under both comparisons (12 rows), so no published
    number moves and index.html's JS mirror stays correct.
    """
    return tuple(_num(row.get(k)) for k in QUOTE_KEY)


def stale_quote_ids(rows, min_repeats=MIN_REPEATS):
    """pick_ids whose quote tuple recurs for the same ticker across sessions.

    `rows` is picks.csv as a list of dicts. Returns a set of pick_id.
    """
    groups = defaultdict(list)
    for r in rows:
        td = (r.get("trading_date") or "").strip()
        if not td or not is_session(td):
            continue
        groups[(r.get("ticker"), _tuple(r))].append(r)

    out = set()
    for members in groups.values():
        if len({m.get("trading_date") for m in members}) >= min_repeats:
            out.update(m.get("pick_id") for m in members)
    return out


def is_stale_candidate(ticker, quote, prior_rows):
    """Scan-time guard: would publishing this candidate create a stale-quote echo?

    `quote` is a dict carrying the QUOTE_KEY fields for the candidate about to be
    published; `prior_rows` is the existing picks.csv. True means the quote has
    not moved since the last time we screened this name, so it must not be logged.
    """
    want = _tuple(quote)
    # A quote we cannot read is not evidence of staleness. Fail OPEN here on purpose:
    # the cost of wrongly dropping a live pick is a hole in the record, while a stale
    # one that slips through is still caught by the cohort-level phantom detector and
    # by the derived exclusion applied at read time.
    if any(v is None for v in want):
        return False
    for r in prior_rows:
        if r.get("ticker") != ticker:
            continue
        td = (r.get("trading_date") or "").strip()
        if td and is_session(td) and _tuple(r) == want:
            return True
    return False


def _selftest():
    fails = []

    def check(name, got, want):
        if got != want:
            fails.append(f"{name}: got {got!r}, want {want!r}")

    def row(pid, tkr, td, px, gap, rvol="1.0", flt="1000"):
        return {"pick_id": pid, "ticker": tkr, "trading_date": td,
                "price_at_screen": px, "gap_pct": gap, "rvol": rvol,
                "float_shares": flt}

    # REGRESSION 2026-09-03 — the shape production actually passes. is_stale_candidate
    # is called from cmd_scan with a LIVE row (floats/ints), never with CSV strings.
    # Every test below this point used strings only, so a crash on the real caller's
    # input went unseen from 08-29 until it destroyed a valid 14-name screen on 09-03.
    live_row = {"ticker": "NCT", "price_at_screen": 4.9, "gap_pct": -6.13,
                "rvol": 13.75, "float_shares": 400000}
    prior_same = [row("p", "NCT", "2026-09-02", "4.9", "-6.13", "13.75", "400000")]
    prior_moved = [row("p", "NCT", "2026-09-02", "4.9", "1.20", "13.75", "400000")]
    check("live float row does not raise",
          is_stale_candidate("NCT", live_row, []), False)
    check("live float row matches stored string quote",
          is_stale_candidate("NCT", live_row, prior_same), True)
    check("live float row vs moved gap is not stale",
          is_stale_candidate("NCT", live_row, prior_moved), False)
    check("unreadable quote is never stale",
          is_stale_candidate("NCT", {"ticker": "NCT"}, prior_same), False)

    # A frozen ticker across three sessions: every member flagged.
    frozen = [row("a", "DEAD", "2026-08-11", "1.91", "0.0"),
              row("b", "DEAD", "2026-08-12", "1.91", "0.0"),
              row("c", "DEAD", "2026-08-13", "1.91", "0.0")]
    check("frozen run flagged", stale_quote_ids(frozen), {"a", "b", "c"})

    # A live ticker at the same price but a different gap is NOT frozen — this is
    # the case that keeps ordinary repeat screens of the same name in the record.
    live = [row("a", "LIVE", "2026-08-11", "1.91", "7.91"),
            row("b", "LIVE", "2026-08-12", "1.91", "0.4")]
    check("same price, moving gap", stale_quote_ids(live), set())

    # One appearance is never an echo.
    check("single row", stale_quote_ids([row("a", "X", "2026-08-11", "1.0", "1.0")]), set())

    # The 06-19 shape: identical tuples on a holiday and the next real session.
    # The holiday row is not a session, so the real row must survive unflagged.
    holiday = [row("a", "PW", "2026-06-19", "9.54", "2.03"),
               row("b", "PW", "2026-06-22", "9.54", "2.03")]
    check("holiday twin spares the real row", stale_quote_ids(holiday), set())

    # Same tuple, same date (a duplicate row rather than a frozen quote) is not
    # an echo — it needs to recur on a DIFFERENT session.
    dup = [row("a", "X", "2026-08-11", "1.0", "1.0"),
           row("b", "X", "2026-08-11", "1.0", "1.0")]
    check("same-session duplicate", stale_quote_ids(dup), set())

    # Scan-time guard.
    prior = [row("a", "DEAD", "2026-08-11", "1.91", "0.0")]
    check("guard blocks frozen",
          is_stale_candidate("DEAD", {"price_at_screen": "1.91", "gap_pct": "0.0",
                                      "rvol": "1.0", "float_shares": "1000"}, prior), True)
    check("guard passes moved",
          is_stale_candidate("DEAD", {"price_at_screen": "1.95", "gap_pct": "2.1",
                                      "rvol": "1.0", "float_shares": "1000"}, prior), False)
    check("guard passes new name",
          is_stale_candidate("FRESH", {"price_at_screen": "1.91", "gap_pct": "0.0",
                                       "rvol": "1.0", "float_shares": "1000"}, prior), False)

    if fails:
        print("SELFTEST FAILED:")
        [print("  -", f) for f in fails]
        sys.exit(1)
    print("quote_integrity selftest OK")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        rows = list(csv.DictReader(open("picks.csv", newline="")))
        ids = stale_quote_ids(rows)
        hit = sorted((r["ticker"], r["trading_date"]) for r in rows if r["pick_id"] in ids)
        print(f"{len(ids)} stale-quote echoes across {len({t for t, _ in hit})} ticker(s)")
        for t, d in hit:
            print(f"  {t:<7}{d}")
    else:
        _selftest()
