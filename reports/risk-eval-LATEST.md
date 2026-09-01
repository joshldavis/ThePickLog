# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-09-01

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W36**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 241

- score -> |MAE| (drawdown depth): rho=+0.033 CI[-0.120,+0.189] n=241 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.236 CI[+0.096,+0.330] n=241 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.001 CI[-0.122,+0.111] n=241 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.080 CI[-0.095,+0.223] n=241 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **4** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 170

- score -> |MAE| (drawdown depth): rho=+0.250 CI[+0.101,+0.397] n=170 tickers=147 SIG
- score -> range (MFE-MAE): rho=+0.344 CI[+0.182,+0.489] n=170 tickers=147 SIG
- score -> same-day return *(must stay ns)*: rho=+0.085 CI[-0.073,+0.243] n=170 tickers=147 ns
- score -> 5-day return *(must stay ns)*: rho=-0.196 CI[-0.352,-0.030] n=170 tickers=147 SIG
- consecutive weekly snapshots with positive |MAE| rho: **4** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1794** vs no-skill baseline **0.1794** -> BEATS baseline
- realised P(MAE <= -20%): Q1 18.9% vs Q5 31.0%
- Q5-Q1 gap: 12.2% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 18.9% · predicted 20.2% · n=53
  - Q2: realised 18.2% · predicted 39.6% · n=44
  - Q3: realised 13.0% · predicted 34.9% · n=54
  - Q4: realised 13.1% · predicted 38.2% · n=61
  - Q5: realised 31.0% · predicted 48.3% · n=29

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
