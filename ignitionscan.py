#!/usr/bin/env python3
"""
IgnitionScan — daily logger / grader (v0.2, personal paper-trading tool)
=======================================================================
Implements Part 1 (pick log) and Part 2 (cost-honest grading) of
VALIDATION-PLAN.md.

DATA SOURCE: Yahoo Finance via the `yfinance` library. No API key needed,
and unlike the FMP free tier it covers low-float / small-cap names with real
public float and daily history. (FMP free is large-cap-only; revisit a paid
feed when this becomes a real product — see VALIDATION-PLAN.md.)

COMMANDS
  scan    Pull the universe, score each name, append an IMMUTABLE row to picks.csv.
  grade   For picks >= GRADE_AFTER_DAYS old, compute realizable (cost-net) returns -> outcomes.csv.
  report  Print the A/B/C/D tier table from graded picks.
  demo    Run on bundled sample data with no network.

TYPICAL USE (paper trading yourself)
  python3 ignitionscan.py scan      # each market morning
  python3 ignitionscan.py grade     # each evening
  python3 ignitionscan.py report    # weekly
  (Or let the included GitHub Action run it automatically — see README.md.)

SETUP:  pip install yfinance
NOTHING HERE IS INVESTMENT ADVICE. The model is unvalidated until report says otherwise.
"""

import argparse, csv, os, sys, uuid, statistics, time
from datetime import datetime, timedelta, timezone

MODEL_VERSION = "v0.2-yf"
HERE = os.path.dirname(os.path.abspath(__file__))
PICKS_CSV    = os.path.join(HERE, "picks.csv")
OUTCOMES_CSV = os.path.join(HERE, "outcomes.csv")
PATHS_CSV    = os.path.join(HERE, "paths.csv")
EDGAR_SNAPSHOT_CSV = os.path.join(HERE, "edgar_snapshot.csv")  # forward-only Group-B + quality sidecar

CONFIG = {
    "UNIVERSE": ["BJDX","MASK","SUGP","GCDT","CODX","VMAR","PW","NCT","HKIT",
                 "IOTR","SVRN","RKDA","BNZI","CUPR","ATPC","JAGX"],
    "WEIGHTS":  {"float":0.30, "rvol":0.35, "gap":0.25, "price":0.10},  # sum=1
    "FILTERS":  {"price_min":0.50, "price_max":10.0, "float_max_m":50.0},
    "WATCH_LEVEL_PCT": 0.20,
    "COST_HAIRCUT_PCT": 2.0,
    "GRADE_AFTER_DAYS": 5,
    "CAPTURE_EDGAR": True,   # forward-only SEC-EDGAR Group-B + quality snapshot (non-fatal)
}

PICK_FIELDS = [
    "pick_id","published_at","trading_date","model_version",
    "ticker","price_at_screen","float_shares","rvol","gap_pct",
    "float_score","rvol_score","gap_score","price_score","score","tier","watch_level",
    "catalyst_type","dilution_flag","short_interest_pct","market_regime",
]
OUTCOME_FIELDS = [
    "pick_id","ticker","trading_date","graded_at",
    "entry_open","same_day_close",
    "ret_open_close_net","ret_open_5dclose_net","mfe_5d","mae_5d","win","note",
]
# Immutable daily-OHLC path of each graded pick (entry session + 5 sessions). Captured at
# grade time so the exit-rule study (exit_sim.py) is reproducible from COMMITTED data rather
# than re-fetching Yahoo (which can silently revise history) — i.e. so a stranger can verify
# the exit numbers from the record alone. Daily (not intraday) on purpose: intraday history
# expires ~60 days on Yahoo and isn't reproducible, which would break the verifiability standard.
PATH_FIELDS = [
    "pick_id","ticker","trading_date","session_idx","bar_date",
    "open","high","low","close","volume",
]

def clamp(x, lo, hi): return max(lo, min(hi, x))

# ----------------------------------------------------------------------------- scoring
def float_score(float_m):
    fmax = CONFIG["FILTERS"]["float_max_m"]
    if float_m <= 3: return 100.0
    if float_m >= fmax: return 0.0
    return clamp(100*(1-(float_m-3)/(fmax-3)), 0, 100)
