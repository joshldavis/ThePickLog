# Bayesian read-out — H-EX1 +10% touch rate

_Generated 2026-07-04 14:33Z by `bayes_h_ex1.py` (selftest passed). Priors frozen 2026-07-02 — see the
script docstring. This is a read-out, **not** the registered pass/fail judge —
that remains `reports/LATEST.md` §4d. Slippage caveat (HYPOTHESES.md H-EX1) applies._

**The question:** what fraction p of picks touch +10% intraday within the 5-day
hold? H-EX1 realizes +8% net on a touch, else the 5-day close (avg shown below as
_m_). The posterior on p updates with every graded pick; the breakeven columns
translate p into economics via plug-in estimates (their own noise is *not*
propagated — roadmap R3).

## all-time (in-sample context)

n = **165** evaluable graded picks, hits (mfe_5d ≥ 10) = **91** (55.2%). Plug-ins:
m (mean 5d-close net of misses) = **-19.29%**, baseline EV (same-day close) = **-3.04%**.
Breakeven touch rates: beat-baseline p\* = **59.5%** · absolute-profit p\* = **70.7%**.

| prior | posterior mean | 90% credible interval | P(p > beat-baseline p\*) | P(p > absolute p\*) |
|---|---|---|---|---|
| flat Beta(1,1) — headline | 55.1% | 48.7% – 61.4% | 12.3% | 0.0% |
| Jeffreys Beta(0.5,0.5) | 55.1% | 48.8% – 61.4% | 12.5% | 0.0% |
| skeptical Beta(10,10) | 54.6% | 48.6% – 60.6% | 8.7% | 0.0% |

## post-2026-06-23 (the honest OOS test)

n = **30** evaluable graded picks, hits (mfe_5d ≥ 10) = **15** (50.0%). Plug-ins:
m (mean 5d-close net of misses) = **-12.80%**, baseline EV (same-day close) = **-4.13%**.
Breakeven touch rates: beat-baseline p\* = **41.7%** · absolute-profit p\* = **61.5%**.

| prior | posterior mean | 90% credible interval | P(p > beat-baseline p\*) | P(p > absolute p\*) |
|---|---|---|---|---|
| flat Beta(1,1) — headline | 50.0% | 35.7% – 64.3% | 82.6% | 9.5% |
| Jeffreys Beta(0.5,0.5) | 50.0% | 35.4% – 64.6% | 82.2% | 9.8% |
| skeptical Beta(10,10) | 50.0% | 38.5% – 61.5% | 88.0% | 5.0% |

**How to read it.** P(p > p\*) near 50% = the log genuinely doesn't know yet;
near 0% or 100% = the log is speaking. If the three priors disagree materially,
the sample is still doing less work than the prior — wait. The all-time window
includes the in-sample picks that *suggested* H-EX1, so it flatters the rule;
judge on the post-registration window as it grows.

**Verify by hand:** flat-prior posterior mean = (1+hits)/(2+n) from the committed
`outcomes.csv`; intervals/probabilities are Beta(1+hits, 1+n−hits) quantiles/tails
(scipy `beta.ppf`/`beta.cdf`, or any stats package). The dashboard recomputes all
of this independently in the browser from the same CSVs (parity-tested).
