#!/usr/bin/env python3
"""
edgar_lens.py — screen-time SEC-EDGAR snapshot for ThePickLog's Group-B variables.

Closes two data gaps the roadmap flagged, using ONLY free SEC EDGAR (no paid feed):

  1. dilution_flag / catalyst_type  → populated into the existing (until-now blank)
     picks.csv columns, going forward, exactly like short_interest_pct did.
  2. Quality-Lens grade at screen time → written to a forward-only sidecar
     (edgar_snapshot.csv, keyed by pick_id), so Finding B (does quality predict
     shallower drawdown?) stays testable OUT-OF-SAMPLE later WITHOUT mutating
     picks.csv's frozen header, and without the look-ahead drift that killed
     back-filling (companyfacts is point-in-time via asof_grader.grade_asof).
  3. insider_net (net open-market insider buy/sell) → parsed from free SEC Form 4
     XML over a trailing window and written to the sidecar. Closes the Quality-Lens
     "insider buy/sell not checked" gap WITHOUT a paid feed (ROADMAP Next #3), and
     feeds the point-in-time grade via the `insiderNet` profile input. Only open-
     market purchases (code P) and sales (code S) are netted — grants, option
     exercises, tax-withholding and gifts (A/M/F/G…) are excluded so the signal
     means "insider chose to buy/sell with their own money," not comp mechanics.
     Insider OWNERSHIP % is deliberately NOT synthesized here: it needs an
     all-insiders aggregate against shares outstanding that Form 4 alone can't give
     truthfully, so it stays honestly "not checked" (see the guardrail below).

Design rules (match the project's discipline):
  • FORWARD-ONLY: past picks stay blank; we never rewrite the immutable log.
  • NON-FATAL: any network/parse failure degrades to blanks — the daily scan must
    never break because SEC was slow. (Same contract as short-interest / paths capture.)
  • VERIFIABLE: the categorical in picks.csv is summarized from filings whose form +
    date are recorded in the sidecar, so a stranger can re-derive the flag from EDGAR.

WHY EDGAR for dilution (and not a fake catalyst feed): a priced offering (424B*) or a
live shelf (S-3*) is an unambiguous public filing — reliable. A *catalyst* in the
news sense (PR / FDA / social) is NOT cleanly in EDGAR, so catalyst_type here is an
honest FILING-derived proxy (offering / 8K / filing / none), not a news classifier.
Per ROADMAP guardrail "don't half-build a lever off an unreliable source," we capture
only what EDGAR can support truthfully and label it as such.

USAGE:
  python3 edgar_lens.py --selftest         # offline logic test (no network)
  python3 edgar_lens.py --ticker JAGX      # live snapshot for one ticker
NOT INVESTMENT ADVICE.
"""
import argparse
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

# Reuse the audited free-SEC machinery (UA header, retries, CIK map, point-in-time grade).
from asof_grader import _get, ticker_to_cik, grade_asof, UA

# ---------------------------------------------------------------------------
# Form taxonomy + windows (the only tunables; kept explicit for auditability)
# ---------------------------------------------------------------------------
def _is_offering(form):          # priced offering / prospectus supplement
    return form.startswith("424B") or form in ("FWP",)
def _is_shelf(form):             # registration that ENABLES future dilution
    return form.startswith(("S-3", "S-1", "F-3", "F-1"))
def _is_8k(form):
    return form.startswith("8-K")

OFFERING_WINDOW = 180   # an offering this recent = active dilution pressure
SHELF_WINDOW    = 365   # a shelf within a year = latent dilution capacity
CATALYST_WINDOW = 7     # what plausibly moved the stock THIS week


def _d(s):
    if isinstance(s, date):
        return s
    return date(int(s[0:4]), int(s[5:7]), int(s[8:10]))


