# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-11-03

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W45**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 628

- score -> |MAE| (drawdown depth): rho=+0.228 CI[+0.095,+0.343] n=628 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.333 CI[+0.191,+0.450] n=628 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.044 CI[-0.149,+0.052] n=628 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.110 CI[-0.229,-0.002] n=628 tickers=16 SIG
- consecutive weekly snapshots with positive |MAE| rho: **13** (need >= 3)

**v0.2-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.110), so the score also carries DIRECTION information; that fails H-RISK1 as registered

### v0.3-yf — n_post = 513

- score -> |MAE| (drawdown depth): rho=+0.228 CI[+0.144,+0.312] n=513 tickers=363 SIG
- score -> range (MFE-MAE): rho=+0.288 CI[+0.201,+0.366] n=513 tickers=363 SIG
- score -> same-day return *(must stay ns)*: rho=+0.038 CI[-0.054,+0.124] n=513 tickers=363 ns
- score -> 5-day return *(must stay ns)*: rho=-0.212 CI[-0.296,-0.125] n=513 tickers=363 SIG
- consecutive weekly snapshots with positive |MAE| rho: **13** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.212), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1924** vs no-skill baseline **0.2011** -> BEATS baseline
- realised P(MAE <= -20%): Q1 17.4% vs Q5 52.6%
- Q5-Q1 gap: 35.2% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 17.4% · predicted 20.2% · n=132
  - Q2: realised 18.1% · predicted 39.6% · n=116
  - Q3: realised 19.3% · predicted 34.9% · n=135
  - Q4: realised 25.7% · predicted 38.2% · n=148
  - Q5: realised 52.6% · predicted 48.3% · n=97

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
