#!/usr/bin/env python3
"""
watchdog_check.py — does the forward log actually cover the last market session?

WHY THIS EXISTS
---------------
The watchdog used to ask "has any forward-log file been committed recently?"
That question has a wrong answer built into it. On 2026-08-27 and 08-28 the
scan never ran, but the grade half of the daily job committed outcomes.csv and
paths.csv both nights, so the freshness test passed and no alarm was raised.
Two sessions went missing in public and the dead-man's-switch stayed green.

A freshness check that ANY job can satisfy cannot tell you that a PARTICULAR
job stopped. So this asks the only question that has the right answer:

    is the newest trading_date in picks.csv the last completed market session?

picks.csv is written by the scan and nothing else, and trading_date is content
rather than metadata, so no other job can accidentally satisfy it.

Emits shell-sourceable KEY=VALUE lines on stdout and exits 0 regardless — the
workflow decides what to do about the numbers. Exiting non-zero here would
just be a second way to fail silently, since a red watchdog run notifies
nobody by itself.
"""

import csv
import sys

from market_time import last_expected_scan_session, sessions_between

PICKS_CSV = "picks.csv"


def logged_sessions(path=PICKS_CSV):
    """Every distinct trading_date present in the pick log."""
    try:
        with open(path, newline="") as f:
            return {
                (r.get("trading_date") or "").strip()
                for r in csv.DictReader(f)
                if (r.get("trading_date") or "").strip()
            }
    except FileNotFoundError:
        return set()


def missing_sessions(dates, expected):
    """Sessions from the newest logged cohort through `expected` that have no cohort.

    Deliberately starts at the newest logged date rather than at the start of the
    record: this answers "have we stopped?", not "was the record ever complete?".
    Holes further back are the weekly verifiability audit's job, and folding them
    in here would make the alarm permanently loud — which is the same as off.
    """
    if not dates or not expected:
        return []
    return [s for s in sessions_between(max(dates), expected) if s not in dates]


def main():
    expected = last_expected_scan_session()
    dates = logged_sessions()
    newest = max(dates) if dates else ""
    missing = missing_sessions(dates, expected)
    # An empty or absent picks.csv is a bigger problem than a late scan, not a
    # smaller one, so it must not read as "gap 0". Fail loud, fail high.
    gap = len(missing) if newest else 999

    print(f"EXPECTED={expected or ''}")
    print(f"NEWEST={newest}")
    print(f"GAP={gap}")
    print("MISSING=" + ",".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
