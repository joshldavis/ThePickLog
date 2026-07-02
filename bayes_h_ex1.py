#!/usr/bin/env python3
"""
Bayesian read-out for H-EX1 — sequential Beta-Binomial posterior on the +10% touch rate.

WHAT THIS IS
  H-EX1 (HYPOTHESES.md, registered 2026-06-23) hinges on one number: p, the probability
  that a pick's 5-day high touches +10% (mfe_5d >= 10, gross). This script maintains a
  Beta posterior on p that updates with every graded pick, instead of waiting for a
  fixed-n frequentist verdict. Bayesian updating is immune to "peeking": checking the
  posterior daily does not corrupt the inference the way repeated significance tests do.

WHAT THIS IS NOT
  Not a new hypothesis and not the pass/fail judge — weekly_report.py §4d expectancy
  vs baseline remains the registered H-EX1 criterion. This is a parallel read-out that
  quantifies *how sure* the log lets anyone be, at any moment, given stated priors.

PRIORS (FROZEN 2026-07-02 — do not tune after this date)
  headline  Beta(1,1)     flat/uniform — "let the log speak", easiest for a stranger
                          to verify (posterior mean = (1+hits)/(2+n)).
  jeffreys  Beta(.5,.5)   standard reference prior — sensitivity check.
  skeptical Beta(10,10)   centered at 50% ("touching +10% is a coin flip"), worth 20
                          pseudo-picks of doubt — sensitivity check against small-n hype.
  If the three disagree materially, the honest statement is "the data don't decide yet."

BREAKEVEN LINES (plug-in diagnostics, recomputed per window — NOT part of the posterior)
  The posterior is on p alone. To make p economically readable we mark:
    p*_base = (EV_base - m) / (8 - m)   fill rate needed to BEAT the same-day-close
                                        baseline, where m = mean 5-day-close net return
                                        of the misses and EV_base = mean same-day-close
                                        net return (both plug-in estimates, shown).
    p*_zero = (0 - m) / (8 - m)         fill rate needed for absolute profitability.
  These lines move as m and EV_base re-estimate; that uncertainty is NOT propagated here
  (a full two-part model is roadmap work — see BAYESIAN-ROADMAP.md item R3).

SEMANTICS (mirrors weekly_report.py §4d / dashboard.html H-EX1 exactly)
  Evaluable pick: joined to picks.csv by pick_id; ret_open_close_net, mfe_5d and
  ret_open_5dclose_net all parseable. Hit: mfe_5d >= 10.0. OOS window: pick's
  trading_date > 2026-06-23 (strict). Fill assumed at exactly +10% -> +8% net; the
  H-EX1 slippage caveat (thin floats gap through limits) applies to every number here.

VERIFY BY HAND (no code needed)
  Count evaluable graded picks n and hits k in outcomes.csv. Flat-prior posterior mean
  is (1+k)/(2+n); the credible interval and tail probabilities come from the Beta(1+k,
  1+n-k) CDF — any stats package (scipy: beta.cdf / beta.ppf) reproduces them.

Output: reports/bayes-h-ex1-LATEST.md (+ stdout summary). Stdlib only, deterministic.
Selftests run on every invocation and abort on failure.
"""

import csv, math, os, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
EX_REG = "2026-06-23"          # H-EX1 registration date (HYPOTHESES.md)
PRIOR_FREEZE = "2026-07-02"    # date the priors below were frozen
PRIORS = [                     # (label, alpha, beta) — FROZEN, see docstring
    ("flat Beta(1,1) — headline", 1.0, 1.0),
    ("Jeffreys Beta(0.5,0.5)",    0.5, 0.5),
    ("skeptical Beta(10,10)",    10.0, 10.0),
]
EX_TARGET = 10.0               # gross target level (percent)
EX_FILL_NET = EX_TARGET - 2.0  # +8% net realized on a fill (2% cost haircut)


# ---------- exact Beta distribution machinery (stdlib only) ----------

def _betacf(a, b, x):
    """Continued fraction for the incomplete beta (Lentz), Numerical Recipes 6.4."""
    MAXIT, EPS, FPMIN = 300, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN: d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        dele = d * c
        h *= dele
        if abs(dele - 1.0) < EPS:
            return h
    raise RuntimeError("betacf: no convergence (a=%g b=%g x=%g)" % (a, b, x))


