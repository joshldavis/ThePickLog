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
from datetime import date

# Reuse the audited free-SEC machinery (UA header, retries, CIK map, point-in-time grade).
from asof_grader import _get, ticker_to_cik, grade_asof

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


# Flat field list for the forward-only sidecar (keyed by pick_id).
SNAPSHOT_FIELDS = [
    "pick_id", "ticker", "trading_date", "captured_at", "cik",
    "dilution_flag", "catalyst_type",
    "recent_dilution_form", "recent_dilution_date", "recent_8k_date",
    "quality_overall", "quality_label", "quality_classification",
    "q_financial", "q_business", "q_management", "q_valuation", "q_risk",
    "q_momentum", "q_governance", "snapshot_note",
]

_BLANK = {k: "" for k in SNAPSHOT_FIELDS}


# ---------------------------------------------------------------------------
# Network (SEC submissions API for filings; companyfacts via grade_asof for quality)
# ---------------------------------------------------------------------------
def recent_filings(cik):
    """Recent filings (form + date) from the SEC submissions API. The 'recent' block
    holds ~1 year / up to 1000 filings — ample for our windows. One request."""
    j = _get(f"https://data.sec.gov/submissions/CIK{cik}.json")
    rec = ((j or {}).get("filings") or {}).get("recent") or {}
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

    # 1) dilution / catalyst from filings
    try:
        cls = classify_filings(recent_filings(cik), asof)
        out.update(cls)
    except Exception as e:
        notes.append(f"filings_err:{type(e).__name__}")

    # 2) quality grade (point-in-time, look-ahead-safe via asof_grader)
    try:
        g = grade_asof(ticker, asof)
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
    print("edgar_lens selftest PASS — dilution/catalyst classification + windows + as-of guard")


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
