# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-08-27

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W35**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 193

- score -> |MAE| (drawdown depth): rho=-0.011 CI[-0.149,+0.119] n=193 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.213 CI[+0.068,+0.323] n=193 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.013 CI[-0.152,+0.126] n=193 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.113 CI[-0.041,+0.246] n=193 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **3** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 140

- score -> |MAE| (drawdown depth): rho=+0.241 CI[+0.074,+0.398] n=140 tickers=125 SIG
- score -> range (MFE-MAE): rho=+0.314 CI[+0.140,+0.467] n=140 tickers=125 SIG
- score -> same-day return *(must stay ns)*: rho=+0.081 CI[-0.100,+0.246] n=140 tickers=125 ns
- score -> 5-day return *(must stay ns)*: rho=-0.199 CI[-0.367,-0.021] n=140 tickers=125 SIG
- consecutive weekly snapshots with positive |MAE| rho: **3** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1870** vs no-skill baseline **0.1842** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 21.7% vs Q5 23.8%
- Q5-Q1 gap: 2.1% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 21.7% · predicted 20.2% · n=46
  - Q2: realised 22.2% · predicted 39.6% · n=36
  - Q3: realised 15.4% · predicted 34.9% · n=39
  - Q4: realised 15.7% · predicted 38.2% · n=51
  - Q5: realised 23.8% · predicted 48.3% · n=21

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
