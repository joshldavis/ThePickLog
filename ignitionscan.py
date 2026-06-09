#!/usr/bin/env python3
"""
IgnitionScan — daily logger / grader (v0, personal paper-trading tool)
=====================================================================
Implements Part 1 (pick log) and Part 2 (cost-honest grading) of
VALIDATION-PLAN.md. Standard library only — no pip install needed.

WHAT IT DOES
  scan   Pull the universe, score each name, append an IMMUTABLE row to picks.csv.
  grade  For picks that are >= GRADE_AFTER_DAYS old, compute realizable returns
         (net of a friction haircut) and write them to outcomes.csv.
  report Print a tier table (A/B/C/D: mean/median net return, win%) from graded picks.
  demo   Run scan on bundled sample data so you can see output with no API key.

DATA
  Uses Financial Modeling Prep (free tier). Set your key:
      export FMP_API_KEY=your_key_here
  Float is approximated from sharesOutstanding (flagged) — replace with true
  public float in production. Short interest / catalyst / dilution columns are
  captured-but-blank for now (instrument first, score later).

TYPICAL USE (paper trading yourself)
  Each market morning:   python ignitionscan.py scan
  Each evening:          python ignitionscan.py grade
  Weekly:                python ignitionscan.py report
  (Or put scan/grade on cron — see README.md.)

NOTHING HERE IS INVESTMENT ADVICE. The model is unvalidated until report says otherwise.
"""

import argparse, csv, json, os, sys, uuid, statistics
import urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone

MODEL_VERSION = "v0.1"
FMP = "https://financialmodelingprep.com/api/v3"
API_KEY = os.environ.get("FMP_API_KEY", "").strip()

HERE = os.path.dirname(os.path.abspath(__file__))
PICKS_CSV    = os.path.join(HERE, "picks.csv")
OUTCOMES_CSV = os.path.join(HERE, "outcomes.csv")

CONFIG = {
    # Seed universe for v0. Replace with a real full-market screen later.
    "UNIVERSE": ["BJDX","MASK","SUGP","GCDT","CODX","VMAR","PW","NCT","HKIT",
                 "IOTR","SVRN","RKDA","BNZI","CUPR","ATPC","JAGX"],
    "WEIGHTS":  {"float":0.30, "rvol":0.35, "gap":0.25, "price":0.10},  # sum=1
    "FILTERS":  {"price_min":0.50, "price_max":10.0, "float_max_m":50.0},
    "WATCH_LEVEL_PCT": 0.20,     # reference level (NOT a target/prediction)
    "COST_HAIRCUT_PCT": 2.0,     # round-trip friction; sensitivity-test 1-3%
    "GRADE_AFTER_DAYS": 5,       # trading days held for the window
}

PICK_FIELDS = [
    # --- Group C: audit / identity ---
    "pick_id","published_at","trading_date","model_version",
    # --- Group A: scored inputs ---
    "ticker","price_at_screen","float_shares","rvol","gap_pct",
    "float_score","rvol_score","gap_score","price_score","score","tier","watch_level",
    # --- Group B: instrumented, NOT scored yet ---
    "catalyst_type","dilution_flag","short_interest_pct","market_regime",
]
OUTCOME_FIELDS = [
    "pick_id","ticker","trading_date","graded_at",
    "entry_open","same_day_close",
    "ret_open_close_net","ret_open_5dclose_net","mfe_5d","mae_5d","win","note",
]

# ----------------------------------------------------------------------------- helpers
def clamp(x, lo, hi): return max(lo, min(hi, x))

def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ignitionscan/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def fmp(path, **params):
    if not API_KEY:
        raise RuntimeError("FMP_API_KEY not set")
    params["apikey"] = API_KEY
    return http_get_json(f"{FMP}/{path}?{urllib.parse.urlencode(params)}")

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

