# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-11-11

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W46**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 690

- score -> |MAE| (drawdown depth): rho=+0.219 CI[+0.081,+0.338] n=690 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.315 CI[+0.179,+0.430] n=690 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.039 CI[-0.151,+0.064] n=690 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.105 CI[-0.218,+0.003] n=690 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **14** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 573

- score -> |MAE| (drawdown depth): rho=+0.234 CI[+0.156,+0.312] n=573 tickers=400 SIG
- score -> range (MFE-MAE): rho=+0.288 CI[+0.209,+0.362] n=573 tickers=400 SIG
- score -> same-day return *(must stay ns)*: rho=+0.036 CI[-0.050,+0.119] n=573 tickers=400 ns
- score -> 5-day return *(must stay ns)*: rho=-0.211 CI[-0.289,-0.132] n=573 tickers=400 SIG
- consecutive weekly snapshots with positive |MAE| rho: **14** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.211), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1987** vs no-skill baseline **0.2060** -> BEATS baseline
- realised P(MAE <= -20%): Q1 19.3% vs Q5 52.4%
- Q5-Q1 gap: 33.1% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 19.3% · predicted 20.2% · n=145
  - Q2: realised 19.0% · predicted 39.6% · n=126
  - Q3: realised 23.2% · predicted 34.9% · n=151
  - Q4: realised 27.9% · predicted 38.2% · n=165
  - Q5: realised 52.4% · predicted 48.3% · n=103

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
