# Bayesian read-out — H-EX1 +10% touch rate

_Generated 2026-10-31 18:15Z by `bayes_h_ex1.py` (selftest passed). Priors frozen 2026-07-02 — see the
script docstring. This is a read-out, **not** the registered pass/fail judge —
that remains `reports/LATEST.md` §4d. Slippage caveat (HYPOTHESES.md H-EX1) applies._

**The question:** what fraction p of picks touch +10% intraday within the 5-day
hold? H-EX1 realizes +8% net on a touch, else the 5-day close (avg shown below as
_m_). The posterior on p updates with every graded pick; the breakeven columns
translate p into economics via plug-in estimates (their own noise is *not*
propagated — roadmap R3).

## all-time (in-sample context)

n = **1042** evaluable graded picks, hits (mfe_5d ≥ 10) = **490** (47.0%). Plug-ins:
m (mean 5d-close net of misses) = **-14.82%**, baseline EV (same-day close) = **-1.84%**.
Breakeven touch rates: beat-baseline p\* = **56.9%** · absolute-profit p\* = **64.9%**.

| prior | posterior mean | 90% credible interval | P(p > beat-baseline p\*) | P(p > absolute p\*) |
|---|---|---|---|---|
| flat Beta(1,1) — headline | 47.0% | 44.5% – 49.6% | 0.0% | 0.0% |
| Jeffreys Beta(0.5,0.5) | 47.0% | 44.5% – 49.6% | 0.0% | 0.0% |
| skeptical Beta(10,10) | 47.1% | 44.6% – 49.6% | 0.0% | 0.0% |

## post-2026-06-23 (the honest OOS test)

n = **920** evaluable graded picks, hits (mfe_5d ≥ 10) = **419** (45.5%). Plug-ins:
m (mean 5d-close net of misses) = **-14.17%**, baseline EV (same-day close) = **-1.74%**.
Breakeven touch rates: beat-baseline p\* = **56.1%** · absolute-profit p\* = **63.9%**.

| prior | posterior mean | 90% credible interval | P(p > beat-baseline p\*) | P(p > absolute p\*) |
|---|---|---|---|---|
| flat Beta(1,1) — headline | 45.6% | 42.9% – 48.3% | 0.0% | 0.0% |
| Jeffreys Beta(0.5,0.5) | 45.5% | 42.9% – 48.3% | 0.0% | 0.0% |
| skeptical Beta(10,10) | 45.6% | 43.0% – 48.3% | 0.0% | 0.0% |

**How to read it.** P(p > p\*) near 50% = the log genuinely doesn't know yet;
near 0% or 100% = the log is speaking. If the three priors disagree materially,
the sample is still doing less work than the prior — wait. The all-time window
includes the in-sample picks that *suggested* H-EX1, so it flatters the rule;
judge on the post-registration window as it grows.

**Verify by hand:** flat-prior posterior mean = (1+hits)/(2+n) from the committed
`outcomes.csv`; intervals/probabilities are Beta(1+hits, 1+n−hits) quantiles/tails
(scipy `beta.ppf`/`beta.cdf`, or any stats package). The dashboard recomputes all
of this independently in the browser from the same CSVs (parity-tested).