def beta_cdf(x, a, b):
    """Regularized incomplete beta I_x(a,b) = P(X <= x), X ~ Beta(a,b)."""
    if x <= 0.0: return 0.0
    if x >= 1.0: return 1.0
    ln_bt = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log1p(-x))
    bt = math.exp(ln_bt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def beta_ppf(q, a, b):
    """Inverse CDF by bisection (deterministic, ~1e-12)."""
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if beta_cdf(mid, a, b) < q: lo = mid
        else: hi = mid
    return 0.5 * (lo + hi)


# ---------- selftests (abort on failure; run every invocation) ----------

def selftest():
    ok = lambda c, msg: (_ for _ in ()).throw(AssertionError(msg)) if not c else None
    # reference values cross-checked against scipy.stats.beta.cdf
    refs = [
        (0.5, 2.0, 2.0, 0.5),
        (0.3, 2.0, 5.0, 0.579825),
        (0.9, 10.0, 2.0, 0.6973568802),
        (0.615, 83.0, 69.0, 0.957541116197),   # ~real-log magnitudes
    ]
    for x, a, b, want in refs:
        got = beta_cdf(x, a, b)
        ok(abs(got - want) < 1e-6, "beta_cdf(%g,%g,%g)=%.9f want %.9f" % (x, a, b, got, want))
    # symmetry identity I_x(a,b) = 1 - I_{1-x}(b,a)
    for (x, a, b) in [(0.2, 3.0, 7.0), (0.77, 12.5, 4.0)]:
        ok(abs(beta_cdf(x, a, b) - (1.0 - beta_cdf(1.0 - x, b, a))) < 1e-12, "symmetry")
    # ppf/cdf roundtrip
    for q in (0.05, 0.5, 0.95):
        ok(abs(beta_cdf(beta_ppf(q, 83.0, 69.0), 83.0, 69.0) - q) < 1e-9, "roundtrip")
    # posterior arithmetic on synthetic data: 7 hits / 10, flat prior
    ok(abs((1.0 + 7) / (2.0 + 10) - 0.6666666667) < 1e-9, "posterior mean arithmetic")
    print("selftest PASS")


# ---------- data loading (mirrors weekly_report.py §4d) ----------

def _read(path):
    if not os.path.exists(path): return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _f(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def load_evaluable():
    """[(trading_date, graded_at, hit, c5, c0)] for every evaluable graded pick."""
    picks = {p["pick_id"]: p for p in _read(os.path.join(HERE, "picks.csv"))}
    rows = []
    for o in _read(os.path.join(HERE, "outcomes.csv")):
        p = picks.get(o.get("pick_id"))
        if not p: continue
        c0, mfe, c5 = _f(o.get("ret_open_close_net")), _f(o.get("mfe_5d")), _f(o.get("ret_open_5dclose_net"))
        if c0 is None or mfe is None or c5 is None: continue
        rows.append((p.get("trading_date", ""), o.get("graded_at", ""), mfe >= EX_TARGET, c5, c0))
    rows.sort(key=lambda r: (r[0], r[1]))   # chronological, same as dashboard equity curve
    return rows


# ---------- posterior summaries ----------

def window_stats(rows):
    n = len(rows)
    k = sum(1 for r in rows if r[2])
    misses = [r[3] for r in rows if not r[2]]
    m = sum(misses) / len(misses) if misses else None          # E[5d-close net | miss], plug-in
    ev_base = sum(r[4] for r in rows) / n if n else None       # mean same-day-close net, plug-in
    return n, k, m, ev_base


def breakevens(m, ev_base):
    """(p*_base, p*_zero) — None when not computable."""
    if m is None or m >= EX_FILL_NET: return None, None
    pz = (0.0 - m) / (EX_FILL_NET - m)
    pb = None if ev_base is None else (ev_base - m) / (EX_FILL_NET - m)
    return pb, pz


def summarize(rows, a0, b0):
    n, k, m, ev_base = window_stats(rows)
    a, b = a0 + k, b0 + (n - k)
    mean = a / (a + b)
    lo, hi = beta_ppf(0.05, a, b), beta_ppf(0.95, a, b)
    pb, pz = breakevens(m, ev_base)
    p_gt_base = None if pb is None else 1.0 - beta_cdf(min(max(pb, 0.0), 1.0), a, b)
    p_gt_zero = None if pz is None else 1.0 - beta_cdf(min(max(pz, 0.0), 1.0), a, b)
    return dict(n=n, k=k, mean=mean, lo=lo, hi=hi, m=m, ev_base=ev_base,
                pb=pb, pz=pz, p_gt_base=p_gt_base, p_gt_zero=p_gt_zero)


# ---------- report ----------

def fmt_p(x, d=1):
    return "—" if x is None else "%.*f%%" % (d, 100.0 * x)


def main():
    selftest()
    rows = load_evaluable()
    windows = [("all-time (in-sample context)", rows),
               ("post-%s (the honest OOS test)" % EX_REG,
                [r for r in rows if r[0] > EX_REG])]

    out = []
    w = out.append
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    w("# Bayesian read-out — H-EX1 +10% touch rate")
    w("")
    w("_Generated %s by `bayes_h_ex1.py` (selftest passed). Priors frozen %s — see the"
      % (now, PRIOR_FREEZE))
    w("script docstring. This is a read-out, **not** the registered pass/fail judge —")
    w("that remains `reports/LATEST.md` §4d. Slippage caveat (HYPOTHESES.md H-EX1) applies._")
    w("")
    w("**The question:** what fraction p of picks touch +10% intraday within the 5-day")
    w("hold? H-EX1 realizes +8% net on a touch, else the 5-day close (avg shown below as")
    w("_m_). The posterior on p updates with every graded pick; the breakeven columns")
    w("translate p into economics via plug-in estimates (their own noise is *not*")
    w("propagated — roadmap R3).")
    w("")
    for label, wrows in windows:
        n, k, m, ev_base = window_stats(wrows)
        pb, pz = breakevens(m, ev_base)
        w("## %s" % label)
        w("")
        if n == 0:
            w("_No evaluable graded picks in this window yet — fills in as post-%s picks grade._" % EX_REG)
            w("")
            continue
        w("n = **%d** evaluable graded picks, hits (mfe_5d ≥ %g) = **%d** (%.1f%%). Plug-ins:"
          % (n, EX_TARGET, k, 100.0 * k / n))
        w("m (mean 5d-close net of misses) = **%s**, baseline EV (same-day close) = **%s**."
          % ("%.2f%%" % m if m is not None else "—",
             "%.2f%%" % ev_base if ev_base is not None else "—"))
        w("Breakeven touch rates: beat-baseline p\\* = **%s** · absolute-profit p\\* = **%s**."
          % (fmt_p(pb), fmt_p(pz)))
        w("")
        w("| prior | posterior mean | 90% credible interval | P(p > beat-baseline p\\*) | P(p > absolute p\\*) |")
        w("|---|---|---|---|---|")
        for plabel, a0, b0 in PRIORS:
            s = summarize(wrows, a0, b0)
            w("| %s | %s | %s – %s | %s | %s |"
              % (plabel, fmt_p(s["mean"]), fmt_p(s["lo"]), fmt_p(s["hi"]),
                 fmt_p(s["p_gt_base"]), fmt_p(s["p_gt_zero"])))
        w("")
    w("**How to read it.** P(p > p\\*) near 50% = the log genuinely doesn't know yet;")
    w("near 0% or 100% = the log is speaking. If the three priors disagree materially,")
    w("the sample is still doing less work than the prior — wait. The all-time window")
    w("includes the in-sample picks that *suggested* H-EX1, so it flatters the rule;")
    w("judge on the post-registration window as it grows.")
    w("")
    w("**Verify by hand:** flat-prior posterior mean = (1+hits)/(2+n) from the committed")
    w("`outcomes.csv`; intervals/probabilities are Beta(1+hits, 1+n−hits) quantiles/tails")
    w("(scipy `beta.ppf`/`beta.cdf`, or any stats package). The dashboard recomputes all")
    w("of this independently in the browser from the same CSVs (parity-tested).")
    w("")

    text = "\n".join(out)
    os.makedirs(os.path.join(HERE, "reports"), exist_ok=True)
    dest = os.path.join(HERE, "reports", "bayes-h-ex1-LATEST.md")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote %s" % os.path.relpath(dest, HERE))
    # stdout summary (flat prior, OOS window)
    oos = [r for r in rows if r[0] > EX_REG]
    s = summarize(oos, 1.0, 1.0)
    if s["n"]:
        print("OOS flat-prior: n=%d k=%d mean=%s CrI %s–%s P(beat-baseline)=%s P(profitable)=%s"
              % (s["n"], s["k"], fmt_p(s["mean"]), fmt_p(s["lo"]), fmt_p(s["hi"]),
                 fmt_p(s["p_gt_base"]), fmt_p(s["p_gt_zero"])))
    else:
        print("OOS window empty so far.")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
