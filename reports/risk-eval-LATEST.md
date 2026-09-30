# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-09-30

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W40**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 378

- score -> |MAE| (drawdown depth): rho=+0.082 CI[-0.048,+0.224] n=378 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.262 CI[+0.131,+0.384] n=378 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.032 CI[-0.131,+0.050] n=378 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.106 CI[-0.059,+0.235] n=378 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **8** (need >= 3)

**v0.2-yf verdict: not yet established** — score -> |MAE| is not positive and significant

### v0.3-yf — n_post = 295

- score -> |MAE| (drawdown depth): rho=+0.284 CI[+0.171,+0.387] n=295 tickers=237 SIG
- score -> range (MFE-MAE): rho=+0.340 CI[+0.232,+0.444] n=295 tickers=237 SIG
- score -> same-day return *(must stay ns)*: rho=+0.051 CI[-0.063,+0.162] n=295 tickers=237 ns
- score -> 5-day return *(must stay ns)*: rho=-0.198 CI[-0.313,-0.077] n=295 tickers=237 SIG
- consecutive weekly snapshots with positive |MAE| rho: **8** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.198), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1894** vs no-skill baseline **0.1904** -> BEATS baseline
- realised P(MAE <= -20%): Q1 23.3% vs Q5 42.6%
- Q5-Q1 gap: 19.2% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 23.3% · predicted 20.2% · n=90
  - Q2: realised 19.4% · predicted 39.6% · n=72
  - Q3: realised 13.8% · predicted 34.9% · n=80
  - Q4: realised 16.9% · predicted 38.2% · n=89
  - Q5: realised 42.6% · predicted 48.3% · n=47

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
