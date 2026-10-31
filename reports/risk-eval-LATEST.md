# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-10-31

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W44**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 617

- score -> |MAE| (drawdown depth): rho=+0.219 CI[+0.083,+0.338] n=617 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.332 CI[+0.188,+0.451] n=617 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.042 CI[-0.151,+0.058] n=617 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.100 CI[-0.226,+0.011] n=617 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **12** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 503

- score -> |MAE| (drawdown depth): rho=+0.240 CI[+0.155,+0.322] n=503 tickers=359 SIG
- score -> range (MFE-MAE): rho=+0.294 CI[+0.206,+0.376] n=503 tickers=359 SIG
- score -> same-day return *(must stay ns)*: rho=+0.040 CI[-0.053,+0.128] n=503 tickers=359 ns
- score -> 5-day return *(must stay ns)*: rho=-0.221 CI[-0.307,-0.133] n=503 tickers=359 SIG
- consecutive weekly snapshots with positive |MAE| rho: **12** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.221), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1918** vs no-skill baseline **0.2001** -> BEATS baseline
- realised P(MAE <= -20%): Q1 17.8% vs Q5 52.6%
- Q5-Q1 gap: 34.8% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 17.8% · predicted 20.2% · n=129
  - Q2: realised 18.3% · predicted 39.6% · n=115
  - Q3: realised 18.7% · predicted 34.9% · n=134
  - Q4: realised 24.3% · predicted 38.2% · n=144
  - Q5: realised 52.6% · predicted 48.3% · n=95

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
