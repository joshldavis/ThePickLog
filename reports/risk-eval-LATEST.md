# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-09-25

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W39**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 339

- score -> |MAE| (drawdown depth): rho=+0.048 CI[-0.104,+0.208] n=339 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.239 CI[+0.125,+0.348] n=339 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.000 CI[-0.112,+0.094] n=339 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.097 CI[-0.081,+0.238] n=339 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **7** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 261

- score -> |MAE| (drawdown depth): rho=+0.270 CI[+0.148,+0.381] n=261 tickers=212 SIG
- score -> range (MFE-MAE): rho=+0.364 CI[+0.246,+0.478] n=261 tickers=212 SIG
- score -> same-day return *(must stay ns)*: rho=+0.089 CI[-0.028,+0.207] n=261 tickers=212 ns
- score -> 5-day return *(must stay ns)*: rho=-0.188 CI[-0.312,-0.056] n=261 tickers=212 SIG
- consecutive weekly snapshots with positive |MAE| rho: **7** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1954** vs no-skill baseline **0.1947** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 26.2% vs Q5 44.2%
- Q5-Q1 gap: 17.9% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 26.2% · predicted 20.2% · n=80
  - Q2: realised 20.9% · predicted 39.6% · n=67
  - Q3: realised 14.3% · predicted 34.9% · n=70
  - Q4: realised 17.7% · predicted 38.2% · n=79
  - Q5: realised 44.2% · predicted 48.3% · n=43

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
