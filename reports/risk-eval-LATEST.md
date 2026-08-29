# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-08-29

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W35**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 219

- score -> |MAE| (drawdown depth): rho=-0.002 CI[-0.148,+0.143] n=219 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.213 CI[+0.061,+0.320] n=219 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=+0.005 CI[-0.130,+0.134] n=219 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.097 CI[-0.061,+0.232] n=219 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **3** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 160

- score -> |MAE| (drawdown depth): rho=+0.273 CI[+0.126,+0.415] n=160 tickers=138 SIG
- score -> range (MFE-MAE): rho=+0.334 CI[+0.174,+0.481] n=160 tickers=138 SIG
- score -> same-day return *(must stay ns)*: rho=+0.073 CI[-0.095,+0.238] n=160 tickers=138 ns
- score -> 5-day return *(must stay ns)*: rho=-0.220 CI[-0.374,-0.051] n=160 tickers=138 SIG
- consecutive weekly snapshots with positive |MAE| rho: **3** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1838** vs no-skill baseline **0.1817** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 20.4% vs Q5 26.9%
- Q5-Q1 gap: 6.5% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 20.4% · predicted 20.2% · n=49
  - Q2: realised 20.0% · predicted 39.6% · n=40
  - Q3: realised 15.2% · predicted 34.9% · n=46
  - Q4: realised 13.8% · predicted 38.2% · n=58
  - Q5: realised 26.9% · predicted 48.3% · n=26

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
