# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-10-14

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W42**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 483

- score -> |MAE| (drawdown depth): rho=+0.183 CI[+0.043,+0.314] n=483 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.332 CI[+0.172,+0.474] n=483 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.034 CI[-0.146,+0.067] n=483 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.015 CI[-0.151,+0.095] n=483 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **10** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 383

- score -> |MAE| (drawdown depth): rho=+0.282 CI[+0.187,+0.372] n=383 tickers=296 SIG
- score -> range (MFE-MAE): rho=+0.319 CI[+0.219,+0.413] n=383 tickers=296 SIG
- score -> same-day return *(must stay ns)*: rho=+0.059 CI[-0.047,+0.157] n=383 tickers=296 ns
- score -> 5-day return *(must stay ns)*: rho=-0.232 CI[-0.327,-0.132] n=383 tickers=296 SIG
- consecutive weekly snapshots with positive |MAE| rho: **10** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.232), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.1869** vs no-skill baseline **0.1929** -> BEATS baseline
- realised P(MAE <= -20%): Q1 19.5% vs Q5 49.3%
- Q5-Q1 gap: 29.8% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 19.5% · predicted 20.2% · n=113
  - Q2: realised 17.0% · predicted 39.6% · n=88
  - Q3: realised 16.0% · predicted 34.9% · n=100
  - Q4: realised 17.4% · predicted 38.2% · n=109
  - Q5: realised 49.3% · predicted 48.3% · n=73

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
