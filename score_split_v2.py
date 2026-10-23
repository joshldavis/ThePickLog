#!/usr/bin/env python3
"""
score_split_v2.py — score the pre-registered split-v2 test (REGISTRATION-split-v2.md)
from the committed files only. No network, no key.

  calibration_v2/candidates.csv      the sample (text pinned by text_sha256)
  calibration_v2/labels.csv          labels frozen in 945e3ad BEFORE any Jev call
  calibration_v2/label_corrections.csv   (optional) corrections, each with a verbatim quote
  calibration_v2/responses/*.json    Jev's logged answers (the record)
  calibration_v2/repro_responses/*.json  the 30 re-asks

  FILING_LENS_QUESTIONS=v2 python3 score_split_v2.py --cal calibration_v2
NOT INVESTMENT ADVICE.
"""
import argparse, csv, glob, json, os, sys
from collections import Counter

os.environ.setdefault("FILING_LENS_QUESTIONS", "v2")
import filing_lens as fl

MODEL = "jev-1.13.0"
FLOOR = 0.90
BAR, SANITY, MIN_POS = 0.95, 0.90, 30


def load(cal, corrected):
    L = {r["cal_id"]: r for r in csv.DictReader(open(os.path.join(cal, "labels.csv")))}
    n = 0
    cp = os.path.join(cal, "label_corrections.csv")
    if corrected and os.path.exists(cp):
        for c in csv.DictReader(open(cp)):
            L[c["cal_id"]][f"label_{c['question']}"] = c["new"]; n += 1
    return L, n


def answers(d):
    return {os.path.basename(f)[:-5]: fl.parse_answers(json.load(open(f)), expected_model=MODEL)
            for f in sorted(glob.glob(os.path.join(d, "*.json")))}


def prec(scope, A, L, v, floor=FLOOR):
    pred = [c for c in scope if A[c]["reverse_split"]["value"] == v and A[c]["reverse_split"]["p"] >= floor]
    tp = [c for c in pred if L[c]["label_reverse_split"] == v]
    pos = [c for c in scope if L[c]["label_reverse_split"] == v]
    return {"predicted": len(pred), "correct": len(tp), "precision": round(len(tp) / len(pred), 4) if pred else None,
            "labeled_positives": len(pos), "recall": round(len(tp) / len(pos), 4) if pos else None,
            "false_positives": [c for c in pred if c not in tp],
            "missed": [{"cal_id": c, "jev": A[c]["reverse_split"]["value"], "p": A[c]["reverse_split"]["p"]} for c in pos if c not in tp]}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cal", default="calibration_v2"); a = ap.parse_args()
    assert fl.QUESTIONS_VERSION == "v2", "score under the v2 question block"
    C = {r["cal_id"]: r for r in csv.DictReader(open(os.path.join(a.cal, "candidates.csv")))}
    A = answers(os.path.join(a.cal, "responses"))
    assert set(A) == set(C), f"{len(A)} responses for {len(C)} filings"
    for c, r in C.items():   # every logged answer must be on this exact text + question block
        raw = json.load(open(os.path.join(a.cal, "responses", c + ".json")))
        assert raw["_text_sha256"] == r["text_sha256"] and raw["_questions_sha256"] == fl.QUESTIONS_SHA256, c
    scope = sorted(c for c, r in C.items() if r["form"] in ("8-K", "8-K/A") and set(fl._items_of(r["items"])) & {"5.03", "3.03"})
    out = {"registration": "REGISTRATION-split-v2.md", "model": MODEL, "questions_sha256": fl.QUESTIONS_SHA256,
           "sample": len(C), "scope_8k_503_303": len(scope), "floor": FLOOR}
    for tag, corr in (("as_labeled", False), ("corrected", True)):
        L, n = load(a.cal, corr)
        sp = [c for c in scope if L[c]["label_reverse_split"] in ("effective", "announced")]
        ok = [c for c in sp if A[c]["split_ratio"]["value"] == L[c]["label_split_ratio"]]
        out[tag] = {"corrections_applied": n,
                    "effective": prec(scope, A, L, "effective"), "announced": prec(scope, A, L, "announced"),
                    "split_ratio_given_split": {"n": len(sp), "correct": len(ok), "accuracy": round(len(ok) / len(sp), 4) if sp else None},
                    "confusion_label_vs_jev": {f"{x}->{y}": k for (x, y), k in sorted(Counter((L[c]["label_reverse_split"], A[c]["reverse_split"]["value"]) for c in scope).items())},
                    "accuracy_all_questions": {q: round(sum(A[c][q]["value"] == L[c][f"label_{q}"] for c in C) / len(C), 4) for q in fl.QUESTION_ORDER}}
    R = answers(os.path.join(a.cal, "repro_responses"))
    ch = {q: sorted(c for c in R if R[c][q]["value"] != A[c][q]["value"]) for q in fl.QUESTION_ORDER}
    out["reproducibility"] = {"n": len(R), "seed": 2028, "changed": ch,
                              "max_probability_move": round(max(abs(R[c][q]["p"] - A[c][q]["p"]) for c in R for q in fl.QUESTION_ORDER), 4)}
    e_c, e_l = out["corrected"]["effective"], out["as_labeled"]["effective"]
    primary = e_c["labeled_positives"] >= MIN_POS and e_c["precision"] is not None and e_c["precision"] >= BAR
    sanity = e_l["precision"] is not None and e_l["precision"] >= SANITY
    out["verdict"] = {"primary_effective_precision_ge_0.95_with_30_pos": primary, "sanity_as_labeled_ge_0.90": sanity,
                      "secondary_announced_ge_0.95": (out["corrected"]["announced"]["precision"] or 0) >= BAR,
                      "secondary_ratio_ge_0.95": (out["corrected"]["split_ratio_given_split"]["accuracy"] or 0) >= BAR,
                      "secondary_repro_0_changed": len(R) == 30 and not ch["reverse_split"],
                      "PASS": primary and sanity}
    json.dump(out, open(os.path.join(a.cal, "registered_outcomes.json"), "w"), indent=2)
    print(json.dumps(out["verdict"], indent=1))
    print("effective:", {k: e_c[k] for k in ("correct", "predicted", "precision", "labeled_positives", "recall")})


if __name__ == "__main__":
    main()
