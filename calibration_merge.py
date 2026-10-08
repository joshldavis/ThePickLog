#!/usr/bin/env python3
"""
calibration_merge.py — combine structured truth + model-reader labels into the
calibration labels file, and draw the human audit sample.

LABEL PRECEDENCE (published with the result)
  1. truth (high)   — market/item-code truth from calibration_truth.py; final, but any
                      disagreement with the model reader is flagged for audit.
  2. model          — the model reader's label (labels_model/batch_*.json) when no
                      structured source answers; for reverse_split, a model "effective"
                      whose Yahoo split is 31-400 days BEFORE the filing is re-labeled
                      "historical" (the criteria's fourth option; the reader ran on v1
                      criteria that lacked it). Flagged for audit.
  3. truth (moderate) is recorded but does NOT override the model; disagreement -> audit.

AUDIT SAMPLE (calibration/audit.csv) = every flagged row + a seeded random draw of
unflagged model-only rows, stratified over listing_status / dilution_event / going_concern
values so every subtype the auto band could act on is checked by a human at least a few
times. The auditor fills `audit_label_<q>` only where they disagree, plus `audit_note`.

OUTPUT
  calibration/labels.csv        cal_id, per question: label, label_src, label_flag
  calibration/audit.csv         the rows for the human, with text_file + model quote
  calibration/merge_summary.json
"""
import argparse
import csv
import glob
import json
import os
import random
from collections import Counter, defaultdict

import filing_lens as fl

Q = fl.QUESTION_ORDER
AUDIT_RANDOM = 10
AUDIT_STRATA = [("listing_status", v) for v in ("deficiency_notice", "delisting_determination", "regained_compliance", "halt")] + \
               [("dilution_event", v) for v in ("priced_offering", "private_placement", "atm_or_equity_line", "convertible_or_warrants")] + \
               [("going_concern", "yes"), ("other_material", "officer_departure"), ("reverse_split", "effective"), ("reverse_split", "announced")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cal", default="calibration")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    cal = args.cal

    cands = {r["cal_id"]: r for r in csv.DictReader(open(os.path.join(cal, "candidates.csv")))}
    truth = {r["cal_id"]: r for r in csv.DictReader(open(os.path.join(cal, "truth.csv")))}
    model = {}
    for f in sorted(glob.glob(os.path.join(cal, "labels_model", "batch_*.json"))):
        for o in json.load(open(f)):
            model[o["cal_id"]] = o
    assert set(cands) == set(truth) == set(model), (len(cands), len(truth), len(model))

    labels, flags = [], defaultdict(list)
    src_count = Counter()
    agree = defaultdict(lambda: [0, 0])
    for cid in sorted(cands):
        t, m = truth[cid], model[cid]
        row = {"cal_id": cid, "ticker": cands[cid]["ticker"], "form": cands[cid]["form"],
               "filing_date": cands[cid]["filing_date"], "items": cands[cid]["items"], "stratum": cands[cid]["stratum"]}
        for q in Q:
            tv, tc = t[f"truth_{q}"], t[f"truth_{q}_conf"]
            mv = m["labels"][q]
            flag = ""
            if tv and tc == "high":
                lab, src = tv, "truth"
                agree[q][1] += 1
                if mv == tv:
                    agree[q][0] += 1
                else:
                    flag = f"truth!=model({mv})"
            else:
                lab, src = mv, "model"
                if q == "reverse_split" and mv == "effective":
                    off = t.get("yahoo_split_offset_days", "")
                    if off != "" and int(off) <= -31:
                        lab, src, flag = "historical", "model+rule", "relabeled_historical"
                    elif off == "" and t["yahoo_split_date"] == "":
                        flag = "effective_but_no_yahoo_split"
                if tv and tc == "moderate" and mv != tv:
                    flag = (flag + ";" if flag else "") + f"moderate_truth({tv})!=model"
                if m["confidence"].get(q) == "low":
                    flag = (flag + ";" if flag else "") + "model_low_conf"
            row[f"label_{q}"], row[f"label_{q}_src"], row[f"label_{q}_flag"] = lab, src, flag
            src_count[(q, src)] += 1
            if flag:
                flags[cid].append(q)
        labels.append(row)

    fields = list(labels[0].keys())
    with open(os.path.join(cal, "labels.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(labels)

    # ---- audit sample --------------------------------------------------------------
    rng = random.Random(args.seed)
    by_id = {r["cal_id"]: r for r in labels}
    audit_ids = sorted(flags)
    # low-confidence-only flags are many; keep hard disagreements mandatory, sample the rest
    hard = [cid for cid in audit_ids if any(("truth!=" in by_id[cid][f"label_{q}_flag"]) or ("moderate_truth" in by_id[cid][f"label_{q}_flag"])
                                            or ("relabeled" in by_id[cid][f"label_{q}_flag"]) or ("no_yahoo" in by_id[cid][f"label_{q}_flag"]) for q in Q)]
    lowonly = [cid for cid in audit_ids if cid not in hard]
    rng.shuffle(lowonly)
    chosen = set(hard) | set(lowonly[:8])
    for q, v in AUDIT_STRATA:
        pool = [r["cal_id"] for r in labels if r[f"label_{q}"] == v and r[f"label_{q}_src"] == "model" and r["cal_id"] not in chosen]
        rng.shuffle(pool)
        chosen |= set(pool[:1])
    rest = [r["cal_id"] for r in labels if r["cal_id"] not in chosen]
    rng.shuffle(rest)
    chosen |= set(rest[:AUDIT_RANDOM])

    audit = []
    for cid in sorted(chosen, key=lambda c: (c not in hard, c)):
        r = by_id[cid]; m = model[cid]; t = truth[cid]
        a = {"cal_id": cid, "priority": "A" if cid in hard else "B", "ticker": r["ticker"], "form": r["form"], "items": r["items"], "filing_date": r["filing_date"],
             "text_file": cands[cid]["text_file"], "doc_url": cands[cid]["doc_url"],
             "why_in_audit": ";".join(f"{q}:{r[f'label_{q}_flag']}" for q in Q if r[f"label_{q}_flag"]) or "random",
             "yahoo_split": f"{t['yahoo_split_date']} 1:{t['yahoo_ratio_n']} off={t.get('yahoo_split_offset_days','')}" if t["yahoo_split_date"] else ""}
        for q in Q:
            a[f"label_{q}"] = r[f"label_{q}"]
            a[f"model_quote_{q}"] = m["rationale"].get(q, "")
            a[f"audit_label_{q}"] = ""
        a["audit_note"] = ""
        audit.append(a)
    with open(os.path.join(cal, "audit.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(audit[0].keys())); w.writeheader(); w.writerows(audit)

    summary = {
        "rows": len(labels), "label_sources": {f"{q}:{s}": n for (q, s), n in sorted(src_count.items())},
        "truth_vs_model_agreement": {q: {"n": v[1], "agree": round(v[0] / v[1], 3) if v[1] else None} for q, v in agree.items()},
        "label_distribution": {q: dict(Counter(r[f"label_{q}"] for r in labels)) for q in Q},
        "flagged_rows": len(flags), "audit_rows": len(audit), "audit_hard_disagreements": len(hard),
        "questions_sha256": fl.QUESTIONS_SHA256, "seed": args.seed,
    }
    json.dump(summary, open(os.path.join(cal, "merge_summary.json"), "w"), indent=2)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