def rvol_score(rvol):  return clamp((rvol/10)*100, 0, 100)
def gap_score(gap):    return clamp((abs(gap)/20)*100, 0, 100)
def price_score(p):
    lo, hi = CONFIG["FILTERS"]["price_min"], CONFIG["FILTERS"]["price_max"]
    if lo <= p <= hi: return 100.0
    if p < lo: return clamp((p/lo)*100, 0, 100)
    return clamp(100-(p-hi)*8, 0, 100)
def tier_of(s): return "A" if s>=75 else "B" if s>=60 else "C" if s>=45 else "D"

def score_inputs(price, prev, vol, avg, float_shares):
    float_m = (float_shares or 0)/1e6
    rvol = (vol/avg) if avg else 0.0
    gap  = ((price-prev)/prev*100) if prev else 0.0
    w = CONFIG["WEIGHTS"]
    fs, rs, gs, ps = float_score(float_m), rvol_score(rvol), gap_score(gap), price_score(price)
    score = fs*w["float"] + rs*w["rvol"] + gs*w["gap"] + ps*w["price"]
    return {
        "price_at_screen": round(price,4), "float_shares": int(float_shares or 0),
        "rvol": round(rvol,2), "gap_pct": round(gap,2),
        "float_score": round(fs,1), "rvol_score": round(rs,1),
        "gap_score": round(gs,1), "price_score": round(ps,1),
        "score": round(score,1), "tier": tier_of(score),
        "watch_level": round(price*(1+CONFIG["WATCH_LEVEL_PCT"]),4),
    }

# ----------------------------------------------------------------------------- yahoo data
def _yf():
    try:
        import yfinance as yf
        return yf
    except ImportError:
        sys.exit("yfinance not installed. Run:  pip install yfinance")

def fetch_one(yf, symbol, retries=3):
    """Return dict of price/prev/vol/avg/float for a symbol, or None.
    yfinance .info is intermittently throttled on CI, so retry with backoff."""
    info = None
    for attempt in range(retries):
        try:
            info = yf.Ticker(symbol).info
            if info and (info.get("regularMarketPrice") or info.get("currentPrice")):
                break
        except Exception:
            if attempt == retries - 1:
                raise
        time.sleep(1.5 * (attempt + 1))  # 1.5s, 3s, 4.5s backoff
    if not info:
        return None
    price = info.get("regularMarketPrice") or info.get("currentPrice")
    prev  = info.get("regularMarketPreviousClose") or info.get("previousClose")
    vol   = info.get("regularMarketVolume") or info.get("volume")
    avg   = info.get("averageVolume") or info.get("averageDailyVolume3Month") or info.get("averageVolume10days")
    flt   = info.get("floatShares") or info.get("sharesOutstanding")
    if price is None:
        return None
    # Group B instrumentation (captured, NOT scored — see VALIDATION-PLAN.md Part 1).
    # Pulled from the .info dict we already fetched above, so this adds ZERO extra
    # network calls / throttle risk. Short interest is the one Group-B variable Yahoo
    # exposes for free; catalyst_type and dilution_flag still need other feeds.
    si  = info.get("shortPercentOfFloat")
    si_pct = round(si*100, 2) if isinstance(si, (int, float)) else ""
    return {"symbol":symbol, "price":float(price), "prev":float(prev or 0),
            "vol":float(vol or 0), "avg":float(avg or 0), "float_shares":int(flt or 0),
            "short_interest_pct": si_pct}

def market_regime(yf):
    try:
        info = yf.Ticker("SPY").info
        p, pc = info.get("regularMarketPrice"), info.get("regularMarketPreviousClose")
        chg = (p-pc)/pc*100 if (p and pc) else 0
        return "risk-on" if chg > 0.3 else "risk-off" if chg < -0.3 else "neutral"
    except Exception:
        return "unknown"

# ----------------------------------------------------------------------------- csv io
def ensure_csv(path, fields):
    if not os.path.exists(path):
        with open(path,"w",newline="") as f: csv.DictWriter(f,fieldnames=fields).writeheader()
