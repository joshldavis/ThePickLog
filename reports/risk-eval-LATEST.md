# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-09-02

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W36**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 253

- score -> |MAE| (drawdown depth): rho=+0.039 CI[-0.114,+0.203] n=253 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.243 CI[+0.114,+0.329] n=253 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=+0.006 CI[-0.111,+0.112] n=253 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.077 CI[-0.108,+0.220] n=253 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **4** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 183

- score -> |MAE| (drawdown depth): rho=+0.277 CI[+0.132,+0.417] n=183 tickers=158 SIG
- score -> range (MFE-MAE): rho=+0.349 CI[+0.201,+0.490] n=183 tickers=158 SIG
- score -> same-day return *(must stay ns)*: rho=+0.079 CI[-0.074,+0.231] n=183 tickers=158 ns
- score -> 5-day return *(must stay ns)*: rho=-0.222 CI[-0.370,-0.064] n=183 tickers=158 SIG
- consecutive weekly snapshots with positive |MAE| rho: **4** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1804** vs no-skill baseline **0.1804** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 19.6% vs Q5 33.3%
- Q5-Q1 gap: 13.7% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 19.6% · predicted 20.2% · n=56
  - Q2: realised 16.7% · predicted 39.6% · n=48
  - Q3: realised 12.7% · predicted 34.9% · n=55
  - Q4: realised 14.1% · predicted 38.2% · n=64
  - Q5: realised 33.3% · predicted 48.3% · n=30

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
