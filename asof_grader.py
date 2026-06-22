#!/usr/bin/env python3
"""
asof_grader.py — Phase 1 of TEST-PLAN-quality-downside.md: the AS-OF-DATE
Quality-Lens grader. Kills the look-ahead threat from STRATEGY §6 Finding B.

The live /api/edgar returns CURRENT filings. This grades a ticker as it would
have looked on a past date D, by pulling SEC XBRL companyfacts and keeping only
values FILED ON OR BEFORE D — i.e. exactly the financials a reader could have
seen that morning. Output feeds quality_lens.compute_quality (the faithful port),
so the as-of grade equals what the site WOULD have shown on date D.

Data: SEC EDGAR companyfacts (free, no key). SEC requires a descriptive
User-Agent and asks for <10 req/s — both handled. 1 request per ticker.

WHY companyfacts can do point-in-time: every value carries a `filed` date and a
`form`. Filtering filed<=D and re-selecting the latest restatement-as-of-D
reconstructs the as-of view. (Verified against JAGX Revenues — run --selftest.)

USAGE (on a machine with network — e.g. Josh's Mac):
    python3 asof_grader.py --selftest                 # offline logic test (no network)
    python3 asof_grader.py --ticker JAGX --asof 2025-08-01
    python3 asof_grader.py --backtest backtest_results.csv --out backtest_quality_asof.csv

NOT INVESTMENT ADVICE. Backtest output is exploratory / in-sample only and is
gitignored — it never touches the immutable forward log (picks.csv/outcomes.csv).
"""
import argparse, csv, json, os, sys, time, urllib.request
from datetime import date

from quality_lens import assemble_fundamentals, compute_quality

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "IgnitionScan/1.0 (research tool; contact davis1163@gmail.com)"
ANNUAL_FORMS = ("10-K", "20-F", "40-F")  # same annual-report set as api/edgar.js

