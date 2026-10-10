# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-10-10

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W41**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 462

- score -> |MAE| (drawdown depth): rho=+0.166 CI[+0.022,+0.303] n=462 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.317 CI[+0.152,+0.463] n=462 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.034 CI[-0.154,+0.075] n=462 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.000 CI[-0.140,+0.117] n=462 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **9** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 363

- score -> |MAE| (drawdown depth): rho=+0.297 CI[+0.201,+0.391] n=363 tickers=285 SIG
- score -> range (MFE-MAE): rho=+0.314 CI[+0.214,+0.408] n=363 tickers=285 SIG
- score -> same-day return *(must stay ns)*: rho=+0.057 CI[-0.049,+0.157] n=363 tickers=285 ns
- score -> 5-day return *(must stay ns)*: rho=-0.251 CI[-0.354,-0.145] n=363 tickers=285 SIG
- consecutive weekly snapshots with positive |MAE| rho: **9** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.251), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1893** vs no-skill baseline **0.1939** -> BEATS baseline
- realised P(MAE <= -20%): Q1 20.8% vs Q5 48.5%
- Q5-Q1 gap: 27.8% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 20.8% · predicted 20.2% · n=106
  - Q2: realised 17.6% · predicted 39.6% · n=85
  - Q3: realised 16.5% · predicted 34.9% · n=97
  - Q4: realised 17.9% · predicted 38.2% · n=106
  - Q5: realised 48.5% · predicted 48.3% · n=68

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
