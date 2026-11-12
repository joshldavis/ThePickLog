# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-11-12

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W46**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 699

- score -> |MAE| (drawdown depth): rho=+0.215 CI[+0.075,+0.335] n=699 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.314 CI[+0.181,+0.425] n=699 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.038 CI[-0.158,+0.070] n=699 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.094 CI[-0.209,+0.014] n=699 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **14** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 583

- score -> |MAE| (drawdown depth): rho=+0.237 CI[+0.159,+0.311] n=583 tickers=406 SIG
- score -> range (MFE-MAE): rho=+0.278 CI[+0.200,+0.354] n=583 tickers=406 SIG
- score -> same-day return *(must stay ns)*: rho=+0.025 CI[-0.060,+0.107] n=583 tickers=406 ns
- score -> 5-day return *(must stay ns)*: rho=-0.217 CI[-0.294,-0.138] n=583 tickers=406 SIG
- consecutive weekly snapshots with positive |MAE| rho: **14** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.217), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1991** vs no-skill baseline **0.2058** -> BEATS baseline
- realised P(MAE <= -20%): Q1 19.9% vs Q5 51.9%
- Q5-Q1 gap: 32.0% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 19.9% · predicted 20.2% · n=146
  - Q2: realised 18.9% · predicted 39.6% · n=127
  - Q3: realised 23.0% · predicted 34.9% · n=152
  - Q4: realised 27.4% · predicted 38.2% · n=168
  - Q5: realised 51.9% · predicted 48.3% · n=106

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
