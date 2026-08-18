# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-08-18

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W34**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 109

- score -> |MAE| (drawdown depth): rho=+0.066 CI[-0.112,+0.243] n=109 tickers=15 ns
- score -> range (MFE-MAE): rho=+0.102 CI[-0.122,+0.289] n=109 tickers=15 ns
- score -> same-day return *(must stay ns)*: rho=-0.100 CI[-0.288,+0.098] n=109 tickers=15 ns
- score -> 5-day return *(must stay ns)*: rho=+0.047 CI[-0.175,+0.260] n=109 tickers=15 ns
- consecutive weekly snapshots with positive |MAE| rho: **2** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 80

- score -> |MAE| (drawdown depth): rho=+0.172 CI[-0.041,+0.377] n=80 tickers=74 ns
- score -> range (MFE-MAE): rho=+0.265 CI[+0.027,+0.488] n=80 tickers=74 SIG
- score -> same-day return *(must stay ns)*: rho=+0.143 CI[-0.121,+0.388] n=80 tickers=74 ns
- score -> 5-day return *(must stay ns)*: rho=-0.105 CI[-0.337,+0.126] n=80 tickers=74 ns
- consecutive weekly snapshots with positive |MAE| rho: **2** (need >= 3)

**v0.3-yf verdict: not yet established**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1838** vs no-skill baseline **0.1819** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 20.0% vs Q5 23.1%
- Q5-Q1 gap: 3.1% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 20.0% · predicted 20.2% · n=25
  - Q2: realised 28.6% · predicted 39.6% · n=14
  - Q3: realised 13.6% · predicted 34.9% · n=22
  - Q4: realised 14.3% · predicted 38.2% · n=35
  - Q5: realised 23.1% · predicted 48.3% · n=13

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
