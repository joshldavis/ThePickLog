# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-09-24

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W39**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 330

- score -> |MAE| (drawdown depth): rho=+0.053 CI[-0.096,+0.212] n=330 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.234 CI[+0.119,+0.343] n=330 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.003 CI[-0.118,+0.096] n=330 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.081 CI[-0.094,+0.219] n=330 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **7** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 249

- score -> |MAE| (drawdown depth): rho=+0.267 CI[+0.139,+0.383] n=249 tickers=204 SIG
- score -> range (MFE-MAE): rho=+0.351 CI[+0.225,+0.471] n=249 tickers=204 SIG
- score -> same-day return *(must stay ns)*: rho=+0.092 CI[-0.038,+0.217] n=249 tickers=204 ns
- score -> 5-day return *(must stay ns)*: rho=-0.202 CI[-0.335,-0.064] n=249 tickers=204 SIG
- consecutive weekly snapshots with positive |MAE| rho: **7** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1966** vs no-skill baseline **0.1964** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 26.6% vs Q5 46.3%
- Q5-Q1 gap: 19.8% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 26.6% · predicted 20.2% · n=79
  - Q2: realised 21.2% · predicted 39.6% · n=66
  - Q3: realised 14.7% · predicted 34.9% · n=68
  - Q4: realised 18.4% · predicted 38.2% · n=76
  - Q5: realised 46.3% · predicted 48.3% · n=41

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
