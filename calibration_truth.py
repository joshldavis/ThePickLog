#!/usr/bin/env python3
"""
calibration_truth.py — STRUCTURED ground truth for the filing_lens calibration set,
from sources that do not involve reading the filing.

WHY: the highest-stakes question (did a reverse split happen, at what ratio, and was
it effective by the filing date) has an answer in the MARKET, not in the prose. If a
1-for-15 split happened on 2026-09-17, Yahoo's split history says so, and ThePickLog's
own candidates.csv shows the float dividing by 15. That is truth a stranger can verify
without trusting any reader, human or model. Likewise several "other material" events
are already stated by 8-K item codes (1.03 bankruptcy, 4.01 auditor change, 4.02
restatement, 2.01 acquisition completed), and a 424B IS a priced offering by form.

WHAT IT WRITES (calibration/truth.csv, one row per cal_id):
  truth_<question>          "" when no structured source can answer it (needs a reader)
  truth_<question>_conf     high | moderate
  truth_<question>_src      what decided it (yahoo_split, float_ratio, item_code, form, no_split_in_window)
  yahoo_split_date, yahoo_ratio_n, float_ratio_n, float_ratio_date   the evidence

RULES v2 (explicit, so the note can publish them; v1 was too aggressive — see note below)
  reverse_split  (S = Yahoo reverse splits for the ticker; d = split date - filing date, in days)
    • No split with -400 <= d <= +75                    -> "none" (high)
    • A split with -30 <= d <= 0 AND filing has 5.03/3.03  -> "effective" (high)
      (a split up to 30 days old is still reported as the filing's own event)
    • A split with 1 <= d <= 3                             -> "" (edge: "effective 4:30 pm
      today" and "effective at tomorrow's open" both land here and Yahoo dates them to the
      next session; announced vs effective is a text call, so the reader decides)
    • A split with 4 <= d <= 15 AND filing has 5.03/3.03   -> "announced" (high)
      (Nasdaq needs 5-15 days' notice, so the announcing 8-K sits inside that window)
    • Any other case (split 16-75 days out, or 31-400 days back, or the filing lacks
      5.03/3.03) -> "" — the split happened, but whether THIS filing reports, announces, or
      merely recites it is a text question. v1 called a 5.03 filing up to 75 days before a
      split "announced"; 12 of 25 disagreements with the model reader were exactly those,
      and on inspection the 5.03 was a different charter amendment.
  split_ratio     follows reverse_split: "none" when none; 1-for-N from Yahoo when effective/
                  announced; "" otherwise.
  other_material  item 1.03 -> bankruptcy, 4.01 -> auditor_change, 4.02 -> restatement,
                  2.01 -> merger_or_acquisition (high). 8-K with none of those AND none of
                  5.02/7.01/8.01 (the free-text items) -> "none" (moderate). Else "".
  dilution_event  8-K without 1.01/3.02/8.01 and not a prospectus -> "none" (moderate). Else "".
                  (v1 said 424B -> priced_offering; wrong for ATM supplements and resale
                   prospectuses — 34 of 41 disagreements — so the form code decides nothing.)
  listing_status  8-K without 3.01 and without 5.03/8.01/7.01 -> "none" (moderate). Else "".
  going_concern   always "" (no structured source at the 8-K level).

Cross-check: candidates.csv float drops (prev/new ~ integer N in 2..250, within 5%) are
recorded as float_ratio_n / float_ratio_date and compared to Yahoo where both exist.

USAGE
  python3 calibration_truth.py --cal calibration --repo .
NOT INVESTMENT ADVICE.
"""
import argparse
import csv
import json
import os
import time
from collections import defaultdict
from datetime import date, timedelta

import filing_lens as fl

WINDOW_BEFORE = 400
WINDOW_AFTER = 75
FREE_TEXT_ITEMS = {"5.02", "7.01", "8.01"}
ITEM_EVENTS = {"1.03": "bankruptcy", "4.01": "auditor_change", "4.02": "restatement",
               "2.01": "merger_or_acquisition"}


