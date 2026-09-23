#!/usr/bin/env python3
"""
calibration_pull.py — build the GATE-2 hand-labeling set for filing_lens.py.

WHAT IT DOES
  1. Population = the tickers ThePickLog has actually screened (picks.csv), optionally
     topped up from candidates.csv. That is the sub-$5 / low-float population the
     classifier will run on, so the calibration curve is measured where it is used.
  2. For each ticker: one SEC submissions request, then filing_lens.select_filings()
     with LONG windows (the whole lookback) — the same prefilter that will run live.
  3. Stratify by what the prefilter matched, oversampling the rare, high-cost classes
     (reverse splits under Item 5.03, delisting notices under 3.01), and draw a
     deterministic sample (seeded) up to the per-stratum targets.
  4. Fetch each primary document, strip it exactly as the live path will
     (filing_lens.strip_html + cap_text), save the text, and write a labeling sheet
     with BLANK label columns — one per question — plus labeler / notes / seconds.

LABELS ARE WRITTEN BEFORE ANY JEV CALL IS MADE. This script never calls Jev.

OUTPUT (default ./calibration/)
  candidates.csv          one row per filing, blank label columns
  text/<accession>.txt    the exact text the model will see (hash in the sheet)
  pull_manifest.json      population size, strata counts, seed, windows, lens version

USAGE
  python3 calibration_pull.py                       # defaults: 400 filings, since 2025-01-01
  python3 calibration_pull.py --since 2025-01-01 --target 400 --seed 7 --out calibration
  python3 calibration_pull.py --max-tickers 50      # quick smoke run
NOT INVESTMENT ADVICE.
"""
import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
from datetime import date

import filing_lens as fl
from edgar_lens import submissions_recent
from asof_grader import ticker_to_cik

# Per-stratum targets (sum = 400). Rare/high-cost classes oversampled on purpose.
TARGETS = {
    "8k_5.03": 90,     # reverse splits live here (also charter amendments generally)
    "8k_3.01": 90,     # deficiency / delisting notices
    "8k_3.02": 50,     # unregistered equity sales
    "8k_1.01": 50,     # material agreements (SPAs, notes, warrants)
    "8k_8.01": 40,     # other events (halts, going-concern language, misc)
    "424B":    50,     # priced offerings / prospectus supplements
    "S-3":     30,     # shelves (S-1/S-3/F-1/F-3)
}
STRATUM_ORDER = list(TARGETS)

LABEL_COLS = [f"label_{q}" for q in fl.QUESTION_ORDER] + ["labeler", "label_seconds", "label_notes"]


def stratum_of(f):
    form = f["form"]
    if fl._is_offering(form):
        return "424B"
    if fl._is_shelf(form):
        return "S-3"
    items = fl._items_of(f["items"])
    # priority: the rarest / most decision-relevant item wins when an 8-K has several
    for it in ("5.03", "3.01", "3.02", "1.01", "8.01"):
        if it in items:
            return f"8k_{it}"
    return None


def population(repo, max_tickers=None, topup=0, seed=7):
    """Tickers from picks.csv (all), plus `topup` random tickers from candidates.csv."""
    seen, ticks = set(), []
    with open(os.path.join(repo, "picks.csv")) as fh:
        for r in csv.DictReader(fh):
            t = (r.get("ticker") or "").upper()
            if t and t not in seen:
                seen.add(t); ticks.append(t)
    n_picks = len(ticks)
    if topup:
        extra = []
        try:
            with open(os.path.join(repo, "candidates.csv")) as fh:
                for r in csv.DictReader(fh):
                    t = (r.get("ticker") or "").upper()
                    if t and t not in seen:
                        seen.add(t); extra.append(t)
        except FileNotFoundError:
            pass
        random.Random(seed).shuffle(extra)
        ticks += extra[:topup]
    if max_tickers:
        ticks = ticks[:max_tickers]
    return ticks, n_picks