# us-gaap tag priority lists — mirror api/edgar.js fyMap() exactly (single source of truth).
TAGS = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
                "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"],
    "netIncome": ["NetIncomeLoss", "ProfitLoss"],
    "operatingIncome": ["OperatingIncomeLoss"],
    "grossProfit": ["GrossProfit"],
    "cost": ["CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold"],
    "da": ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization",
           "DepreciationAmortizationAndAccretionNet"],
    "shares": ["WeightedAverageNumberOfDilutedSharesOutstanding",
               "WeightedAverageNumberOfSharesOutstandingBasic"],
    "ocf": ["NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue",
             "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
    "equity": ["StockholdersEquity",
               "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "currentAssets": ["AssetsCurrent"],
    "currentLiabilities": ["LiabilitiesCurrent"],
    "ltd": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "std": ["LongTermDebtCurrent", "DebtCurrent", "ShortTermBorrowings"],
}


# ----------------------------------------------------------------------------
# THE POINT-IN-TIME CORE (pure, unit-tested by --selftest)
# ----------------------------------------------------------------------------
def fy_map_asof(concept_unit_entries, asof, annual_forms=ANNUAL_FORMS):
    """Given one XBRL concept's unit entries (the units.USD / units.shares list),
    return {fiscal_year: value} using ONLY annual-report values FILED <= asof.

    Differs intentionally from api/edgar.js fyMap (which has no as-of need): for a
    given fiscal year we keep the value from the LATEST `filed` <= asof (the most
    recent restatement a reader could have seen by date D), tie-broken by latest
    period `end`. The live proxy keeps latest-`end` only, which is fine for
    'current' but wrong for point-in-time when a year gets restated.
    """
    asof = _d(asof)
    best = {}  # fy -> (filed_date, end_str, val)
    for p in concept_unit_entries or []:
        form = p.get("form") or ""
        if not any(form.startswith(f) for f in annual_forms):
            continue
        if p.get("fp") != "FY":
            continue
        filed = p.get("filed")
        if not filed or _d(filed) > asof:
            continue
        end = p.get("end") or ""
        fy = p.get("fy") or (int(end[:4]) if end[:4].isdigit() else None)
        if fy is None:
            continue
        key = (_d(filed), end)
        if fy not in best or key > (best[fy][0], best[fy][1]):
            best[fy] = (_d(filed), end, p.get("val"))
    return {fy: v[2] for fy, v in best.items()}


def _d(s):
    if isinstance(s, date):
        return s
    return date(int(s[0:4]), int(s[5:7]), int(s[8:10]))


def _first_nonempty_map(facts_usgaap, tag_list, asof):
    """First tag in priority order that yields any as-of FY values -> {fy: val}."""
    for tag in tag_list:
        node = facts_usgaap.get(tag)
        if not node or "units" not in node:
            continue
        unit_key = "USD" if "USD" in node["units"] else (
            "shares" if "shares" in node["units"] else next(iter(node["units"]), None))
        if unit_key is None:
            continue
        m = fy_map_asof(node["units"][unit_key], asof)
        if m:
            return m
    return {}


def build_asof_statements(facts_usgaap, asof, top_n=4):
    """Reconstruct the same statement shape api/edgar.js returns, but as-of `asof`."""
    M = {k: _first_nonempty_map(facts_usgaap, tags, asof) for k, tags in TAGS.items()}
    years = sorted((int(y) for y in M["revenue"].keys()), reverse=True)[:top_n]
    if not years:
        return None

    def arr(m):
        return [m.get(y) for y in years]

    gross = [M["grossProfit"].get(y) if M["grossProfit"].get(y) is not None
             else (M["revenue"].get(y) - M["cost"].get(y)
                   if (M["revenue"].get(y) is not None and M["cost"].get(y) is not None) else None)
             for y in years]
    ebitda = [(M["operatingIncome"].get(y) + M["da"].get(y))
              if (M["operatingIncome"].get(y) is not None and M["da"].get(y) is not None) else None
              for y in years]
    ocf = arr(M["ocf"])
    capex = arr(M["capex"])
    fcf = [(ocf[i] - capex[i]) if (ocf[i] is not None and capex[i] is not None) else ocf[i]
           for i in range(len(years))]
    y0 = years[0]
    ltd0, std0 = M["ltd"].get(y0), M["std"].get(y0)
    debt0 = ((ltd0 or 0) + (std0 or 0)) if (ltd0 is not None or std0 is not None) else None

    return {
        "fiscalYears": years,
        "revenue": arr(M["revenue"]), "grossProfit": gross,
        "operatingIncome": arr(M["operatingIncome"]), "netIncome": arr(M["netIncome"]),
        "ebitda": ebitda, "shares": arr(M["shares"]),
        "operatingCashFlow": ocf, "freeCashFlow": fcf,
        "totalDebt": debt0, "cash": M["cash"].get(y0), "equity": M["equity"].get(y0),
        "currentAssets": M["currentAssets"].get(y0), "currentLiabilities": M["currentLiabilities"].get(y0),
    }


# ----------------------------------------------------------------------------
# Network (runs on a machine with internet; uses SEC UA, no key)
# ----------------------------------------------------------------------------
_TICKER_MAP = None


def _get(url, _retries=2):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    last = None
    for attempt in range(_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                enc = (r.headers.get("Content-Encoding") or "").lower()
                if enc == "gzip" or raw[:2] == b"\x1f\x8b":   # gzip magic, even if header absent
                    import gzip
                    raw = gzip.decompress(raw)
                elif enc == "deflate":
                    import zlib
                    raw = zlib.decompress(raw)
                return json.loads(raw)
        except Exception as e:                                # transient SEC hiccup -> brief backoff + retry
            last = e
            if attempt < _retries:
                time.sleep(1.5 * (attempt + 1))
    raise last


def ticker_to_cik(ticker):
    global _TICKER_MAP
    if _TICKER_MAP is None:
        j = _get("https://www.sec.gov/files/company_tickers.json")
        _TICKER_MAP = {str(o["ticker"]).upper(): str(o["cik_str"]).zfill(10) for o in j.values()}
        time.sleep(0.2)
    return _TICKER_MAP.get(ticker.upper())


_FACTS = {}  # cik -> us-gaap facts dict (download companyfacts once per ticker)


def _get_usgaap(cik):
    if cik not in _FACTS:
        facts = _get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        time.sleep(0.15)  # be polite: <10 req/s
        _FACTS[cik] = (facts.get("facts") or {}).get("us-gaap") or {}
    return _FACTS[cik]


def grade_asof(ticker, asof, profile=None):
    cik = ticker_to_cik(ticker)
    if not cik:
        return {"symbol": ticker, "error": "no CIK (foreign/OTC or non-filer)"}
    usgaap = _get_usgaap(cik)
    stmts = build_asof_statements(usgaap, asof)
    if not stmts:
        return {"symbol": ticker, "error": f"no annual revenue filed on/before {asof}"}
    f = assemble_fundamentals(ticker, stmts, profile or {})
    g = compute_quality(f)
    g["asof"] = str(asof)
    g["fiscalYears"] = stmts["fiscalYears"]
    return g


# ----------------------------------------------------------------------------
# Offline self-test of the point-in-time core (no network) — real JAGX data
# ----------------------------------------------------------------------------
JAGX_REVENUE_FIXTURE = [
    # (subset of CIK0001585608 us-gaap:Revenues units.USD, captured 2026-06-16)
    {"end": "2020-12-31", "val": 9385000, "fy": 2020, "fp": "FY", "form": "10-K", "filed": "2021-03-31"},
    {"end": "2021-12-31", "val": 4335000, "fy": 2022, "fp": "FY", "form": "10-K", "filed": "2023-03-24"},
    {"end": "2022-12-31", "val": 11956000, "fy": 2022, "fp": "FY", "form": "10-K", "filed": "2023-03-24"},
    {"end": "2023-12-31", "val": 9761000, "fy": 2024, "fp": "FY", "form": "10-K", "filed": "2025-03-31"},
    {"end": "2024-12-31", "val": 11689000, "fy": 2024, "fp": "FY", "form": "10-K", "filed": "2025-03-31"},
    {"end": "2024-12-31", "val": 11689000, "fy": 2025, "fp": "FY", "form": "10-K", "filed": "2026-04-07"},
    {"end": "2025-12-31", "val": 11511000, "fy": 2025, "fp": "FY", "form": "10-K", "filed": "2026-04-07"},
    # noise that MUST be excluded: quarterlies
    {"end": "2025-03-31", "val": 2214000, "fy": 2025, "fp": "Q1", "form": "10-Q", "filed": "2025-05-15"},
    {"end": "2026-03-31", "val": 20272000, "fy": 2026, "fp": "Q1", "form": "10-Q", "filed": "2026-05-20"},
]


def _selftest():
    # Keying mirrors api/edgar.js fyMap (by the filing's fiscal-year field, latest
    # period-end wins), so the as-of grade matches what the SITE would have shown.
    # That keying collapses comparative years, so JAGX yields the primary period of
    # each distinct 10-K (2020, 2022, 2024, ...) — by design, matching production.

    # As-of 2025-08-01: latest 10-K is the 2025-03-31 filing. The 2026-04-07 10-K
    # (which first reports FY2025) is in the FUTURE and must be invisible.
    m1 = fy_map_asof(JAGX_REVENUE_FIXTURE, "2025-08-01")
    assert m1.get(2024) == 11689000, m1
    assert m1.get(2022) == 11956000, m1
    assert m1.get(2020) == 9385000, m1
    assert 2025 not in m1, f"FY2025 (first filed 2026) leaked into the 2025-08-01 view: {m1}"
    top_1 = [m1[y] for y in sorted(m1, reverse=True)]
    assert top_1 == [11689000, 11956000, 9385000], top_1

    # As-of 2026-05-01: the 2026-04-07 10-K is now visible -> FY2025 appears,
    # reproducing exactly the CURRENT live-proxy array for JAGX.
    m2 = fy_map_asof(JAGX_REVENUE_FIXTURE, "2026-05-01")
    assert m2.get(2025) == 11511000, m2
    top_2 = [m2[y] for y in sorted(m2, reverse=True)[:4]]
    assert top_2 == [11511000, 11689000, 11956000, 9385000], top_2

    # The two as-of views DIFFER (length + content) -> point-in-time works,
    # and the later one equals the site's current view -> fidelity to production.
    assert top_1 != top_2 and 2025 in m2

    # Quarterlies excluded entirely (only FY 10-K values survive).
    assert all(v in (9385000, 11956000, 11689000, 11511000) for v in m2.values()), m2
    print("selftest PASS — point-in-time fy_map_asof reconstructs distinct as-of views")
    print(f"  as-of 2025-08-01 revenue = {top_1}   (FY2025 not yet filed)")
    print(f"  as-of 2026-05-01 revenue = {top_2}   (FY2025 visible; == live-proxy current view)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--ticker")
    ap.add_argument("--asof")
    ap.add_argument("--backtest")
    ap.add_argument("--out", default=os.path.join(HERE, "backtest_quality_asof.csv"))
    a = ap.parse_args()

    if a.selftest:
        _selftest(); return

    if a.ticker and a.asof:
        prof = {}
        cache = os.path.join(HERE, "fundamentals_cache.json")
        if os.path.exists(cache):
            prof = json.load(open(cache)).get("profile", {}).get(a.ticker.upper(), {})
        print(json.dumps(grade_asof(a.ticker, a.asof, prof), indent=2)); return

    if a.backtest:
        prof_all = {}
        cache = os.path.join(HERE, "fundamentals_cache.json")
        if os.path.exists(cache):
            prof_all = json.load(open(cache)).get("profile", {})
        rows = list(csv.DictReader(open(a.backtest)))
        # one grade per (ticker, pick-date) — caches companyfacts per ticker internally
        gcache = {}
        with open(a.out, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["trading_date", "ticker", "tier", "asof_label", "asof_score", "asof_class", "mae_5d", "win"])
            for r in rows:
                tk, d = r["ticker"], r["trading_date"]
                key = (tk, d)
                if key not in gcache:
                    try:
                        gcache[key] = grade_asof(tk, d, prof_all.get(tk.upper(), {}))
                    except Exception as e:
                        gcache[key] = {"error": str(e)}
                g = gcache[key]
                w.writerow([d, tk, r.get("tier"), g.get("label_name", "Ungraded"),
                            g.get("overall", ""), g.get("classification", ""),
                            r.get("mae_5d"), r.get("win")])
        print(f"wrote {a.out} ({len(gcache)} unique ticker-date grades)")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
