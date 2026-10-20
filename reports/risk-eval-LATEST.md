# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-10-20

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W43**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 540

- score -> |MAE| (drawdown depth): rho=+0.203 CI[+0.057,+0.341] n=540 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.334 CI[+0.177,+0.468] n=540 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.047 CI[-0.165,+0.058] n=540 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.051 CI[-0.198,+0.068] n=540 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **11** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 433

- score -> |MAE| (drawdown depth): rho=+0.259 CI[+0.172,+0.344] n=433 tickers=324 SIG
- score -> range (MFE-MAE): rho=+0.341 CI[+0.247,+0.424] n=433 tickers=324 SIG
- score -> same-day return *(must stay ns)*: rho=+0.062 CI[-0.035,+0.152] n=433 tickers=324 ns
- score -> 5-day return *(must stay ns)*: rho=-0.194 CI[-0.285,-0.098] n=433 tickers=324 SIG
- consecutive weekly snapshots with positive |MAE| rho: **11** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.194), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1909** vs no-skill baseline **0.1981** -> BEATS baseline
- realised P(MAE <= -20%): Q1 18.8% vs Q5 51.2%
- Q5-Q1 gap: 32.4% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 18.8% · predicted 20.2% · n=117
  - Q2: realised 18.8% · predicted 39.6% · n=101
  - Q3: realised 17.0% · predicted 34.9% · n=112
  - Q4: realised 22.2% · predicted 38.2% · n=126
  - Q5: realised 51.2% · predicted 48.3% · n=84

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