def append_row(path, fields, row):
    ensure_csv(path, fields)
    with open(path,"a",newline="") as f: csv.DictWriter(f,fieldnames=fields).writerow(row)
def read_rows(path):
    if not os.path.exists(path): return []
    with open(path,newline="") as f: return list(csv.DictReader(f))

# ----------------------------------------------------------------------------- commands
# NYSE full-day closures. Weekends are already excluded by the cron (Mon-Fri); this catches
# weekday holidays. A PRE-MARKET scan can't infer "is the market open" from a daily bar (today's
# bar doesn't exist yet at 7:30am ET), so an explicit list is needed. The stale/duplicate-quote
# guard below is the SOURCE-AGNOSTIC backstop for anything this list misses (future years, half
# days, feed outages): on a closed market the feed returns the prior session's quotes unchanged —
# exactly the bug that logged a phantom 2026-06-19 (Juneteenth) cohort identical to the 06-22 session.
NYSE_HOLIDAYS = {
    "2026-01-01","2026-01-19","2026-02-16","2026-04-03","2026-05-25","2026-06-19",
    "2026-07-03","2026-09-07","2026-11-26","2026-12-25",
    "2027-01-01","2027-01-18","2027-02-15","2027-03-26","2027-05-31","2027-06-18",
    "2027-07-05","2027-09-06","2027-11-25","2027-12-24",
}


def _is_stale_duplicate_scan(today, rows):
    """Phantom-scan detector. A closed market / frozen feed returns the previous session's
    quotes unchanged, so if today's screen is a near-exact price clone of the most recently
    logged session, it is not a real scan. Returns (is_stale: bool, detail: str)."""
    prior = read_rows(PICKS_CSV)
    dates = [r["trading_date"] for r in prior if r.get("trading_date") and r["trading_date"] < today]
    if not dates:
        return False, ""
    last_date = max(dates)
    last_px = {r["ticker"]: r["price_at_screen"] for r in prior if r["trading_date"] == last_date}
    overlap = [s for s in rows if s["ticker"] in last_px]
    if len(overlap) < 3:
        return False, ""
    def same(a, b):
        try:
            return abs(float(a) - float(b)) < 1e-9
        except (TypeError, ValueError):
            return False
    ident = [s["ticker"] for s in overlap if same(s["price_at_screen"], last_px[s["ticker"]])]
    if len(ident) / len(overlap) >= 0.8:
        return True, f"{len(ident)}/{len(overlap)} quotes byte-identical to last session {last_date}"
    return False, ""


