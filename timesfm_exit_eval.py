#!/usr/bin/env python3
"""
H-TSFM1 — can a time-series foundation model forecast the EXIT PATH better than
a random walk?

WHAT THIS IS NOT
----------------
This is not a trading rule and it is not a harness experiment. There is no entry
condition, no exit rule, no cost model and no P&L. Registering it as EXP-anything
would be a category error: every EXP row in the harness asks "does this rule make
money", and this asks "can a forecaster beat naive on the shape of the fade".
It lives in HYPOTHESES.md as H-TSFM1. EXP10/EXP11 stay reserved for the gap and
squeeze experiments.

THE QUESTION
------------
The one durable, repeatedly-measured feature of the record is spike-then-fade:
median MFE +16.4% against -2.8% at the close. Selection is a null (Gate 1 FAIL)
and the exit family is a null (H-EX1 REFUTED: no rule beat same-day close). So
the only open question left in the exit family is whether the *path* is
forecastable at all -- not whether we can trade it.

If a 200M-parameter foundation model cannot beat a random walk at forecasting
this path, that closes the question cheaply and permanently, and that is a
publishable null in the same family as H-EX1. That is the expected outcome and
the reason the test is worth running: it is cheap to run and cheap to lose.

DESIGN
------
Decision point: you already hold the position and session 0 (the entry day) has
closed. You know its OHLC. You want the path over sessions 1..5.

  context  = daily closes up to and including session 0's close
  target   = log(C_h / C_0) for h = 1..5
  forecast = quantiles {0.1, 0.25, 0.5, 0.75, 0.9} of the same

No look-ahead is possible by construction: the context ends at the close of a
session that is fully realised before the forecast is scored.

THE SPLIT-ADJUSTMENT DEFENCE  (this is the trap that flips sign by universe)
---------------------------------------------------------------------------
paths.csv holds prices as they stood AT GRADE TIME. A vendor restates the entire
history on every split. Mixing a stored paths.csv price with a freshly downloaded
context price invents returns out of nothing.

So this harness NEVER mixes them:

  1. Context AND forward window are downloaded in ONE call per ticker, from one
     provider, in one adjustment basis. Internally self-consistent by
     construction, whatever splits have happened since.
  2. paths.csv is then used ONLY as a validator: the fresh bars are compared
     against the stored bars on the six known session dates. A disagreement
     beyond SPLIT_TOL means the history was restated -> the pick is EXCLUDED and
     counted. paths.csv is the split detector, not a data source.
  3. All scoring is in log-return space relative to C_0, which is invariant to a
     uniform rescaling of a self-consistent series.

SURVIVORSHIP
------------
Microcaps halt and delist. A name that cannot be downloaded today is not missing
at random -- it is disproportionately a name that died, and dying names are
exactly where the fade is most violent. Dropping them silently would flatter any
forecaster, which is the same defect the 2026-08-09 grading-gap fix closed in
cmd_grade. So every exclusion is counted, classified, and its realised outcome
(known from paths.csv, which survives regardless) is compared against the
included set. If the excluded names fade harder, the headline is biased and the
report says so.

PRE-DECLARED, ONE LOOK
----------------------
Bars are declared in PRE_DECLARED below and are checked into git BEFORE any
result is computed. One configuration, one look. Any second configuration
(different context length, model variant, quantile set) is a NEW hypothesis with
its own row -- not a re-read of this one. The verdict is written once to an
append-only file and never recomputed.

Usage:
  python3 timesfm_exit_eval.py --backend naive_rw     # baseline, no model needed
  python3 timesfm_exit_eval.py --backend naive_flat   # degenerate reference
  python3 timesfm_exit_eval.py --backend timesfm      # requires timesfm[torch]
  python3 timesfm_exit_eval.py --backend all --report
"""

import argparse
import json
import math
import os
import sys
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PATHS_CSV = os.path.join(HERE, "paths.csv")
OUT_DIR = os.path.join(HERE, "experiments")
CACHE = os.path.join(HERE, "tsfm_bars_cache.json")