def yahoo_reverse_splits(ticker, pace=0.6):
    """[(date, N)] for reverse splits (ratio < 1) in Yahoo's history; None when the
    query FAILED (rate limit, unknown ticker) — never confuse failure with 'no splits'."""
    try:
        import yfinance as yf
        tk = yf.Ticker(ticker)
        s = tk.splits
        time.sleep(pace)
        if s is None or len(s) == 0:
            # empty can mean "no splits" or "no data at all": require a price history to exist
            h = tk.history(period="5d")
            time.sleep(pace)
            if h is None or len(h) == 0:
                return None
        out = []
        for ts, r in s.items():
            r = float(r)
            if 0 < r < 1:
                out.append((ts.date(), int(round(1.0 / r))))
        return out
    except Exception:
        return None


def float_ratio_events(repo):
    """From candidates.csv: per ticker, dated float drops by an integer factor."""
    ev = defaultdict(list)
    path = os.path.join(repo, "candidates.csv")
    if not os.path.exists(path):
        return ev
    seq = defaultdict(list)
    with open(path) as fh:
        for r in csv.DictReader(fh):
            try:
                seq[r["ticker"].upper()].append((r["trading_date"], float(r["float_shares"])))
            except (KeyError, ValueError):
                continue
    for t, rows in seq.items():
        rows.sort()
        last = None
        for d, f in rows:
            if last and f > 0 and last[1] / f >= 1.9:
                n = last[1] / f
                if abs(n - round(n)) / n <= 0.05 and 2 <= round(n) <= 250:
                    ev[t].append((d, int(round(n))))
            last = (d, f)
    return ev


