# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-08-12

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W33**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 40

- score -> |MAE| (drawdown depth): rho=+0.024 CI[-0.362,+0.356] n=40 tickers=14 ns
- score -> range (MFE-MAE): rho=+0.232 CI[-0.140,+0.512] n=40 tickers=14 ns
- score -> same-day return *(must stay ns)*: rho=-0.093 CI[-0.456,+0.293] n=40 tickers=14 ns
- score -> 5-day return *(must stay ns)*: rho=+0.106 CI[-0.217,+0.458] n=40 tickers=14 ns
- consecutive weekly snapshots with positive |MAE| rho: **1** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 30

- score -> |MAE| (drawdown depth): rho=+0.103 CI[-0.279,+0.487] n=30 tickers=29 ns
- score -> range (MFE-MAE): rho=+0.294 CI[-0.090,+0.649] n=30 tickers=29 ns
- score -> same-day return *(must stay ns)*: rho=-0.066 CI[-0.455,+0.396] n=30 tickers=29 ns
- score -> 5-day return *(must stay ns)*: rho=-0.039 CI[-0.439,+0.371] n=30 tickers=29 ns
- consecutive weekly snapshots with positive |MAE| rho: **1** (need >= 3)

**v0.3-yf verdict: not yet established**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1945** vs no-skill baseline **0.1864** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 30.0% vs Q5 33.3%
- Q5-Q1 gap: 3.3% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 30.0% · predicted 20.2% · n=10
  - Q2: realised 14.3% · predicted 39.6% · n=7
  - Q3: realised 16.7% · predicted 34.9% · n=6
  - Q4: realised 14.3% · predicted 38.2% · n=14
  - Q5: realised 33.3% · predicted 48.3% · n=3

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
