# ThePickLog — H-RISK1 / H-RISK2 forward evaluation · 2026-11-27

Pre-registered **2026-07-29** (HYPOTHESES.md batch #6). Only picks with `trading_date` strictly after that date are counted. Snapshot week: **2026-W48**.

**H-RISK1** — the composite score ranks *magnitude* (drawdown depth, total range), not *direction*. The claim has two halves and BOTH must hold: the magnitude correlations are positive and clear the ticker-clustered 95% CI, **and** the signed-return correlation stays non-significant — at **both** horizons, same-day and 5-day (enforced in code since the 2026-09-25 amendment; before that only same-day was checked, though both were always labelled *must stay ns*).

### v0.2-yf — n_post = 792

- score -> |MAE| (drawdown depth): rho=+0.176 CI[+0.059,+0.282] n=792 tickers=16 SIG
- score -> range (MFE-MAE): rho=+0.287 CI[+0.167,+0.393] n=792 tickers=16 SIG
- score -> same-day return *(must stay ns)*: rho=-0.035 CI[-0.154,+0.077] n=792 tickers=16 ns
- score -> 5-day return *(must stay ns)*: rho=-0.063 CI[-0.171,+0.032] n=792 tickers=16 ns
- consecutive weekly snapshots with positive |MAE| rho: **16** (need >= 3)

**v0.2-yf verdict: PASSES all H-RISK1 criteria**

### v0.3-yf — n_post = 691

- score -> |MAE| (drawdown depth): rho=+0.239 CI[+0.168,+0.311] n=691 tickers=474 SIG
- score -> range (MFE-MAE): rho=+0.297 CI[+0.226,+0.368] n=691 tickers=474 SIG
- score -> same-day return *(must stay ns)*: rho=+0.016 CI[-0.063,+0.091] n=691 tickers=474 ns
- score -> 5-day return *(must stay ns)*: rho=-0.215 CI[-0.287,-0.141] n=691 tickers=474 SIG
- consecutive weekly snapshots with positive |MAE| rho: **16** (need >= 3)

**v0.3-yf verdict: not yet established** — score -> 5-day return is significant (rho -0.215), so the score also carries DIRECTION information; that fails H-RISK1 as registered

---

**H-RISK2** — is the gauge *calibrated*, not merely correlated? v0.2 cohort only; the frozen probabilities are explicitly NOT transferable to v0.3 (different score distributions — see H-STR3).

- Brier (frozen model) **0.2064** vs no-skill baseline **0.2102** -> BEATS baseline
- realised P(MAE <= -20%): Q1 24.2% vs Q5 52.5%
- Q5-Q1 gap: 28.2% (need >= 15%) -> OK
- per-quintile realised / predicted / n:

  - Q1: realised 24.2% · predicted 20.2% · n=165
  - Q2: realised 18.8% · predicted 39.6% · n=144
  - Q3: realised 25.3% · predicted 34.9% · n=170
  - Q4: realised 27.7% · predicted 38.2% · n=191
  - Q5: realised 52.5% · predicted 48.3% · n=122

**H-RISK2 verdict: PASSES**

---

**Registered framing — do not drop it.** A confirmation here demonstrates *volatility persistence*, a long-documented market regularity, and is **not evidence of alpha**. It does not reopen Gate 1 (failed 2026-07-29). Knowing how far a name will move says nothing about which way it will move — which is precisely what the signed-return rows above keep testing.

_Not investment advice. Frozen constants live at the top of `risk_eval.py`; changing them voids the pre-registration._
