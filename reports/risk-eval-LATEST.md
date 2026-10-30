# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-10-30

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W44**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 606

- score -> |MAE| (drawdown depth): rho=+0.224 CI[+0.090,+0.344] n=606 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.332 CI[+0.189,+0.452] n=606 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.050 CI[-0.156,+0.049] n=606 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.097 CI[-0.224,+0.011] n=606 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **12** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 493

- score -> |MAE| (drawdown depth): rho=+0.240 CI[+0.155,+0.325] n=493 tickers=353 SIG
- score -> range (MFE-MAE): rho=+0.292 CI[+0.203,+0.374] n=493 tickers=353 SIG
- score -> same-day return *(must stay ns)*: rho=+0.031 CI[-0.064,+0.120] n=493 tickers=353 ns
- score -> 5-day return *(must stay ns)*: rho=-0.220 CI[-0.308,-0.132] n=493 tickers=353 SIG
- consecutive weekly snapshots with positive |MAE| rho: **12** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.220), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1913** vs no-skill baseline **0.2000** -> BEATS baseline
- realised P(MAE <= -20%): Q1 17.5% vs Q5 53.2%
- Q5-Q1 gap: 35.7% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 17.5% · predicted 20.2% · n=126
  - Q2: realised 18.4% · predicted 39.6% · n=114
  - Q3: realised 18.5% · predicted 34.9% · n=130
  - Q4: realised 23.9% · predicted 38.2% · n=142
  - Q5: realised 53.2% · predicted 48.3% · n=94

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
