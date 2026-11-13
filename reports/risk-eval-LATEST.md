# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-11-13

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W46**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 709

- score -> |MAE| (drawdown depth): rho=+0.207 CI[+0.066,+0.329] n=709 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.309 CI[+0.178,+0.419] n=709 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.042 CI[-0.167,+0.072] n=709 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.089 CI[-0.202,+0.022] n=709 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **14** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 593

- score -> |MAE| (drawdown depth): rho=+0.241 CI[+0.165,+0.317] n=593 tickers=414 SIG
- score -> range (MFE-MAE): rho=+0.279 CI[+0.200,+0.354] n=593 tickers=414 SIG
- score -> same-day return *(must stay ns)*: rho=+0.017 CI[-0.068,+0.098] n=593 tickers=414 ns
- score -> 5-day return *(must stay ns)*: rho=-0.224 CI[-0.300,-0.148] n=593 tickers=414 SIG
- consecutive weekly snapshots with positive |MAE| rho: **14** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.224), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.2002** vs no-skill baseline **0.2063** -> BEATS baseline
- realised P(MAE <= -20%): Q1 20.9% vs Q5 52.3%
- Q5-Q1 gap: 31.4% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 20.9% · predicted 20.2% · n=148
  - Q2: realised 18.6% · predicted 39.6% · n=129
  - Q3: realised 23.1% · predicted 34.9% · n=156
  - Q4: realised 27.2% · predicted 38.2% · n=169
  - Q5: realised 52.3% · predicted 48.3% · n=107

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
