#!/usr/bin/env python3
"""
market_time.py — one definition of "was this pick logged before the open?"

WHY THIS EXISTS
---------------
The whole record rests on a single claim: every pick was written down before
the market opened, so nobody could have known the outcome. On 2026-08-04 an
outside review found that claim was false for 128 picks across 7 cohorts —
the scheduled scan had drifted past the 09:30 ET opening bell by 2 to 72
minutes and logged anyway. See AUDIT_LOG.md 2026-08-04 and
/late-cohorts.html for the full disclosure.

GitHub Actions cron is explicitly best-effort: a run scheduled for 07:30 ET
can start an hour later under load. The scanner guarded against holidays and
against a frozen quote feed, but never checked the clock. So this module
provides two things, and both of them are enforced rather than assumed:

  pre_open_guard()  the scanner refuses to log anything at or after the
                    cutoff. A late run produces NO picks. Ever.
  is_timely()       every analysis surface derives, from the public CSV,
                    whether a given row beat the bell — so a stranger can
                    recompute the same exclusion we apply.

Deriving timeliness (rather than storing a flag) is deliberate: the inputs
are already public in picks.csv, so the exclusion itself is verifiable and
cannot silently disagree with the data.

DST is handled properly via zoneinfo. 09:30 ET is 13:30 UTC in summer and
14:30 UTC in winter; hard-coding either would have broken the check for half
the year.
"""

from datetime import datetime, time as _time
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

# NYSE regular session opening auction.
MARKET_OPEN = _time(9, 30)

# The scanner must be finished well before the bell, not merely at it. A run
# that starts at 09:29 is not "on time", it is a near miss that happened to
# land. Ten minutes of margin, chosen so that ordinary Actions scheduling
# jitter fails loudly instead of silently producing a contaminated cohort.
SCAN_CUTOFF = _time(9, 20)


def now_et():
    """Current wall-clock time in US market time, regardless of runner TZ."""
    return datetime.now(ET)


def trading_date_et(now=None):
    """Today's date in market time.

    Derived in ET rather than from the runner's clock: CI runs in UTC, and a
    job firing late in the UTC evening would otherwise stamp tomorrow's date
    on an American session that has already closed.
    """
    return (now or now_et()).astimezone(ET).strftime("%Y-%m-%d")


def _et(ts):
    """Parse an ISO-8601 timestamp from the log into market time."""
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return None
    if dt.tzinfo is None:                       # naive stamps are UTC by convention here
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(ET)


def is_timely(published_at, trading_date):
    """True if this pick was logged strictly before its own session opened.

    A row missing either field cannot be shown to have beaten the bell, so it
    is treated as untimely. Failing closed is the only safe direction: the
    cost of wrongly excluding a pick is a slightly smaller sample, and the
    cost of wrongly including one is a return computed against a price that
    had already printed.
    """
    t = _et(published_at)
    if t is None or not trading_date:
        return False
    try:
        session = datetime.strptime(trading_date, "%Y-%m-%d")
    except ValueError:
        return False
    open_et = datetime.combine(session.date(), MARKET_OPEN, tzinfo=ET)
    return t < open_et


def is_timely_row(row):
    """is_timely() for a picks.csv DictReader row."""
    return is_timely(row.get("published_at"), row.get("trading_date"))


def split_timely(rows):
    """Partition picks.csv rows into (timely, late)."""
    timely, late = [], []
    for r in rows:
        (timely if is_timely_row(r) else late).append(r)
    return timely, late


def late_cohort_summary(rows):
    """{trading_date: n_late} — for reporting what an exclusion actually dropped.

    Every surface that filters must be able to say what it removed. Silent
    truncation reads as "we covered everything" when we did not, which is the
    exact failure this module exists to correct.
    """
    out = {}
    for r in rows:
        if not is_timely_row(r):
            d = r.get("trading_date") or "?"
            out[d] = out.get(d, 0) + 1
    return dict(sorted(out.items()))


