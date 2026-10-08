#!/usr/bin/env python3
"""Reproducibility check for the split-v2 test (REGISTRATION-split-v2.md, secondary outcome):
30 sample filings (random.Random(2028)) re-asked once; count changed answers.

Runs from anywhere. Paths are relative to this file (calibration_v2/):
  responses/<cal_id>.json        first answers (the record)
  repro_responses/<cal_id>.json  the registered re-asks (committed)
With both committed, this re-scores OFFLINE with no key. A missing re-ask is fetched from
EDGAR (doc_url), stripped and capped exactly as Jev saw it, checked against the committed
text_sha256, and only then sent to Jev (needs JEV_API_KEY, JEV_MODEL=jev-1.13.0).

  FILING_LENS_QUESTIONS=v2 python3 calibration_v2/repro.py
"""
import csv, json, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ.setdefault("FILING_LENS_QUESTIONS", "v2")
import filing_lens as fl

MODEL = "jev-1.13.0"
C = sorted(csv.DictReader(open(os.path.join(HERE, "candidates.csv"))), key=lambda r: r["cal_id"])
pick = sorted(random.Random(2028).sample([r["cal_id"] for r in C], 30))
RESP, REPRO = os.path.join(HERE, "responses"), os.path.join(HERE, "repro_responses")
os.makedirs(REPRO, exist_ok=True)


def reask(r):
    p = os.path.join(REPRO, r["cal_id"] + ".json")
    if os.path.exists(p):
        return json.load(open(p))
    raw = fl.fetch_doc(r["doc_url"])
    text, _ = fl.cap_text(fl.strip_html(raw))
    if fl._sha(text) != r["text_sha256"]:
        raise SystemExit(f"{r['cal_id']}: fetched text does not match the registered sha256; not re-asking")
    f = {"form": r["form"], "items": r["items"], "filingDate": r["filing_date"],
         "accession": r["accession"], "primaryDocument": ""}
    resp = fl.call_jev(fl.build_request(f, text, MODEL))
    json.dump(resp, open(p, "w")); time.sleep(0.1)
    return resp


out = []
for r in C:
    if r["cal_id"] not in pick:
        continue
    a = fl.parse_answers(json.load(open(os.path.join(RESP, r["cal_id"] + ".json"))), expected_model=MODEL)
    b = fl.parse_answers(reask(r), expected_model=MODEL)
    out.append({"cal_id": r["cal_id"], **{f"{q}_changed": int(a[q]["value"] != b[q]["value"]) for q in fl.QUESTION_ORDER},
                "rs_first": a["reverse_split"]["value"], "rs_p1": a["reverse_split"]["p"], "rs_p2": b["reverse_split"]["p"],
                "max_dp": round(max(abs(float(a[q]["p"] or 0) - float(b[q]["p"] or 0)) for q in fl.QUESTION_ORDER), 3)})
summary = {"seed": 2028, "n": len(out), "reverse_split_changed": sum(o["reverse_split_changed"] for o in out),
           "any_changed": sum(sum(v for k, v in o.items() if k.endswith("_changed")) for o in out),
           "max_dp": max(o["max_dp"] for o in out)}
print(json.dumps(summary))
