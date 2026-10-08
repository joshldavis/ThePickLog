#!/usr/bin/env python3
"""
jev_backfill.py — H-JEV1 (REGISTRATION-H-JEV1.md): read every screened pick's recent SEC
filings through Jev, as of each pick's pre-open moment, then run the registered analysis.

This file and the registration were committed TOGETHER, before the first Jev call on any
pick's filings. The analysis below (analyze()) is the registered analysis; changing it after
that commit is an amendment and must be recorded as one.

STAGES (each idempotent; re-running never re-spends or re-reads)
  select   SEC only, no key. For each pick: CIK -> submissions block -> keep filings ACCEPTED
           BEFORE 09:30 ET on the trading date -> filing_lens.select_filings() (the exact
           production prefilter). Writes jev_backfill/pick_filings.csv.
  read     Jev. Every unique accession in pick_filings.csv not already in events.jsonl is
           fetched once and read once. The logged response is the record: a filing is never
           re-asked, because re-asking drifts (calibration run 2 measured up to 0.10).
  analyze  Pure, offline. Joins picks + outcomes + pick_filings + events and prints the
           registered Part A / Part B result (JSON to jev_backfill/result_<part>.json).

USAGE
  python3 jev_backfill.py --selftest
  python3 jev_backfill.py select --from 2026-06-01 --to 2026-09-30
  JEV_API_KEY=... JEV_MODEL=jev-1.13.0 python3 jev_backfill.py read --max-reads 3000
  python3 jev_backfill.py analyze --part A
NOT INVESTMENT ADVICE. Nothing here changes which tickers are picked.
"""
import argparse
import collections
import csv
import json
import os
import random
import sys
import time
from datetime import date, datetime, timedelta, timezone
from datetime import time as dtime

try:
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
except Exception:                                   # pragma: no cover
    ET = timezone(timedelta(hours=-4))

import filing_lens as fl

__version__ = "1.2.0"

OUT_DIR   = "jev_backfill"
PICKMAP   = os.path.join(OUT_DIR, "pick_filings.csv")
EVENTS    = os.path.join(OUT_DIR, "events.jsonl")
ERRORS    = os.path.join(OUT_DIR, "errors.jsonl")
PICKS     = "picks.csv"
OUTCOMES  = "outcomes.csv"

# ---- registered constants (REGISTRATION-H-JEV1.md) ---------------------------------
PART_A = ("2026-06-01", "2026-09-30")     # retrospective: outcomes already known
PART_B = ("2026-10-01", "2026-12-31")     # forward, confirmatory: one look, on/after 2027-01-11
# Amendment 2 (2026-10-01): H-JEV2 (REGISTRATION-H-JEV2.md) tests the 8-K-only flag forward
# from the day after its registration. H-JEV1 Part B and H-JEV2 form a family of two,
# judged by Holm's step-down: a test passes on its 97.5% CI, or on its 95% CI once the
# other test has passed on its 97.5% CI. Part A stays at 95% as originally reported.
JEV2_WINDOW  = ("2026-10-02", "2026-12-31")
# Amendment 3 (2026-10-08): the registered instrument, enforced on every read and every
# event the analysis uses; and Part B may run only on complete data, exactly once.
REG_MODEL    = "jev-1.13.0"
REG_QSHA     = "394e6c22687a3ce282e839b69041d31418df6135e1e9267c077967db71726c6a"
MAX_UNGRADED = 0.05                        # Part B refuses to run above this share
CI_FAMILY    = 0.975
EFFECT_BAR   = -3.0                        # percentage points of mae_5d
MIN_TICKERS  = 25                          # distinct tickers required in EACH arm
BOOT, SEED   = 2000, 2026
FLAG_ROUTES  = ("auto", "review")
NOT_A_FLAG   = ("split_ratio",)            # the ratio rides with reverse_split
# The 23 tickers whose flagged picks were already seen in the 2026-09-28 replay of
# calibration run 2 against the ledger. Part A is reported with and without them.
SEEN_TICKERS = set("AIXC AMIX ATER BJDX BOXL BRLS DOMO GTBP HCTI IQST IVF MEDS PFSA SKYE "
                   "SRXH SST TNON TOP USDE VIVK XPON YHC ZSTK".split())
