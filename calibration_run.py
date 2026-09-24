#!/usr/bin/env python3
"""
calibration_run.py — GATE 2 proper: send the calibration set through the PINNED Jev
model, score its probabilities against the labels, and write the calibration result
that the site's Trust page will link to.

THE BAR IS WRITTEN DOWN BEFORE THE RUN (see PASS_BAR) so it cannot move afterwards.

WHAT IT DOES
  1. For each cal_id in calibration/candidates.csv: read the stored text (the exact
     text the labels were made on), build the request with filing_lens.QUESTIONS,
     call Jev ONCE, cache the raw response under run_<model>/responses/<cal_id>.json.
     Re-runs reuse the cache; a response whose model differs from the pinned one is
     discarded as version drift (never scored).
  2. Score per question against calibration/labels.csv, with calibration/audit.csv
     overrides applied where the auditor filled audit_label_<q>:
       • reliability diagram, 10 equal-width bins on the probability of the CHOSEN answer
       • expected calibration error (ECE), weighted by bin count
       • accuracy overall, and accuracy of the top bin (p >= 0.90)
       • for each (question, value) in filing_lens.THRESHOLDS: precision and recall at
         the proposed auto floor, and the floor that would deliver 0.95 precision
       • split_ratio accuracy conditional on reverse_split in {announced, effective}
  3. Write run_<model>/result.json, run_<model>/reliability.csv, and
     run_<model>/FIELD-NOTE-DRAFT.md; print PASS / FAIL per question against PASS_BAR.

NOTHING HERE TOUCHES filing_lens.THRESHOLDS. Threshold changes are a separate commit
that cites this run's result.json by path and sha.

USAGE
  python3 calibration_run.py --cal calibration   # reads ../jev.env (outside the repo)
  JEV_ENV_FILE=/path/to/other.env python3 calibration_run.py --cal calibration
  python3 calibration_run.py --cal calibration --fake        # plumbing test, no key
NOT INVESTMENT ADVICE.
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import date


def _load_env(path):
    """KEY=VALUE lines into os.environ (existing env wins). Must run BEFORE importing
    filing_lens, which reads JEV_* at import. Never prints values."""
    if not path or not os.path.exists(path):
        return False
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())
    return True


_ENV = os.environ.get("JEV_ENV_FILE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "jev.env")
_ENV_LOADED = _load_env(_ENV)

import filing_lens as fl  # noqa: E402  (after env load on purpose)

Q = fl.QUESTION_ORDER
BINS = 10
TOP_BIN = 0.90

# The pass bar, fixed before the run (mirrors the spec doc, "Calibration test").
PASS_BAR = {
    "ece_max": 0.05,                       # every question with a positive class
    "top_bin_min_accuracy": 0.90,          # p >= 0.90 must be right >= 90% of the time
    "auto_precision_min": {                # at the proposed auto floor in THRESHOLDS
        ("reverse_split", "effective"): 0.95,
        ("listing_status", "halt"): 0.95,
        ("listing_status", "delisting_determination"): 0.95,
    },
    "split_ratio_conditional_accuracy_min": 0.95,
    "min_positives_to_score": 30,          # a class with fewer labeled positives is reported, not gated
}


def load_labels(cal):
    labels = {r["cal_id"]: r for r in csv.DictReader(open(os.path.join(cal, "labels.csv")))}
    overrides = 0
    ap = os.path.join(cal, "audit.csv")
    if os.path.exists(ap):
        for a in csv.DictReader(open(ap)):
            for q in Q:
                v = (a.get(f"audit_label_{q}") or "").strip()
                if v:
                    labels[a["cal_id"]][f"label_{q}"] = v
                    labels[a["cal_id"]][f"label_{q}_src"] = "audit"
                    overrides += 1
    return labels, overrides


def get_response(cal, run_dir, r, call, model):
    """Cached, pinned. Returns (response, from_cache) or (None, reason)."""
    path = os.path.join(run_dir, "responses", r["cal_id"] + ".json")
    if os.path.exists(path):
        resp = json.load(open(path))
        # a cached answer is only valid for the exact text it was made on
        if resp.get("_text_sha256") == r["text_sha256"] and resp.get("_questions_sha256") == fl.QUESTIONS_SHA256:
            return resp, "cache"
    text = open(os.path.join(cal, r["text_file"])).read()
    if hashlib.sha256(text.encode()).hexdigest() != r["text_sha256"]:
        return None, "text_hash_mismatch"
    filing = {"form": r["form"], "items": r["items"], "filingDate": r["filing_date"],
              "accession": r["accession"], "primaryDocument": ""}
    req = fl.build_request(filing, text, model)
    for attempt in range(4):
        try:
            resp = call(req)
            break
        except Exception as e:                       # 429 / transient: backoff
            if attempt == 3:
                return None, f"call_err:{type(e).__name__}"
            time.sleep(2 ** attempt)
    if str(resp.get("model", "")) != model:
        return None, f"version_drift:{resp.get('model')}"
    resp = dict(resp, _text_sha256=r["text_sha256"], _questions_sha256=fl.QUESTIONS_SHA256)
    json.dump(resp, open(path, "w"))
    return resp, "live"


def score(rows, answers, labels):
    """rows: list of candidates rows scored; answers: cal_id -> parsed answers."""
    out = {}
    for q in Q:
        pts = []                                     # (p_of_chosen, correct, chosen, truth)
        for r in rows:
            cid = r["cal_id"]
            a = answers[cid][q]
            truth = labels[cid][f"label_{q}"]
            if a["value"] == "" or a["p"] == "" or not truth:
                continue
            pts.append((float(a["p"]), a["value"] == truth, a["value"], truth))
        n = len(pts)
        res = {"n": n}
        if not n:
            out[q] = res; continue
        res["accuracy"] = round(sum(c for _, c, _, _ in pts) / n, 4)
        # reliability
        bins = [[] for _ in range(BINS)]
        for p, c, _, _ in pts:
            i = min(BINS - 1, int(p * BINS))
            bins[i].append(c)
        rel, ece = [], 0.0
        for i, b in enumerate(bins):
            if not b:
                rel.append({"bin": i, "lo": i / BINS, "hi": (i + 1) / BINS, "n": 0}); continue
            acc = sum(b) / len(b)
            mid = (i + 0.5) / BINS
            ece += abs(acc - mid) * len(b) / n
            rel.append({"bin": i, "lo": i / BINS, "hi": (i + 1) / BINS, "n": len(b), "accuracy": round(acc, 4)})
        res["ece"] = round(ece, 4)
        res["reliability"] = rel
        top = [c for p, c, _, _ in pts if p >= TOP_BIN]
        res["top_bin"] = {"n": len(top), "accuracy": round(sum(top) / len(top), 4) if top else None}
        # per value: positives, precision/recall at the proposed floor, floor for 0.95 precision
        per = {}
        for (qq, v), (auto_floor, _) in fl.THRESHOLDS.items():
            if qq != q:
                continue
            pos = [x for x in pts if x[3] == v]
            pred = [x for x in pts if x[2] == v and x[0] >= auto_floor]
            tp = sum(1 for x in pred if x[3] == v)
            prec = round(tp / len(pred), 4) if pred else None
            rec = round(tp / len(pos), 4) if pos else None
            # smallest floor (on a 0.01 grid) giving >= 0.95 precision with >= 5 predictions
            floor95 = None
            for f in [i / 100 for i in range(50, 100)]:
                pr = [x for x in pts if x[2] == v and x[0] >= f]
                if len(pr) >= 5 and sum(1 for x in pr if x[3] == v) / len(pr) >= 0.95:
                    floor95 = f; break
            per[v] = {"labeled_positives": len(pos), "proposed_auto_floor": auto_floor,
                      "precision_at_floor": prec, "recall_at_floor": rec, "n_predicted_at_floor": len(pred),
                      "floor_for_0.95_precision": floor95}
        res["per_value"] = per
        out[q] = res
    # split_ratio conditional on a real split
    cond = [(answers[r["cal_id"]]["split_ratio"]["value"], labels[r["cal_id"]]["label_split_ratio"])
            for r in rows if labels[r["cal_id"]]["label_reverse_split"] in ("announced", "effective")
            and labels[r["cal_id"]]["label_split_ratio"]]
    out["split_ratio"]["conditional"] = {"n": len(cond),
                                         "accuracy": round(sum(1 for a, b in cond if a == b) / len(cond), 4) if cond else None}
    return out


def verdicts(res):
    v = {}
    for q in Q:
        r = res.get(q, {})
        reasons = []
        if not r.get("n"):
            v[q] = ("UNSCORED", ["no scored rows"]); continue
        if r["ece"] > PASS_BAR["ece_max"]:
            reasons.append(f"ECE {r['ece']} > {PASS_BAR['ece_max']}")
        tb = r["top_bin"]
        if tb["n"] and tb["accuracy"] is not None and tb["accuracy"] < PASS_BAR["top_bin_min_accuracy"]:
            reasons.append(f"top-bin accuracy {tb['accuracy']} < {PASS_BAR['top_bin_min_accuracy']}")
        for (qq, val), pmin in PASS_BAR["auto_precision_min"].items():
            if qq != q:
                continue
            pv = r["per_value"].get(val, {})
            if pv.get("labeled_positives", 0) < PASS_BAR["min_positives_to_score"]:
                reasons.append(f"{val}: only {pv.get('labeled_positives', 0)} positives (<{PASS_BAR['min_positives_to_score']}) — UNDERPOWERED, not gated")
            elif pv.get("precision_at_floor") is not None and pv["precision_at_floor"] < pmin:
                reasons.append(f"{val}: precision {pv['precision_at_floor']} at floor {pv['proposed_auto_floor']} < {pmin}")
        if q == "split_ratio":
            c = r.get("conditional", {})
            if c.get("accuracy") is not None and c["accuracy"] < PASS_BAR["split_ratio_conditional_accuracy_min"]:
                reasons.append(f"conditional ratio accuracy {c['accuracy']} < {PASS_BAR['split_ratio_conditional_accuracy_min']}")
        hard = [x for x in reasons if "UNDERPOWERED" not in x]
        v[q] = ("FAIL" if hard else ("PASS*" if reasons else "PASS"), reasons)
    return v


def field_note(model, res, verd, meta):
    L = [f"# Calibration result — filing_lens × {model}", "",
         f"Run {meta['run_date']} · {meta['scored']} filings scored ({meta['n_skipped']} skipped) · "
         f"questions sha `{fl.QUESTIONS_SHA256[:12]}` · lens `{fl.__version__}` · seed {meta['seed']}", "",
         "This is the calibration test the spec requires before any answer from the model appears on the site. "
         "The bar was fixed before the run; the numbers below are the run.", "",
         "| Question | n | Accuracy | ECE | Top bin (p≥0.90) | Verdict |", "| --- | --- | --- | --- | --- | --- |"]
    for q in Q:
        r = res.get(q, {}); tb = r.get("top_bin", {})
        L.append(f"| `{q}` | {r.get('n', 0)} | {r.get('accuracy', '')} | {r.get('ece', '')} | "
                 f"{tb.get('accuracy', '')} (n={tb.get('n', 0)}) | **{verd[q][0]}** |")
    L += ["", "## Per-value, at the proposed auto floor", "",
          "| Question · value | Positives | Floor | Precision | Recall | Predicted | Floor for 0.95 precision |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    for q in Q:
        for v, pv in res.get(q, {}).get("per_value", {}).items():
            L.append(f"| `{q}` · {v} | {pv['labeled_positives']} | {pv['proposed_auto_floor']} | {pv['precision_at_floor']} | "
                     f"{pv['recall_at_floor']} | {pv['n_predicted_at_floor']} | {pv['floor_for_0.95_precision']} |")
    L += ["", "## Verdict reasons", ""]
    for q in Q:
        for reason in verd[q][1]:
            L.append(f"- `{q}`: {reason}")
    if not any(verd[q][1] for q in Q):
        L.append("- none")
    L += ["", "## How the labels were made", "",
          "Market truth (Yahoo split history, cross-checked against float drops in candidates.csv) decided "
          "`reverse_split`/`split_ratio` where it could; 8-K item codes decided bankruptcy/auditor/restatement/M&A; "
          "a model reader labeled the rest with a verbatim quote per label; a human audited every disagreement plus a "
          "seeded sample. Precedence and rules: `calibration_truth.py`, `calibration_merge.py`. "
          f"Audit overrides applied: {meta['audit_overrides']}.", "",
          "## Reproduce", "",
          "Every request is the stored text (hash in candidates.csv) plus the question block in `filing_lens.QUESTIONS`, "
          f"sent to `{model}`; raw responses are cached under `responses/`. Re-running against the same pinned version "
          "must reproduce `result.json`.", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cal", default="calibration")
    ap.add_argument("--fake", action="store_true", help="plumbing test with filing_lens._fake_jev")
    ap.add_argument("--limit", type=int, default=None, help="score only the first N filings (e.g. --limit 3 as a live smoke test)")
    ap.add_argument("--pace", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    if args.fake:
        model, call = "jev-0.0.0-selftest", fl._fake_jev
    else:
        model = fl.JEV_MODEL
        if not model or model.endswith("latest"):
            sys.exit("JEV_MODEL must be an exact pinned version (never 'latest')")
        if not fl.JEV_API_KEY:
            sys.exit(f"JEV_API_KEY is empty. Paste your key into {os.path.abspath(_ENV)} "
                     f"({'found' if _ENV_LOADED else 'NOT found'}), after 'JEV_API_KEY='.")
        print(f"key loaded from {os.path.abspath(_ENV) if _ENV_LOADED else 'environment'} "
              f"(…{fl.JEV_API_KEY[-4:]}); model {model}; endpoint {fl.JEV_ENDPOINT}")
        call = fl.call_jev
    run_dir = os.path.join(args.cal, f"run_{model}")
    os.makedirs(os.path.join(run_dir, "responses"), exist_ok=True)

    cands = list(csv.DictReader(open(os.path.join(args.cal, "candidates.csv"))))
    if args.limit:
        cands = cands[: args.limit]
    labels, overrides = load_labels(args.cal)

    answers, skipped, src = {}, Counter(), Counter()
    for i, r in enumerate(cands, 1):
        resp, how = get_response(args.cal, run_dir, r, call, model)
        if resp is None:
            skipped[how.split(":")[0]] += 1; continue
        src[how] += 1
        answers[r["cal_id"]] = fl.parse_answers(resp, expected_model=model)
        if how == "live":
            time.sleep(args.pace)
        if i % 50 == 0:
            print(f"  {i}/{len(cands)} ({dict(src)}, skipped {dict(skipped)})")
    rows = [r for r in cands if r["cal_id"] in answers]
    print(f"scored {len(rows)} / {len(cands)}  sources={dict(src)}  skipped={dict(skipped)}")

    res = score(rows, answers, labels)
    verd = verdicts(res)
    meta = {"run_date": date.today().isoformat(), "model": model, "scored": len(rows), "skipped": dict(skipped), "n_skipped": sum(skipped.values()),
            "seed": args.seed, "audit_overrides": overrides, "questions_sha256": fl.QUESTIONS_SHA256,
            "lens_version": fl.__version__,
            "pass_bar": {k: ({f"{a}:{b}": x for (a, b), x in v.items()} if isinstance(v, dict) else v) for k, v in PASS_BAR.items()}}
    result = {"meta": meta, "verdicts": {q: {"verdict": v[0], "reasons": v[1]} for q, v in verd.items()}, "scores": res}
    json.dump(result, open(os.path.join(run_dir, "result.json"), "w"), indent=2, default=str)
    with open(os.path.join(run_dir, "reliability.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["question", "bin", "lo", "hi", "n", "accuracy"])
        for q in Q:
            for b in res.get(q, {}).get("reliability", []):
                w.writerow([q, b["bin"], b["lo"], b["hi"], b["n"], b.get("accuracy", "")])
    open(os.path.join(run_dir, "FIELD-NOTE-DRAFT.md"), "w").write(field_note(model, res, verd, meta))
    for q in Q:
        print(f"  {q:16s} {verd[q][0]:9s} n={res[q].get('n', 0):3d} acc={res[q].get('accuracy', '')} ece={res[q].get('ece', '')}")
    print(f"-> {run_dir}/result.json, reliability.csv, FIELD-NOTE-DRAFT.md")


if __name__ == "__main__":
    main()