# ----------------------------------------------------------------- pre-declared
PRE_DECLARED = {
    "hypothesis_id": "H-TSFM1",
    "registered_utc": None,          # filled on first run, then immutable
    "question": (
        "Does a zero-shot time-series foundation model produce a better-calibrated "
        "5-session forward path for a graded pick than a random walk with "
        "trailing-volatility quantiles?"
    ),
    "primary_metric": "mean pinball loss over q in {0.1,0.25,0.5,0.75,0.9}, h in 1..5",
    "baseline": "naive_rw",
    "pass_bar": {
        "relative_improvement_min": 0.05,   # >=5% lower pinball loss than naive_rw
        "clustered_ci_excludes_zero": True, # bootstrap clustered BY TICKER
        "distinct_ticker_floor": 20,        # H-IND1 effective-N floor, as in the harness
    },
    "secondary_report_only": [
        "point accuracy (MAE of median log-return) vs naive_flat",
        "MFE-timing hit rate implied by the q90 path",
    ],
    "quantiles": [0.1, 0.25, 0.5, 0.75, 0.9],
    "horizons": [1, 2, 3, 4, 5],
    "context_max_bars": 512,
    "context_min_bars": 60,
    "split_tol": 0.01,
    "notes": (
        "Secondary metrics are REPORT-ONLY and are declared here so they cannot be "
        "promoted to the pass bar after the fact. A pass on a secondary metric with "
        "a fail on the primary is a FAIL."
    ),
}

QUANTILES = PRE_DECLARED["quantiles"]
HORIZONS = PRE_DECLARED["horizons"]
CTX_MAX = PRE_DECLARED["context_max_bars"]
CTX_MIN = PRE_DECLARED["context_min_bars"]
SPLIT_TOL = PRE_DECLARED["split_tol"]

# z-scores for the random-walk baseline's quantiles
_Z = {0.1: -1.2816, 0.25: -0.6745, 0.5: 0.0, 0.75: 0.6745, 0.9: 1.2816}


# ---------------------------------------------------------------------- io
def read_paths():
    """paths.csv -> {pick_id: {ticker, trading_date, bars[6]}}. Immutable record."""
    import csv
    picks = {}
    with open(PATHS_CSV, newline="") as fh:
        for r in csv.DictReader(fh):
            p = picks.setdefault(r["pick_id"], {
                "pick_id": r["pick_id"], "ticker": r["ticker"],
                "trading_date": r["trading_date"], "bars": {},
            })
            try:
                p["bars"][int(r["session_idx"])] = {
                    "date": r["bar_date"],
                    "open": float(r["open"]), "high": float(r["high"]),
                    "low": float(r["low"]), "close": float(r["close"]),
                }
            except (ValueError, KeyError):
                pass
    # keep only complete 6-session paths
    return {k: v for k, v in picks.items() if len(v["bars"]) == 6}


def fetch_bars(tickers, start, end, use_cache=True):
    """ONE download per ticker covering context + forward window. Self-consistent
    by construction -- never merged with stored paths.csv prices."""
    cache = {}
    if use_cache and os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE))
        except Exception:
            cache = {}

    todo = [t for t in tickers if t not in cache]
    if todo:
        import yfinance as yf
        for i, t in enumerate(todo, 1):
            try:
                df = yf.download(t, start=start, end=end, progress=False,
                                 auto_adjust=False, threads=False)
                if df is None or len(df) == 0:
                    cache[t] = {"error": "empty"}
                else:
                    if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
                        df.columns = df.columns.get_level_values(0)
                    cache[t] = {
                        "dates": [str(d)[:10] for d in df.index],
                        "close": [float(x) for x in df["Close"].tolist()],
                        "high": [float(x) for x in df["High"].tolist()],
                        "low": [float(x) for x in df["Low"].tolist()],
                    }
            except Exception as e:
                cache[t] = {"error": f"{type(e).__name__}: {str(e)[:80]}"}
            if i % 20 == 0:
                print(f"  fetched {i}/{len(todo)}", file=sys.stderr)
                json.dump(cache, open(CACHE, "w"))
        json.dump(cache, open(CACHE, "w"))
    return cache


# ------------------------------------------------------------------ assembly
def build_case(pick, series):
    """Assemble one scoreable case, or return (None, reason).

    Enforces the split defence: the freshly downloaded bars must agree with the
    immutable stored bars on all six session dates."""
    if not series or "error" in series:
        return None, "no_data"

    dates, closes = series["dates"], series["close"]
    idx = {d: i for i, d in enumerate(dates)}

    sess = [pick["bars"][i] for i in range(6)]
    for s in sess:
        if s["date"] not in idx:
            return None, "session_date_missing"

    # --- split / restatement detector -------------------------------------
    for s in sess:
        fresh = closes[idx[s["date"]]]
        stored = s["close"]
        if stored <= 0 or fresh <= 0:
            return None, "nonpositive_price"
        if abs(fresh - stored) / stored > SPLIT_TOL:
            return None, "restated_split"

    i0 = idx[sess[0]["date"]]
    ctx = closes[max(0, i0 - CTX_MAX + 1): i0 + 1]
    ctx = [c for c in ctx if c and c > 0]
    if len(ctx) < CTX_MIN:
        return None, "context_too_short"

    c0 = closes[i0]
    target = {}
    for h in HORIZONS:
        j = idx[sess[h]["date"]]
        if j != i0 + h:
            return None, "nonconsecutive_sessions"
        target[h] = math.log(closes[j] / c0)

    return {
        "pick_id": pick["pick_id"], "ticker": pick["ticker"],
        "trading_date": pick["trading_date"],
        "context": ctx, "c0": c0, "target": target,
        "realised_close_ret": target[5],
        "realised_mfe": max(
            (max(series["high"][idx[s["date"]]] for s in sess[1:]) / c0) - 1.0, -1.0),
    }, None


