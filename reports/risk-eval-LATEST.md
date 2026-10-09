# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-10-09

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W41**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 450

- score -> |MAE| (drawdown depth): rho=+0.152 CI[+0.005,+0.295] n=450 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.309 CI[+0.150,+0.450] n=450 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.028 CI[-0.144,+0.079] n=450 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.003 CI[-0.144,+0.127] n=450 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **9** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 353

- score -> |MAE| (drawdown depth): rho=+0.307 CI[+0.208,+0.402] n=353 tickers=278 SIG
- score -> range (MFE-MAE): rho=+0.332 CI[+0.232,+0.427] n=353 tickers=278 SIG
- score -> same-day return *(must stay ns)*: rho=+0.059 CI[-0.050,+0.162] n=353 tickers=278 ns
- score -> 5-day return *(must stay ns)*: rho=-0.254 CI[-0.355,-0.148] n=353 tickers=278 SIG
- consecutive weekly snapshots with positive |MAE| rho: **9** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.254), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1891** vs no-skill baseline **0.1944** -> BEATS baseline
- realised P(MAE <= -20%): Q1 21.0% vs Q5 50.8%
- Q5-Q1 gap: 29.8% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 21.0% · predicted 20.2% · n=105
  - Q2: realised 18.1% · predicted 39.6% · n=83
  - Q3: realised 16.1% · predicted 34.9% · n=93
  - Q4: realised 17.3% · predicted 38.2% · n=104
  - Q5: realised 50.8% · predicted 48.3% · n=65

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