PICKMAP_FIELDS = ["pick_id", "ticker", "trading_date", "cik", "status", "accession", "form",
                  "items", "filingDate", "primaryDocument", "reason"]


# =====================================================================================
# SELECT — pure helpers
# =====================================================================================
def preopen_cutoff(trading_date):
    d = date.fromisoformat(trading_date)
    return datetime.combine(d, dtime(9, 30), ET)


def _accepted(s):
    """EDGAR acceptanceDateTime, e.g. '2026-09-18T16:05:12.000Z' -> aware datetime or None."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def preopen_recent(recent, trading_date):
    """Keep only filings knowable before the open: accepted before 09:30 ET on the trading
    date. A filing with no acceptance time is kept only if its filingDate is strictly earlier."""
    cut = preopen_cutoff(trading_date)
    forms = recent.get("form") or []
    n = len(forms)
    keys = ["form", "filingDate", "items", "accessionNumber", "primaryDocument", "acceptanceDateTime"]
    cols = {k: (recent.get(k) or [""] * n) for k in keys}
    out = {k: [] for k in keys}
    for i in range(n):
        acc = _accepted(cols["acceptanceDateTime"][i])
        if acc is not None:
            ok = acc < cut
        else:
            ok = (cols["filingDate"][i] or "9999") < trading_date
        if ok:
            for k in keys:
                out[k].append(cols[k][i])
    return out


def _load_pickmap():
    if not os.path.exists(PICKMAP):
        return []
    return list(csv.DictReader(open(PICKMAP)))


def select(date_from, date_to, cik_of=None, recent_of=None, picks_path=PICKS):
    """SEC only. Idempotent per pick_id."""
    os.makedirs(OUT_DIR, exist_ok=True)
    if cik_of is None:
        from asof_grader import ticker_to_cik as cik_of
    if recent_of is None:
        from edgar_lens import submissions_recent as recent_of
    done = {r["pick_id"] for r in _load_pickmap()}
    picks = [r for r in csv.DictReader(open(picks_path))
             if date_from <= r["trading_date"] <= date_to and r["pick_id"] not in done]
    new_file = not os.path.exists(PICKMAP)
    fh = open(PICKMAP, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=PICKMAP_FIELDS)
    if new_file:
        w.writeheader()
    ciks, recents = {}, {}
    counts = collections.Counter()
    for p in picks:
        t = p["ticker"]
        base = {"pick_id": p["pick_id"], "ticker": t, "trading_date": p["trading_date"]}
        try:
            if t not in ciks:
                ciks[t] = cik_of(t) or ""
            cik = ciks[t]
            if not cik:
                w.writerow({**base, "status": "no_cik"}); counts["no_cik"] += 1; continue
            if cik not in recents:
                recents[cik] = recent_of(cik)
                time.sleep(0.15)                           # SEC fair-use pacing
            sel = fl.select_filings(preopen_recent(recents[cik], p["trading_date"]), p["trading_date"])
        except Exception as e:
            w.writerow({**base, "status": f"sec_err:{type(e).__name__}"}); counts["sec_err"] += 1; continue
        if not sel:
            w.writerow({**base, "cik": cik, "status": "no_filings"}); counts["no_filings"] += 1; continue
        for f in sel:
            w.writerow({**base, "cik": cik, "status": "selected", "accession": f["accession"],
                        "form": f["form"], "items": f["items"], "filingDate": f["filingDate"],
                        "primaryDocument": f["primaryDocument"], "reason": f["reason"]})
        counts["with_filings"] += 1
        fh.flush()
    fh.close()
    rows = _load_pickmap()
    acc = {r["accession"] for r in rows if r["status"] == "selected"}
    return {"picks_new": len(picks), **counts, "unique_accessions_total": len(acc)}


# =====================================================================================
# READ — Jev, once per accession
# =====================================================================================
def _events():
    ev = {}
    if os.path.exists(EVENTS):
        for line in open(EVENTS):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            ev.setdefault(r.get("accession", ""), r)     # first logged response is the record
    return ev


def read(max_reads, call=None, fetch=None):
    call = call or fl.call_jev
    fetch = fetch or fl.fetch_doc
    if call is fl.call_jev and not (fl.JEV_API_KEY and fl.JEV_MODEL):
        raise SystemExit("JEV_API_KEY and JEV_MODEL (pinned) are required for read")
    if call is fl.call_jev and (fl.JEV_MODEL != REG_MODEL or fl.QUESTIONS_SHA256 != REG_QSHA):
        raise SystemExit(f"refusing: instrument is {fl.JEV_MODEL} / questions {fl.QUESTIONS_SHA256[:12]}, "
                         f"registered is {REG_MODEL} / {REG_QSHA[:12]} (set FILING_LENS_QUESTIONS=v2)")
    done = set(_events())
    todo, seen = [], set()
    for r in _load_pickmap():
        a = r["accession"]
        if r["status"] != "selected" or not a or a in done or a in seen:
            continue
        seen.add(a); todo.append(r)
    summary = collections.Counter(todo=len(todo))
    for r in todo[:max_reads]:
        f = {"form": r["form"], "filingDate": r["filingDate"], "items": r["items"],
             "accession": r["accession"], "primaryDocument": r["primaryDocument"], "reason": r["reason"]}
        err = None
        if not f["primaryDocument"]:
            err = "no_primary_doc"
        else:
            try:
                raw = fetch(fl.doc_url(r["cik"], f["accession"], f["primaryDocument"]))
                time.sleep(0.12)
                res = fl.classify_filing(f, raw, call, ticker=r["ticker"], cik=r["cik"])
                rec = res["record"]
                rec["pick_id"] = ""                        # filing-level record, shared by picks
                with open(EVENTS, "a") as fh:
                    fh.write(json.dumps(rec, sort_keys=True) + "\n")
                summary["read"] += 1
            except fl.VersionDrift:
                err = "version_drift"
            except fl.ConfigError as e:
                raise SystemExit(f"config: {e}")
            except Exception as e:
                err = f"{type(e).__name__}: {str(e)[:120]}"
        if err:
            summary["errors"] += 1
            with open(ERRORS, "a") as fh:
                fh.write(json.dumps({"accession": f["accession"], "ticker": r["ticker"], "error": err,
                                     "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}) + "\n")
    summary["remaining"] = max(0, len(todo) - max_reads)
    return dict(summary)


# =====================================================================================
# ANALYZE — the registered analysis. Pure given the four files.
# =====================================================================================
def _f(x):
    """float or None. NaN counts as missing (amendment 1, 2026-09-30: outcomes.csv carries
    literal 'nan' in ret_open_5dclose_net for 42 rows; float('nan') leaked into S4)."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if v != v else v


