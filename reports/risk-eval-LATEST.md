# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-09-18

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W38**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 304

- score -> |MAE| (drawdown depth): rho=+0.040 CI[-0.101,+0.190] n=304 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.239 CI[+0.129,+0.339] n=304 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=+0.016 CI[-0.098,+0.114] n=304 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.108 CI[-0.066,+0.251] n=304 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **6** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 225

- score -> |MAE| (drawdown depth): rho=+0.261 CI[+0.125,+0.386] n=225 tickers=188 SIG
- score -> range (MFE-MAE): rho=+0.339 CI[+0.207,+0.465] n=225 tickers=188 SIG
- score -> same-day return *(must stay ns)*: rho=+0.098 CI[-0.040,+0.229] n=225 tickers=188 ns
- score -> 5-day return *(must stay ns)*: rho=-0.197 CI[-0.335,-0.052] n=225 tickers=188 SIG
- consecutive weekly snapshots with positive |MAE| rho: **6** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1908** vs no-skill baseline **0.1902** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 24.7% vs Q5 41.7%
- Q5-Q1 gap: 17.0% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 24.7% · predicted 20.2% · n=73
  - Q2: realised 19.4% · predicted 39.6% · n=62
  - Q3: realised 13.1% · predicted 34.9% · n=61
  - Q4: realised 16.7% · predicted 38.2% · n=72
  - Q5: realised 41.7% · predicted 48.3% · n=36

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
