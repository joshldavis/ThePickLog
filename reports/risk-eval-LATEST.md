# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-09-22

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W39**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 315

- score -> |MAE| (drawdown depth): rho=+0.035 CI[-0.109,+0.189] n=315 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.236 CI[+0.121,+0.343] n=315 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=+0.022 CI[-0.096,+0.125] n=315 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.112 CI[-0.067,+0.255] n=315 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **7** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 236

- score -> |MAE| (drawdown depth): rho=+0.265 CI[+0.135,+0.386] n=236 tickers=195 SIG
- score -> range (MFE-MAE): rho=+0.324 CI[+0.189,+0.449] n=236 tickers=195 SIG
- score -> same-day return *(must stay ns)*: rho=+0.078 CI[-0.058,+0.211] n=236 tickers=195 ns
- score -> 5-day return *(must stay ns)*: rho=-0.209 CI[-0.341,-0.067] n=236 tickers=195 SIG
- consecutive weekly snapshots with positive |MAE| rho: **7** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1957** vs no-skill baseline **0.1943** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 26.3% vs Q5 42.1%
- Q5-Q1 gap: 15.8% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 26.3% · predicted 20.2% · n=76
  - Q2: realised 21.9% · predicted 39.6% · n=64
  - Q3: realised 15.4% · predicted 34.9% · n=65
  - Q4: realised 16.7% · predicted 38.2% · n=72
  - Q5: realised 42.1% · predicted 48.3% · n=38

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