def pick_flags(pickmap_rows, events):
    """-> {pick_id: {status, flag_any, flag_8k, cats:set, n_sel, n_read}}"""
    out = {}
    for r in pickmap_rows:
        p = out.setdefault(r["pick_id"], {"ticker": r["ticker"], "status": r["status"], "flag_any": False,
                                          "flag_8k": False, "cats": set(), "n_sel": 0, "n_read": 0})
        if r["status"] != "selected":
            p["status"] = r["status"]
            continue
        p["n_sel"] += 1
        ev = events.get(r["accession"])
        if not ev:
            continue
        p["n_read"] += 1
        for q, route in (ev.get("routing") or {}).items():
            if q in NOT_A_FLAG or route not in FLAG_ROUTES:
                continue
            p["flag_any"] = True
            if fl._is_8k(r["form"]):
                p["flag_8k"] = True
            a = (ev.get("answers") or {}).get(q) or {}
            v = a.get("choice") or ("yes" if q == "going_concern" else "?")
            p["cats"].add(f"{q}:{v}")
    for p in out.values():
        if p["status"] == "selected":
            p["status"] = "ok" if p["n_read"] == p["n_sel"] else ("partial" if p["n_read"] else "unread")
    return out


def tercile_cuts(values):
    v = sorted(values)
    if not v:
        return (0.0, 0.0)
    q = lambda f: v[min(len(v) - 1, int(f * len(v)))]
    return (q(1 / 3), q(2 / 3))


