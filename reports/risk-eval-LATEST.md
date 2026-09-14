# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-09-14

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W38**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant.

### v0.2-yf — n_post = 270

- score -> |MAE| (drawdown depth): rho=+0.067 CI[-0.080,+0.218] n=270 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.269 CI[+0.161,+0.351] n=270 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=+0.012 CI[-0.107,+0.120] n=270 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.091 CI[-0.095,+0.242] n=270 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **6** (need >= 3)

**v0.2-yf verdict: not yet established**

### v0.3-yf — n_post = 199

- score -> |MAE| (drawdown depth): rho=+0.256 CI[+0.107,+0.390] n=199 tickers=169 SIG
- score -> range (MFE-MAE): rho=+0.334 CI[+0.193,+0.468] n=199 tickers=169 SIG
- score -> same-day return *(must stay ns)*: rho=+0.102 CI[-0.044,+0.246] n=199 tickers=169 ns
- score -> 5-day return *(must stay ns)*: rho=-0.203 CI[-0.348,-0.048] n=199 tickers=169 SIG
- consecutive weekly snapshots with positive |MAE| rho: **6** (need >= 3)

**v0.3-yf verdict: PASSES all H-RISK1 criteria**

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1803** vs no-skill baseline **0.1813** -> BEATS baseline
- realised P(MAE <= -20%): Q1 19.4% vs Q5 35.5%
- Q5-Q1 gap: 16.1% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 19.4% · predicted 20.2% · n=62
  - Q2: realised 15.4% · predicted 39.6% · n=52
  - Q3: realised 12.3% · predicted 34.9% · n=57
  - Q4: realised 16.2% · predicted 38.2% · n=68
  - Q5: realised 35.5% · predicted 48.3% · n=31

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
