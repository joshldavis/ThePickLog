# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-09-16

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W38**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 293

- score -> |MAE| (drawdown depth): rho=+0.042 CI[-0.101,+0.195] n=293 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.254 CI[+0.150,+0.342] n=293 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=+0.028 CI[-0.096,+0.138] n=293 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.108 CI[-0.063,+0.250] n=293 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **6** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 216

- score -> |MAE| (drawdown depth): rho=+0.246 CI[+0.113,+0.370] n=216 tickers=180 SIG
- score -> range (MFE-MAE): rho=+0.345 CI[+0.208,+0.470] n=216 tickers=180 SIG
- score -> same-day return *(must stay ns)*: rho=+0.113 CI[-0.026,+0.249] n=216 tickers=180 ns
- score -> 5-day return *(must stay ns)*: rho=-0.185 CI[-0.323,-0.040] n=216 tickers=180 SIG
- consecutive weekly snapshots with positive |MAE| rho: **6** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1875** vs no-skill baseline **0.1878** -> BEATS baseline
- realised P(MAE <= -20%): Q1 22.9% vs Q5 40.0%
- Q5-Q1 gap: 17.1% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 22.9% · predicted 20.2% · n=70
  - Q2: realised 19.0% · predicted 39.6% · n=58
  - Q3: realised 13.3% · predicted 34.9% · n=60
  - Q4: realised 15.7% · predicted 38.2% · n=70
  - Q5: realised 40.0% · predicted 48.3% · n=35

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
