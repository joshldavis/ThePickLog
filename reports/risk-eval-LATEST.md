# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-10-28

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W44**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 584

- score -> |MAE| (drawdown depth): rho=+0.225 CI[+0.086,+0.348] n=584 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.335 CI[+0.187,+0.460] n=584 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.051 CI[-0.153,+0.043] n=584 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.089 CI[-0.222,+0.023] n=584 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **12** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 473

- score -> |MAE| (drawdown depth): rho=+0.242 CI[+0.159,+0.328] n=473 tickers=344 SIG
- score -> range (MFE-MAE): rho=+0.302 CI[+0.215,+0.383] n=473 tickers=344 SIG
- score -> same-day return *(must stay ns)*: rho=+0.030 CI[-0.067,+0.118] n=473 tickers=344 ns
- score -> 5-day return *(must stay ns)*: rho=-0.212 CI[-0.299,-0.128] n=473 tickers=344 SIG
- consecutive weekly snapshots with positive |MAE| rho: **12** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.212), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1915** vs no-skill baseline **0.1997** -> BEATS baseline
- realised P(MAE <= -20%): Q1 18.0% vs Q5 52.2%
- Q5-Q1 gap: 34.1% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 18.0% · predicted 20.2% · n=122
  - Q2: realised 18.9% · predicted 39.6% · n=106
  - Q3: realised 17.5% · predicted 34.9% · n=126
  - Q4: realised 23.9% · predicted 38.2% · n=138
  - Q5: realised 52.2% · predicted 48.3% · n=92

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
