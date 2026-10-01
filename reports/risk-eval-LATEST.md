# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-10-01

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W40**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 388

- score -> |MAE| (drawdown depth): rho=+0.091 CI[-0.040,+0.231] n=388 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.262 CI[+0.126,+0.389] n=388 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.031 CI[-0.133,+0.053] n=388 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.112 CI[-0.051,+0.239] n=388 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **8** (need >= 3)

**v0.2-yf verdict: not yet established** — score -> |MAE| is not positive and significant

### v0.3-yf — n_post = 305

- score -> |MAE| (drawdown depth): rho=+0.290 CI[+0.179,+0.394] n=305 tickers=245 SIG
- score -> range (MFE-MAE): rho=+0.339 CI[+0.234,+0.441] n=305 tickers=245 SIG
- score -> same-day return *(must stay ns)*: rho=+0.048 CI[-0.060,+0.162] n=305 tickers=245 ns
- score -> 5-day return *(must stay ns)*: rho=-0.190 CI[-0.302,-0.070] n=305 tickers=245 SIG
- consecutive weekly snapshots with positive |MAE| rho: **8** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.190), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1886** vs no-skill baseline **0.1896** -> BEATS baseline
- realised P(MAE <= -20%): Q1 23.1% vs Q5 42.9%
- Q5-Q1 gap: 19.8% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 23.1% · predicted 20.2% · n=91
  - Q2: realised 18.9% · predicted 39.6% · n=74
  - Q3: realised 13.6% · predicted 34.9% · n=81
  - Q4: realised 16.1% · predicted 38.2% · n=93
  - Q5: realised 42.9% · predicted 48.3% · n=49

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
