# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-10-23

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W43**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 562

- score -> |MAE| (drawdown depth): rho=+0.209 CI[+0.066,+0.341] n=562 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.336 CI[+0.185,+0.463] n=562 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.040 CI[-0.147,+0.053] n=562 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.071 CI[-0.210,+0.048] n=562 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **11** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 453

- score -> |MAE| (drawdown depth): rho=+0.265 CI[+0.180,+0.349] n=453 tickers=331 SIG
- score -> range (MFE-MAE): rho=+0.329 CI[+0.236,+0.411] n=453 tickers=331 SIG
- score -> same-day return *(must stay ns)*: rho=+0.029 CI[-0.071,+0.124] n=453 tickers=331 ns
- score -> 5-day return *(must stay ns)*: rho=-0.216 CI[-0.303,-0.125] n=453 tickers=331 SIG
- consecutive weekly snapshots with positive |MAE| rho: **11** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.216), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1912** vs no-skill baseline **0.1994** -> BEATS baseline
- realised P(MAE <= -20%): Q1 18.3% vs Q5 52.8%
- Q5-Q1 gap: 34.5% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 18.3% · predicted 20.2% · n=120
  - Q2: realised 18.8% · predicted 39.6% · n=101
  - Q3: realised 17.5% · predicted 34.9% · n=120
  - Q4: realised 22.7% · predicted 38.2% · n=132
  - Q5: realised 52.8% · predicted 48.3% · n=89

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
