# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-08-18

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W34**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 93

- score -> |MAE| (drawdown depth): rho=+0.067 CI[-0.124,+0.255] n=93 tickers=15 ns
- score -> range (MFE-MAE): rho=+0.132 CI[-0.114,+0.347] n=93 tickers=15 ns
- score -> same-day return *(must stay ns)*: rho=-0.077 CI[-0.266,+0.122] n=93 tickers=15 ns
- score -> 5-day return *(must stay ns)*: rho=+0.025 CI[-0.208,+0.255] n=93 tickers=15 ns
- consecutive weekly snapshots with positive |MAE| rho: **2** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 70

- score -> |MAE| (drawdown depth): rho=+0.177 CI[-0.052,+0.394] n=70 tickers=65 ns
- score -> range (MFE-MAE): rho=+0.261 CI[+0.008,+0.498] n=70 tickers=65 SIG
- score -> same-day return *(must stay ns)*: rho=+0.074 CI[-0.194,+0.338] n=70 tickers=65 ns
- score -> 5-day return *(must stay ns)*: rho=-0.131 CI[-0.365,+0.119] n=70 tickers=65 ns
- consecutive weekly snapshots with positive |MAE| rho: **2** (need >= 3)

**v0.3-yf verdict: not yet established**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1902** vs no-skill baseline **0.1876** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 22.7% vs Q5 27.3%
- Q5-Q1 gap: 4.5% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 22.7% · predicted 20.2% · n=22
  - Q2: realised 30.8% · predicted 39.6% · n=13
  - Q3: realised 16.7% · predicted 34.9% · n=18
  - Q4: realised 13.8% · predicted 38.2% · n=29
  - Q5: realised 27.3% · predicted 48.3% · n=11

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
