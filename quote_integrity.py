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


# ---------------------------------------------------------------- scale reconciliation
# A stale SCALE is invisible to every staleness test ever written. VMAR reverse-split
# ~1:10 on 2026-08-18; the market moved, our quote feed did not, and for seven graded
# sessions price_at_screen sat at $0.67-0.72 against a real opening price of $6.48-7.56.
# The frozen-quote guard above saw nothing wrong, correctly: the price ticked 0.714 →
# 0.703 → 0.668 → 0.7035 like a living stock. It was CHANGING. It was just changing on
# a scale that no longer existed.
#
# The only thing that catches this is reconciling the screen-time observation against an
# INDEPENDENT later observation of the same quantity — and entry_open had been sitting in
# outcomes.csv the whole time. Both inputs are public, so a stranger recomputes the
# identical set and nothing is deleted, exactly like the late-cohort and frozen-quote seals.
#
# The band is not delicate: the whole log runs p1 = 0.84 to p99 = 1.78, and only 10 of 983
# graded rows fall outside [0.5, 2.0] — the 7 VMAR rows at 9.19-10.53x plus three single
# sessions of the same class (SUGP 2.73x, CPHI 0.40x, SLE 2.30x).
#
# NOTE ON ORDERING: this exclusion is applied at READ time, never at grade time. It needs
# entry_open, which only exists after a pick is graded, so the grader cannot consult it
# without a circular dependency. Grade everything; exclude when reporting.
SCALE_LO, SCALE_HI = 0.5, 2.0


def scale_mismatch_ids(picks, outcomes):
    """pick_ids whose screen price and grade-time entry_open are on different scales.

    `picks` is picks.csv and `outcomes` outcomes.csv, both as lists of dicts. A pick with
    no graded outcome cannot be checked and is never flagged.

    What this does and does not impugn: the RETURN on these rows is sound — entry_open and
    same_day_close come from the same post-split series and reconcile to the 2% haircut
    like every other row. What is damaged is SELECTION: gap_pct was computed against a
    stale prior close, and gap is the dominant score input, so the score and tier on these
    rows do not describe the stock that actually traded. They are not evidence about the
    screen.
    """
    entry = {}
    for o in outcomes:
        pid = (o.get("pick_id") or "").strip()
        eo = _num(o.get("entry_open"))
        if pid and eo:
            entry[pid] = eo
    out = set()
    for p in picks:
        pid = (p.get("pick_id") or "").strip()
        px = _num(p.get("price_at_screen"))
        eo = entry.get(pid)
        if not pid or not px or not eo or px <= 0:
            continue
        ratio = eo / px
        if ratio < SCALE_LO or ratio > SCALE_HI:
            out.add(pid)
    return out


# Price band within which a price counts as "did not move" for the purposes below.
FLAT_LO, FLAT_HI = 0.8, 1.25


def is_corporate_action(ticker, quote, prior_rows, lo=SCALE_LO, hi=SCALE_HI):
    """(suspected, detail) — scan-time SUSPICION that the float and price feeds disagree.

    The split signature was sitting in our own CSV and nothing read it: on 2026-08-26
    VMAR's float divided by ten while its price did not, so that row screened a 227K float
    against a $0.72 price at the same instant — two mutually contradictory scales inside
    one record, and precisely the combination the score rewards most.

    ⚠️ THIS IS A WARNING, NOT A FILTER, AND THAT IS DELIBERATE — SEE THE NUMBERS.
    `float_shares` on these names is approximated from shares outstanding and is revised
    between sessions, so it is a NOISY series. Replayed over the whole live log, a rule
    that dropped candidates on this signal would have removed **11 picks** on the
    flat-price form (16 on a float×price form) against exactly **one** genuine defect,
    VMAR 08-26. Names like NCT (3.49x), BJDX (3.36x) and JAGX (8.57x) simply had their
    reported float revised. Dropping those would be a selection distortion — the same
    harm class as the contamination this exists to catch, and the same mistake the
    frozen-quote guard made on 2026-09-03 when it destroyed a valid cohort.

    The PRECISE instrument is `scale_mismatch_ids` at read time, which reconciles against
    `entry_open` — a genuinely independent observation — and selects exactly the ten
    contaminated rows with no false positives. This function exists to make the condition
    VISIBLE in the run log on the morning it happens, rather than a week later in an audit.

    Signature: the float re-scales while the price stays essentially flat. A real
    corporate action large enough to move float by >2x necessarily moves the price too,
    so a flat price alongside a re-scaled float means the two feeds are not describing
    the same instant.
    """
    prev = None
    for r in prior_rows:
        if (r.get("ticker") or "") != ticker:
            continue
        td = (r.get("trading_date") or "").strip()
        if not td or not is_session(td):
            continue
        if prev is None or td > (prev.get("trading_date") or ""):
            prev = r
    if prev is None:
        return False, ""
    f_now, f_prev = _num(quote.get("float_shares")), _num(prev.get("float_shares"))
    p_now, p_prev = _num(quote.get("price_at_screen")), _num(prev.get("price_at_screen"))
    if not f_now or not f_prev or not p_now or not p_prev or f_prev <= 0 or p_prev <= 0:
        return False, ""
    fr = f_now / f_prev
    if lo <= fr <= hi:
        return False, ""                       # float did not re-scale; nothing to check
    pr = p_now / p_prev
    if not (FLAT_LO <= pr <= FLAT_HI):
        return False, ""                       # price moved too — a real corporate action
    return True, (f"float moved {fr:.3f}x since {prev.get('trading_date')} while the price "
                  f"barely moved ({pr:.3f}x) — the float and price feeds may be on "
                  f"different scales; if this name grades with entry_open far from "
                  f"price_at_screen it will be excluded by scale_mismatch_ids")