# ---------------------------------------------------------------------------
# PURE CORE (offline-testable): filings list -> categorical flags + evidence
# filings: list of {"form": str, "filingDate": "YYYY-MM-DD"}
# ---------------------------------------------------------------------------
def classify_filings(filings, asof):
    asof = _d(asof)
    offerings, shelves, eightks = [], [], []
    for r in filings or []:
        form = (r.get("form") or "").strip()
        fds = (r.get("filingDate") or "").strip()
        if not form or len(fds) < 10:
            continue
        try:
            fd = _d(fds)
        except Exception:
            continue
        age = (asof - fd).days
        if age < 0:
            continue  # filed after the screen date — not knowable at screen time
        if _is_offering(form):
            offerings.append((fd, form))
        if _is_shelf(form):
            shelves.append((fd, form))
        if _is_8k(form):
            eightks.append((fd, form))

    def within(items, days):
        return [it for it in items if (asof - it[0]).days <= days]

    off_recent = within(offerings, OFFERING_WINDOW)
    shelf_recent = within(shelves, SHELF_WINDOW)

    # dilution_flag: active offering > latent shelf > none
    if off_recent:
        dilution_flag = "offering"
    elif shelf_recent:
        dilution_flag = "shelf"
    else:
        dilution_flag = "none"

    # catalyst_type: what filed this week (honest filing proxy, NOT a news classifier)
    if within(offerings, CATALYST_WINDOW):
        catalyst_type = "offering"
    elif within(eightks, CATALYST_WINDOW):
        catalyst_type = "8K"
    elif any((asof - _d(r["filingDate"])).days <= CATALYST_WINDOW
             for r in filings or []
             if (r.get("filingDate") or "")[:10].count("-") == 2 and len(r.get("filingDate") or "") >= 10
             and (asof - _d(r["filingDate"])).days >= 0):
        catalyst_type = "filing"
    else:
        catalyst_type = "none"

    dil = sorted(offerings + shelves, reverse=True)  # most-recent dilution-relevant filing
    recent_dilution_form = dil[0][1] if dil else ""
    recent_dilution_date = dil[0][0].isoformat() if dil else ""
    recent_8k_date = max(eightks)[0].isoformat() if eightks else ""

    return {
        "dilution_flag": dilution_flag,
        "catalyst_type": catalyst_type,
        "recent_dilution_form": recent_dilution_form,
        "recent_dilution_date": recent_dilution_date,
        "recent_8k_date": recent_8k_date,
    }


# ---------------------------------------------------------------------------
# INSIDER (Form 4) — PURE CORE (offline-testable)
# Net open-market insider buy/sell over a trailing window, from Form 4 XML.
# ---------------------------------------------------------------------------
INSIDER_WINDOW = 90       # trailing days of Form 4 activity to net (recent conviction)
FORM4_CAP      = 12       # at most this many recent Form 4 docs fetched per ticker (politeness)

# Only DISCRETIONARY open-market trades carry signal. transactionCode:
#   P = open-market/private purchase (own money in)   -> +1
#   S = open-market/private sale     (own money out)  -> -1
# Excluded on purpose: A (grant/award), M (option exercise), F (tax withhold),
#   G (gift), C/X/etc. — comp mechanics, not a discretionary bet.
_OPEN = {"P": 1, "S": -1}


def _is_form4(form):
    return form in ("4", "4/A")


def _xt(node, path):
    """Text at a child path (namespace-free ownership docs). '' if absent."""
    el = node.find(path)
    return (el.text or "").strip() if (el is not None and el.text is not None) else ""


def parse_form4_xml(xml_text):
    """Form 4 XML instance -> list of non-derivative transactions.
    [{"code","ad","shares","price","date"}]. NON-FATAL: [] on any parse problem.
    (SEC ownership documents are namespace-free, so plain child paths resolve.)"""
    out = []
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return out
    for tx in root.iter("nonDerivativeTransaction"):
        out.append({
            "code":   _xt(tx, "transactionCoding/transactionCode"),
            "ad":     _xt(tx, "transactionAmounts/transactionAcquiredDisposedCode/value"),
            "shares": _xt(tx, "transactionAmounts/transactionShares/value"),
            "price":  _xt(tx, "transactionAmounts/transactionPricePerShare/value"),
            "date":   _xt(tx, "transactionDate/value"),
        })
    return out


