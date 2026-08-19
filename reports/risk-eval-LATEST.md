# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-08-19

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W34**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 123

- score -> |MAE| (drawdown depth): rho=+0.042 CI[-0.112,+0.200] n=123 tickers=15 ns
- score -> range (MFE-MAE): rho=+0.090 CI[-0.089,+0.239] n=123 tickers=15 ns
- score -> same-day return *(must stay ns)*: rho=-0.113 CI[-0.276,+0.064] n=123 tickers=15 ns
- score -> 5-day return *(must stay ns)*: rho=+0.066 CI[-0.112,+0.216] n=123 tickers=15 ns
- consecutive weekly snapshots with positive |MAE| rho: **2** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 90

- score -> |MAE| (drawdown depth): rho=+0.189 CI[-0.016,+0.385] n=90 tickers=84 ns
- score -> range (MFE-MAE): rho=+0.250 CI[+0.024,+0.464] n=90 tickers=84 SIG
- score -> same-day return *(must stay ns)*: rho=+0.112 CI[-0.126,+0.345] n=90 tickers=84 ns
- score -> 5-day return *(must stay ns)*: rho=-0.126 CI[-0.344,+0.093] n=90 tickers=84 ns
- consecutive weekly snapshots with positive |MAE| rho: **2** (need >= 3)

**v0.3-yf verdict: not yet established**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1844** vs no-skill baseline **0.1806** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 22.2% vs Q5 21.4%
- Q5-Q1 gap: -0.8% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 22.2% · predicted 20.2% · n=27
  - Q2: realised 27.8% · predicted 39.6% · n=18
  - Q3: realised 11.1% · predicted 34.9% · n=27
  - Q4: realised 13.5% · predicted 38.2% · n=37
  - Q5: realised 21.4% · predicted 48.3% · n=14

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
