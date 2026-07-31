#!/usr/bin/env python3
"""ThePickLog — forward evaluator for H-RISK1 and H-RISK2 (registered 2026-07-29).

WHY THIS EXISTS
    The 2026-07-29 audit found six hypotheses that had been registered and then never
    evaluated (H-EX10, H-REG, H-SUB1, H-STR1, H-DIL, H-DEDUP). Registering H-RISK1/H-RISK2
    without an evaluator would repeat that exact failure, so the evaluator ships with the
    registration.

WHAT IT TESTS
    H-RISK1 — the composite score ranks MAGNITUDE, not direction. Per cohort, on picks with
      trading_date strictly AFTER the registration date:
        rho(score, |mae_5d|)   > 0, ticker-clustered 95% CI excluding zero
        rho(score, range)      > 0, ticker-clustered 95% CI excluding zero
        rho(score, signed ret) remains NON-significant  <- the discriminant half of the claim
      Pass also needs n >= 30 and the sign holding across >= 3 consecutive weekly snapshots.

    H-RISK2 — the risk gauge is CALIBRATED, not merely correlated. v0.2 cohort ONLY: the
      frozen absolute score cutpoints and predicted P(mae_5d <= -20%) below are scored with a
      Brier score against a no-skill baseline (the pooled base rate). Pass = Brier beats
      baseline AND the realised Q5-Q1 gap stays >= 15pp.
      NOT applied to v0.3: the two cohorts have different score distributions (v0.2 median
      45.2 vs v0.3 median 92.5), so the calibrated probabilities are explicitly declared
      non-transferable. That is the H-STR3 cohort-incomparability finding, honoured here.

FROZEN 2026-07-29 — these constants define the pre-registration and must never be re-fit.
    Changing them voids the test; a re-derivation is a NEW hypothesis with its own window.

HONEST FRAMING (registered in advance)
    Confirmation demonstrates volatility persistence, a long-documented market regularity.
    It is NOT evidence of alpha, must never be presented as one, and does not reopen Gate 1
    (failed 2026-07-29). Knowing how far a name will move says nothing about which way.

USAGE
    python3 risk_eval.py             # evaluate + append this week's snapshot
    python3 risk_eval.py --selftest  # offline logic check, no data needed
"""
import argparse
import csv
import io
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_MD = os.path.join(HERE, "reports", "risk-eval-LATEST.md")
SNAPS = os.path.join(HERE, "risk_snapshots.csv")

# ---- FROZEN PRE-REGISTRATION CONSTANTS (2026-07-29) ------------------------
REGISTERED_AT = "2026-07-29"
MIN_N = 30
BOOT = 4000
SEED = 7
DD_THRESHOLD = -20.0                      # "deep drawdown" definition for H-RISK2
V02_CUTPOINTS = [42.12, 43.90, 46.98, 54.02]      # v0.2 score quintile edges, frozen
V02_PRED_P = [0.2022, 0.3956, 0.3488, 0.3820, 0.4831]  # predicted P(dd<=-20%) per quintile
V02_BASE_RATE = 0.3626                    # no-skill baseline at registration
MIN_Q5_Q1_GAP = 0.15                      # H-RISK2 pass bar on the realised spread
# ---------------------------------------------------------------------------

SNAP_FIELDS = ["iso_week", "computed_at", "cohort", "n_post", "rho_absmae", "rho_range",
               "rho_ret1", "rho_ret5", "sig_absmae", "sig_range", "sig_ret1"]


