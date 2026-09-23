# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-09-23

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W39**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 326

- score -> |MAE| (drawdown depth): rho=+0.046 CI[-0.099,+0.200] n=326 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.236 CI[+0.123,+0.345] n=326 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.000 CI[-0.107,+0.089] n=326 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.095 CI[-0.079,+0.228] n=326 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **7** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 245

- score -> |MAE| (drawdown depth): rho=+0.265 CI[+0.142,+0.382] n=245 tickers=203 SIG
- score -> range (MFE-MAE): rho=+0.339 CI[+0.214,+0.461] n=245 tickers=203 SIG
- score -> same-day return *(must stay ns)*: rho=+0.082 CI[-0.045,+0.209] n=245 tickers=203 ns
- score -> 5-day return *(must stay ns)*: rho=-0.199 CI[-0.331,-0.060] n=245 tickers=203 SIG
- consecutive weekly snapshots with positive |MAE| rho: **7** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1973** vs no-skill baseline **0.1964** -> does NOT beat baseline
- realised P(MAE <= -20%): Q1 26.9% vs Q5 45.0%
- Q5-Q1 gap: 18.1% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 26.9% · predicted 20.2% · n=78
  - Q2: realised 21.5% · predicted 39.6% · n=65
  - Q3: realised 14.9% · predicted 34.9% · n=67
  - Q4: realised 18.4% · predicted 38.2% · n=76
  - Q5: realised 45.0% · predicted 48.3% · n=40

**H-RISK2 verdict: not yet established**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
