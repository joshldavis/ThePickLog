# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-10-06

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W41**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 425

- score -> |MAE| (drawdown depth): rho=+0.130 CI[-0.010,+0.267] n=425 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.283 CI[+0.128,+0.428] n=425 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.023 CI[-0.133,+0.085] n=425 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.095 CI[-0.050,+0.208] n=425 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **9** (need >= 3)

**v0.2-yf verdict: not yet established** — score -> |MAE| is not positive and significant

### v0.3-yf — n_post = 334

- score -> |MAE| (drawdown depth): rho=+0.324 CI[+0.221,+0.422] n=334 tickers=262 SIG
- score -> range (MFE-MAE): rho=+0.350 CI[+0.249,+0.446] n=334 tickers=262 SIG
- score -> same-day return *(must stay ns)*: rho=+0.041 CI[-0.065,+0.145] n=334 tickers=262 ns
- score -> 5-day return *(must stay ns)*: rho=-0.179 CI[-0.288,-0.062] n=334 tickers=262 SIG
- consecutive weekly snapshots with positive |MAE| rho: **9** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.179), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1880** vs no-skill baseline **0.1916** -> BEATS baseline
- realised P(MAE <= -20%): Q1 21.8% vs Q5 47.5%
- Q5-Q1 gap: 25.7% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 21.8% · predicted 20.2% · n=101
  - Q2: realised 19.0% · predicted 39.6% · n=79
  - Q3: realised 13.1% · predicted 34.9% · n=84
  - Q4: realised 16.7% · predicted 38.2% · n=102
  - Q5: realised 47.5% · predicted 48.3% · n=59

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