def _selftest():
    fails = []

    def check(name, got, want):
        if got != want:
            fails.append(f"{name}: got {got!r}, want {want!r}")

    def row(pid, tkr, td, px, gap, rvol="1.0", flt="1000"):
        return {"pick_id": pid, "ticker": tkr, "trading_date": td,
                "price_at_screen": px, "gap_pct": gap, "rvol": rvol,
                "float_shares": flt}

    # SCALE RECONCILIATION 2026-09-12 — the VMAR reverse-split class.
    def orow(pid, eo):
        return {"pick_id": pid, "entry_open": eo}

    split_pick = [row("v1", "VMAR", "2026-08-18", "0.714", "7.37"),
                  row("v2", "VMAR", "2026-08-17", "0.665", "1.0")]
    split_out = [orow("v1", "7.20"), orow("v2", "0.66")]
    check("reverse split flagged", scale_mismatch_ids(split_pick, split_out), {"v1"})
    check("same-scale row not flagged",
          scale_mismatch_ids([row("ok", "X", "2026-08-18", "5.00", "1.0")], [orow("ok", "5.10")]), set())
    check("ungraded pick never flagged",
          scale_mismatch_ids([row("ng", "X", "2026-08-18", "5.00", "1.0")], []), set())
    check("band edge 2.0 is inside",
          scale_mismatch_ids([row("e", "X", "2026-08-18", "1.00", "1.0")], [orow("e", "2.0")]), set())
    check("just past the band is flagged",
          scale_mismatch_ids([row("e2", "X", "2026-08-18", "1.00", "1.0")], [orow("e2", "2.01")]), {"e2"})
    check("forward split (0.4x) flagged",
          scale_mismatch_ids([row("f", "X", "2026-08-18", "7.26", "1.0")], [orow("f", "2.89")]), {"f"})

    # Scan-time corporate-action guard: float re-scales, price does not.
    prior_v = [row("p", "VMAR", "2026-08-25", "0.7082", "5.54", "1.0", "2270087")]
    now_v = {"ticker": "VMAR", "price_at_screen": 0.7182, "float_shares": 227009}
    check("float/10 with flat price is flagged",
          is_corporate_action("VMAR", now_v, prior_v)[0], True)
    # A REAL split moves both together — float/10 and price*10 — and must pass.
    check("float and price re-scale together is fine",
          is_corporate_action("VMAR", {"ticker": "VMAR", "price_at_screen": 7.082,
                                       "float_shares": 227009}, prior_v)[0], False)
    # A dilutive offering moves the price materially and must NOT be flagged.
    check("offering (float up, price down) is fine",
          is_corporate_action("VMAR", {"ticker": "VMAR", "price_at_screen": 0.12,
                                       "float_shares": 22700870}, prior_v)[0], False)
    check("ordinary day is fine",
          is_corporate_action("VMAR", {"ticker": "VMAR", "price_at_screen": 0.70,
                                       "float_shares": 2270087}, prior_v)[0], False)
    check("unknown ticker is fine", is_corporate_action("ZZZZ", now_v, prior_v)[0], False)

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
