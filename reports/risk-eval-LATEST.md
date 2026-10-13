# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-10-13

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W42**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 473

- score -> |MAE| (drawdown depth): rho=+0.184 CI[+0.042,+0.315] n=473 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.333 CI[+0.173,+0.474] n=473 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.044 CI[-0.164,+0.064] n=473 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.008 CI[-0.144,+0.102] n=473 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **10** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 373

- score -> |MAE| (drawdown depth): rho=+0.287 CI[+0.191,+0.379] n=373 tickers=290 SIG
- score -> range (MFE-MAE): rho=+0.321 CI[+0.220,+0.415] n=373 tickers=290 SIG
- score -> same-day return *(must stay ns)*: rho=+0.065 CI[-0.036,+0.165] n=373 tickers=290 ns
- score -> 5-day return *(must stay ns)*: rho=-0.240 CI[-0.339,-0.138] n=373 tickers=290 SIG
- consecutive weekly snapshots with positive |MAE| rho: **10** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.240), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1876** vs no-skill baseline **0.1931** -> BEATS baseline
- realised P(MAE <= -20%): Q1 19.8% vs Q5 48.6%
- Q5-Q1 gap: 28.8% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 19.8% · predicted 20.2% · n=111
  - Q2: realised 17.2% · predicted 39.6% · n=87
  - Q3: realised 16.5% · predicted 34.9% · n=97
  - Q4: realised 17.6% · predicted 38.2% · n=108
  - Q5: realised 48.6% · predicted 48.3% · n=70

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