def stratified_diff(rows, ykey, flagkey):
    """D = sum_s n_s * (mean_y[flag] - mean_y[not flag]) / sum_s n_s over strata with both arms."""
    by = collections.defaultdict(lambda: ([], []))
    for r in rows:
        y = r.get(ykey)
        if y is None:
            continue
        by[r["stratum"]][0 if r[flagkey] else 1].append(y)
    num = den = 0.0
    for a, b in by.values():
        if a and b:
            n = len(a) + len(b)
            num += n * (sum(a) / len(a) - sum(b) / len(b))
            den += n
    return (num / den) if den else None


def cluster_boot(rows, ykey, flagkey, B=BOOT, seed=SEED, level=0.95):
    by = collections.defaultdict(list)
    for r in rows:
        by[r["ticker"]].append(r)
    ks = sorted(by)
    rng = random.Random(seed)
    est = []
    for _ in range(B):
        samp = [x for k in (rng.choice(ks) for _ in ks) for x in by[k]]
        d = stratified_diff(samp, ykey, flagkey)
        if d is not None:
            est.append(d)
    est.sort()
    if len(est) < B * 0.9:
        return (None, None)
    tail = (1.0 - level) / 2.0
    return (est[int(tail * len(est))], est[int((1.0 - tail) * len(est)) - 1])


def check_instrument(events):
    """Every event must come from the registered model and question block."""
    bad = [a for a, e in events.items()
           if e.get("model") != REG_MODEL or e.get("questions_sha256") != REG_QSHA]
    if bad:
        raise SystemExit(f"refusing: {len(bad)} event(s) not from {REG_MODEL} / {REG_QSHA[:12]}, e.g. {bad[:3]}")


def part_b_blockers(status):
    """-> list of reasons Part B may not run yet (empty = ready)."""
    n = sum(v for k, v in status.items() if k != "ungraded")
    why = []
    for k in ("not_selected_yet", "unread"):
        if status.get(k):
            why.append(f"{status[k]} pick(s) {k}")
    if n and status.get("ungraded", 0) / n > MAX_UNGRADED:
        why.append(f"{status['ungraded']} of {n} picks ungraded (> {MAX_UNGRADED:.0%})")
    if not n:
        why.append("no picks in the window")
    return why


def build_rows(part, picks_path=PICKS, outcomes_path=OUTCOMES, pickmap=None, events=None):
    lo, hi = PART_A if part == "A" else PART_B
    pickmap = _load_pickmap() if pickmap is None else pickmap
    events = _events() if events is None else events
    check_instrument({r["accession"]: events[r["accession"]] for r in pickmap
                      if r.get("status") == "selected" and r["accession"] in events
                      and lo <= r["trading_date"] <= hi})
    flags = pick_flags(pickmap, events)
    outs = {o["pick_id"]: o for o in csv.DictReader(open(outcomes_path))}
    picks = [p for p in csv.DictReader(open(picks_path)) if lo <= p["trading_date"] <= hi]
    status = collections.Counter()
    rows = []
    for p in picks:
        fg = flags.get(p["pick_id"])
        o = outs.get(p["pick_id"])
        st = fg["status"] if fg else "not_selected_yet"
        status[st] += 1
        if not o or _f(o.get("mae_5d")) is None:
            status["ungraded"] += 1
            continue
        if st not in ("ok", "partial", "no_filings"):
            continue                                       # no_cik / sec_err / unread: excluded, counted
        rows.append({"pick_id": p["pick_id"], "ticker": p["ticker"], "cohort": p["model_version"],
                     "trading_date": p["trading_date"],
                     "score": _f(p["score"]) or 0.0, "dilution_flag": p.get("dilution_flag", ""),
                     "status": st, "flag_any": bool(fg and fg["flag_any"]),
                     "flag_8k": bool(fg and fg["flag_8k"]), "cats": sorted(fg["cats"]) if fg else [],
                     "mae": _f(o["mae_5d"]), "r0": _f(o["ret_open_close_net"]),
                     "r5": _f(o["ret_open_5dclose_net"])})
    cuts = {c: tercile_cuts([r["score"] for r in rows if r["cohort"] == c])
            for c in {r["cohort"] for r in rows}}
    for r in rows:
        lo_c, hi_c = cuts[r["cohort"]]
        t = 0 if r["score"] <= lo_c else (1 if r["score"] <= hi_c else 2)
        r["stratum"] = f"{r['cohort']}|T{t}"
    return rows, dict(status), cuts


