# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-08-21

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W34**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 138

- score -> |MAE| (drawdown depth): rho=+0.031 CI[-0.107,+0.168] n=138 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.145 CI[-0.017,+0.285] n=138 tickers=16 ns
- score -> same-day return *(must stay ns)*: rho=-0.090 CI[-0.249,+0.076] n=138 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.083 CI[-0.089,+0.223] n=138 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **2** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 100

- score -> |MAE| (drawdown depth): rho=+0.181 CI[-0.015,+0.368] n=100 tickers=93 ns
- score -> range (MFE-MAE): rho=+0.262 CI[+0.043,+0.453] n=100 tickers=93 SIG
- score -> same-day return *(must stay ns)*: rho=+0.126 CI[-0.104,+0.336] n=100 tickers=93 ns
- score -> 5-day return *(must stay ns)*: rho=-0.124 CI[-0.329,+0.084] n=100 tickers=93 ns
- consecutive weekly snapshots with positive |MAE| rho: **2** (need >= 3)

**v0.3-yf verdict: not yet established**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1840** vs no-skill baseline **0.1793** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 22.6% vs Q5 20.0%
- Q5-Q1 gap: -2.6% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 22.6% · predicted 20.2% · n=31
  - Q2: realised 23.8% · predicted 39.6% · n=21
  - Q3: realised 13.3% · predicted 34.9% · n=30
  - Q4: realised 12.2% · predicted 38.2% · n=41
  - Q5: realised 20.0% · predicted 48.3% · n=15

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
