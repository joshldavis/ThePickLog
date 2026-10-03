# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-10-03

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W40**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 412

- score -> |MAE| (drawdown depth): rho=+0.123 CI[-0.016,+0.271] n=412 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.283 CI[+0.126,+0.427] n=412 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.024 CI[-0.130,+0.073] n=412 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.117 CI[-0.029,+0.236] n=412 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **8** (need >= 3)

**v0.2-yf verdict: not yet established** — score -> |MAE| is not positive and significant

### v0.3-yf — n_post = 325

- score -> |MAE| (drawdown depth): rho=+0.311 CI[+0.202,+0.413] n=325 tickers=259 SIG
- score -> range (MFE-MAE): rho=+0.348 CI[+0.242,+0.445] n=325 tickers=259 SIG
- score -> same-day return *(must stay ns)*: rho=+0.040 CI[-0.068,+0.150] n=325 tickers=259 ns
- score -> 5-day return *(must stay ns)*: rho=-0.156 CI[-0.270,-0.037] n=325 tickers=259 SIG
- consecutive weekly snapshots with positive |MAE| rho: **8** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.156), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1876** vs no-skill baseline **0.1902** -> BEATS baseline
- realised P(MAE <= -20%): Q1 21.6% vs Q5 44.6%
- Q5-Q1 gap: 23.0% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 21.6% · predicted 20.2% · n=97
  - Q2: realised 18.2% · predicted 39.6% · n=77
  - Q3: realised 13.6% · predicted 34.9% · n=81
  - Q4: realised 16.8% · predicted 38.2% · n=101
  - Q5: realised 44.6% · predicted 48.3% · n=56

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
