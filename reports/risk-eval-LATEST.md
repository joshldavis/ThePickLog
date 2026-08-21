# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-08-21

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W34**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 153

- score -> |MAE| (drawdown depth): rho=+0.007 CI[-0.140,+0.146] n=153 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.179 CI[+0.023,+0.302] n=153 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.030 CI[-0.196,+0.135] n=153 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.112 CI[-0.055,+0.254] n=153 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **2** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 110

- score -> |MAE| (drawdown depth): rho=+0.191 CI[+0.009,+0.369] n=110 tickers=101 SIG
- score -> range (MFE-MAE): rho=+0.271 CI[+0.066,+0.452] n=110 tickers=101 SIG
- score -> same-day return *(must stay ns)*: rho=+0.142 CI[-0.062,+0.342] n=110 tickers=101 ns
- score -> 5-day return *(must stay ns)*: rho=-0.137 CI[-0.327,+0.057] n=110 tickers=101 ns
- consecutive weekly snapshots with positive |MAE| rho: **2** (need >= 3)

**v0.3-yf verdict: not yet established**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1843** vs no-skill baseline **0.1818** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 21.6% vs Q5 23.5%
- Q5-Q1 gap: 1.9% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 21.6% · predicted 20.2% · n=37
  - Q2: realised 26.1% · predicted 39.6% · n=23
  - Q3: realised 12.9% · predicted 34.9% · n=31
  - Q4: realised 13.3% · predicted 38.2% · n=45
  - Q5: realised 23.5% · predicted 48.3% · n=17

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