def net_insider(transactions, asof, window=INSIDER_WINDOW):
    """Net open-market insider buy/sell over `window` days ending `asof`.
    as-of-safe (drops future-dated txns). Returns categorical + evidence.
      insider_net: 1 net buying / -1 net selling / 0 neutral / "" no activity."""
    asof = _d(asof)
    buy_val = sell_val = 0.0
    buy_sh = sell_sh = 0.0
    n_buy = n_sell = 0
    last_dt = ""
    for t in transactions or []:
        ds = (t.get("date") or "").strip()
        if len(ds) < 10:
            continue
        try:
            td = _d(ds)
        except Exception:
            continue
        age = (asof - td).days
        if age < 0 or age > window:        # future = not knowable at screen time; too old = out of window
            continue
        sgn = _OPEN.get((t.get("code") or "").strip().upper())
        if sgn is None:                    # not a discretionary open-market trade
            continue
        try:
            sh = float(t.get("shares") or 0)
        except Exception:
            sh = 0.0
        try:
            pr = float(t.get("price") or 0)
        except Exception:
            pr = 0.0
        val = sh * pr
        if sgn > 0:
            buy_val += val; buy_sh += sh; n_buy += 1
        else:
            sell_val += val; sell_sh += sh; n_sell += 1
        if ds > last_dt:
            last_dt = ds
    net_val = buy_val - sell_val
    if n_buy == 0 and n_sell == 0:
        insider_net = ""                   # honestly unknown — no open-market activity in window
        net_out = ""
    else:
        insider_net = 1 if net_val > 0 else (-1 if net_val < 0 else 0)
        net_out = round(net_val, 2)
    return {
        "insider_net": insider_net,
        "insider_net_val": net_out,
        "insider_buy_val": round(buy_val, 2) if n_buy else "",
        "insider_sell_val": round(sell_val, 2) if n_sell else "",
        "insider_buy_ct": n_buy,
        "insider_sell_ct": n_sell,
        "insider_window_days": window,
        "recent_form4_date": last_dt,
    }