def _f(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def _read(path):
    if not os.path.exists(path):
        return []
    with io.open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------- PURE CORE (offline-testable)
def _rank(xs):
    """Average-rank transform (ties averaged), stdlib only."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    rx, ry = _rank(xs), _rank(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def cluster_boot_rho(rows, xk, yk, seed=SEED, B=BOOT):
    """Spearman rho + 95% CI, resampling TICKERS (H-IND1: the unit is the name)."""
    import random
    pts = [(r[xk], r[yk], r["ticker"]) for r in rows
           if r.get(xk) is not None and r.get(yk) is not None]
    if len(pts) < 10:
        return None
    obs = spearman([p[0] for p in pts], [p[1] for p in pts])
    if obs is None:
        return None
    by = {}
    for x, y, t in pts:
        by.setdefault(t, []).append((x, y))
    tk = list(by)
    rnd = random.Random(seed)
    out = []
    for _ in range(B):
        samp = []
        for _ in range(len(tk)):
            samp.extend(by[tk[rnd.randrange(len(tk))]])
        r = spearman([s[0] for s in samp], [s[1] for s in samp])
        if r is not None:
            out.append(r)
    if len(out) < 100:
        return None
    out.sort()
    lo = out[int(0.025 * len(out))]
    hi = out[min(len(out) - 1, int(0.975 * len(out)))]
    return {"rho": obs, "lo": lo, "hi": hi, "n": len(pts),
            "tickers": len(tk), "sig": (lo > 0 or hi < 0)}


def quintile_of(score, cuts=V02_CUTPOINTS):
    for i, c in enumerate(cuts):
        if score <= c:
            return i
    return len(cuts)


def brier(preds, actuals):
    return sum((p - a) ** 2 for p, a in zip(preds, actuals)) / len(preds)


# ------------------------------------------------------------------ evaluation
def load_rows():
    picks = {p["pick_id"]: p for p in _read(os.path.join(HERE, "picks.csv"))}
    rows = []
    for o in _read(os.path.join(HERE, "outcomes.csv")):
        p = picks.get(o.get("pick_id"))
        if not p:
            continue
        td = (p.get("trading_date") or "")
        if td <= REGISTERED_AT:          # strictly AFTER registration
            continue
        r1, mae, mfe = _f(o.get("ret_open_close_net")), _f(o.get("mae_5d")), _f(o.get("mfe_5d"))
        sc = _f(p.get("score"))
        if r1 is None or sc is None:
            continue
        rows.append({"ticker": p.get("ticker"), "cohort": p.get("model_version", ""),
                     "score": sc, "ret1": r1 + 2.0, "ret5": (_f(o.get("ret_open_5dclose_net")) or 0) + 2.0,
                     "absmae": abs(mae) if mae is not None else None,
                     "mae": mae,
                     "range": (mfe - mae) if (mfe is not None and mae is not None) else None})
    return rows


def evaluate(rows):
    res = {}
    for cohort in sorted({r["cohort"] for r in rows}):
        sub = [r for r in rows if r["cohort"] == cohort]
        res[cohort] = {
            "n": len(sub),
            "absmae": cluster_boot_rho(sub, "score", "absmae"),
            "range": cluster_boot_rho(sub, "score", "range"),
            "ret1": cluster_boot_rho(sub, "score", "ret1"),
            "ret5": cluster_boot_rho(sub, "score", "ret5"),
        }
    return res


def evaluate_risk2(rows):
    sub = [r for r in rows if r["cohort"].startswith("v0.2") and r["mae"] is not None]
    if len(sub) < MIN_N:
        return {"n": len(sub), "ready": False}
    preds, acts, buckets = [], [], {i: [] for i in range(5)}
    for r in sub:
        q = quintile_of(r["score"])
        a = 1.0 if r["mae"] <= DD_THRESHOLD else 0.0
        preds.append(V02_PRED_P[q]); acts.append(a); buckets[q].append(a)
    b_model = brier(preds, acts)
    b_base = brier([V02_BASE_RATE] * len(acts), acts)
    q1 = sum(buckets[0]) / len(buckets[0]) if buckets[0] else None
    q5 = sum(buckets[4]) / len(buckets[4]) if buckets[4] else None
    gap = (q5 - q1) if (q1 is not None and q5 is not None) else None
    return {"n": len(sub), "ready": True, "brier_model": b_model, "brier_base": b_base,
            "beats_baseline": b_model < b_base, "q1": q1, "q5": q5, "gap": gap,
            "gap_ok": (gap is not None and gap >= MIN_Q5_Q1_GAP),
            "realised": {i: (sum(v) / len(v) if v else None) for i, v in buckets.items()},
            "counts": {i: len(v) for i, v in buckets.items()}}


def snapshot(res, now):
    """Append one row per cohort per ISO week (idempotent)."""
    iso = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]:02d}"
    have = {(r["iso_week"], r["cohort"]) for r in _read(SNAPS)}
    new = []
    for cohort, r in res.items():
        if (iso, cohort) in have or not r["n"]:
            continue
        g = lambda k, f: (f"{r[k][f]:.4f}" if r.get(k) else "")
        s = lambda k: ("1" if (r.get(k) and r[k]["sig"]) else "0") if r.get(k) else ""
        new.append({"iso_week": iso, "computed_at": now.isoformat(timespec="seconds"),
                    "cohort": cohort, "n_post": r["n"],
                    "rho_absmae": g("absmae", "rho"), "rho_range": g("range", "rho"),
                    "rho_ret1": g("ret1", "rho"), "rho_ret5": g("ret5", "rho"),
                    "sig_absmae": s("absmae"), "sig_range": s("range"), "sig_ret1": s("ret1")})
    if new:
        first = not os.path.exists(SNAPS)
        with io.open(SNAPS, "a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=SNAP_FIELDS)
            if first:
                w.writeheader()
            for r in new:
                w.writerow(r)
    return iso, len(new)


def consecutive_positive(cohort, key="rho_absmae"):
    """How many consecutive most-recent weekly snapshots have a positive rho."""
    rs = [r for r in _read(SNAPS) if r["cohort"] == cohort]
    rs.sort(key=lambda r: r["iso_week"])
    c = 0
    for r in reversed(rs):
        v = _f(r.get(key))
        if v is not None and v > 0:
            c += 1
        else:
            break
    return c


def fmt(r):
    if not r:
        return "insufficient data"
    return (f"rho={r['rho']:+.3f} CI[{r['lo']:+.3f},{r['hi']:+.3f}] "
            f"n={r['n']} tickers={r['tickers']} {'SIG' if r['sig'] else 'ns'}")


def write_report(res, r2, iso, now):
    L = ["# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · " + now.date().isoformat(), "",
         f"Pre-registered **{REGISTERED_AT}** (HYPOTHESES.md batch #6). Only picks with "
         f"`trading_date` strictly after that date are counted. Snapshot week: **{iso}**.", "",
         "**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), "
         "not *direction*. The claim has two halves and BOTH must hold: the magnitude "
         "correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return "
         "correlation stays non-significant.", ""]
    for cohort, r in sorted(res.items()):
        L += [f"### {cohort} — n_post = {r['n']}", "",
              f"- score -> |MAE| (drawdown depth): {fmt(r['absmae'])}",
              f"- score -> range (MFE-MAE): {fmt(r['range'])}",
              f"- score -> same-day return *(must stay ns)*: {fmt(r['ret1'])}",
              f"- score -> 5-day return *(must stay ns)*: {fmt(r['ret5'])}",
              f"- consecutive weekly snapshots with positive |MAE| rho: "
              f"**{consecutive_positive(cohort)}** (need >= 3)", ""]
        ok = (r["n"] >= MIN_N and r["absmae"] and r["absmae"]["sig"] and r["absmae"]["rho"] > 0
              and r["range"] and r["range"]["sig"] and r["range"]["rho"] > 0
              and r["ret1"] and not r["ret1"]["sig"]
              and consecutive_positive(cohort) >= 3)
        L += [f"**{cohort} verdict: {'PASSES all H-RISK1 criteria' if ok else 'not yet established'}**", ""]
    L += ["---", "", "**H-RISK2** — is the gauge *calibrated*, not merely correlated? "
          "v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 "
          "(different score distributions — see H-STR3).", ""]
    if not r2.get("ready"):
        L += [f"Not evaluable yet: {r2['n']} post-registration v0.2 picks with a drawdown "
              f"(need {MIN_N}).", ""]
    else:
        pct = lambda v: "n/a" if v is None else f"{v:.1%}"
        L += [f"- Brier (frozen model) **{r2['brier_model']:.4f}** vs no-skill baseline "
              f"**{r2['brier_base']:.4f}** -> "
              f"{'BEATS baseline' if r2['beats_baseline'] else 'does NOT beat baseline'}",
              f"- realised P(MAE <= {DD_THRESHOLD:.0f}%): Q1 {pct(r2['q1'])} vs Q5 {pct(r2['q5'])}",
              f"- Q5-Q1 gap: {pct(r2['gap'])} (need >= {MIN_Q5_Q1_GAP:.0%}) -> "
              f"{'OK' if r2['gap_ok'] else 'not met'}",
              "- per-quintile realised / predicted / n:", ""]
        for i in range(5):
            got = r2["realised"][i]
            L.append(f"  - Q{i+1}: realised {pct(got)} · "
                     f"predicted {V02_PRED_P[i]:.1%} · n={r2['counts'][i]}")
        L += ["", f"**H-RISK2 verdict: "
              f"{'PASSES' if (r2['beats_baseline'] and r2['gap_ok']) else 'not yet established'}**", ""]
    L += ["---", "",
          "**Registered framing — do not drop it.** A confirmation here demonstrates "
          "*volatility persistence*, a long-documented market regularity, and is **not evidence "
          "of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will "
          "move says nothing about which way it will move — which is precisely what the "
          "signed-return rows above keep testing.", "",
          "_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing "
          "them voids the pre-registration._"]
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with io.open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"wrote {OUT_MD}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    if ap.parse_args().selftest:
        return _selftest()
    now = datetime.now(timezone.utc)
    rows = load_rows()
    print(f"risk_eval: {len(rows)} post-{REGISTERED_AT} graded picks")
    res = evaluate(rows)
    r2 = evaluate_risk2(rows)
    iso, added = snapshot(res, now)
    print(f"risk_eval: snapshot {iso}, {added} row(s) appended")
    write_report(res, r2, iso, now)
    return 0


def _selftest():
    assert _rank([10, 20, 30]) == [1.0, 2.0, 3.0]
    assert _rank([10, 10, 30]) == [1.5, 1.5, 3.0]
    assert abs(spearman([1, 2, 3, 4], [1, 2, 3, 4]) - 1.0) < 1e-9
    assert abs(spearman([1, 2, 3, 4], [4, 3, 2, 1]) + 1.0) < 1e-9
    assert quintile_of(40.0) == 0 and quintile_of(100.0) == 4
    assert quintile_of(42.12) == 0 and quintile_of(42.13) == 1
    assert abs(brier([1.0, 0.0], [1.0, 0.0])) < 1e-9
    assert abs(brier([0.5, 0.5], [1.0, 0.0]) - 0.25) < 1e-9
    # a monotone magnitude relationship must be detected; direction must not be
    rows = []
    for i in range(60):
        rows.append({"ticker": f"T{i%12}", "score": float(i),
                     "absmae": float(i) + (i % 5), "range": float(i) * 1.5,
                     "ret1": (1.0 if i % 2 else -1.0), "ret5": (2.0 if i % 3 else -2.0)})
    a = cluster_boot_rho(rows, "score", "absmae")
    assert a and a["rho"] > 0.9 and a["sig"], a
    d = cluster_boot_rho(rows, "score", "ret1")
    assert d and abs(d["rho"]) < 0.3, d
    print("risk_eval selftest PASS — rank/spearman/quintile/brier + cluster bootstrap verified")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:      # never block the daily commit
        print(f"risk_eval: non-fatal error {type(e).__name__}: {e}")
        sys.exit(0)
