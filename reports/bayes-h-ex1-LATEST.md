# Bayesian read-out — H-EX1 +10% touch rate

_Generated 2026-08-08 14:32Z by `bayes_h_ex1.py` (selftest passed). Priors frozen 2026-07-02 — see the
script docstring. This is a read-out, **not** the registered pass/fail judge —
that remains `reports/LATEST.md` §4d. Slippage caveat (HYPOTHESES.md H-EX1) applies._

**The question:** what fraction p of picks touch +10% intraday within the 5-day
hold? H-EX1 realizes +8% net on a touch, else the 5-day close (avg shown below as
_m_). The posterior on p updates with every graded pick; the breakeven columns
translate p into economics via plug-in estimates (their own noise is *not*
propagated — roadmap R3).

## all-time (in-sample context)

n = **452** evaluable graded picks, hits (mfe_5d ≥ 10) = **207** (45.8%). Plug-ins:
m (mean 5d-close net of misses) = **-15.93%**, baseline EV (same-day close) = **-3.19%**.
Breakeven touch rates: beat-baseline p\* = **53.2%** · absolute-profit p\* = **66.6%**.

| prior | posterior mean | 90% credible interval | P(p > beat-baseline p\*) | P(p > absolute p\*) |
|---|---|---|---|---|
| flat Beta(1,1) — headline | 45.8% | 42.0% – 49.7% | 0.1% | 0.0% |
| Jeffreys Beta(0.5,0.5) | 45.8% | 42.0% – 49.7% | 0.1% | 0.0% |
| skeptical Beta(10,10) | 46.0% | 42.2% – 49.8% | 0.1% | 0.0% |

## post-2026-06-23 (the honest OOS test)

n = **330** evaluable graded picks, hits (mfe_5d ≥ 10) = **136** (41.2%). Plug-ins:
m (mean 5d-close net of misses) = **-14.55%**, baseline EV (same-day close) = **-3.40%**.
Breakeven touch rates: beat-baseline p\* = **49.5%** · absolute-profit p\* = **64.5%**.

| prior | posterior mean | 90% credible interval | P(p > beat-baseline p\*) | P(p > absolute p\*) |
|---|---|---|---|---|
| flat Beta(1,1) — headline | 41.3% | 36.9% – 45.7% | 0.1% | 0.0% |
| Jeffreys Beta(0.5,0.5) | 41.2% | 36.8% – 45.7% | 0.1% | 0.0% |
| skeptical Beta(10,10) | 41.7% | 37.4% – 46.1% | 0.2% | 0.0% |

**How to read it.** P(p > p\*) near 50% = the log genuinely doesn't know yet;
near 0% or 100% = the log is speaking. If the three priors disagree materially,
the sample is still doing less work than the prior — wait. The all-time window
includes the in-sample picks that *suggested* H-EX1, so it flatters the rule;
judge on the post-registration window as it grows.

**Verify by hand:** flat-prior posterior mean = (1+hits)/(2+n) from the committed
`outcomes.csv`; intervals/probabilities are Beta(1+hits, 1+n−hits) quantiles/tails
(scipy `beta.ppf`/`beta.cdf`, or any stats package). The dashboard recomputes all
of this independently in the browser from the same CSVs (parity-tested).