# ------------------------------------------------------------------ backends
def backend_naive_flat(ctx):
    """Degenerate reference: tomorrow = today, zero dispersion. Reported for
    point accuracy only -- it is not a legitimate quantile baseline."""
    return {h: {q: 0.0 for q in QUANTILES} for h in HORIZONS}


def backend_naive_rw(ctx):
    """The real baseline. Random walk with trailing-volatility quantiles:
    r_h ~ N(0, sigma^2 * h). This is what TimesFM has to beat."""
    rets = [math.log(ctx[i] / ctx[i - 1]) for i in range(1, len(ctx))
            if ctx[i - 1] > 0 and ctx[i] > 0]
    tail = rets[-60:] if len(rets) >= 60 else rets
    if len(tail) < 2:
        return None
    m = sum(tail) / len(tail)
    sd = math.sqrt(sum((r - m) ** 2 for r in tail) / (len(tail) - 1))
    if sd <= 0:
        return None
    return {h: {q: _Z[q] * sd * math.sqrt(h) for q in QUANTILES} for h in HORIZONS}


_TSFM = None


def backend_timesfm(ctx):
    """Zero-shot TimesFM quantile head. Forecasts the log-price path, then
    converts to log-return relative to C_0."""
    global _TSFM
    if _TSFM is None:
        import timesfm
        _TSFM = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
            "google/timesfm-2.5-200m-pytorch")
        _TSFM.compile(timesfm.ForecastConfig(
            max_context=CTX_MAX, max_horizon=max(HORIZONS),
            normalize_inputs=True, use_continuous_quantile_head=True))

    log_ctx = [math.log(c) for c in ctx]
    point, quant = _TSFM.forecast(horizon=max(HORIZONS), inputs=[log_ctx])
    # quant: (batch, horizon, 1+len(model_quantiles)); index 0 is the mean
    model_q = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    base = math.log(ctx[-1])
    out = {}
    for h in HORIZONS:
        row = quant[0][h - 1]
        out[h] = {}
        for q in QUANTILES:
            k = model_q.index(round(q, 1)) + 1 if round(q, 1) in model_q else None
            if k is None:
                return None
            out[h][q] = float(row[k]) - base
    return out


BACKENDS = {
    "naive_flat": backend_naive_flat,
    "naive_rw": backend_naive_rw,
    "timesfm": backend_timesfm,
}


# ------------------------------------------------------------------- scoring
def pinball(actual, pred, q):
    d = actual - pred
    return q * d if d >= 0 else (q - 1) * d


def score_cases(cases, backend_name):
    fn = BACKENDS[backend_name]
    per_case, failures = [], 0
    for c in cases:
        fc = fn(c["context"])
        if fc is None:
            failures += 1
            continue
        losses, abs_err = [], []
        for h in HORIZONS:
            a = c["target"][h]
            for q in QUANTILES:
                losses.append(pinball(a, fc[h][q], q))
            abs_err.append(abs(a - fc[h][0.5]))
        per_case.append({
            "pick_id": c["pick_id"], "ticker": c["ticker"],
            "pinball": sum(losses) / len(losses),
            "mae": sum(abs_err) / len(abs_err),
        })
    return per_case, failures


def clustered_bootstrap(paired, n=5000, seed=20260813):
    """Bootstrap the paired per-case difference, RESAMPLING TICKERS not rows.
    Repeated bets on BJDX are not independent evidence -- H-IND1."""
    import random
    rng = random.Random(seed)
    by_ticker = defaultdict(list)
    for r in paired:
        by_ticker[r["ticker"]].append(r["diff"])
    tickers = list(by_ticker)
    if len(tickers) < 2:
        return None
    means = []
    for _ in range(n):
        draw = [rng.choice(tickers) for _ in tickers]
        vals = [v for t in draw for v in by_ticker[t]]
        if vals:
            means.append(sum(vals) / len(vals))
    means.sort()
    return {
        "lo": means[int(0.025 * len(means))],
        "hi": means[int(0.975 * len(means))],
        "n_tickers": len(tickers),
    }


