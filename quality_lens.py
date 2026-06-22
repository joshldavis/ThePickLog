"""
quality_lens.py — faithful Python port of the IgnitionScan Quality Lens.

Ports computeQuality() + its helpers (band, cagr, avgDefined) and the
EDGAR/profile -> normalized-fundamentals assembly from index.html
(fetchFundamentals / computeQuality), so the SAME Buffett-style grade
(Green / Yellow / Red / Black + 0-100 score + Investable/Speculative/Too Hard)
can be computed offline and joined onto the backtest.

Source of truth: index.html (functions band, cagr, avgDefined, computeQuality,
and the fetchFundamentals normalization block). Kept deliberately line-for-line
so a diff against the JS is auditable (verifiability standard).
"""

QUALITY_WEIGHTS = {
    "financial": 0.25, "business": 0.20, "management": 0.15,
    "valuation": 0.15, "risk": 0.15, "momentum": 0.05, "governance": 0.05,
}
LABEL_NAME = {"green": "Green", "yellow": "Yellow", "red": "Red", "black": "Black"}


def band(x, pts):
    """Piecewise-linear map; pts ascending by x. Mirrors band() in index.html."""
    if x is None or not _finite(x):
        return None
    if x <= pts[0][0]:
        return pts[0][1]
    for i in range(1, len(pts)):
        if x <= pts[i][0]:
            x0, s0 = pts[i - 1]
            x1, s1 = pts[i]
            return s0 + (s1 - s0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


def cagr(newest, oldest, years):
    if not (_gt0(oldest)) or not (_gt0(newest)) or not (_gt0(years)):
        return None
    return ((newest / oldest) ** (1.0 / years) - 1.0) * 100.0


def avg_defined(a):
    v = [x for x in a if x is not None and _finite(x)]
    return sum(v) / len(v) if v else None


def _finite(x):
    try:
        return x == x and x not in (float("inf"), float("-inf"))
    except TypeError:
        return False


def _gt0(x):
    return x is not None and _finite(x) and x > 0


def js_round(x):
    """JS Math.round: rounds half toward +Infinity (NOT Python banker's rounding).
    Math.round(2.5)=3, Math.round(-0.5)=0. Faithfulness matters at label boundaries."""
    import math
    return math.floor(x + 0.5)


def num(x):
    if x is None or not _finite(x):
        return None
    return float(x)


def assemble_fundamentals(symbol, edgar, profile):
    """Replicates the EDGAR/profile -> f normalization in fetchFundamentals()."""
    s = edgar
    P = profile or {}

    rev = num((s.get("revenue") or [None])[0])
    ni = num((s.get("netIncome") or [None])[0])
    oi = num((s.get("operatingIncome") or [None])[0])
    ebitda = num((s.get("ebitda") or [None])[0])
    gp0 = num((s.get("grossProfit") or [None])[0])
    fcf0 = num((s.get("freeCashFlow") or [None])[0])
    shares0 = num((s.get("shares") or [None])[0])
    equity = num(s.get("equity"))
    total_debt = num(s.get("totalDebt"))
    cash_bal = num(s.get("cash"))
    cA = num(s.get("currentAssets"))
    cL = num(s.get("currentLiabilities"))
    price = num(P.get("price")) or 0
    mcap = num(P.get("marketCap"))
    market_cap = mcap if mcap is not None else (price * shares0 if (price and shares0) else None)
    invested_cap = ((total_debt or 0) + (equity or 0)) if (total_debt is not None or equity is not None) else None

    exch = (P.get("exchange") or "") + " " + (P.get("exchangeFullName") or "")

    f = {
        "symbol": symbol,
        "sector": P.get("sector") or "",
        "industry": P.get("industry") or "",
        "exchange": P.get("exchange") or P.get("exchangeFullName") or "",
        "price": price,
        "marketCap": market_cap,
        "otc": bool(_re_otc(exch)),
        "revenue": [num(x) for x in (s.get("revenue") or [])],
        "grossProfit": [num(x) for x in (s.get("grossProfit") or [])],
        "operatingIncome": [num(x) for x in (s.get("operatingIncome") or [])],
        "netIncome": [num(x) for x in (s.get("netIncome") or [])],
        "shares": [num(x) for x in (s.get("shares") or [])],
        "operatingCashFlow": [num(x) for x in (s.get("operatingCashFlow") or [])],
        "freeCashFlow": [num(x) for x in (s.get("freeCashFlow") or [])],
        "totalDebt": total_debt, "cash": cash_bal, "equity": equity,
        "currentAssets": cA, "currentLiabilities": cL,
        "grossMargin": (gp0 / rev * 100) if (rev and gp0 is not None) else None,
        "operatingMargin": (oi / rev * 100) if (rev and oi is not None) else None,
        "netMargin": (ni / rev * 100) if (rev and ni is not None) else None,
        "roic": (oi * 0.79 / invested_cap * 100) if (_gt0(invested_cap) and oi is not None) else None,
        "roe": (ni / equity * 100) if (_gt0(equity) and ni is not None) else None,
        "debtToEquity": (total_debt / equity) if (_gt0(equity) and total_debt is not None) else None,
        "currentRatio": (cA / cL) if (cA is not None and _gt0(cL)) else None,
        "ps": (market_cap / rev) if (market_cap and _gt0(rev)) else None,
        "pe": (market_cap / ni) if (market_cap and ni) else None,
        "pfcf": (market_cap / fcf0) if (market_cap and _gt0(fcf0)) else (-1 if (fcf0 is not None and fcf0 < 0) else None),
        "evEbitda": ((market_cap + (total_debt or 0) - (cash_bal or 0)) / ebitda) if (market_cap is not None and _gt0(ebitda)) else (-1 if (ebitda is not None and ebitda < 0) else None),
        "insiderOwnership": None, "insiderNet": None, "founderLed": False, "goingConcern": False,
        "rvol": None,
        "dataSource": "edgar",
    }
    return f


def _re_otc(s):
    s = (s or "").lower()
    return ("otc" in s) or ("pink" in s) or ("grey" in s)


def compute_quality(f):
    """Faithful port of computeQuality(f) -> {overall, label, classification, ...}."""
    flags, positives = [], []
    rev = f.get("revenue") or []
    ocf = f.get("operatingCashFlow") or []
    fcf = f.get("freeCashFlow") or []
    shares = f.get("shares") or []
    rev_new = rev[0] if rev else None
    rev_old = rev[-1] if rev else None
    years = max(1, len(rev) - 1)
    rev_cagr = cagr(rev_new, rev_old, years)
    fcf0 = fcf[0] if fcf else None
    gm, om, nm = f.get("grossMargin"), f.get("operatingMargin"), f.get("netMargin")
    fcf_margin = (fcf0 / rev_new * 100) if (fcf0 is not None and _gt0(rev_new)) else None
    de, cr = f.get("debtToEquity"), f.get("currentRatio")
    ocf_neg3 = len(ocf) >= 3 and all(x is not None and x < 0 for x in ocf[:3])

    # 1. Financial Health (25%)
    s_rev = 45 if rev_cagr is None else band(rev_cagr, [[-20, 0], [0, 40], [10, 72], [20, 90], [35, 100]])
    if rev_cagr is not None and rev_cagr < -5:
        flags.append({"sev": "yellow", "t": "Declining revenue"})
    if fcf0 is None:
        s_fcf = 45
    else:
        s_fcf = band(fcf_margin, [[-15, 0], [0, 50], [5, 75], [15, 95], [25, 100]])
        if fcf0 <= 0:
            flags.append({"sev": "yellow", "t": "Negative FCF"})
    # Fidelity: when fcf0 present but revenue<=0, JS fcfMargin=null -> band=null and
    # null*0.25 contributes 0 to the sum. Replicate that (Python would otherwise crash).
    if s_fcf is None:
        s_fcf = 0.0
    if ocf_neg3:
        flags.append({"sev": "red", "t": "Cash burn"})
    s_mar = avg_defined([
        band(gm, [[0, 10], [20, 45], [40, 75], [60, 95], [80, 100]]),
        band(om, [[-20, 0], [0, 45], [10, 75], [25, 100]]),
        band(nm, [[-20, 0], [0, 45], [8, 72], [20, 100]]),
    ])
    if s_mar is None:
        s_mar = 45
    if de is None:
        s_debt = 55
    else:
        s_debt = band(de, [[0, 100], [0.3, 92], [1, 62], [2, 28], [2.5, 8], [4, 0]])
        if de > 2.5:
            flags.append({"sev": "red", "t": "High leverage"})
    if cr is None:
        s_liq = 55
    else:
        s_liq = band(cr, [[0.5, 5], [1, 45], [1.5, 78], [2, 95], [3, 100]])
        if cr < 1:
            flags.append({"sev": "yellow", "t": "Weak liquidity"})
    financial = s_rev * .20 + s_fcf * .25 + s_mar * .20 + s_debt * .20 + s_liq * .15

    # 2. Business Quality (20%)
    s_roic = avg_defined([
        band(f.get("roic"), [[-10, 0], [0, 35], [8, 60], [15, 82], [25, 100]]),
        band(f.get("roe"), [[-15, 0], [0, 35], [10, 60], [20, 85], [35, 100]]),
    ])
    if s_roic is None:
        s_roic = 45
    s_mq = band(gm, [[10, 20], [30, 55], [50, 82], [70, 100]])
    if s_mq is None:
        s_mq = 45
    s_cons = 50
    if len(rev) >= 3:
        g = []
        for i in range(len(rev) - 1):
            nxt = rev[i + 1]
            if nxt is not None and nxt > 0:               # JS guard: rev[i+1] > 0
                cur = rev[i] if rev[i] is not None else 0  # JS: a null year coerces to 0 (= -100% growth)
                g.append((cur - nxt) / nxt * 100)
        if g:
            m = avg_defined(g)
            sd = (avg_defined([(x - m) ** 2 for x in g]) or 0) ** 0.5
            all_pos = all(x > 0 for x in g)
            s_cons = max(0, min(100, 60 + (20 if all_pos else -10) - min(sd / 2, 40) + max(-10, min(20, m / 2))))
    s_moat = avg_defined([s_mq, band(f.get("roic"), [[0, 20], [10, 60], [20, 100]])])
    if s_moat is None:
        s_moat = s_mq
    business = s_roic * .30 + s_mq * .25 + s_cons * .25 + s_moat * .20

    # 3. Management / Alignment (15%)
    s_share, dil, reverse_split = 55, None, False
    if len(shares) >= 2 and shares[-1] is not None and shares[-1] > 0 and shares[0] is not None:
        dil = (shares[0] - shares[-1]) / shares[-1] * 100
        if dil <= -40:
            reverse_split = True
            s_share = 42
            flags.append({"sev": "yellow", "t": "Reverse split"})
        else:
            s_share = band(dil, [[-10, 100], [0, 90], [5, 70], [15, 45], [30, 20], [50, 5], [100, 0]])
            if dil > 50:
                flags.append({"sev": "red", "t": "Heavy dilution"})
            elif dil > 15:
                flags.append({"sev": "yellow", "t": "Dilution"})
    s_own = 50 if f.get("insiderOwnership") is None else band(f["insiderOwnership"], [[0, 20], [5, 50], [10, 72], [20, 92], [35, 100]])
    iv_net = f.get("insiderNet")
    s_ins = 50 if iv_net is None else (75 if iv_net > 0 else (35 if iv_net < 0 else 50))
    s_stab = 80 if f.get("founderLed") else 60
    management = s_share * .30 + s_own * .30 + s_ins * .20 + s_stab * .20

    # 4. Valuation (15%)
    vps = None if f.get("ps") is None else band(f["ps"], [[0.5, 100], [1, 92], [3, 60], [6, 30], [10, 5]])
    pfcf = f.get("pfcf")
    vpfcf = None if (pfcf is None or pfcf < 0) else band(pfcf, [[5, 100], [10, 88], [20, 58], [35, 22], [50, 5]])
    eve = f.get("evEbitda")
    vev = None if (eve is None or eve < 0) else band(eve, [[4, 100], [6, 90], [12, 55], [20, 15]])
    pe = f.get("pe")
    vpe = None if pe is None else (15 if pe < 0 else band(pe, [[6, 100], [10, 88], [20, 58], [35, 22], [50, 5]]))
    valuation = avg_defined([vps, vpfcf, vev, vpe])
    if valuation is None:
        valuation = 45
    net_cash = (f["cash"] - f["totalDebt"]) if (f.get("cash") is not None and f.get("totalDebt") is not None) else None
    if net_cash is not None and net_cash > 0:
        valuation = min(100, valuation + 8)
    if pe is not None and pe < 0 and (fcf0 is None or fcf0 < 0):
        flags.append({"sev": "yellow", "t": "No profits to value"})

    # 5. Risk / Red Flags (15%) — starts at 100, penalties reduce
    risk = 100
    if ocf_neg3:
        risk -= 30
    elif fcf0 is not None and fcf0 < 0:
        risk -= 12
    if dil is not None and dil > 50:
        risk -= 25
    elif dil is not None and dil > 15:
        risk -= 10
    if reverse_split:
        risk -= 8
    if de is not None and de > 2.5:
        risk -= 18
    if cr is not None and cr < 1:
        risk -= 8
    if nm is not None and nm < 0:
        risk -= 8
    if f.get("goingConcern"):
        risk -= 40
        flags.append({"sev": "black", "t": "Going concern"})
    if f.get("otc"):
        risk -= 12
        flags.append({"sev": "yellow", "t": "OTC listing"})
    if f.get("marketCap") is not None and f["marketCap"] < 50e6:
        risk -= 6
    risk = max(0, min(100, risk))

    # 6. Momentum / Recognition (5%)
    momentum = 50
    if f.get("rvol") is not None:
        momentum = band(f["rvol"], [[0.5, 30], [1, 50], [3, 70], [6, 78]]) or 50
        if f["rvol"] > 12:
            momentum = 35

    # 7. Governance / Transparency (5%)
    complete = len(rev) >= 2 and f.get("equity") is not None and fcf0 is not None
    governance = 70 if complete else 40
    if not complete:
        flags.append({"sev": "yellow", "t": "Sparse financials"})

    W = QUALITY_WEIGHTS
    overall = js_round(financial * W["financial"] + business * W["business"] + management * W["management"]
                       + valuation * W["valuation"] + risk * W["risk"] + momentum * W["momentum"]
                       + governance * W["governance"])

    has_black = any(x["sev"] == "black" for x in flags)
    if has_black or (ocf_neg3 and dil is not None and dil > 50):
        label = "black"
    elif risk < 45 or overall < 42:
        label = "red"
    elif risk < 68 or overall < 60:
        label = "yellow"
    else:
        label = "green"

    sec = ((f.get("sector") or "") + " " + (f.get("industry") or "")).lower()
    import re
    too_hard_sector = bool(re.search(r"bio|pharma|therapeut|clinical|mining|explorat|gold|silver|metal|drilling", sec))
    pre_rev = rev_new is not None and rev_new < 1e6
    profitable = nm is not None and nm > 0 and fcf0 is not None and fcf0 > 0
    classification = "Too Hard" if (too_hard_sector or pre_rev) else ("Investable" if profitable else "Speculative")

    return {
        "symbol": f.get("symbol"),
        "overall": overall,
        "label": label,
        "label_name": LABEL_NAME[label],
        "classification": classification,
        "risk": js_round(risk),
        "cats": {
            "financial": js_round(financial), "business": js_round(business),
            "management": js_round(management), "valuation": js_round(valuation),
            "risk": js_round(risk), "momentum": js_round(momentum), "governance": js_round(governance),
        },
    }
