# Bayesian read-out — H-EX1 +10% touch rate

_Generated 2026-09-19 17:01Z by `bayes_h_ex1.py` (selftest passed). Priors frozen 2026-07-02 — see the
script docstring. This is a read-out, **not** the registered pass/fail judge —
that remains `reports/LATEST.md` §4d. Slippage caveat (HYPOTHESES.md H-EX1) applies._

**The question:** what fraction p of picks touch +10% intraday within the 5-day
hold? H-EX1 realizes +8% net on a touch, else the 5-day close (avg shown below as
_m_). The posterior on p updates with every graded pick; the breakeven columns
translate p into economics via plug-in estimates (their own noise is *not*
propagated — roadmap R3).

## all-time (in-sample context)

n = **740** evaluable graded picks, hits (mfe_5d ≥ 10) = **352** (47.6%). Plug-ins:
m (mean 5d-close net of misses) = **-14.60%**, baseline EV (same-day close) = **-2.78%**.
Breakeven touch rates: beat-baseline p\* = **52.3%** · absolute-profit p\* = **64.6%**.

| prior | posterior mean | 90% credible interval | P(p > beat-baseline p\*) | P(p > absolute p\*) |
|---|---|---|---|---|
| flat Beta(1,1) — headline | 47.6% | 44.6% – 50.6% | 0.5% | 0.0% |
| Jeffreys Beta(0.5,0.5) | 47.6% | 44.6% – 50.6% | 0.5% | 0.0% |
| skeptical Beta(10,10) | 47.6% | 44.7% – 50.6% | 0.5% | 0.0% |

## post-2026-06-23 (the honest OOS test)

n = **618** evaluable graded picks, hits (mfe_5d ≥ 10) = **281** (45.5%). Plug-ins:
m (mean 5d-close net of misses) = **-13.61%**, baseline EV (same-day close) = **-2.81%**.
Breakeven touch rates: beat-baseline p\* = **50.0%** · absolute-profit p\* = **63.0%**.

| prior | posterior mean | 90% credible interval | P(p > beat-baseline p\*) | P(p > absolute p\*) |
|---|---|---|---|---|
| flat Beta(1,1) — headline | 45.5% | 42.2% – 48.8% | 1.3% | 0.0% |
| Jeffreys Beta(0.5,0.5) | 45.5% | 42.2% – 48.8% | 1.3% | 0.0% |
| skeptical Beta(10,10) | 45.6% | 42.4% – 48.9% | 1.4% | 0.0% |

**How to read it.** P(p > p\*) near 50% = the log genuinely doesn't know yet;
near 0% or 100% = the log is speaking. If the three priors disagree materially,
the sample is still doing less work than the prior — wait. The all-time window
includes the in-sample picks that *suggested* H-EX1, so it flatters the rule;
judge on the post-registration window as it grows.

**Verify by hand:** flat-prior posterior mean = (1+hits)/(2+n) from the committed
`outcomes.csv`; intervals/probabilities are Beta(1+hits, 1+n−hits) quantiles/tails
(scipy `beta.ppf`/`beta.cdf`, or any stats package). The dashboard recomputes all
of this independently in the browser from the same CSVs (parity-tested).
