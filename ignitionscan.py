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

CONFIG = {
    "UNIVERSE": ["BJDX","MASK","SUGP","GCDT","CODX","VMAR","PW","NCT","HKIT",
                 "IOTR","SVRN","RKDA","BNZI","CUPR","ATPC","JAGX"],
    "WEIGHTS":  {"float":0.30, "rvol":0.35, "gap":0.25, "price":0.10},  # sum=1
    "FILTERS":  {"price_min":0.50, "price_max":10.0, "float_max_m":50.0},
    "WATCH_LEVEL_PCT": 0.20,
    "COST_HAIRCUT_PCT": 2.0,
    "GRADE_AFTER_DAYS": 5,
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

def fetch_one(yf, symbol):
    """Return dict of price/prev/vol/avg/float for a symbol, or None."""
    info = yf.Ticker(symbol).info
    price = info.get("regularMarketPrice") or info.get("currentPrice")
    prev  = info.get("regularMarketPreviousClose") or info.get("previousClose")
    vol   = info.get("regularMarketVolume") or info.get("volume")
    avg   = info.get("averageVolume") or info.get("averageDailyVolume3Month") or info.get("averageVolume10days")
    flt   = info.get("floatShares") or info.get("sharesOutstanding")
    if price is None:
        return None
    return {"symbol":symbol, "price":float(price), "prev":float(prev or 0),
            "vol":float(vol or 0), "avg":float(avg or 0), "float_shares":int(flt or 0)}

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
        yf = _yf()
        regime = market_regime(yf)
        for sym in CONFIG["UNIVERSE"]:
            try:
                q = fetch_one(yf, sym)
                if not q: print(f"  skip {sym}: no price"); continue
                s = score_inputs(q["price"], q["prev"], q["vol"], q["avg"], q["float_shares"])
                s["ticker"] = sym; rows.append(s)
                time.sleep(0.4)  # be gentle with Yahoo
            except Exception as e:
                print(f"  skip {sym}: {type(e).__name__} {str(e)[:80]}")
    rows = [s for s in rows if f["price_min"] <= s["price_at_screen"] <= f["price_max"]]
    rows.sort(key=lambda s: s["score"], reverse=True)

    print(f"\n{today}  |  {len(rows)} names screened  |  regime: {regime}")
    print(f"{'TICK':<7}{'TIER':<5}{'SCORE':>6}{'PRICE':>9}{'GAP%':>8}{'RVOL':>7}{'FLOAT':>10}{'WATCH':>9}")
    for s in rows:
        print(f"{s['ticker']:<7}{s['tier']:<5}{s['score']:>6.1f}{s['price_at_screen']:>9.2f}"
              f"{s['gap_pct']:>7.1f}%{s['rvol']:>6.1f}x{s['float_shares']/1e6:>9.2f}M{s['watch_level']:>9.2f}")

    if sample:
        print("\n(SAMPLE mode — nothing written.)"); return
    # Dedupe guard: never log the same ticker twice for the same trading date
    # (e.g. a manual run after the scheduled run must not double-count picks).
    already = {(r["ticker"], r["trading_date"]) for r in read_rows(PICKS_CSV)}
    skipped = [s["ticker"] for s in rows if (s["ticker"], today) in already]
    rows = [s for s in rows if (s["ticker"], today) not in already]
    if skipped:
        print(f"Dedupe guard: skipped {len(skipped)} already-logged picks for {today}: {', '.join(skipped)}")
    for s in rows:
        append_row(PICKS_CSV, PICK_FIELDS, {
            "pick_id":str(uuid.uuid4()), "published_at":now_iso, "trading_date":today,
            "model_version":MODEL_VERSION, **s,
            "catalyst_type":"", "dilution_flag":"", "short_interest_pct":"", "market_regime":regime,
        })
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
    for p in picks:
        if p["pick_id"] in done: continue
        if _trading_days_since(p["trading_date"]) < CONFIG["GRADE_AFTER_DAYS"]: continue
        try:
            start = p["trading_date"]
            end = (datetime.strptime(start,"%Y-%m-%d")+timedelta(days=16)).strftime("%Y-%m-%d")
            df = yf.Ticker(p["ticker"]).history(start=start, end=end, auto_adjust=False)
            if df is None or len(df)==0:
                append_outcome(p, "no history"); graded += 1; continue
            df = df.reset_index()
            df["d"] = df["Date"].astype(str).str[:10]
            idx = df.index[df["d"]==start]
            if len(idx)==0:
                append_outcome(p, "no entry bar"); graded += 1; continue
            i0 = idx[0]
            window = df.iloc[i0:i0+CONFIG["GRADE_AFTER_DAYS"]+1]
            o = float(window.iloc[0]["Open"]); c = float(window.iloc[0]["Close"])
            close_5d = float(window.iloc[-1]["Close"])
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
            graded += 1
        except Exception as e:
            print(f"  grade error {p['ticker']} {p['trading_date']}: {type(e).__name__} {str(e)[:80]}")
    print(f"Graded {graded} picks -> {OUTCOMES_CSV}")

def append_outcome(p, note):
    append_row(OUTCOMES_CSV, OUTCOME_FIELDS, {
        "pick_id":p["pick_id"],"ticker":p["ticker"],"trading_date":p["trading_date"],
        "graded_at":datetime.now(timezone.utc).isoformat(),"entry_open":"","same_day_close":"",
        "ret_open_close_net":"","ret_open_5dclose_net":"","mfe_5d":"","mae_5d":"","win":"","note":note})

def cmd_report():
    picks = {p["pick_id"]: p for p in read_rows(PICKS_CSV)}
    outs  = [o for o in read_rows(OUTCOMES_CSV) if o.get("ret_open_close_net") not in ("", None)]
    if not outs:
        print("No graded outcomes yet. Run scan daily, then grade after 5 trading days."); return
    by = {"A":[], "B":[], "C":[], "D":[]}
    for o in outs:
        p = picks.get(o["pick_id"])
        if p: by[p["tier"]].append(float(o["ret_open_close_net"]))
    print(f"\nTier table — net same-day open->close return (after {CONFIG['COST_HAIRCUT_PCT']}% haircut)")
    print(f"  graded picks: {len(outs)}\n")
    print(f"{'TIER':<6}{'N':>5}{'MEAN%':>9}{'MEDIAN%':>10}{'WIN%':>8}")
    for t in ["A","B","C","D"]:
        v = by[t]
        if not v: print(f"{t:<6}{0:>5}{'-':>9}{'-':>10}{'-':>8}"); continue
        win = 100*sum(1 for x in v if x>0)/len(v)
        print(f"{t:<6}{len(v):>5}{statistics.mean(v):>9.2f}{statistics.median(v):>10.2f}{win:>8.1f}")
    print("\nPASS BAR (VALIDATION-PLAN.md): A>B>C>D monotonic on mean AND median,")
    print("A-tier mean > 0 after costs, >=200 picks, ordering holds out-of-sample.")

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
    ap.add_argument("command", choices=["scan","grade","report","demo"])
    args = ap.parse_args()
    if   args.command=="scan":   cmd_scan()
    elif args.command=="demo":   cmd_scan(sample=True)
    elif args.command=="grade":  cmd_grade()
    elif args.command=="report": cmd_report()

if __name__ == "__main__":
    main()
