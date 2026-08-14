# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-08-14

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W33**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 61

- score -> |MAE| (drawdown depth): rho=-0.048 CI[-0.335,+0.210] n=61 tickers=14 ns
- score -> range (MFE-MAE): rho=+0.182 CI[-0.191,+0.458] n=61 tickers=14 ns
- score -> same-day return *(must stay ns)*: rho=-0.047 CI[-0.319,+0.260] n=61 tickers=14 ns
- score -> 5-day return *(must stay ns)*: rho=+0.117 CI[-0.104,+0.383] n=61 tickers=14 ns
- consecutive weekly snapshots with positive |MAE| rho: **1** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 46

- score -> |MAE| (drawdown depth): rho=+0.103 CI[-0.173,+0.362] n=46 tickers=44 ns
- score -> range (MFE-MAE): rho=+0.192 CI[-0.135,+0.497] n=46 tickers=44 ns
- score -> same-day return *(must stay ns)*: rho=+0.052 CI[-0.279,+0.399] n=46 tickers=44 ns
- score -> 5-day return *(must stay ns)*: rho=-0.056 CI[-0.354,+0.267] n=46 tickers=44 ns
- consecutive weekly snapshots with positive |MAE| rho: **1** (need >= 3)

**v0.3-yf verdict: not yet established**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.2045** vs no-skill baseline **0.1900** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 31.2% vs Q5 14.3%
- Q5-Q1 gap: -17.0% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 31.2% · predicted 20.2% · n=16
  - Q2: realised 11.1% · predicted 39.6% · n=9
  - Q3: realised 25.0% · predicted 34.9% · n=12
  - Q4: realised 17.6% · predicted 38.2% · n=17
  - Q5: realised 14.3% · predicted 48.3% · n=7

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