def score_quote(q):
    price = float(q.get("price") or 0)
    prev  = float(q.get("previousClose") or 0)
    vol   = float(q.get("volume") or 0)
    avg   = float(q.get("avgVolume") or 0)
    shrs  = float(q.get("sharesOutstanding") or 0)
    float_m = shrs/1e6
    rvol = (vol/avg) if avg else 0.0
    gap  = ((price-prev)/prev*100) if prev else 0.0
    w = CONFIG["WEIGHTS"]
    fs, rs, gs, ps = float_score(float_m), rvol_score(rvol), gap_score(gap), price_score(price)
    score = fs*w["float"] + rs*w["rvol"] + gs*w["gap"] + ps*w["price"]
    return {
        "ticker": q.get("symbol"), "price_at_screen": round(price,4),
        "float_shares": int(shrs), "rvol": round(rvol,2), "gap_pct": round(gap,2),
        "float_score": round(fs,1), "rvol_score": round(rs,1),
        "gap_score": round(gs,1), "price_score": round(ps,1),
        "score": round(score,1), "tier": tier_of(score),
        "watch_level": round(price*(1+CONFIG["WATCH_LEVEL_PCT"]),4),
    }

# ----------------------------------------------------------------------------- regime
def market_regime():
    try:
        spy = fmp(f"quote/SPY")[0]
        chg = float(spy.get("changesPercentage") or 0)
        return "risk-on" if chg > 0.3 else "risk-off" if chg < -0.3 else "neutral"
    except Exception:
        return "unknown"

# ----------------------------------------------------------------------------- csv io
def ensure_csv(path, fields):
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=fields).writeheader()

def append_row(path, fields, row):
    ensure_csv(path, fields)
    with open(path, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=fields).writerow(row)

def read_rows(path):
    if not os.path.exists(path): return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

# ----------------------------------------------------------------------------- commands
def cmd_scan(sample=False):
    today = datetime.now().strftime("%Y-%m-%d")
    now_iso = datetime.now(timezone.utc).isoformat()
    if sample or not API_KEY:
        if not sample:
            print("No FMP_API_KEY set — running in SAMPLE mode (not logged).")
        quotes = SAMPLE_QUOTES
        regime = "sample"
        dry = True
    else:
        quotes = fmp("quote/" + ",".join(CONFIG["UNIVERSE"]))
        regime = market_regime()
        dry = False

    f = CONFIG["FILTERS"]
    scored = [score_quote(q) for q in quotes]
    scored = [s for s in scored if f["price_min"] <= s["price_at_screen"] <= f["price_max"]]
    scored.sort(key=lambda s: s["score"], reverse=True)

    print(f"\n{today}  |  {len(scored)} names screened  |  regime: {regime}")
    print(f"{'TICK':<7}{'TIER':<5}{'SCORE':>6}{'PRICE':>9}{'GAP%':>8}{'RVOL':>7}{'FLOAT':>9}{'WATCH':>9}")
    for s in scored:
        print(f"{s['ticker']:<7}{s['tier']:<5}{s['score']:>6.1f}"
              f"{s['price_at_screen']:>9.2f}{s['gap_pct']:>7.1f}%{s['rvol']:>6.1f}x"
              f"{s['float_shares']/1e6:>8.1f}M{s['watch_level']:>9.2f}")

    if dry:
        print("\n(SAMPLE mode — nothing written. Set FMP_API_KEY to log real picks.)")
        return
    for s in scored:
        append_row(PICKS_CSV, PICK_FIELDS, {
            "pick_id": str(uuid.uuid4()), "published_at": now_iso,
            "trading_date": today, "model_version": MODEL_VERSION, **s,
            "catalyst_type":"", "dilution_flag":"", "short_interest_pct":"",
            "market_regime": regime,
        })
    print(f"\nLogged {len(scored)} picks -> {PICKS_CSV}")

def _trading_days_since(date_str):
    d0 = datetime.strptime(date_str, "%Y-%m-%d").date()
    d1 = datetime.now().date()
    days = 0
    cur = d0
    while cur < d1:
        cur += timedelta(days=1)
        if cur.weekday() < 5:  # Mon-Fri (ignores holidays; close enough for v0)
            days += 1
    return days

