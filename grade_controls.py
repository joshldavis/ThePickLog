#!/usr/bin/env python3
"""ThePickLog — forward grading for the CONTROL pool (closes H-CTRL).

WHY THIS EXISTS
    H-CTRL (registered 2026-07-07) asks the discriminant question the whole validity
    argument is missing: does the screen's published set actually outperform comparable
    names it looked at and did NOT publish? Until 2026-07-29 that was unanswerable —
    `candidates.csv` captured the control pool but no forward outcome was ever recorded
    for it, so there was nothing to compare against.

WHAT IT DOES
    Reads `candidates.csv`, takes the rows that were ELIGIBLE but NOT published
    (`eligible == "yes"` and `published != "1"`), and once a control's entry session is
    at least WINDOW sessions in the past, records its forward outcome into
    `control_outcomes.csv` using the SAME definitions as the pick grader:
        entry              = the entry session's OPEN
        ret_open_close_net = (same-day close - open)/open*100 - HAIRCUT
        ret_open_5dclose_net = (5th-session close - open)/open*100 - HAIRCUT
        mfe_5d / mae_5d    = best/worst excursion vs the entry open (NOT achievable returns)
        win                = sign of ret_open_close_net

DATA-INTEGRITY NOTES (read before trusting a comparison)
  * Append-only and forward-only. A control row is written once and never edited. A
    candidate already present in control_outcomes.csv is never regraded.
  * Entry and outcome come from the SAME fetch, so they are internally consistent. This
    is exactly how outcomes.csv is produced for picks, and it is NOT the defect that was
    removed from exit_sim.py on 2026-07-29 — that bug compared freshly re-fetched
    (split-adjusted) bars against an entry price stored unadjusted weeks earlier. Here
    nothing historical is being re-priced.
  * A split between the entry session and grading would still distort a control the same
    way it distorts a pick. Grading runs 5 sessions after entry, so the exposure is small
    but real; a control whose computed same-day move exceeds ±SANITY_PCT is written with
    note="SUSPECT: implausible move, review before use" rather than silently averaged in.
  * CONFOUND, registered in HYPOTHESES.md: the screen publishes the top 10 eligible names
    by score, and the observed publish rate among eligibles is ~81%. Controls are
    therefore the LOWEST-SCORING eligible names, not a random sample. Any comparison is
    "top-10 vs the eligible remainder", never "screened vs comparable unscreened".
  * Non-fatal by construction: every failure is logged and skipped, and the script always
    exits 0 so it can never block the daily data commit.

USAGE
    python3 grade_controls.py            # grade whatever is ready
    python3 grade_controls.py --selftest # offline logic check, no network
"""
import argparse
import csv
import io
import os
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATES = os.path.join(HERE, "candidates.csv")
OUT = os.path.join(HERE, "control_outcomes.csv")

WINDOW = 5          # trading sessions held, matching the pick grader
HAIRCUT = 2.0       # % round-trip cost, matching the pick grader
SANITY_PCT = 300.0  # flag a same-day move beyond this as suspect (split/bad data)

FIELDS = ["candidate_id", "ticker", "trading_date", "graded_at", "score", "tier",
          "entry_open", "same_day_close", "ret_open_close_net", "ret_open_5dclose_net",
          "mfe_5d", "mae_5d", "win", "note"]


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _read(path):
    if not os.path.exists(path):
        return []
    with io.open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# PURE CORE (offline-testable): bars -> outcome dict
# bars: list of {"o","h","l","c"}, bars[0] is the entry session, len >= WINDOW+1
# ---------------------------------------------------------------------------
def grade_from_bars(bars):
    entry = bars[0]["o"]
    if not entry or entry <= 0:
        return None
    same_close = bars[0]["c"]
    last_close = bars[WINDOW]["c"]
    win_bars = bars[:WINDOW + 1]
    hi = max(b["h"] for b in win_bars)
    lo = min(b["l"] for b in win_bars)
    r1 = (same_close - entry) / entry * 100.0 - HAIRCUT
    r5 = (last_close - entry) / entry * 100.0 - HAIRCUT
    note = ""
    if abs(r1 + HAIRCUT) > SANITY_PCT:
        note = "SUSPECT: implausible move, review before use"
    return {
        "entry_open": round(entry, 6),
        "same_day_close": round(same_close, 6),
        "ret_open_close_net": round(r1, 4),
        "ret_open_5dclose_net": round(r5, 4),
        "mfe_5d": round((hi - entry) / entry * 100.0, 4),
        "mae_5d": round((lo - entry) / entry * 100.0, 4),
        "win": 1 if r1 > 0 else 0,
        "note": note,
    }


def controls_pending(candidates, already):
    """Eligible-but-unpublished candidates not yet graded, de-duplicated by candidate_id."""
    out, seen = [], set()
    for c in candidates:
        cid = (c.get("candidate_id") or "").strip()
        if not cid or cid in already or cid in seen:
            continue
        if (c.get("eligible") or "").strip().lower() != "yes":
            continue
        if (c.get("published") or "").strip() in ("1", "true", "True"):
            continue
        if not (c.get("ticker") or "").strip() or not (c.get("trading_date") or "").strip():
            continue
        seen.add(cid)
        out.append(c)
    return out


