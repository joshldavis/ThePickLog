# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-11-05

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W45**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 650

- score -> |MAE| (drawdown depth): rho=+0.225 CI[+0.090,+0.344] n=650 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.323 CI[+0.184,+0.441] n=650 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.035 CI[-0.147,+0.057] n=650 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.110 CI[-0.232,+0.001] n=650 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **13** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 533

- score -> |MAE| (drawdown depth): rho=+0.233 CI[+0.151,+0.309] n=533 tickers=374 SIG
- score -> range (MFE-MAE): rho=+0.289 CI[+0.204,+0.369] n=533 tickers=374 SIG
- score -> same-day return *(must stay ns)*: rho=+0.040 CI[-0.048,+0.125] n=533 tickers=374 ns
- score -> 5-day return *(must stay ns)*: rho=-0.209 CI[-0.290,-0.130] n=533 tickers=374 SIG
- consecutive weekly snapshots with positive |MAE| rho: **13** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.209), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1945** vs no-skill baseline **0.2025** -> BEATS baseline
- realised P(MAE <= -20%): Q1 18.4% vs Q5 53.0%
- Q5-Q1 gap: 34.6% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 18.4% · predicted 20.2% · n=136
  - Q2: realised 17.8% · predicted 39.6% · n=118
  - Q3: realised 20.6% · predicted 34.9% · n=141
  - Q4: realised 25.8% · predicted 38.2% · n=155
  - Q5: realised 53.0% · predicted 48.3% · n=100

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