def pre_open_guard(trading_date=None, now=None):
    """(blocked, detail) — may the scanner log a cohort for this session?

    Blocks at or after SCAN_CUTOFF on the session's own date. Callers must
    exit without writing when blocked: a partial or late cohort is worse than
    no cohort, because it silently contaminates the headline for months.
    """
    now = (now or now_et()).astimezone(ET)
    trading_date = trading_date or trading_date_et(now)
    try:
        session = datetime.strptime(trading_date, "%Y-%m-%d").date()
    except ValueError:
        return True, f"unparseable trading_date {trading_date!r}"

    if now.date() > session:
        return True, f"session {trading_date} is already in the past (now {now:%Y-%m-%d %H:%M %Z})"
    if now.date() < session:
        return False, ""                      # scanning ahead of the session is fine

    cutoff = datetime.combine(session, SCAN_CUTOFF, tzinfo=ET)
    if now >= cutoff:
        opened = datetime.combine(session, MARKET_OPEN, tzinfo=ET)
        rel = (now - opened).total_seconds() / 60.0
        when = (f"{rel:+.0f} min relative to the 09:30 open"
                if abs(rel) < 600 else f"{now:%H:%M %Z}")
        return True, (f"scan started {now:%H:%M:%S %Z}, at or past the {SCAN_CUTOFF:%H:%M} ET "
                      f"cutoff for {trading_date} ({when})")
    return False, ""


if __name__ == "__main__":
    # Selftest — runs without network. `python3 market_time.py`
    import sys
    fails = []

    def check(label, got, want):
        if got != want:
            fails.append(f"{label}: got {got!r}, want {want!r}")

    # DST both ways: 09:30 ET is 13:30Z in summer, 14:30Z in winter.
    check("summer 13:29Z is timely", is_timely("2026-07-09T13:29:00+00:00", "2026-07-09"), True)
    check("summer 13:30Z is late",   is_timely("2026-07-09T13:30:00+00:00", "2026-07-09"), False)
    check("summer 13:31Z is late",   is_timely("2026-07-09T13:31:00+00:00", "2026-07-09"), False)
    check("winter 14:29Z is timely", is_timely("2026-12-09T14:29:00+00:00", "2026-12-09"), True)
    check("winter 14:30Z is late",   is_timely("2026-12-09T14:30:00+00:00", "2026-12-09"), False)
    check("winter 13:30Z is timely", is_timely("2026-12-09T13:30:00+00:00", "2026-12-09"), True)

    # Real rows from the incident.
    check("06-15 cohort late", is_timely("2026-06-15T13:32:06+00:00", "2026-06-15"), False)
    check("07-06 cohort late", is_timely("2026-07-06T14:42:17+00:00", "2026-07-06"), False)
    check("normal 07:30 ET scan", is_timely("2026-07-08T11:30:12+00:00", "2026-07-08"), True)

    # Fail closed on junk.
    check("missing stamp", is_timely("", "2026-07-09"), False)
    check("missing date",  is_timely("2026-07-09T11:00:00+00:00", ""), False)
    check("junk stamp",    is_timely("not-a-date", "2026-07-09"), False)

    # Guard.
    def at(s):
        return datetime.fromisoformat(s).astimezone(ET)
    check("guard 07:30 ET open",  pre_open_guard("2026-07-09", at("2026-07-09T11:30:00+00:00"))[0], False)
    check("guard 09:19 ET open",  pre_open_guard("2026-07-09", at("2026-07-09T13:19:00+00:00"))[0], False)
    check("guard 09:20 ET block", pre_open_guard("2026-07-09", at("2026-07-09T13:20:00+00:00"))[0], True)
    check("guard 09:57 ET block", pre_open_guard("2026-07-09", at("2026-07-09T13:57:00+00:00"))[0], True)
    check("guard past session",   pre_open_guard("2026-07-08", at("2026-07-09T11:00:00+00:00"))[0], True)
    check("guard future session", pre_open_guard("2026-07-10", at("2026-07-09T11:00:00+00:00"))[0], False)

    if fails:
        print("SELFTEST FAILED:"); [print("  -", f) for f in fails]; sys.exit(1)
    print("market_time selftest OK")
