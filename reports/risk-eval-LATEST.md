# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-08-28

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W35**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 206

- score -> |MAE| (drawdown depth): rho=-0.008 CI[-0.149,+0.127] n=206 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.219 CI[+0.071,+0.325] n=206 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=+0.019 CI[-0.120,+0.158] n=206 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.105 CI[-0.043,+0.234] n=206 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **3** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 150

- score -> |MAE| (drawdown depth): rho=+0.252 CI[+0.089,+0.403] n=150 tickers=132 SIG
- score -> range (MFE-MAE): rho=+0.328 CI[+0.159,+0.479] n=150 tickers=132 SIG
- score -> same-day return *(must stay ns)*: rho=+0.090 CI[-0.084,+0.260] n=150 tickers=132 ns
- score -> 5-day return *(must stay ns)*: rho=-0.196 CI[-0.363,-0.019] n=150 tickers=132 SIG
- consecutive weekly snapshots with positive |MAE| rho: **3** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1846** vs no-skill baseline **0.1822** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 21.3% vs Q5 26.1%
- Q5-Q1 gap: 4.8% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 21.3% · predicted 20.2% · n=47
  - Q2: realised 21.1% · predicted 39.6% · n=38
  - Q3: realised 14.0% · predicted 34.9% · n=43
  - Q4: realised 14.5% · predicted 38.2% · n=55
  - Q5: realised 26.1% · predicted 48.3% · n=23

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