def cmd_scan(sample=False):
    today = datetime.now().strftime("%Y-%m-%d")
    now_iso = datetime.now(timezone.utc).isoformat()
    f = CONFIG["FILTERS"]
    rows = []
    if sample:
        regime = "sample"
        for q in SAMPLE_QUOTES:
            s = score_inputs(q["price"], q["prev"], q["vol"], q["avg"], q["float_shares"])
            s["ticker"] = q["symbol"]; rows.append(s)
    else:
        if today in NYSE_HOLIDAYS:
            # Known market closure: clean no-op (exit 0), not a failure. Logging nothing is
            # correct — a closed day must NOT produce a screen (cf. the 2026-06-19 phantom bug).
            print(f"Market holiday ({today}) — NYSE closed. No scan; nothing logged.")
            return
        yf = _yf()
        regime = market_regime(yf)
        fetched = 0
        si_by_sym = {}  # Group B: short interest captured at scan time, keyed by ticker
        for sym in CONFIG["UNIVERSE"]:
            try:
                q = fetch_one(yf, sym)
                if not q: print(f"  skip {sym}: no price"); continue
                fetched += 1
                s = score_inputs(q["price"], q["prev"], q["vol"], q["avg"], q["float_shares"])
                s["ticker"] = sym; rows.append(s)
                si_by_sym[sym] = q.get("short_interest_pct", "")
                time.sleep(0.4)  # be gentle with Yahoo
            except Exception as e:
                print(f"  skip {sym}: {type(e).__name__} {str(e)[:80]}")
        # Total data outage → fail loudly so the run is flagged, not a silent gap.
        if fetched == 0:
            sys.exit("ERROR: data feed returned nothing for the entire universe "
                     "(likely throttled). No picks logged for today — run will be marked failed.")
    rows = [s for s in rows if f["price_min"] <= s["price_at_screen"] <= f["price_max"]]
    rows.sort(key=lambda s: s["score"], reverse=True)

    print(f"\n{today}  |  {len(rows)} names screened  |  regime: {regime}")
    print(f"{'TICK':<7}{'TIER':<5}{'SCORE':>6}{'PRICE':>9}{'GAP%':>8}{'RVOL':>7}{'FLOAT':>10}{'WATCH':>9}")
    for s in rows:
        print(f"{s['ticker']:<7}{s['tier']:<5}{s['score']:>6.1f}{s['price_at_screen']:>9.2f}"
              f"{s['gap_pct']:>7.1f}%{s['rvol']:>6.1f}x{s['float_shares']/1e6:>9.2f}M{s['watch_level']:>9.2f}")

    if sample:
        print("\n(SAMPLE mode — nothing written.)"); return
    # Phantom-scan backstop: if the feed handed back the prior session's quotes unchanged
    # (closed market not in NYSE_HOLIDAYS, or a frozen data source), fail LOUDLY and log
    # nothing rather than recording a fake screen. This would have caught the 06-19 cohort.
    stale, detail = _is_stale_duplicate_scan(today, rows)
    if stale:
        sys.exit(f"ERROR: stale/duplicate feed — {detail}. Likely a market holiday or frozen "
                 f"data source. No picks logged for {today}; run flagged failed so it is caught. "
                 "(If this is a known closure, add the date to NYSE_HOLIDAYS.)")
    # Dedupe guard: never log the same ticker twice for the same trading date
    # (e.g. a manual run after the scheduled run must not double-count picks).
    already = {(r["ticker"], r["trading_date"]) for r in read_rows(PICKS_CSV)}
    skipped = [s["ticker"] for s in rows if (s["ticker"], today) in already]
    rows = [s for s in rows if (s["ticker"], today) not in already]
    if skipped:
        print(f"Dedupe guard: skipped {len(skipped)} already-logged picks for {today}: {', '.join(skipped)}")
    # Forward-only SEC-EDGAR enrichment: dilution_flag/catalyst_type (into the existing
    # picks.csv columns, like short_interest did) + a quality snapshot into a sidecar so
    # Finding B stays testable OOS. NON-FATAL: if edgar_lens or SEC is unavailable, every
    # field degrades to blank and picks still log exactly as before.
    edgar_mod = None
    if CONFIG.get("CAPTURE_EDGAR", True):
        try:
            import edgar_lens as edgar_mod
        except Exception as e:
            print(f"  edgar_lens unavailable — Group-B capture skipped: {type(e).__name__} {str(e)[:60]}")

    for s in rows:
        pid = str(uuid.uuid4())
        snap = {}
        if edgar_mod:
            try:
                snap = edgar_mod.snapshot(s["ticker"], today)
            except Exception as e:
                snap = {"snapshot_note": f"{type(e).__name__}:{str(e)[:40]}"}
        append_row(PICKS_CSV, PICK_FIELDS, {
            "pick_id":pid, "published_at":now_iso, "trading_date":today,
            "model_version":MODEL_VERSION, **s,
            "catalyst_type": snap.get("catalyst_type", ""), "dilution_flag": snap.get("dilution_flag", ""),
            "short_interest_pct": si_by_sym.get(s["ticker"], ""), "market_regime":regime,
        })
        if snap and edgar_mod:
            row = {k: snap.get(k, "") for k in edgar_mod.SNAPSHOT_FIELDS}
            row.update({"pick_id":pid, "ticker":s["ticker"], "trading_date":today, "captured_at":now_iso})
            append_row(EDGAR_SNAPSHOT_CSV, edgar_mod.SNAPSHOT_FIELDS, row)
    print(f"\nLogged {len(rows)} picks -> {PICKS_CSV}")

