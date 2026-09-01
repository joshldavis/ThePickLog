# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-09-01

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W36**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 232

- score -> |MAE| (drawdown depth): rho=+0.032 CI[-0.116,+0.180] n=232 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.232 CI[+0.088,+0.328] n=232 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.013 CI[-0.143,+0.107] n=232 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.085 CI[-0.077,+0.221] n=232 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **4** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 167

- score -> |MAE| (drawdown depth): rho=+0.253 CI[+0.102,+0.395] n=167 tickers=145 SIG
- score -> range (MFE-MAE): rho=+0.329 CI[+0.170,+0.475] n=167 tickers=145 SIG
- score -> same-day return *(must stay ns)*: rho=+0.086 CI[-0.077,+0.247] n=167 tickers=145 ns
- score -> 5-day return *(must stay ns)*: rho=-0.208 CI[-0.362,-0.041] n=167 tickers=145 SIG
- consecutive weekly snapshots with positive |MAE| rho: **4** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1806** vs no-skill baseline **0.1800** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 19.2% vs Q5 29.6%
- Q5-Q1 gap: 10.4% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 19.2% · predicted 20.2% · n=52
  - Q2: realised 18.2% · predicted 39.6% · n=44
  - Q3: realised 14.0% · predicted 34.9% · n=50
  - Q4: realised 13.6% · predicted 38.2% · n=59
  - Q5: realised 29.6% · predicted 48.3% · n=27

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