# ---------------------------------------------------------------------------
# INSIDER — network layer (fetch + parse Form 4 XML docs)
# ---------------------------------------------------------------------------
def _get_text(url, _retries=2):
    """Raw-text GET with SEC UA + gzip/deflate handling (asof_grader._get is JSON-only)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    last = None
    for attempt in range(_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                enc = (r.headers.get("Content-Encoding") or "").lower()
                if enc == "gzip" or raw[:2] == b"\x1f\x8b":
                    import gzip
                    raw = gzip.decompress(raw)
                elif enc == "deflate":
                    import zlib
                    raw = zlib.decompress(raw)
                return raw.decode("utf-8", "replace")
        except Exception as e:
            last = e
            if attempt < _retries:
                time.sleep(1.5 * (attempt + 1))
    raise last


def form4_urls_from_block(recent, cik, asof, window=INSIDER_WINDOW, cap=FORM4_CAP):
    """From the SEC submissions 'recent' block, the raw XML URLs of Form 4 docs
    filed within `window` days on/before `asof`, most-recent first, capped."""
    forms = recent.get("form") or []
    dates = recent.get("filingDate") or []
    accs  = recent.get("accessionNumber") or []
    docs  = recent.get("primaryDocument") or []
    asofd = _d(asof)
    cik_int = str(int(cik))
    out = []
    for i, frm in enumerate(forms):
        if not _is_form4((frm or "").strip()):
            continue
        ds = dates[i] if i < len(dates) else ""
        if len(ds) < 10:
            continue
        try:
            fd = _d(ds)
        except Exception:
            continue
        age = (asofd - fd).days
        if age < 0 or age > window:
            continue
        acc = (accs[i] if i < len(accs) else "").strip()
        doc = (docs[i] if i < len(docs) else "").strip()
        # primaryDocument is often the XSL-RENDERED path (e.g. "xslF345X06/form4.xml"), which
        # serves HTML — not parseable. The raw XML instance is the same basename at the accession
        # root ("form4.xml"). Take the basename to hit the machine-readable instance.
        doc_base = doc.split("/")[-1]
        if not acc or not doc_base.lower().endswith(".xml"):
            continue
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc.replace('-', '')}/{doc_base}"
        out.append((ds, url))
    out.sort(reverse=True)
    return out[:cap]


def insider_from_block(recent, cik, asof, window=INSIDER_WINDOW, cap=FORM4_CAP):
    """Fetch + parse recent Form 4 XML, return net_insider(...) enriched with a
    form4_seen count. NON-FATAL per filing: a bad doc is skipped, not raised."""
    urls = form4_urls_from_block(recent, cik, asof, window, cap)
    txns = []
    seen = 0
    for _ds, url in urls:
        try:
            txns.extend(parse_form4_xml(_get_text(url)))
            seen += 1
            time.sleep(0.12)  # be polite: <10 req/s
        except Exception:
            continue
    res = net_insider(txns, asof, window)
    res["insider_form4_seen"] = seen
    return res


# Flat field list for the forward-only sidecar (keyed by pick_id).
SNAPSHOT_FIELDS = [
    "pick_id", "ticker", "trading_date", "captured_at", "cik",
    "dilution_flag", "catalyst_type",
    "recent_dilution_form", "recent_dilution_date", "recent_8k_date",
    "insider_net", "insider_net_val", "insider_buy_val", "insider_sell_val",
    "insider_buy_ct", "insider_sell_ct", "insider_window_days",
    "recent_form4_date", "insider_form4_seen",
    "quality_overall", "quality_label", "quality_classification",
    "q_financial", "q_business", "q_management", "q_valuation", "q_risk",
    "q_momentum", "q_governance", "snapshot_note",
]

_BLANK = {k: "" for k in SNAPSHOT_FIELDS}


# ---------------------------------------------------------------------------
# Network (SEC submissions API for filings; companyfacts via grade_asof for quality)
# ---------------------------------------------------------------------------
def submissions_recent(cik):
    """The SEC submissions 'recent' block (~1 year / up to 1000 filings — ample for
    our windows). ONE request, shared by dilution/catalyst AND insider capture."""
    j = _get(f"https://data.sec.gov/submissions/CIK{cik}.json")
    return ((j or {}).get("filings") or {}).get("recent") or {}


def recent_filings(cik):
    """Back-compat shim: recent filings as [{form, filingDate}] for classify_filings."""
    rec = submissions_recent(cik)
    forms = rec.get("form") or []
    dates = rec.get("filingDate") or []
    return [{"form": f, "filingDate": d} for f, d in zip(forms, dates)]


def snapshot(ticker, asof):
    """Full screen-time EDGAR snapshot for one ticker. Fully NON-FATAL: every failure
    path returns blanks (current behaviour) with a note, never raises to the caller."""
    out = dict(_BLANK)
    out["ticker"] = ticker
    notes = []
    try:
        cik = ticker_to_cik(ticker)
    except Exception as e:
        out["snapshot_note"] = f"cikmap_err:{type(e).__name__}"
        return out
    if not cik:
        out["snapshot_note"] = "no_cik"   # OTC / foreign / non-filer — honestly unknown
        return out
    out["cik"] = cik

    # 0) one submissions request, shared by dilution AND insider capture
    recent = None
    try:
        recent = submissions_recent(cik)
    except Exception as e:
        notes.append(f"submissions_err:{type(e).__name__}")

    # 1) dilution / catalyst from filings
    if recent is not None:
        try:
            filings = [{"form": f, "filingDate": d}
                       for f, d in zip(recent.get("form") or [], recent.get("filingDate") or [])]
            out.update(classify_filings(filings, asof))
        except Exception as e:
            notes.append(f"filings_err:{type(e).__name__}")

    # 1b) insider net (open-market buy/sell) from Form 4 XML — feeds the grade below
    insider_net_for_grade = None
    if recent is not None:
        try:
            ins = insider_from_block(recent, cik, asof)
            out.update(ins)
            if ins.get("insider_net") != "":
                insider_net_for_grade = ins.get("insider_net")
        except Exception as e:
            notes.append(f"insider_err:{type(e).__name__}")

    # 2) quality grade (point-in-time, look-ahead-safe via asof_grader), now fed the
    #    Form-4-derived insider signal so the "insider buy/sell" input is no longer blank.
    try:
        prof = {"insiderNet": insider_net_for_grade} if insider_net_for_grade is not None else None
        g = grade_asof(ticker, asof, prof)
        if g.get("error"):
            notes.append("quality:" + g["error"][:40])
        else:
            cats = g.get("cats", {})
            out.update({
                "quality_overall": g.get("overall", ""),
                "quality_label": g.get("label_name", ""),
                "quality_classification": g.get("classification", ""),
                "q_financial": cats.get("financial", ""), "q_business": cats.get("business", ""),
                "q_management": cats.get("management", ""), "q_valuation": cats.get("valuation", ""),
                "q_risk": cats.get("risk", ""), "q_momentum": cats.get("momentum", ""),
                "q_governance": cats.get("governance", ""),
            })
    except Exception as e:
        notes.append(f"quality_err:{type(e).__name__}")

    out["snapshot_note"] = ";".join(notes)
    return out


# ---------------------------------------------------------------------------
def _selftest():
    asof = "2026-06-24"
    # A: recent priced offering + an old shelf + an 8-K two days ago.
    A = [{"form": "424B5", "filingDate": "2026-06-10"},
         {"form": "S-3",   "filingDate": "2025-09-01"},
         {"form": "8-K",   "filingDate": "2026-06-22"},
         {"form": "10-Q",  "filingDate": "2026-05-15"}]
    a = classify_filings(A, asof)
    assert a["dilution_flag"] == "offering", a
    assert a["catalyst_type"] == "8K", a          # no offering in last 7d, but an 8-K is
    assert a["recent_dilution_form"] == "424B5" and a["recent_dilution_date"] == "2026-06-10", a
    assert a["recent_8k_date"] == "2026-06-22", a

    # B: only a year-old shelf, nothing recent → latent capacity, no fresh catalyst.
    B = [{"form": "S-3", "filingDate": "2025-12-01"}]
    b = classify_filings(B, asof)
    assert b["dilution_flag"] == "shelf" and b["catalyst_type"] == "none", b

    # C: offering filed 3 days ago → both dilution AND catalyst = offering.
    C = [{"form": "424B5", "filingDate": "2026-06-22"}]
    c = classify_filings(C, asof)
    assert c["dilution_flag"] == "offering" and c["catalyst_type"] == "offering", c

    # D: clean — no dilution filings, just a recent non-8K filing → catalyst "filing".
    D = [{"form": "SC 13G", "filingDate": "2026-06-23"}]
    d = classify_filings(D, asof)
    assert d["dilution_flag"] == "none" and d["catalyst_type"] == "filing", d

    # E: nothing at all → none/none, no evidence.
    e = classify_filings([], asof)
    assert e["dilution_flag"] == "none" and e["catalyst_type"] == "none" and e["recent_dilution_form"] == "", e

    # F: a future-dated filing must be ignored (not knowable at screen time).
    F = [{"form": "424B5", "filingDate": "2026-07-01"}]
    f = classify_filings(F, asof)
    assert f["dilution_flag"] == "none", f

    # G: shelf forms variants all detected.
    for frm in ("S-3", "S-3/A", "S-3ASR", "S-1", "F-3"):
        assert _is_shelf(frm), frm
    assert _is_offering("424B3") and _is_offering("FWP") and not _is_offering("8-K")

    # -------- INSIDER (Form 4) core --------
    iasof = "2026-06-24"
    # H: net BUYING — two open-market purchases, one small sale, all in window.
    tx = [
        {"code": "P", "ad": "A", "shares": "10000", "price": "2.00", "date": "2026-06-10"},
        {"code": "P", "ad": "A", "shares": "5000",  "price": "2.10", "date": "2026-06-18"},
        {"code": "S", "ad": "D", "shares": "1000",  "price": "2.50", "date": "2026-06-20"},
    ]
    h = net_insider(tx, iasof)
    assert h["insider_net"] == 1, h                       # 20k+10.5k bought vs 2.5k sold => net buy
    assert h["insider_buy_ct"] == 2 and h["insider_sell_ct"] == 1, h
    assert h["insider_net_val"] == round(20000 + 10500 - 2500, 2), h
    assert h["recent_form4_date"] == "2026-06-20", h

    # I: comp mechanics excluded — a big grant (A) + option exercise (M) are NOT buys.
    j2 = net_insider([
        {"code": "A", "ad": "A", "shares": "100000", "price": "0",   "date": "2026-06-15"},
        {"code": "M", "ad": "A", "shares": "50000",  "price": "1.0", "date": "2026-06-16"},
        {"code": "S", "ad": "D", "shares": "8000",   "price": "3.0", "date": "2026-06-17"},
    ], iasof)
    assert j2["insider_net"] == -1 and j2["insider_buy_ct"] == 0 and j2["insider_sell_ct"] == 1, j2

    # J: window + as-of guard — a purchase 200d old and one dated in the future are ignored.
    k = net_insider([
        {"code": "P", "ad": "A", "shares": "9999", "price": "5", "date": "2025-12-01"},  # too old
        {"code": "P", "ad": "A", "shares": "9999", "price": "5", "date": "2026-07-01"},  # future
    ], iasof)
    assert k["insider_net"] == "" and k["insider_buy_ct"] == 0, k    # nothing in window => unknown

    # K: no Form 4 activity at all => honestly blank, not a fabricated 0.
    assert net_insider([], iasof)["insider_net"] == "", "empty must be blank"

    # L: XML parse — a minimal namespace-free Form 4 instance yields its transaction.
    xml = ("<ownershipDocument><nonDerivativeTable><nonDerivativeTransaction>"
           "<transactionDate><value>2026-06-19</value></transactionDate>"
           "<transactionCoding><transactionCode>P</transactionCode></transactionCoding>"
           "<transactionAmounts>"
           "<transactionShares><value>2500</value></transactionShares>"
           "<transactionPricePerShare><value>1.80</value></transactionPricePerShare>"
           "<transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>"
           "</transactionAmounts></nonDerivativeTransaction></nonDerivativeTable></ownershipDocument>")
    parsed = parse_form4_xml(xml)
    assert len(parsed) == 1 and parsed[0]["code"] == "P" and parsed[0]["shares"] == "2500", parsed
    assert net_insider(parsed, iasof)["insider_net"] == 1, parsed
    assert parse_form4_xml("<not xml") == [], "malformed XML must be non-fatal"

    # M: URL builder — Form 4 within window becomes a raw XML URL; strips CIK zero-pad + dashes.
    block = {
        "form": ["4", "10-Q", "4"],
        "filingDate": ["2026-06-20", "2026-05-15", "2025-01-01"],
        "accessionNumber": ["0001209191-26-000123", "x", "0001209191-25-000001"],
        # first doc is given as the XSL-rendered path — must resolve to the raw XML basename.
        "primaryDocument": ["xslF345X06/form4.xml", "y.htm", "wk-form4_old.xml"],
    }
    urls = form4_urls_from_block(block, "0000320193", iasof)
    assert len(urls) == 1, urls                          # only the in-window Form 4
    assert urls[0][1] == ("https://www.sec.gov/Archives/edgar/data/320193/"
                          "000120919126000123/form4.xml"), urls   # xsl prefix stripped

    print("edgar_lens selftest PASS — dilution/catalyst + Form-4 insider net + windows + as-of guard")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--ticker")
    ap.add_argument("--asof", default=date.today().isoformat())
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if a.ticker:
        import json
        print(json.dumps(snapshot(a.ticker, a.asof), indent=2))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
