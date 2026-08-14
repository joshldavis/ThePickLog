# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-08-14

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W33**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 75

- score -> |MAE| (drawdown depth): rho=+0.108 CI[-0.159,+0.326] n=75 tickers=15 ns
- score -> range (MFE-MAE): rho=+0.154 CI[-0.103,+0.354] n=75 tickers=15 ns
- score -> same-day return *(must stay ns)*: rho=-0.118 CI[-0.381,+0.169] n=75 tickers=15 ns
- score -> 5-day return *(must stay ns)*: rho=-0.032 CI[-0.253,+0.248] n=75 tickers=15 ns
- consecutive weekly snapshots with positive |MAE| rho: **1** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 59

- score -> |MAE| (drawdown depth): rho=+0.109 CI[-0.124,+0.341] n=59 tickers=56 ns
- score -> range (MFE-MAE): rho=+0.276 CI[+0.003,+0.529] n=59 tickers=56 SIG
- score -> same-day return *(must stay ns)*: rho=+0.052 CI[-0.228,+0.342] n=59 tickers=56 ns
- score -> 5-day return *(must stay ns)*: rho=-0.054 CI[-0.311,+0.221] n=59 tickers=56 ns
- consecutive weekly snapshots with positive |MAE| rho: **1** (need >= 3)

**v0.3-yf verdict: not yet established**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1959** vs no-skill baseline **0.1901** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 26.3% vs Q5 30.0%
- Q5-Q1 gap: 3.7% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 26.3% · predicted 20.2% · n=19
  - Q2: realised 11.1% · predicted 39.6% · n=9
  - Q3: realised 20.0% · predicted 34.9% · n=15
  - Q4: realised 18.2% · predicted 38.2% · n=22
  - Q5: realised 30.0% · predicted 48.3% · n=10

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