def contrast(rows, ykey, flagkey, label, level=0.95):
    arm = lambda f: [r for r in rows if r[flagkey] == f and r.get(ykey) is not None]
    a, b = arm(True), arm(False)
    d = stratified_diff(rows, ykey, flagkey)
    lo, hi = cluster_boot(rows, ykey, flagkey, level=level) if d is not None else (None, None)
    mean = lambda xs: round(sum(x[ykey] for x in xs) / len(xs), 3) if xs else None
    return {"label": label, "y": ykey, "flag": flagkey,
            "n_flag": len(a), "n_clean": len(b),
            "tickers_flag": len({r["ticker"] for r in a}), "tickers_clean": len({r["ticker"] for r in b}),
            "mean_flag": mean(a), "mean_clean": mean(b),
            "D_stratified": None if d is None else round(d, 3),
            "ci_level": level,
            "ci95" if level == 0.95 else "ci": [None if lo is None else round(lo, 3),
                                                None if hi is None else round(hi, 3)]}


def verdict(c):
    if c["tickers_flag"] < MIN_TICKERS or c["tickers_clean"] < MIN_TICKERS:
        return "INSUFFICIENT (fewer than %d tickers in an arm)" % MIN_TICKERS
    ci = c.get("ci95") or c.get("ci")
    if c["D_stratified"] is None or ci[1] is None:
        return "INSUFFICIENT (no estimable strata)"
    if c["D_stratified"] <= EFFECT_BAR and ci[1] < 0:
        return "PASS"
    return "FAIL"


def holm(c1, c1_strict, c2, c2_strict):
    """Holm step-down for two tests via CIs -> (verdict1, verdict2)."""
    s1, s2 = verdict(c1_strict) == "PASS", verdict(c2_strict) == "PASS"
    l1, l2 = verdict(c1), verdict(c2)
    def one(strict, loose, other_strict):
        if loose.startswith("INSUFFICIENT"):
            return loose
        if strict:
            return "PASS (97.5% CI, Holm step 1)"
        if other_strict and loose == "PASS":
            return "PASS (95% CI, Holm step 2)"
        return "FAIL (Holm)"
    return one(s1, l1, s2), one(s2, l2, s1)


def analyze(part, **kw):
    rows, status, cuts = build_rows(part, **kw)
    res = {"part": part, "window": PART_A if part == "A" else PART_B,
           "confirmatory": part == "B", "status_counts": status,
           "score_tercile_cuts": {k: [round(x, 3) for x in v] for k, v in cuts.items()},
           "n_rows": len(rows), "n_tickers": len({r["ticker"] for r in rows})}
    prim = contrast(rows, "mae", "flag_any", "PRIMARY: mae_5d, any Jev flag")
    prim["verdict"] = verdict(prim)
    if part == "A":   # amendment 1: never print a bare PASS for the part that cannot pass
        prim["verdict"] = f"RETROSPECTIVE: numeric bar {prim['verdict']}; Part A cannot establish H-JEV1"
    res["primary"] = prim
    sec = []
    dil = [r for r in rows if r["dilution_flag"] in ("offering", "shelf")]
    sec.append(contrast(dil, "mae", "flag_any", "S1: mae_5d within form-code dilution_flag offering/shelf"))
    sec.append(contrast(rows, "mae", "flag_8k", "S2: mae_5d, flag from 8-K text only"))
    sec.append(contrast(rows, "r0", "flag_any", "S3: same-day return (direction; expected null)"))
    sec.append(contrast(rows, "r5", "flag_any", "S4: 5-day return (direction; expected null)"))
    res["secondary"] = sec
    if part == "B":   # H-JEV2 + Holm across the family of two
        r2 = [r for r in rows if JEV2_WINDOW[0] <= r["trading_date"] <= JEV2_WINDOW[1]]
        h2 = contrast(r2, "mae", "flag_8k", "H-JEV2 PRIMARY: mae_5d, flag from 8-K text only")
        h2["window"] = JEV2_WINDOW
        p975 = contrast(rows, "mae", "flag_any", "H-JEV1 at 97.5%", level=CI_FAMILY)
        h975 = contrast(r2, "mae", "flag_8k", "H-JEV2 at 97.5%", level=CI_FAMILY)
        prim["ci975"], h2["ci975"] = p975["ci"], h975["ci"]
        prim["verdict"], h2["verdict"] = holm(prim, p975, h2, h975)
        res["h_jev2"] = h2
    if part == "A":
        unseen = [r for r in rows if r["ticker"] not in SEEN_TICKERS]
        s = contrast(unseen, "mae", "flag_any", "A-sens1: primary excluding the 23 replay-seen tickers")
        s["verdict_if_this_were_B"] = verdict(s)
        res["sensitivity"] = [s,
            contrast([r for r in rows if r["status"] != "partial"], "mae", "flag_any",
                     "A-sens2: primary excluding picks with an unread filing")]
    cats = collections.Counter(c for r in rows for c in r["cats"])
    res["flag_categories_pick_counts"] = dict(cats.most_common())
    res["flag_rate"] = round(sum(r["flag_any"] for r in rows) / len(rows), 3) if rows else None
    return res


