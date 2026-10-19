# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-10-19

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W43**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 515

- score -> |MAE| (drawdown depth): rho=+0.195 CI[+0.051,+0.325] n=515 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.331 CI[+0.172,+0.469] n=515 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.038 CI[-0.164,+0.070] n=515 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.034 CI[-0.168,+0.077] n=515 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **11** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 413

- score -> |MAE| (drawdown depth): rho=+0.283 CI[+0.197,+0.371] n=413 tickers=312 SIG
- score -> range (MFE-MAE): rho=+0.335 CI[+0.236,+0.424] n=413 tickers=312 SIG
- score -> same-day return *(must stay ns)*: rho=+0.043 CI[-0.056,+0.135] n=413 tickers=312 ns
- score -> 5-day return *(must stay ns)*: rho=-0.230 CI[-0.322,-0.134] n=413 tickers=312 SIG
- consecutive weekly snapshots with positive |MAE| rho: **11** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.230), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1891** vs no-skill baseline **0.1955** -> BEATS baseline
- realised P(MAE <= -20%): Q1 19.3% vs Q5 50.6%
- Q5-Q1 gap: 31.3% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 19.3% · predicted 20.2% · n=114
  - Q2: realised 17.9% · predicted 39.6% · n=95
  - Q3: realised 16.8% · predicted 34.9% · n=107
  - Q4: realised 19.2% · predicted 38.2% · n=120
  - Q5: realised 50.6% · predicted 48.3% · n=79

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
