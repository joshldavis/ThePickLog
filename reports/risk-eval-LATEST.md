# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-08-25

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W35**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 179

- score -> |MAE| (drawdown depth): rho=-0.032 CI[-0.178,+0.107] n=179 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.212 CI[+0.045,+0.335] n=179 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.029 CI[-0.180,+0.117] n=179 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.150 CI[-0.012,+0.287] n=179 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **3** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 130

- score -> |MAE| (drawdown depth): rho=+0.244 CI[+0.069,+0.412] n=130 tickers=119 SIG
- score -> range (MFE-MAE): rho=+0.328 CI[+0.147,+0.492] n=130 tickers=119 SIG
- score -> same-day return *(must stay ns)*: rho=+0.104 CI[-0.081,+0.281] n=130 tickers=119 ns
- score -> 5-day return *(must stay ns)*: rho=-0.204 CI[-0.383,-0.018] n=130 tickers=119 SIG
- consecutive weekly snapshots with positive |MAE| rho: **3** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1850** vs no-skill baseline **0.1821** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 21.7% vs Q5 21.1%
- Q5-Q1 gap: -0.7% (need >= 15%) -> not met
- per-quintile realised / predicted / n:

  - Q1: realised 21.7% · predicted 20.2% · n=46
  - Q2: realised 23.3% · predicted 39.6% · n=30
  - Q3: realised 13.9% · predicted 34.9% · n=36
  - Q4: realised 14.6% · predicted 38.2% · n=48
  - Q5: realised 21.1% · predicted 48.3% · n=19

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
