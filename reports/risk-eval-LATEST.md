# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-11-26

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W48**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 785

- score -> |MAE| (drawdown depth): rho=+0.182 CI[+0.061,+0.288] n=785 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.287 CI[+0.166,+0.394] n=785 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.040 CI[-0.160,+0.075] n=785 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.066 CI[-0.175,+0.032] n=785 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **16** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 681

- score -> |MAE| (drawdown depth): rho=+0.241 CI[+0.170,+0.312] n=681 tickers=468 SIG
- score -> range (MFE-MAE): rho=+0.294 CI[+0.221,+0.363] n=681 tickers=468 SIG
- score -> same-day return *(must stay ns)*: rho=+0.011 CI[-0.068,+0.089] n=681 tickers=468 ns
- score -> 5-day return *(must stay ns)*: rho=-0.217 CI[-0.287,-0.145] n=681 tickers=468 SIG
- consecutive weekly snapshots with positive |MAE| rho: **16** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.217), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.2058** vs no-skill baseline **0.2099** -> BEATS baseline
- realised P(MAE <= -20%): Q1 24.4% vs Q5 53.3%
- Q5-Q1 gap: 28.9% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 24.4% · predicted 20.2% · n=164
  - Q2: realised 18.8% · predicted 39.6% · n=144
  - Q3: realised 24.0% · predicted 34.9% · n=167
  - Q4: realised 27.9% · predicted 38.2% · n=190
  - Q5: realised 53.3% · predicted 48.3% · n=120

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