def _trading_days_since(date_str):
    d0 = datetime.strptime(date_str,"%Y-%m-%d").date(); d1 = datetime.now().date()
    days, cur = 0, d0
    while cur < d1:
        cur += timedelta(days=1)
        if cur.weekday() < 5: days += 1
    return days

def cmd_grade():
    yf = _yf()
    picks = read_rows(PICKS_CSV)
    done = {o["pick_id"] for o in read_rows(OUTCOMES_CSV)}
    haircut = CONFIG["COST_HAIRCUT_PCT"]; graded = 0
    GRADE = CONFIG["GRADE_AFTER_DAYS"]
    for p in picks:
        if p["pick_id"] in done: continue
        tds = _trading_days_since(p["trading_date"])
        if tds < GRADE: continue
        # Past ~4 weeks of weekdays with still-no-gradeable-data, treat the symbol as
        # genuinely dead (delisted/halted) and record a terminal note. Before that, a
        # missing fetch is treated as TRANSIENT: skip and retry next run rather than
        # permanently dropping a real win/loss from the record (survivorship bias). [H1]
        stale = tds > 20
        try:
            start = p["trading_date"]
            end = (datetime.strptime(start,"%Y-%m-%d")+timedelta(days=16)).strftime("%Y-%m-%d")
            df = yf.Ticker(p["ticker"]).history(start=start, end=end, auto_adjust=False)
            if df is None or len(df)==0:
                if stale: append_outcome(p, "no history (gave up after retries)"); graded += 1
                continue  # transient: leave ungraded so the next run retries
            df = df.reset_index()
            df["d"] = df["Date"].astype(str).str[:10]
            idx = df.index[df["d"]==start]
            if len(idx)==0:
                if stale: append_outcome(p, "no entry bar"); graded += 1
                continue
            i0 = idx[0]
            window = df.iloc[i0:i0+GRADE+1]
            # Grade on ACTUAL trading sessions, not wall-clock weekdays: if the 5th
            # session hasn't closed yet (e.g., a market-holiday week), defer rather than
            # grade off a short window — which would mis-state the return. [H2]
            if len(window) < GRADE+1:
                continue
            o = float(window.iloc[0]["Open"]); c = float(window.iloc[0]["Close"])
            close_5d = float(window.iloc[GRADE]["Close"])
            hi = float(window["High"].max()); lo = float(window["Low"].min())
            roc = (c-o)/o*100 - haircut
            r5d = (close_5d-o)/o*100 - haircut
            append_row(OUTCOMES_CSV, OUTCOME_FIELDS, {
                "pick_id":p["pick_id"], "ticker":p["ticker"], "trading_date":start,
                "graded_at":datetime.now(timezone.utc).isoformat(),
                "entry_open":round(o,4), "same_day_close":round(c,4),
                "ret_open_close_net":round(roc,2), "ret_open_5dclose_net":round(r5d,2),
                "mfe_5d":round((hi-o)/o*100,2), "mae_5d":round((lo-o)/o*100,2),
                "win": "1" if roc>0 else "0", "note":"",
            })
            persist_path(p, window)   # immutable daily path for reproducible exit study
            graded += 1
        except Exception as e:
            print(f"  grade error {p['ticker']} {p['trading_date']}: {type(e).__name__} {str(e)[:80]}")
    print(f"Graded {graded} picks -> {OUTCOMES_CSV}")

def persist_path(p, window):
    """Append the daily-OHLC path of a graded pick to paths.csv. Purely additive and
    NON-FATAL: any failure here must never block grading or alter the outcome record.
    `window` is the entry session + GRADE sessions slice already fetched by the grader."""
    try:
        if os.path.exists(PATHS_CSV):
            have = {r["pick_id"] for r in read_rows(PATHS_CSV)}
            if p["pick_id"] in have:
                return  # already captured — keep it immutable, never rewrite
        for idx in range(len(window)):
            bar = window.iloc[idx]
            append_row(PATHS_CSV, PATH_FIELDS, {
                "pick_id": p["pick_id"], "ticker": p["ticker"],
                "trading_date": p["trading_date"], "session_idx": idx,
                "bar_date": str(bar["Date"])[:10],
                "open": round(float(bar["Open"]), 4), "high": round(float(bar["High"]), 4),
                "low": round(float(bar["Low"]), 4), "close": round(float(bar["Close"]), 4),
                "volume": int(bar["Volume"]) if bar["Volume"] == bar["Volume"] else "",
            })
    except Exception as e:
        print(f"  path-persist warn {p['ticker']} {p['trading_date']}: {type(e).__name__} {str(e)[:60]}")


