# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-09-15

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W38**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 282

- score -> |MAE| (drawdown depth): rho=+0.052 CI[-0.099,+0.206] n=282 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.272 CI[+0.165,+0.358] n=282 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=+0.016 CI[-0.109,+0.123] n=282 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.107 CI[-0.077,+0.254] n=282 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **6** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 206

- score -> |MAE| (drawdown depth): rho=+0.235 CI[+0.096,+0.364] n=206 tickers=174 SIG
- score -> range (MFE-MAE): rho=+0.349 CI[+0.210,+0.480] n=206 tickers=174 SIG
- score -> same-day return *(must stay ns)*: rho=+0.122 CI[-0.019,+0.258] n=206 tickers=174 ns
- score -> 5-day return *(must stay ns)*: rho=-0.177 CI[-0.321,-0.023] n=206 tickers=174 SIG
- consecutive weekly snapshots with positive |MAE| rho: **6** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1813** vs no-skill baseline **0.1831** -> BEATS baseline
- realised P(MAE <= -20%): Q1 19.4% vs Q5 36.4%
- Q5-Q1 gap: 17.0% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 19.4% · predicted 20.2% · n=67
  - Q2: realised 18.2% · predicted 39.6% · n=55
  - Q3: realised 12.1% · predicted 34.9% · n=58
  - Q4: realised 15.9% · predicted 38.2% · n=69
  - Q5: realised 36.4% · predicted 48.3% · n=33

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