def fetch_bars(ticker, start):
    """Daily OHLC: entry session + WINDOW sessions. Returns None if not enough sessions yet."""
    import yfinance as yf
    end = (datetime.strptime(start, "%Y-%m-%d") + timedelta(days=20)).strftime("%Y-%m-%d")
    df = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
    if df is None or len(df) == 0:
        return None
    df = df.reset_index()
    df["d"] = df["Date"].astype(str).str[:10]
    idx = df.index[df["d"] == start]
    if len(idx) == 0:
        return None
    w = df.iloc[idx[0]:idx[0] + WINDOW + 1]
    if len(w) < WINDOW + 1:
        return None  # not matured yet — try again on a later run
    return [{"o": float(r["Open"]), "h": float(r["High"]),
             "l": float(r["Low"]), "c": float(r["Close"])} for _, r in w.iterrows()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--limit", type=int, default=200)
    a = ap.parse_args()
    if a.selftest:
        return _selftest()

    candidates = _read(CANDIDATES)
    if not candidates:
        print("grade_controls: no candidates.csv — nothing to do")
        return 0
    existing = _read(OUT)
    already = {(r.get("candidate_id") or "").strip() for r in existing}
    pending = controls_pending(candidates, already)
    print(f"grade_controls: {len(pending)} ungraded control(s) of "
          f"{len(candidates)} candidate rows ({len(already)} already graded)")
    if not pending:
        return 0

    graded, immature, failed = [], 0, 0
    for c in pending[:a.limit]:
        try:
            bars = fetch_bars(c["ticker"], c["trading_date"])
        except Exception as e:
            print(f"  skip {c['ticker']} {c['trading_date']}: {type(e).__name__}")
            failed += 1
            continue
        if not bars:
            immature += 1
            continue
        g = grade_from_bars(bars)
        if not g:
            failed += 1
            continue
        row = {"candidate_id": c["candidate_id"], "ticker": c["ticker"],
               "trading_date": c["trading_date"],
               "graded_at": datetime.utcnow().isoformat(timespec="seconds"),
               "score": c.get("score", ""), "tier": c.get("tier", "")}
        row.update(g)
        graded.append(row)

    if graded:
        new_file = not os.path.exists(OUT)
        with io.open(OUT, "a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            if new_file:
                w.writeheader()
            for r in graded:
                w.writerow({k: r.get(k, "") for k in FIELDS})
    suspect = sum(1 for r in graded if r["note"])
    print(f"grade_controls: wrote {len(graded)} ({suspect} flagged suspect), "
          f"{immature} not matured, {failed} failed")
    return 0


def _selftest():
    # entry open 100. same-day close 90 -> -10 -2 = -12. 5th close 80 -> -20 -2 = -22.
    bars = [{"o": 100.0, "h": 110.0, "l": 95.0, "c": 90.0},
            {"o": 90.0, "h": 105.0, "l": 88.0, "c": 100.0},
            {"o": 100.0, "h": 120.0, "l": 99.0, "c": 110.0},
            {"o": 110.0, "h": 115.0, "l": 70.0, "c": 75.0},
            {"o": 75.0, "h": 85.0, "l": 74.0, "c": 84.0},
            {"o": 84.0, "h": 88.0, "l": 79.0, "c": 80.0}]
    g = grade_from_bars(bars)
    assert g["ret_open_close_net"] == -12.0, g
    assert g["ret_open_5dclose_net"] == -22.0, g
    assert g["mfe_5d"] == 20.0, g   # high 120 vs entry 100
    assert g["mae_5d"] == -30.0, g  # low 70 vs entry 100
    assert g["win"] == 0 and g["note"] == "", g
    # winner + suspect flag
    up = [{"o": 1.0, "h": 9.0, "l": 1.0, "c": 8.0}] + [{"o": 8.0, "h": 8.0, "l": 8.0, "c": 8.0}] * 5
    g2 = grade_from_bars(up)
    assert g2["win"] == 1 and "SUSPECT" in g2["note"], g2
    # pending-selection logic
    cands = [
        {"candidate_id": "c1", "ticker": "AAA", "trading_date": "2026-07-20", "eligible": "yes", "published": "0"},
        {"candidate_id": "c2", "ticker": "BBB", "trading_date": "2026-07-20", "eligible": "yes", "published": "1"},
        {"candidate_id": "c3", "ticker": "CCC", "trading_date": "2026-07-20", "eligible": "price_band", "published": "0"},
        {"candidate_id": "c4", "ticker": "DDD", "trading_date": "2026-07-20", "eligible": "yes", "published": "0"},
        {"candidate_id": "c1", "ticker": "AAA", "trading_date": "2026-07-20", "eligible": "yes", "published": "0"},
    ]
    got = [c["candidate_id"] for c in controls_pending(cands, {"c4"})]
    assert got == ["c1"], got
    print("grade_controls selftest PASS — grading math, suspect flag and control selection verified")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # never block the daily commit
        print(f"grade_controls: non-fatal error {type(e).__name__}: {e}")
        sys.exit(0)