# =====================================================================================
# SELFTEST — offline
# =====================================================================================
def _selftest():
    rec = {"form": ["8-K", "8-K", "424B5", "8-K"], "filingDate": ["2026-09-18", "2026-09-18", "2026-09-10", "2026-09-17"],
           "items": ["3.01", "5.03", "", "8.01"], "accessionNumber": ["a1", "a2", "a3", "a4"],
           "primaryDocument": ["x.htm"] * 4,
           "acceptanceDateTime": ["2026-09-18T12:00:00.000Z",   # 08:00 ET -> before open, kept
                                  "2026-09-18T14:00:00.000Z",   # 10:00 ET -> after open, dropped
                                  "2026-09-10T20:00:00.000Z", ""]}
    kept = preopen_recent(rec, "2026-09-18")
    assert kept["accessionNumber"] == ["a1", "a3", "a4"], kept["accessionNumber"]
    sel = fl.select_filings(kept, "2026-09-18")
    assert {s["accession"] for s in sel} == {"a1", "a3", "a4"}, sel
    # flags
    pm = [{"pick_id": "p1", "ticker": "AAA", "status": "selected", "accession": "a1", "form": "8-K"},
          {"pick_id": "p1", "ticker": "AAA", "status": "selected", "accession": "a3", "form": "424B5"},
          {"pick_id": "p2", "ticker": "BBB", "status": "selected", "accession": "a3", "form": "424B5"},
          {"pick_id": "p3", "ticker": "CCC", "status": "no_filings", "accession": "", "form": ""}]
    ev = {"a1": {"routing": {"listing_status": "review", "split_ratio": "review", "dilution_event": "ignore"},
                 "answers": {"listing_status": {"choice": "deficiency_notice"}}},
          "a3": {"routing": {"split_ratio": "review", "dilution_event": "ignore"}, "answers": {}}}
    f = pick_flags(pm, ev)
    assert f["p1"]["flag_any"] and f["p1"]["flag_8k"] and f["p1"]["status"] == "ok"
    assert f["p1"]["cats"] == {"listing_status:deficiency_notice"}
    assert not f["p2"]["flag_any"], "split_ratio alone must never flag"
    assert f["p3"]["status"] == "no_filings" and not f["p3"]["flag_any"]
    # stratified difference: flagged 5 points deeper in every stratum -> D = -5
    rows = []
    for s in ("c|T0", "c|T1"):
        for i in range(10):
            rows.append({"stratum": s, "ticker": f"F{s}{i}", "flag": True, "y": -20.0 - (i % 3)})
            rows.append({"stratum": s, "ticker": f"N{s}{i}", "flag": False, "y": -15.0 - (i % 3)})
    assert abs(stratified_diff(rows, "y", "flag") + 5.0) < 1e-9
    lo, hi = cluster_boot(rows, "y", "flag", B=300)
    assert lo <= -5.0 <= hi and hi < 0, (lo, hi)
    # a stratum with one arm only is dropped, not averaged in
    rows.append({"stratum": "c|T2", "ticker": "Z", "flag": True, "y": 100.0})
    assert abs(stratified_diff(rows, "y", "flag") + 5.0) < 1e-9
    # verdict thresholds
    base = {"tickers_flag": 30, "tickers_clean": 30, "D_stratified": -3.5, "ci95": [-6, -0.5]}
    assert verdict(base) == "PASS"
    assert verdict({**base, "D_stratified": -2.9}) == "FAIL"
    assert verdict({**base, "ci95": [-6, 0.1]}) == "FAIL"
    assert verdict({**base, "tickers_clean": 24}).startswith("INSUFFICIENT")
    assert tercile_cuts([1, 2, 3, 4, 5, 6]) == (3, 5)
    assert part_b_blockers({"ok": 100, "no_filings": 20, "ungraded": 3}) == []
    assert part_b_blockers({"ok": 100, "ungraded": 6})[0].startswith("6 of 100")
    assert part_b_blockers({"ok": 100, "unread": 1}) == ["1 pick(s) unread"]
    assert part_b_blockers({"ok": 100, "not_selected_yet": 4})[0].startswith("4 pick(s)")
    try:
        check_instrument({"x": {"model": "jev-9.9.9", "questions_sha256": REG_QSHA}})
        raise AssertionError("foreign model accepted")
    except SystemExit:
        pass
    check_instrument({"x": {"model": REG_MODEL, "questions_sha256": REG_QSHA}})
    assert verdict({"tickers_flag": 30, "tickers_clean": 30, "D_stratified": -4.0, "ci": [-7, -0.1]}) == "PASS"
    G = lambda hi: {"tickers_flag": 30, "tickers_clean": 30, "D_stratified": -4.0, "ci": [-7, hi]}
    assert holm(G(-0.5), G(0.3), G(-2), G(-1)) == ("PASS (95% CI, Holm step 2)", "PASS (97.5% CI, Holm step 1)")
    assert holm(G(-0.5), G(0.3), G(-0.5), G(0.3)) == ("FAIL (Holm)", "FAIL (Holm)")
    assert holm(G(0.2), G(0.9), G(-2), G(-1))[0] == "FAIL (Holm)"
    lo95, hi95 = cluster_boot(rows, "y", "flag", B=400, seed=3)
    lo975, hi975 = cluster_boot(rows, "y", "flag", B=400, seed=3, level=0.975)
    assert lo975 <= lo95 and hi975 >= hi95, "97.5% interval must be at least as wide"
    assert _f("nan") is None and _f("") is None and _f("-4.5") == -4.5
    print("jev_backfill selftest: OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", nargs="?", choices=["select", "read", "analyze"])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--from", dest="date_from", default=PART_A[0])
    ap.add_argument("--to", dest="date_to", default=PART_A[1])
    ap.add_argument("--max-reads", type=int, default=3000)
    ap.add_argument("--part", choices=["A", "B"], default="A")
    a = ap.parse_args()
    if a.selftest:
        _selftest(); return
    if a.stage == "select":
        print(json.dumps(select(a.date_from, a.date_to), indent=1))
    elif a.stage == "read":
        print(json.dumps(read(a.max_reads), indent=1))
    elif a.stage == "analyze":
        out_path = os.path.join(OUT_DIR, f"result_{a.part}.json")
        if a.part == "B":
            if date.today() < date(2027, 1, 11):
                raise SystemExit("Part B has one registered look, on or after 2027-01-11.")
            if os.path.exists(out_path):
                raise SystemExit(f"Part B already looked: {out_path} exists. One look only; it is never replaced.")
            _, status, _ = build_rows("B")            # counts only; no outcome is summarized
            why = part_b_blockers(status)
            if why:
                raise SystemExit("Part B not ready, nothing analyzed: " + "; ".join(why))
        res = analyze(a.part)
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(out_path, "x" if a.part == "B" else "w") as fh:
            json.dump(res, fh, indent=1)
        print(json.dumps(res, indent=1))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
