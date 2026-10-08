# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-10-08

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W41**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 437

- score -> |MAE| (drawdown depth): rho=+0.139 CI[-0.001,+0.278] n=437 tickers=16 ns
- score -> range (MFE-MAE): rho=+0.295 CI[+0.136,+0.440] n=437 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.024 CI[-0.133,+0.084] n=437 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=+0.009 CI[-0.131,+0.128] n=437 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **9** (need >= 3)

**v0.2-yf verdict: not yet established** — score -> |MAE| is not positive and significant

### v0.3-yf — n_post = 343

- score -> |MAE| (drawdown depth): rho=+0.307 CI[+0.209,+0.406] n=343 tickers=269 SIG
- score -> range (MFE-MAE): rho=+0.345 CI[+0.245,+0.439] n=343 tickers=269 SIG
- score -> same-day return *(must stay ns)*: rho=+0.050 CI[-0.059,+0.152] n=343 tickers=269 ns
- score -> 5-day return *(must stay ns)*: rho=-0.248 CI[-0.353,-0.138] n=343 tickers=269 SIG
- consecutive weekly snapshots with positive |MAE| rho: **9** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.248), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1889** vs no-skill baseline **0.1931** -> BEATS baseline
- realised P(MAE <= -20%): Q1 21.4% vs Q5 48.4%
- Q5-Q1 gap: 27.0% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 21.4% · predicted 20.2% · n=103
  - Q2: realised 18.8% · predicted 39.6% · n=80
  - Q3: realised 15.7% · predicted 34.9% · n=89
  - Q4: realised 16.5% · predicted 38.2% · n=103
  - Q5: realised 48.4% · predicted 48.3% · n=62

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