def cmd_grade():
    if not API_KEY:
        print("FMP_API_KEY not set — cannot fetch history to grade."); return
    picks = read_rows(PICKS_CSV)
    done = {o["pick_id"] for o in read_rows(OUTCOMES_CSV)}
    haircut = CONFIG["COST_HAIRCUT_PCT"]
    graded = 0
    for p in picks:
        if p["pick_id"] in done: continue
        if _trading_days_since(p["trading_date"]) < CONFIG["GRADE_AFTER_DAYS"]: continue
        try:
            start = p["trading_date"]
            end = (datetime.strptime(start,"%Y-%m-%d") + timedelta(days=16)).strftime("%Y-%m-%d")
            hist = fmp(f"historical-price-full/{p['ticker']}", **{"from":start,"to":end})
            bars = sorted(hist.get("historical", []), key=lambda b: b["date"])
            entry = next((b for b in bars if b["date"] == start), None)
            if not entry:
                append_outcome(p, note="no entry bar for trading_date"); graded += 1; continue
            window = [b for b in bars if b["date"] >= start][:CONFIG["GRADE_AFTER_DAYS"]+1]
            o = float(entry["open"]); c = float(entry["close"])
            close_5d = float(window[-1]["close"])
            hi = max(float(b["high"]) for b in window)
            lo = min(float(b["low"])  for b in window)
            roc  = (c-o)/o*100 - haircut          # net same-day open->close
            r5d  = (close_5d-o)/o*100 - haircut    # net open->+5 close
            mfe  = (hi-o)/o*100                     # excursion (not haircut-adjusted)
            mae  = (lo-o)/o*100
            append_row(OUTCOMES_CSV, OUTCOME_FIELDS, {
                "pick_id":p["pick_id"], "ticker":p["ticker"], "trading_date":start,
                "graded_at": datetime.now(timezone.utc).isoformat(),
                "entry_open":round(o,4), "same_day_close":round(c,4),
                "ret_open_close_net":round(roc,2), "ret_open_5dclose_net":round(r5d,2),
                "mfe_5d":round(mfe,2), "mae_5d":round(mae,2),
                "win": "1" if roc > 0 else "0", "note":"",
            })
            graded += 1
        except Exception as e:
            print(f"  grade error {p['ticker']} {p['trading_date']}: {e}")
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
        if not p: continue
        by[p["tier"]].append(float(o["ret_open_close_net"]))
    print(f"\nTier table — net same-day open->close return (after {CONFIG['COST_HAIRCUT_PCT']}% haircut)")
    print(f"  graded picks: {len(outs)}\n")
    print(f"{'TIER':<6}{'N':>5}{'MEAN%':>9}{'MEDIAN%':>10}{'WIN%':>8}")
    for t in ["A","B","C","D"]:
        v = by[t]
        if not v:
            print(f"{t:<6}{0:>5}{'-':>9}{'-':>10}{'-':>8}"); continue
        win = 100*sum(1 for x in v if x>0)/len(v)
        print(f"{t:<6}{len(v):>5}{statistics.mean(v):>9.2f}{statistics.median(v):>10.2f}{win:>8.1f}")
    print("\nPASS BAR (see VALIDATION-PLAN.md): A>B>C>D monotonic on mean AND median,")
    print("A-tier mean > 0 after costs, >=200 picks, and the ordering holds out-of-sample.")

# ----------------------------------------------------------------------------- sample data
SAMPLE_QUOTES = [
    {"symbol":"BJDX","price":2.18,"previousClose":1.81,"volume":41200000,"avgVolume":2900000,"sharesOutstanding":3100000},
    {"symbol":"SUGP","price":1.12,"previousClose":0.95,"volume":18600000,"avgVolume":1500000,"sharesOutstanding":4200000},
    {"symbol":"MASK","price":4.21,"previousClose":3.55,"volume":9800000,"avgVolume":1200000,"sharesOutstanding":5600000},
    {"symbol":"HKIT","price":0.68,"previousClose":0.60,"volume":5400000,"avgVolume":520000,"sharesOutstanding":7400000},
    {"symbol":"CODX","price":11.41,"previousClose":9.90,"volume":14900000,"avgVolume":2600000,"sharesOutstanding":28000000},
    {"symbol":"PW","price":8.47,"previousClose":7.10,"volume":6600000,"avgVolume":880000,"sharesOutstanding":11200000},
]

# ----------------------------------------------------------------------------- cli
def main():
    ap = argparse.ArgumentParser(description="IgnitionScan logger/grader (v0)")
    ap.add_argument("command", choices=["scan","grade","report","demo"],
                    help="scan=log today's picks, grade=score outcomes, report=tier table, demo=sample run")
    args = ap.parse_args()
    if   args.command == "scan":   cmd_scan()
    elif args.command == "demo":   cmd_scan(sample=True)
    elif args.command == "grade":  cmd_grade()
    elif args.command == "report": cmd_report()

if __name__ == "__main__":
    main()
