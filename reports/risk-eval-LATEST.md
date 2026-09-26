# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-09-26

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W39**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 356

- score -> |MAE| (drawdown depth): rho=+0.050 CI[-0.101,+0.211] n=356 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.242 CI[+0.121,+0.362] n=356 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.004 CI[-0.114,+0.087] n=356 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.107 CI[-0.065,+0.237] n=356 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **7** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 275

- score -> |MAE| (drawdown depth): rho=+0.274 CI[+0.160,+0.383] n=275 tickers=223 SIG
- score -> range (MFE-MAE): rho=+0.346 CI[+0.231,+0.457] n=275 tickers=223 SIG
- score -> same-day return *(must stay ns)*: rho=+0.058 CI[-0.064,+0.173] n=275 tickers=223 ns
- score -> 5-day return *(must stay ns)*: rho=-0.199 CI[-0.319,-0.068] n=275 tickers=223 SIG
- consecutive weekly snapshots with positive |MAE| rho: **7** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1930** vs no-skill baseline **0.1925** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 25.3% vs Q5 42.2%
- Q5-Q1 gap: 16.9% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 25.3% · predicted 20.2% · n=83
  - Q2: realised 20.3% · predicted 39.6% · n=69
  - Q3: realised 14.1% · predicted 34.9% · n=78
  - Q4: realised 17.3% · predicted 38.2% · n=81
  - Q5: realised 42.2% · predicted 48.3% · n=45

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