# ---------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="naive_rw",
                    choices=list(BACKENDS) + ["all"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    picks = read_paths()
    print(f"paths.csv: {len(picks)} complete 6-session paths, "
          f"{len({p['ticker'] for p in picks.values()})} distinct tickers")

    dates = sorted(p["trading_date"] for p in picks.values())
    start = (datetime.strptime(dates[0], "%Y-%m-%d")
             - timedelta(days=int(CTX_MAX * 1.6))).strftime("%Y-%m-%d")
    end = (datetime.strptime(dates[-1], "%Y-%m-%d")
           + timedelta(days=30)).strftime("%Y-%m-%d")

    tickers = sorted({p["ticker"] for p in picks.values()})
    print(f"fetching {len(tickers)} tickers, one call each, {start} -> {end}")
    bars = fetch_bars(tickers, start, end, use_cache=not args.no_cache)

    cases, reasons = [], Counter()
    excluded_outcomes = []
    for p in picks.values():
        case, why = build_case(p, bars.get(p["ticker"]))
        if case:
            cases.append(case)
        else:
            reasons[why] += 1
            # realised outcome survives in paths.csv even when the fetch fails
            b = p["bars"]
            if b[0]["close"] > 0:
                excluded_outcomes.append(b[5]["close"] / b[0]["close"] - 1.0)
    if args.limit:
        cases = cases[:args.limit]

    print(f"\nscoreable: {len(cases)} / {len(picks)}")
    print("exclusions:", dict(reasons))

    # --- survivorship check ------------------------------------------------
    inc = [c["realised_close_ret"] for c in cases]
    if inc and excluded_outcomes:
        mi = sum(math.exp(x) - 1 for x in inc) / len(inc)
        me = sum(excluded_outcomes) / len(excluded_outcomes)
        print(f"\nSURVIVORSHIP CHECK  included mean 5d ret {mi:+.2%} "
              f"(n={len(inc)})  vs  excluded {me:+.2%} (n={len(excluded_outcomes)})")
        if me < mi - 0.02:
            print("  WARNING: excluded names faded harder. Any result below is "
                  "measured on a survivor-biased subset and must say so.")

    which = list(BACKENDS) if args.backend == "all" else [args.backend]
    results = {}
    for b in which:
        per_case, fails = score_cases(cases, b)
        if not per_case:
            print(f"\n{b}: no scoreable cases ({fails} backend failures)")
            continue
        results[b] = {r["pick_id"]: r for r in per_case}
        mp = sum(r["pinball"] for r in per_case) / len(per_case)
        mm = sum(r["mae"] for r in per_case) / len(per_case)
        print(f"\n{b:12s} n={len(per_case):4d} backend_fail={fails:3d}  "
              f"mean_pinball={mp:.6f}  mean_mae={mm:.6f}")

    # --- primary comparison, exactly as pre-declared ------------------------
    base = PRE_DECLARED["baseline"]
    if "timesfm" in results and base in results:
        common = set(results["timesfm"]) & set(results[base])
        paired = [{
            "ticker": results[base][k]["ticker"],
            "diff": results[base][k]["pinball"] - results["timesfm"][k]["pinball"],
        } for k in common]
        mean_diff = sum(r["diff"] for r in paired) / len(paired)
        base_mean = sum(results[base][k]["pinball"] for k in common) / len(common)
        rel = mean_diff / base_mean if base_mean else 0.0
        ci = clustered_bootstrap(paired)

        print("\n" + "=" * 68)
        print("H-TSFM1 PRIMARY — TimesFM vs naive_rw (positive = TimesFM better)")
        print(f"  n paired            : {len(paired)}")
        print(f"  relative improvement: {rel:+.2%}  (bar: >= +5.00%)")
        if ci:
            print(f"  clustered 95% CI    : [{ci['lo']:+.6f}, {ci['hi']:+.6f}]  "
                  f"tickers={ci['n_tickers']} (floor: 20)")
        bar = PRE_DECLARED["pass_bar"]
        passed = (rel >= bar["relative_improvement_min"]
                  and ci and ci["lo"] > 0
                  and ci["n_tickers"] >= bar["distinct_ticker_floor"])
        print(f"  VERDICT             : {'CLEARS THE BAR' if passed else 'FAIL'}")
        print("=" * 68)

        if args.report:
            os.makedirs(OUT_DIR, exist_ok=True)
            vf = os.path.join(OUT_DIR, "H-TSFM1-verdict.json")
            if os.path.exists(vf):
                print(f"\nverdict already written at {vf} — NOT recomputed (one look).")
            else:
                json.dump({
                    "pre_declared": PRE_DECLARED,
                    "computed_utc": datetime.now(timezone.utc).isoformat(),
                    "n_paired": len(paired), "relative_improvement": rel,
                    "clustered_ci": ci, "verdict": "PASS" if passed else "FAIL",
                    "exclusions": dict(reasons),
                }, open(vf, "w"), indent=2)
                print(f"\nverdict written once to {vf}")


if __name__ == "__main__":
    main()