def snippet(text, n=320):
    i = text.find("Item ")
    s = text[i:] if i >= 0 else text
    return " ".join(s.split())[:n]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--out", default="calibration")
    ap.add_argument("--since", default="2025-01-01", help="earliest filing date")
    ap.add_argument("--asof", default=date.today().isoformat())
    ap.add_argument("--target", type=int, default=400)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--max-tickers", type=int, default=None)
    ap.add_argument("--topup", type=int, default=0, help="extra tickers drawn from candidates.csv")
    ap.add_argument("--pace", type=float, default=0.12, help="seconds between SEC requests")
    args = ap.parse_args()

    scale = args.target / sum(TARGETS.values())
    targets = {k: max(1, round(v * scale)) for k, v in TARGETS.items()}
    lookback = (fl._d(args.asof) - fl._d(args.since)).days

    ticks, n_picks = population(args.repo, args.max_tickers, args.topup, args.seed)
    print(f"population: {len(ticks)} tickers ({n_picks} from picks.csv), lookback {lookback}d, "
          f"targets {targets}")

    # ---- 1) enumerate prefilter hits per ticker -------------------------------
    pool = {k: [] for k in TARGETS}
    no_cik, sub_err = 0, 0
    t0 = time.time()
    for i, t in enumerate(ticks, 1):
        try:
            cik = ticker_to_cik(t)
        except Exception as e:
            print(f"  cik map error: {e}"); break
        if not cik:
            no_cik += 1; continue
        try:
            recent = submissions_recent(cik)
        except Exception as e:
            sub_err += 1; continue
        time.sleep(args.pace)
        sel = fl.select_filings(recent, args.asof, eightk_window=lookback,
                                offering_window=lookback, cap=10_000)
        for f in sel:
            if f["filingDate"] < args.since or not f["primaryDocument"]:
                continue
            s = stratum_of(f)
            if s:
                f = dict(f, ticker=t, cik=cik, stratum=s)
                pool[s].append(f)
        if i % 25 == 0:
            print(f"  {i}/{len(ticks)} tickers, {sum(len(v) for v in pool.values())} hits, "
                  f"{int(time.time() - t0)}s")
    print(f"enumerated: no_cik={no_cik} submissions_err={sub_err} "
          f"pool={{{', '.join(f'{k}:{len(v)}' for k, v in pool.items())}}}")

    # ---- 2) deterministic stratified draw -------------------------------------
    rng = random.Random(args.seed)
    chosen = []
    seen_acc = set()
    for s in STRATUM_ORDER:
        cands = [f for f in pool[s] if f["accession"] not in seen_acc]
        rng.shuffle(cands)
        # spread across tickers: at most 3 filings per ticker per stratum
        per_t = {}
        take = []
        for f in cands:
            if per_t.get(f["ticker"], 0) >= 3:
                continue
            per_t[f["ticker"]] = per_t.get(f["ticker"], 0) + 1
            take.append(f)
            if len(take) >= targets[s]:
                break
        for f in take:
            seen_acc.add(f["accession"])
        chosen += take
        print(f"  {s}: {len(take)}/{targets[s]} (pool {len(pool[s])})")

    # ---- 3) fetch + strip + write -------------------------------------------------
    os.makedirs(os.path.join(args.out, "text"), exist_ok=True)
    rows, fetch_err = [], 0
    for n, f in enumerate(chosen, 1):
        url = fl.doc_url(f["cik"], f["accession"], f["primaryDocument"])
        try:
            raw = fl.fetch_doc(url)
        except Exception as e:
            fetch_err += 1
            print(f"  fetch failed {f['ticker']} {f['accession']}: {type(e).__name__}")
            continue
        time.sleep(args.pace)
        text, trunc = fl.cap_text(fl.strip_html(raw))
        if len(text) < 200:                       # PDF-only / empty shell — not labelable
            continue
        fn = f["accession"].replace("/", "_") + ".txt"
        with open(os.path.join(args.out, "text", fn), "w") as fh:
            fh.write(text)
        rows.append({
            "cal_id": f"CAL-{len(rows) + 1:04d}",
            "stratum": f["stratum"], "ticker": f["ticker"], "cik": f["cik"],
            "form": f["form"], "filing_date": f["filingDate"], "items": f["items"],
            "accession": f["accession"], "doc_url": url,
            "prefilter_reason": f["reason"],
            "text_file": f"text/{fn}", "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "text_tokens": fl.est_tokens(text), "truncated": int(trunc),
            "snippet": snippet(text),
            **{c: "" for c in LABEL_COLS},
        })
        if n % 50 == 0:
            print(f"  fetched {n}/{len(chosen)}")

    rng.shuffle(rows)                              # labeling order independent of stratum
    for i, r in enumerate(rows, 1):
        r["cal_id"] = f"CAL-{i:04d}"
    fields = list(rows[0].keys()) if rows else []
    with open(os.path.join(args.out, "candidates.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

    manifest = {
        "generated": date.today().isoformat(), "asof": args.asof, "since": args.since,
        "seed": args.seed, "targets": targets, "population_tickers": len(ticks),
        "population_from_picks": n_picks, "no_cik": no_cik, "submissions_err": sub_err,
        "pool_sizes": {k: len(v) for k, v in pool.items()},
        "drawn": len(chosen), "fetch_err": fetch_err, "written": len(rows),
        "strata_written": {s: sum(1 for r in rows if r["stratum"] == s) for s in STRATUM_ORDER},
        "lens_version": fl.__version__, "questions_sha256": fl.QUESTIONS_SHA256,
        "label_columns": LABEL_COLS,
        "label_values": {q: (list(fl.QUESTIONS[q]["criteria"]) if fl.QUESTIONS[q]["type"] == "choice" else ["yes", "no"])
                         for q in fl.QUESTION_ORDER},
    }
    with open(os.path.join(args.out, "pull_manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"wrote {len(rows)} rows -> {args.out}/candidates.csv  ({fetch_err} fetch errors)")
    print(json.dumps(manifest["strata_written"]))


if __name__ == "__main__":
    main()