def append_outcome(p, note):
    append_row(OUTCOMES_CSV, OUTCOME_FIELDS, {
        "pick_id":p["pick_id"],"ticker":p["ticker"],"trading_date":p["trading_date"],
        "graded_at":datetime.now(timezone.utc).isoformat(),"entry_open":"","same_day_close":"",
        "ret_open_close_net":"","ret_open_5dclose_net":"","mfe_5d":"","mae_5d":"","win":"","note":note})

def _f(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def cmd_report():
    picks = {p["pick_id"]: p for p in read_rows(PICKS_CSV)}
    outs  = [o for o in read_rows(OUTCOMES_CSV) if o.get("ret_open_close_net") not in ("", None)]
    if not outs:
        print("No graded outcomes yet. Run scan daily, then grade after 5 trading days."); return

    # ---- Tier table: return AND downside (MAE) per momentum tier --------------
    by_ret = {"A":[], "B":[], "C":[], "D":[]}
    by_mae = {"A":[], "B":[], "C":[], "D":[]}
    for o in outs:
        p = picks.get(o["pick_id"]);  r = _f(o.get("ret_open_close_net"))
        if not p or r is None: continue
        by_ret[p["tier"]].append(r)
        m = _f(o.get("mae_5d"))
        if m is not None: by_mae[p["tier"]].append(m)
    print(f"\nTier table — net same-day open->close return (after {CONFIG['COST_HAIRCUT_PCT']}% haircut)")
    print(f"  graded picks: {len(outs)}\n")
    print(f"{'TIER':<6}{'N':>5}{'MEAN%':>9}{'MEDIAN%':>10}{'WIN%':>8}{'MEAN_MAE%':>11}")
    for t in ["A","B","C","D"]:
        v = by_ret[t]
        if not v: print(f"{t:<6}{0:>5}{'-':>9}{'-':>10}{'-':>8}{'-':>11}"); continue
        win = 100*sum(1 for x in v if x>0)/len(v)
        mae = statistics.mean(by_mae[t]) if by_mae[t] else float('nan')
        print(f"{t:<6}{len(v):>5}{statistics.mean(v):>9.2f}{statistics.median(v):>10.2f}{win:>8.1f}{mae:>11.2f}")

    # ---- Calibration: does a higher raw score => higher % positive? -----------
    # Finer than tiers; this is the curve that's hardest to fake (SYNTHESIS 1.3).
    bands = [(0,45),(45,55),(55,65),(65,75),(75,85),(85,101)]
    buck = {b: [] for b in bands}
    for o in outs:
        p = picks.get(o["pick_id"]);  r = _f(o.get("ret_open_close_net"))
        if not p or r is None: continue
        sc = _f(p.get("score"))
        if sc is None: continue
        for b in bands:
            if b[0] <= sc < b[1]: buck[b].append(r); break
    print("\nCalibration — % positive by score band (the validity curve)")
    print(f"{'BAND':<9}{'N':>5}{'%POS':>8}{'MEAN%':>9}")
    for b in bands:
        v = buck[b]; lbl = f"{b[0]}-{b[1]-1}"
        if not v: print(f"{lbl:<9}{0:>5}{'-':>8}{'-':>9}"); continue
        pos = 100*sum(1 for x in v if x>0)/len(v)
        print(f"{lbl:<9}{len(v):>5}{pos:>8.1f}{statistics.mean(v):>9.2f}")

    print("\nPASS BAR (VALIDATION-PLAN.md): A>B>C>D monotonic on mean AND median,")
    print("A-tier mean > 0 after costs, >=200 picks, ordering holds out-of-sample.")
    print("Downside read (SYNTHESIS 1.1): is MEAN_MAE shallower for higher tiers / score bands?")
    print("Note: the Quality-Lens downside test (Green vs Red MAE) needs quality grades")
    print("logged into picks.csv first — that's a Group-B instrumentation item (IMPROVEMENTS C2).")

BRIEF_MD = os.path.join(HERE, "brief.md")

def finding_a_stats():
    """Live-log drawdown by momentum tier — the Finding A signal (hotter A/B = deeper
    drawdown / higher rug rate). Computed from the immutable forward log, so the brief's
    risk flag is grounded in real graded outcomes, not assertion. Returns None if too few
    graded picks across tiers to be worth showing."""
    picks = read_rows(PICKS_CSV); outs = read_rows(OUTCOMES_CSV)
    if not outs: return None
    tier_by_id = {p.get("pick_id"): p.get("tier") for p in picks if p.get("pick_id")}
    hi, lo = [], []
    for o in outs:
        mae = _f(o.get("mae_5d"))
        if mae is None: continue
        t = tier_by_id.get(o.get("pick_id"))
        if t in ("A", "B"): hi.append(mae)
        elif t in ("C", "D"): lo.append(mae)
    if len(hi) < 3 or len(lo) < 3: return None
    rug = lambda xs: 100.0 * sum(1 for m in xs if m < -30) / len(xs)
    return {"n_hi": len(hi), "mae_hi": statistics.median(hi), "rug_hi": rug(hi),
            "n_lo": len(lo), "mae_lo": statistics.median(lo), "rug_lo": rug(lo),
            "holds": statistics.median(hi) < statistics.median(lo)}

def cmd_brief():
    """Generate an IMPERSONAL, educational morning brief from the latest logged screen.
    Same content for everyone, objective observations only, no buy/sell language — this
    keeps it inside the publisher's exclusion (REQUIREMENTS.md §7). NOTE: wiring this to
    the public site / charging for it still needs securities-counsel review (gate G4,
    IMPROVEMENTS-v0.3 B4). For now it just writes brief.md for review."""
    picks = read_rows(PICKS_CSV)
    if not picks:
        print("No picks logged yet — run `scan` first."); return
    latest = max(p["trading_date"] for p in picks)
    todays = [p for p in picks if p["trading_date"] == latest]
    todays.sort(key=lambda p: _f(p.get("score")) or 0, reverse=True)
    regime = todays[0].get("market_regime", "unknown") if todays else "unknown"

    def obs(p):
        notes = []
        rvol = _f(p.get("rvol")); fl = _f(p.get("float_shares")); gap = _f(p.get("gap_pct"))
        si = _f(p.get("short_interest_pct"))
        if rvol and rvol >= 10: notes.append(f"very high relative volume ({rvol:.0f}×)")
        elif rvol and rvol >= 5: notes.append(f"elevated relative volume ({rvol:.1f}×)")
        if fl and fl < 3e6: notes.append(f"thin float ({fl/1e6:.1f}M)")
        if gap and abs(gap) >= 15: notes.append(f"large {'up' if gap>0 else 'down'}-gap ({gap:+.0f}%)")
        return "; ".join(notes) or "screened on the published criteria"

    def caution(p):
        c = []
        si = _f(p.get("short_interest_pct")); price = _f(p.get("price_at_screen"))
        gap = _f(p.get("gap_pct")); fl = _f(p.get("float_shares"))
        if si and si >= 20: c.append(f"high short interest ({si:.0f}% of float) — squeeze-prone and violent both ways")
        if gap and gap >= 20: c.append("already extended pre-market — chasing buys the top")
        if fl and fl < 1e6: c.append("ultra-thin float — spreads and slippage can be severe")
        if price and price < 1: c.append("sub-$1 — heightened manipulation / delisting risk")
        return c

    L = []
    L.append(f"# IgnitionScan — Morning Brief · {latest}")
    L.append("")
    L.append(f"_Impersonal, educational watchlist — identical for all readers. Market regime: **{regime}**. "
             f"Nothing here is a recommendation to buy, sell, or hold; it describes how names rank on objective, "
             f"published criteria. Low-float / low-priced stocks are highly volatile._")
    L.append("")
    fa = finding_a_stats()
    top = todays[:5]
    L.append("## What stands out today")
    for p in top:
        flag = ""
        if fa and fa["holds"] and p["tier"] in ("A", "B"):
            flag = "  ⚠️ **Finding A — runs hot:** highest-momentum tier; historically the *deepest* drawdowns. Hardest to hold."
        L.append(f"- **{p['ticker']}** (tier {p['tier']}, score {p['score']}) — {obs(p)}. "
                 f"Watch level (reference only, +{int(CONFIG['WATCH_LEVEL_PCT']*100)}%): ${p['watch_level']}.{flag}")
    L.append("")
    cautions = [(p["ticker"], caution(p)) for p in todays if caution(p)]
    L.append("## Risk area — read before anything")
    if cautions:
        for tk, cs in cautions:
            for c in cs: L.append(f"- **{tk}**: {c}.")
    else:
        L.append("- Standard low-float risks apply to every name: wide spreads, fast reversals, and gap-fills. "
                 "A high score measures activity, not safety.")
    L.append("")
    if fa and fa["holds"]:
        L.append("## Finding A — the one edge that holds (from your own log)")
        L.append(f"- Across **{fa['n_hi']+fa['n_lo']}** graded picks, the **hottest momentum tier (A/B) "
                 f"draws down deeper**: median worst-dip **{fa['mae_hi']:+.0f}%** (rug rate {fa['rug_hi']:.0f}%) "
                 f"vs **{fa['mae_lo']:+.0f}%** (rug {fa['rug_lo']:.0f}%) for C/D.")
        L.append("- **Actionable read:** a top-of-leaderboard A/B name is the part most likely to gut you. "
                 "Treat a high score as a *warning label on the downside*, not a green light.")
        L.append("")
    L.append("## How to read this")
    L.append("- The score answers *“is this moving?”* — not *“is this worth buying?”* Pair it with the Quality "
             "Lens and the primary filings before doing anything.")
    L.append("- Every pick above is logged immutably and graded honestly after 5 trading days on the public "
             "track record — winners and losers.")
    L.append("")
    L.append("_Educational / informational only. Not investment advice. The operators may hold positions in "
             "screened securities. Past performance does not predict future results._")
    md = "\n".join(L) + "\n"
    with open(BRIEF_MD, "w") as f: f.write(md)
    # Also write a committed copy so the daily Action can publish it to the repo
    # for phone viewing (reports/ is tracked; brief.md stays gitignored).
    reports_dir = os.path.join(HERE, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    with open(os.path.join(reports_dir, "brief-LATEST.md"), "w") as f: f.write(md)
    print(md)
    print(f"\n(Wrote {BRIEF_MD} and reports/brief-LATEST.md — personal use; not wired to the public site.)")

# sample data (price, prev, vol, avg, float_shares) for offline demo
SAMPLE_QUOTES = [
    {"symbol":"BJDX","price":2.18,"prev":1.81,"vol":41200000,"avg":2900000,"float_shares":3100000},
    {"symbol":"SUGP","price":1.12,"prev":0.95,"vol":18600000,"avg":1500000,"float_shares":468000},
    {"symbol":"MASK","price":4.21,"prev":3.55,"vol":9800000,"avg":1200000,"float_shares":5600000},
    {"symbol":"HKIT","price":0.68,"prev":0.60,"vol":5400000,"avg":520000,"float_shares":7400000},
    {"symbol":"PW","price":8.47,"prev":7.10,"vol":6600000,"avg":880000,"float_shares":11200000},
]

def main():
    ap = argparse.ArgumentParser(description="IgnitionScan logger/grader (v0.2, Yahoo Finance)")
    ap.add_argument("command", choices=["scan","grade","report","brief","demo"])
    args = ap.parse_args()
    if   args.command=="scan":   cmd_scan()
    elif args.command=="demo":   cmd_scan(sample=True)
    elif args.command=="grade":  cmd_grade()
    elif args.command=="report": cmd_report()
    elif args.command=="brief":  cmd_brief()

if __name__ == "__main__":
    main()