def ratio_label(n):
    lab = f"1-for-{n}"
    return lab if lab in fl.SPLIT_RATIOS else "other"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cal", default="calibration")
    ap.add_argument("--repo", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--no-yahoo", action="store_true")
    ap.add_argument("--recheck-empty", action="store_true", help="re-query tickers whose cached split list is empty")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(os.path.join(args.cal, "candidates.csv"))))
    tickers = sorted({r["ticker"] for r in rows})
    print(f"{len(rows)} filings, {len(tickers)} tickers")

    ysplits = {}
    cache = os.path.join(args.cal, "yahoo_splits.json")
    if os.path.exists(cache):
        ysplits = {t: (None if v is None else [(date.fromisoformat(d), n) for d, n in v]) for t, v in json.load(open(cache)).items()}
        print(f"  yahoo splits from cache ({len(ysplits)} tickers)")
    if not args.no_yahoo:
        missing = [t for t in tickers if ysplits.get(t) is None or (ysplits.get(t) == [] and args.recheck_empty)]
        for i, t in enumerate(missing, 1):
            ysplits[t] = yahoo_reverse_splits(t)
            if i % 25 == 0:
                print(f"  yahoo {i}/{len(missing)} (new)")
        if missing:
            json.dump({t: (None if v is None else [(d.isoformat(), n) for d, n in v]) for t, v in ysplits.items()}, open(cache, "w"))
    # A ticker with NO Yahoo entry (never queried, or the query failed) has no market truth:
    # "no split" may only be asserted when the history was actually fetched.
    fsplits = float_ratio_events(args.repo)
    print(f"yahoo reverse splits: {sum(len(v) for v in ysplits.values() if v)} ({sum(1 for v in ysplits.values() if v is None)} tickers unknown); "
          f"float-ratio events in candidates.csv: {sum(len(v) for v in fsplits.values())}")

    out = []
    for r in rows:
        fd = fl._d(r["filing_date"])
        items = set(fl._items_of(r["items"]))
        form = r["form"]
        t = {"cal_id": r["cal_id"], "ticker": r["ticker"], "form": form, "filing_date": r["filing_date"], "items": r["items"]}

        def setq(q, val, conf, src):
            t[f"truth_{q}"] = val; t[f"truth_{q}_conf"] = conf; t[f"truth_{q}_src"] = src

        for q in fl.QUESTION_ORDER:
            setq(q, "", "", "")

        # ---- reverse split / ratio from the market (RULES v2) --------------------
        allS = [(d, n, (d - fd).days) for d, n in (ysplits.get(r["ticker"]) or [])]
        near = [x for x in allS if -400 <= x[2] <= 75]
        eff = [x for x in allS if -30 <= x[2] <= 0]
        edge = [x for x in allS if 1 <= x[2] <= 3]
        ann = [x for x in allS if 4 <= x[2] <= 15]
        fwin = [(d, n) for d, n in fsplits.get(r["ticker"], [])
                if fd - timedelta(days=30) <= fl._d(d) <= fd + timedelta(days=WINDOW_AFTER + 10)]
        win = eff or edge or ann or [x for x in near if x[2] > 3] or near
        t["yahoo_split_date"] = win[0][0].isoformat() if win else ""
        t["yahoo_ratio_n"] = win[0][1] if win else ""
        t["yahoo_split_offset_days"] = win[0][2] if win else ""
        t["float_ratio_date"] = fwin[0][0] if fwin else ""
        t["float_ratio_n"] = fwin[0][1] if fwin else ""
        if ysplits.get(r["ticker"]) is None:
            pass                                   # no market data (query failed) -> reader decides
        elif not near:
            setq("reverse_split", "none", "high", "no_split_in_window")
            setq("split_ratio", "none", "high", "no_split_in_window")
        elif edge:
            pass                                   # reader decides announced vs effective
        elif eff and items & {"5.03", "3.03"}:
            setq("reverse_split", "effective", "high", "yahoo_split")
            setq("split_ratio", ratio_label(eff[0][1]), "high", "yahoo_split")
        elif ann and items & {"5.03", "3.03"}:
            setq("reverse_split", "announced", "high", "yahoo_split")
            setq("split_ratio", ratio_label(ann[0][1]), "high", "yahoo_split")
        # else: needs a reader

        # ---- other material from item codes ------------------------------------------
        hit = [ITEM_EVENTS[i] for i in ("1.03", "4.02", "4.01", "2.01") if i in items]
        if hit:
            setq("other_material", hit[0], "high", "item_code")
        elif form.startswith("8-K") and not (items & FREE_TEXT_ITEMS):
            setq("other_material", "none", "moderate", "item_code")

        # ---- dilution from form / items ----------------------------------------------
        if form.startswith("8-K") and not (items & {"1.01", "3.02", "8.01"}):
            setq("dilution_event", "none", "moderate", "item_code")

        # ---- listing status from items -----------------------------------------------
        if form.startswith("8-K") and not (items & {"3.01", "5.03", "8.01", "7.01"}):
            setq("listing_status", "none", "moderate", "item_code")

        out.append(t)

    fields = list(out[0].keys())
    with open(os.path.join(args.cal, "truth.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(out)

    # summary
    summ = {}
    for q in fl.QUESTION_ORDER:
        vals = [t[f"truth_{q}"] for t in out]
        summ[q] = {"answered": sum(1 for v in vals if v), "high": sum(1 for t in out if t[f"truth_{q}_conf"] == "high"),
                   "by_value": {v: vals.count(v) for v in sorted(set(vals)) if v}}
    agree = [(t["cal_id"], t["yahoo_ratio_n"], t["float_ratio_n"]) for t in out if t["yahoo_ratio_n"] and t["float_ratio_n"]]
    xcheck = {"both_present": len(agree), "ratio_agree": sum(1 for _, a, b in agree if a == b)}
    with open(os.path.join(args.cal, "truth_summary.json"), "w") as fh:
        json.dump({"rules": "see calibration_truth.py docstring", "window_days": [WINDOW_BEFORE, WINDOW_AFTER],
                   "summary": summ, "yahoo_vs_float_crosscheck": xcheck}, fh, indent=2)
    print(json.dumps(summ, indent=1)); print("yahoo vs float cross-check:", xcheck)


if __name__ == "__main__":
    main()
